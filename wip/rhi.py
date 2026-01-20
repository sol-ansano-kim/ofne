import os
import sys
import struct
from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui


class RhiWindow(QtGui.QWindow):
    def __init__(self):
        super().__init__()
        self.rhi = None
        self.swapchain = None
        self.render_pass = None
        self.depth_stencil = None

        self.has_swapchain = False
        self.newly_exposed = False
        self.not_exposed = True

        self.img = None
        self.img_size = QtCore.QSize(1, 1)
        self.tex = None
        self.sampler = None
        self.srb = None
        self.pso = None
        self.vbuf = None
        self._pending_upload = None
        self._pending_geom_update = None

        self.rect_pos = QtCore.QPointF(100.0, 100.0)
        self.rect_scale = 1.0
        self.dragging = False
        self.drag_offset = QtCore.QPointF(0.0, 0.0)
        self.geometry_dirty = True

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.render)
        self.timer.start(16)  # about 60 FPS

        self.resize(1024, 1024)

        self.init_rhi()
        self.init_resources()


    def init_rhi(self):
        params = QtGui.QRhiD3D11InitParams()
        self.rhi = QtGui.QRhi.create(QtGui.QRhi.Implementation.D3D11, params)

        self.swapchain = self.rhi.newSwapChain()
        self.swapchain.setWindow(self)

        self.swapchain.setFormat(QtGui.QRhiSwapChain.Format.HDR10)

        self.depth_stencil = self.rhi.newRenderBuffer(
            QtGui.QRhiRenderBuffer.Type.DepthStencil,
            QtCore.QSize(),
            1,
            QtGui.QRhiRenderBuffer.Flag.UsedWithSwapChainOnly
        )
        self.depth_stencil.create()
        self.swapchain.setDepthStencil(self.depth_stencil)

        self.render_pass = self.swapchain.newCompatibleRenderPassDescriptor()
        self.swapchain.setRenderPassDescriptor(self.render_pass)

        self.has_swapchain = self.swapchain.createOrResize()

    def init_resources(self):
        img = QtGui.QImage(os.path.join(os.path.dirname(__file__), "test.jpg"))
        if img.isNull():
            img = QtGui.QImage(64, 64, QtGui.QImage.Format_RGBA32FPx4)
            img.fill(QtGui.QColor(255, 255, 255))
        up_img = img.convertToFormat(QtGui.QImage.Format_RGBA32FPx4)
        self.img = up_img
        self.img_size = up_img.size()

        self.tex = self.rhi.newTexture(QtGui.QRhiTexture.RGBA32F, self.img_size, 1)
        self.tex.create()
        u = self.rhi.nextResourceUpdateBatch()
        u.uploadTexture(self.tex, up_img)
        self._pending_upload = u

        self.sampler = self.rhi.newSampler(
            QtGui.QRhiSampler.Linear, QtGui.QRhiSampler.Linear, QtGui.QRhiSampler.Linear,
            QtGui.QRhiSampler.ClampToEdge, QtGui.QRhiSampler.ClampToEdge, QtGui.QRhiSampler.ClampToEdge
        )
        self.sampler.create()

        self.srb = self.rhi.newShaderResourceBindings()
        self.srb.setBindings([
            QtGui.QRhiShaderResourceBinding.sampledTexture(
                0, QtGui.QRhiShaderResourceBinding.FragmentStage, self.tex, self.sampler
            )
        ])
        self.srb.create()


        with open(os.path.join(os.path.dirname(__file__), "shaders/quad.vert.qsb"), "rb") as f:
            vs_qsb = f.read()
        with open(os.path.join(os.path.dirname(__file__), "shaders/quad.frag.qsb"), "rb") as f:
            fs_qsb = f.read()

        vs = QtGui.QShader.fromSerialized(QtCore.QByteArray(vs_qsb))
        fs = QtGui.QShader.fromSerialized(QtCore.QByteArray(fs_qsb))
        if not (vs.isValid() and fs.isValid()):
            raise Exception("SHADER ERROR")

        self.pso = self.rhi.newGraphicsPipeline()
        self.pso.setShaderStages([
            QtGui.QRhiShaderStage(QtGui.QRhiShaderStage.Type.Vertex,   vs),
            QtGui.QRhiShaderStage(QtGui.QRhiShaderStage.Type.Fragment, fs)
        ])
        self.pso.setRenderPassDescriptor(self.render_pass)
        self.pso.setSampleCount(self.swapchain.sampleCount())

        layout = QtGui.QRhiVertexInputLayout()
        layout.setBindings([QtGui.QRhiVertexInputBinding(16)])  # 4 floats * 4 bytes
        layout.setAttributes([
            QtGui.QRhiVertexInputAttribute(0, 0, QtGui.QRhiVertexInputAttribute.Float2, 0),
            QtGui.QRhiVertexInputAttribute(0, 1, QtGui.QRhiVertexInputAttribute.Float2, 8)
        ])
        self.pso.setVertexInputLayout(layout)
        self.pso.setTopology(QtGui.QRhiGraphicsPipeline.Topology.Triangles)
        self.pso.setShaderResourceBindings(self.srb)
        self.pso.create()

        # 6 vertices * 16bytes
        self.vbuf = self.rhi.newBuffer(
            QtGui.QRhiBuffer.Dynamic,
            QtGui.QRhiBuffer.VertexBuffer,
            96
        )
        self.vbuf.create()
        self.geometry_dirty = True

    def release_rhi(self):
        self._pending_upload = None
        self._pending_geom_update = None
        self.vbuf = None
        self.pso = None
        self.srb = None
        self.sampler = None
        self.tex = None
        self.swapchain = None
        self.depth_stencil = None
        self.render_pass = None
        if self.rhi is not None:
            self.rhi = None


    def exposeEvent(self, ev):
        self.not_exposed = not self.isExposed()
        if self.isExposed():
            self.newly_exposed = True

    def resizeEvent(self, ev):
        pass

    def closeEvent(self, ev):
        self.release_rhi()
        super().closeEvent(ev)


    def _update_geometry(self):
        if self.rhi is None:
            return
        w = max(1, self.width())
        h = max(1, self.height())
        iw = self.img_size.width()
        ih = self.img_size.height()

        disp_w = iw * self.rect_scale
        disp_h = ih * self.rect_scale

        x0, y0 = self.rect_pos.x(), self.rect_pos.y()
        x1, y1 = x0 + disp_w, y0 + disp_h

        def to_ndc(px, py):
            ndc_x = (px / w) * 2.0 - 1.0
            ndc_y = 1.0 - (py / h) * 2.0
            return ndc_x, ndc_y

        p00 = to_ndc(x0, y0)
        p10 = to_ndc(x1, y0)
        p11 = to_ndc(x1, y1)
        p01 = to_ndc(x0, y1)

        uv00 = (0.0, 0.0)
        uv10 = (1.0, 0.0)
        uv11 = (1.0, 1.0)
        uv01 = (0.0, 1.0)

        verts = [
            (*p00, *uv00), (*p10, *uv10), (*p11, *uv11),
            (*p00, *uv00), (*p11, *uv11), (*p01, *uv01),
        ]
        data = struct.pack("<" + "f" * (4 * 6), *[f for v in verts for f in v])

        u = self.rhi.nextResourceUpdateBatch()
        u.updateDynamicBuffer(self.vbuf, 0, len(data), data)
        self._pending_geom_update = u
        self.geometry_dirty = False

    def _hit_rect(self, pos):
        iw, ih = self.img_size.width(), self.img_size.height()
        w = iw * self.rect_scale
        h = ih * self.rect_scale
        x0, y0 = self.rect_pos.x(), self.rect_pos.y()
        return (x0 <= pos.x() <= x0 + w) and (y0 <= pos.y() <= y0 + h)

    def _pixel_at(self, pos):
        if not self._hit_rect(pos):
            return (None, None)
        iw, ih = self.img_size.width(), self.img_size.height()
        local = pos - self.rect_pos
        u = local.x() / (iw * self.rect_scale)
        v = local.y() / (ih * self.rect_scale)
        u = max(0.0, min(0.999999, u))
        v = max(0.0, min(0.999999, v))
        return (int(u * iw), int(v * ih))

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            if self._hit_rect(e.position()):
                self.dragging = True
                self.drag_offset = e.position() - self.rect_pos
                px, py = self._pixel_at(e.position())
                if px is not None:
                    print(f"pixel = ({px}, {py})")
            else:
                self.dragging = False

    def mouseMoveEvent(self, e):
        if self.dragging:
            self.rect_pos = e.position() - self.drag_offset
            self.geometry_dirty = True

    def mouseReleaseEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self.dragging = False

    def wheelEvent(self, e):
        delta = e.angleDelta().y() / 120.0
        factor = 1.1 ** delta
        self.rect_scale = max(0.05, min(20.0, self.rect_scale * factor))
        self.geometry_dirty = True

    def render(self):
        if self.rhi is None or self.swapchain is None:
            return
        if self.not_exposed or not self.has_swapchain:
            return

        if self.rhi.isRecordingFrame():
            return

        if (self.swapchain.currentPixelSize() != self.swapchain.surfacePixelSize()) or self.newly_exposed:
            self.has_swapchain = self.swapchain.createOrResize()
            if not self.has_swapchain:
                return
            self.newly_exposed = False

        res = self.rhi.beginFrame(self.swapchain)
        if res != QtGui.QRhi.FrameOpSuccess:
            return

        cb = self.swapchain.currentFrameCommandBuffer()
        rt = self.swapchain.currentFrameRenderTarget()

        if self.geometry_dirty:
            self._update_geometry()

        update_batch = None
        if self._pending_upload and self._pending_geom_update:
            self._pending_upload.merge(self._pending_geom_update)
            update_batch = self._pending_upload
            self._pending_upload = None
            self._pending_geom_update = None
        elif self._pending_upload:
            update_batch = self._pending_upload
            self._pending_upload = None
        elif self._pending_geom_update:
            update_batch = self._pending_geom_update
            self._pending_geom_update = None

        cb.beginPass(rt, QtGui.QColor.fromRgbF(0.4, 0.2, 0.2, 1.0),
                     QtGui.QRhiDepthStencilClearValue(1.0, 0),
                     update_batch)

        output_size = rt.pixelSize()
        cb.setViewport(QtGui.QRhiViewport(0, 0, output_size.width(), output_size.height()))

        cb.setGraphicsPipeline(self.pso)
        cb.setShaderResources(self.srb)
        cb.setVertexInput(0, [(self.vbuf, 0)])
        cb.draw(6)

        cb.endPass()
        self.rhi.endFrame(self.swapchain)


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = RhiWindow()
    w = QtWidgets.QMainWindow()
    container = QtWidgets.QWidget.createWindowContainer(win)
    cnt = QtWidgets.QWidget(w)
    l = QtWidgets.QVBoxLayout(cnt)
    l.addWidget(container)
    w.setCentralWidget(cnt)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

