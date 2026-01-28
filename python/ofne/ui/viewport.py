import os
import sys
import struct
from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui
from . import model


class OFnUIHardwareResources(object):
    def __init__(self, window, impl):
        super(OFnUIHardwareResources, self).__init__()
        self.__rendering = False
        self.__window = window
        self.__impl = impl
        self.__format = QtGui.QRhiSwapChain.Format.SDR
        self.__rhi = None
        self.__swapchain = None
        self.__render_pass = None
        self.__depth_stencil = None

        self.__createRhi()
        self.__genSwapchain()

    def __createRhi(self):
        if self.__impl == QtGui.QRhi.Vulkan:
            param = QtGui.QRhiVulkanInitParams()
        elif self.__impl == QtGui.QRhi.OpenGLES2:
            param = QtGui.QRhiGles2InitParams()
        elif self.__impl == QtGui.QRhi.D3D11:
            param = QtGui.QRhiD3D11InitParams()
        elif self.__impl == QtGui.QRhi.D3D12:
            param = QtGui.QRhiD3D12InitParams()
        elif self.__impl == QtGui.QRhi.Metal:
            param = QtGui.QRhiMetalInitParams()
        else:
            param = QtGui.QRhiNullInitParams()

        self.__rhi = QtGui.QRhi.create(self.__impl, param)

    def __genSwapchain(self):
        self.__resetResources()

        self.__swapchain = self.__rhi.newSwapChain()
        self.__swapchain.setWindow(self.__window)
        self.__swapchain.setFormat(self.__format)

        self.__depth_stencil = self.__rhi.newRenderBuffer(
            QtGui.QRhiRenderBuffer.Type.DepthStencil,
            QtCore.QSize(),
            1,
            QtGui.QRhiRenderBuffer.Flag.UsedWithSwapChainOnly
        )
        self.__depth_stencil.create()
        self.__swapchain.setDepthStencil(self.__depth_stencil)

        self.__render_pass = self.__swapchain.newCompatibleRenderPassDescriptor()
        self.__swapchain.setRenderPassDescriptor(self.__render_pass)

        self.__swapchain.createOrResize()

    def implementation(self):
        return self.__impl

    def rhi(self):
        return self.__rhi

    def swapchain(self):
        return self.__swapchain

    def pixelSize(self):
        s = self.__swapchain.currentPixelSize()

        return (s.width(), s.height())

    def readyToRender(self):
        if self.__rendering:
            return False

        if (self.__swapchain.currentPixelSize() != self.__swapchain.surfacePixelSize()) and not self.__swapchain.createOrResize():
            return False

        return True

    def beginFrame(self):
        self.__rendering = True
        return self.__rhi.beginFrame(self.__swapchain)

    def endFrame(self):
        self.__rendering = False
        return self.__rhi.endFrame(self.__swapchain)

    def cbuffer(self):
        return self.__swapchain.currentFrameCommandBuffer()

    def rtarget(self):
        return self.__swapchain.currentFrameRenderTarget()

    def renderPass(self):
        return self.__render_pass

    def setFormat(self, format):
        if self.__format != format:
            self.__format = format
            self.__genSwapchain()

    def __resetResources(self):
        if self.__depth_stencil:
            self.__depth_stencil.destroy()
            self.__depth_stencil = None
        if self.__render_pass:
            self.__render_pass.destroy()
            self.__render_pass = None
        if self.__swapchain:
            self.__swapchain.destroy()
            self.__swapchain = None

    def destroy(self):
        self.__resetResources()

        if self.__rhi:
            self.__rhi = None

    def __del__(self):
        self.destroy()


class OFnUITextureShader(object):
    def __init__(self, hr):
        super(OFnUITextureShader, self).__init__()
        self.__view = model.OFnUIViewResource()
        self.__hardware = hr
        self.__texture = None
        self.__binding = None
        self.__pipeline = None

        with open(os.path.join(os.path.dirname(__file__), "shaders/quad.vert.qsb"), "rb") as f:
            self.__vs = QtGui.QShader.fromSerialized(QtCore.QByteArray(f.read()))
        with open(os.path.join(os.path.dirname(__file__), "shaders/quad.frag.qsb"), "rb") as f:
            self.__fs = QtGui.QShader.fromSerialized(QtCore.QByteArray(f.read()))

        if not (self.__vs.isValid() and self.__fs.isValid()):
            raise Exception("SHADER ERROR")

        self.__sampler = self.__hardware.rhi().newSampler(
            QtGui.QRhiSampler.Nearest,
            QtGui.QRhiSampler.Nearest,
            QtGui.QRhiSampler.None_,
            QtGui.QRhiSampler.ClampToEdge,
            QtGui.QRhiSampler.ClampToEdge,
            QtGui.QRhiSampler.ClampToEdge
        )
        self.__sampler.create()

    def getPixelValues(self, x, y):
        return self.__view.getPixelValues(x, y)

    def __del__(self):
        self.destroy()

    def destroy(self):
        self.__resetResources()

        if self.__sampler:
            self.__sampler.destroy()
            self.__sampler = None

    def __resetResources(self):
        if self.__texture:
            self.__texture.destroy()
            self.__texture = None
        if self.__binding:
            self.__binding.destroy()
            self.__binding = None
        if self.__pipeline:
            self.__pipeline.destroy()
            self.__pipeline = None

    def acceptCommandBuffer(self, cbuffer):
        cbuffer.setGraphicsPipeline(self.__pipeline)
        cbuffer.setShaderResources(self.__binding)

    def binding(self):
        return self.__binding

    def pipeline(self):
        return self.__pipeline

    def imageSize(self):
        s = self.__view.image().size()

        return (s.width(), s.height())

    def isDirty(self):
        if self.__view.isDirty():
            return True

        return False

    def updateTexture(self, batch):
        self.__resetResources()

        self.__texture = self.__hardware.rhi().newTexture(QtGui.QRhiTexture.RGBA32F, self.__view.image().size(), 1)
        self.__texture.create()

        self.__binding = self.__hardware.rhi().newShaderResourceBindings()
        self.__binding.setBindings(
            [
                QtGui.QRhiShaderResourceBinding.sampledTexture(
                    0,
                    QtGui.QRhiShaderResourceBinding.FragmentStage,
                    self.__texture,
                    self.__sampler
                )
            ]
        )
        self.__binding.create()

        self.__pipeline = self.__hardware.rhi().newGraphicsPipeline()
        self.__pipeline.setShaderStages(
            [
                QtGui.QRhiShaderStage(
                    QtGui.QRhiShaderStage.Type.Vertex,
                    self.__vs
                ),
                QtGui.QRhiShaderStage(
                    QtGui.QRhiShaderStage.Type.Fragment,
                    self.__fs
                )
            ]
        )
        self.__pipeline.setRenderPassDescriptor(self.__hardware.renderPass())
        self.__pipeline.setSampleCount(self.__hardware.swapchain().sampleCount())

        layout = QtGui.QRhiVertexInputLayout()
        layout.setBindings([QtGui.QRhiVertexInputBinding(16)])
        layout.setAttributes(
            [
                QtGui.QRhiVertexInputAttribute(
                    0,
                    0,
                    QtGui.QRhiVertexInputAttribute.Float2,
                    0
                ),
                QtGui.QRhiVertexInputAttribute(0,
                    1,
                    QtGui.QRhiVertexInputAttribute.Float2,
                    8
                )
            ]
        )

        self.__pipeline.setVertexInputLayout(layout)
        self.__pipeline.setTopology(QtGui.QRhiGraphicsPipeline.Topology.Triangles)
        self.__pipeline.setShaderResourceBindings(self.__binding)
        self.__pipeline.create()

        batch.uploadTexture(self.__texture, self.__view.image())


class OFnUIAimShader(object):
    def __init__(self, hr):
        self.__hardware = hr
        self.__pipeline = None
        self.__binding = None

        with open(os.path.join(os.path.dirname(__file__), "shaders/aim.vert.qsb"), "rb") as f:
            self.__vs = QtGui.QShader.fromSerialized(QtCore.QByteArray(f.read()))
        with open(os.path.join(os.path.dirname(__file__), "shaders/aim.frag.qsb"), "rb") as f:
            self.__fs = QtGui.QShader.fromSerialized(QtCore.QByteArray(f.read()))

        if not (self.__vs.isValid() and self.__fs.isValid()):
            raise RuntimeError("AIM SHADER ERROR")

        self.updateShader()

    def __del__(self):
        self.destroy()

    def destroy(self):
        self.__resetResources()

    def __resetResources(self):
        if self.__binding:
            self.__binding.destroy()
            self.__binding = None

        if self.__pipeline:
            self.__pipeline.destroy()
            self.__pipeline = None

    def acceptCommandBuffer(self, cbuffer):
        cbuffer.setGraphicsPipeline(self.__pipeline)
        cbuffer.setShaderResources(self.__binding)

    def updateShader(self):
        self.__resetResources()

        self.__binding = self.__hardware.rhi().newShaderResourceBindings()
        self.__binding.create()

        self.__pipeline = self.__hardware.rhi().newGraphicsPipeline()
        self.__pipeline.setShaderStages([
            QtGui.QRhiShaderStage(
                QtGui.QRhiShaderStage.Vertex, self.__vs
            ),
            QtGui.QRhiShaderStage(
                QtGui.QRhiShaderStage.Fragment, self.__fs
            )
        ])

        self.__pipeline.setRenderPassDescriptor(self.__hardware.renderPass())
        self.__pipeline.setTopology(QtGui.QRhiGraphicsPipeline.Triangles)

        layout = QtGui.QRhiVertexInputLayout()
        layout.setBindings([QtGui.QRhiVertexInputBinding(8)])

        layout.setAttributes([
            QtGui.QRhiVertexInputAttribute(
                0,
                0,
                QtGui.QRhiVertexInputAttribute.Float2,
                0
            )
        ])

        self.__pipeline.setVertexInputLayout(layout)
        self.__pipeline.setSampleCount(self.__hardware.swapchain().sampleCount())
        self.__pipeline.setShaderResourceBindings(self.__binding)

        self.__pipeline.create()


class OFnUIGeometry(object):
    def __init__(self, hr):
        super(OFnUIGeometry, self).__init__()
        self.__hardware = hr
        self.__vbuffer = self.__hardware.rhi().newBuffer(
            QtGui.QRhiBuffer.Dynamic,
            QtGui.QRhiBuffer.VertexBuffer,
            96
        )
        self.__vbuffer.create()

    def __del__(self):
        self.destroy()

    def destroy(self):
        if self.__vbuffer:
            self.__vbuffer.destroy()
            self.__vbuffer = None

    def acceptCommandBuffer(self, cbuffer):
        cbuffer.setVertexInput(0, [(self.__vbuffer, 0)])

    def updateGeometry(self, batch, pixelWidth, pixelHeight, iWidth, iHeight, planePosX, planePosY, scale):
        wf = 2.0 / max(1, pixelWidth)
        hf = -2.0 / max(1, pixelHeight)

        hw = iWidth * 0.5
        hh = iHeight * 0.5
        x0 = -hw * scale + planePosX
        y0 = -hh * scale + planePosY
        x1 = hw * scale + planePosX
        y1 = hh * scale + planePosY

        p00 = (x0 * wf, y0 * hf)
        p10 = (x1 * wf, y0 * hf)
        p11 = (x1 * wf, y1 * hf)
        p01 = (x0 * wf, y1 * hf)

        uv00 = (0.0, 0.0)
        uv10 = (1.0, 0.0)
        uv11 = (1.0, 1.0)
        uv01 = (0.0, 1.0)

        verts = [
            (*p00, *uv00),
            (*p10, *uv10),
            (*p11, *uv11),
            (*p00, *uv00),
            (*p11, *uv11),
            (*p01, *uv01),
        ]
        data = struct.pack("<" + "f" * (4 * 6), *[f for v in verts for f in v])

        batch.updateDynamicBuffer(self.__vbuffer, 0, len(data), data)


class OFnUIAimGeometry(object):
    def __init__(self, hr):
        super(OFnUIAimGeometry, self).__init__()
        self.__hardware = hr
        self.__vbuffer = self.__hardware.rhi().newBuffer(
            QtGui.QRhiBuffer.Dynamic,
            QtGui.QRhiBuffer.VertexBuffer,
            96
        )

        self.__vbuffer.create()

    def destroy(self):
        if self.__vbuffer:
            self.__vbuffer.destroy()
            self.__vbuffer = None

    def acceptCommandBuffer(self, cbuffer):
        cbuffer.setVertexInput(0, [(self.__vbuffer, 0)])

    def __quad(self, x0, y0, x1, y1):
        return [
            (x0, y0),
            (x1, y0),
            (x1, y1),
            (x0, y0),
            (x1, y1),
            (x0, y1),
        ]

    def updateGeometry(self, batch, iX, iY, pixelWidth, pixelHeight, iWidth, iHeight, imagePosX, imagePosY, scale):
        wf = 2.0 / max(1.0, pixelWidth)
        hf = -2.0 / max(1.0, pixelHeight)

        scrx = (iX + 0.5) - (iWidth * 0.5)
        sxru = (iY + 0.5) - (iHeight * 0.5)
        sx = scrx * scale + imagePosX
        sy = sxru * scale + imagePosY

        verts = []
        for px, py in self.__quad(sx - 12.0, sy - 1.0,sx + 12.0, sy + 1.0):
            verts.append(px * wf)
            verts.append(py * hf)

        for px, py in self.__quad(sx - 1.0, sy - 12.0,sx + 1.0, sy + 12.0):
            verts.append(px * wf)
            verts.append(py * hf)

        data = struct.pack("<" + "f" * len(verts), *verts)

        batch.updateDynamicBuffer(self.__vbuffer, 0, len(data), data)


class OFnUIView(QtGui.QWindow):
    aimPositionChanged = QtCore.Signal()

    def __init__(self):
        super(OFnUIView, self).__init__()
        # TODO : other platform
        rhi_impl = QtGui.QRhi.D3D11
        if sys.platform == "darwin":
            self.setSurfaceType(QtGui.QSurface.MetalSurface)
            rhi_impl = QtGui.QRhi.Metal

        self.__wait = False
        self.__hardware = OFnUIHardwareResources(self, rhi_impl)
        self.__tex_shader = OFnUITextureShader(self.__hardware)
        self.__vertices = OFnUIGeometry(self.__hardware)
        self.__aim = OFnUIAimGeometry(self.__hardware)
        self.__aim_shader = OFnUIAimShader(self.__hardware)
        self.__scale = 1.0
        self.__move_anchor = None
        self.__img_pos = QtCore.QPointF(0, 0)
        self.__geom_dirty = True
        self.__aim_pixel = None
        self.__aim_move = False

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.render)
        self.timer.start(16)  # about 60 FPS

        self.resize(1024, 1024)
        self.__hardware.swapchain().setWindow(self)

    def setFormat(self, format):
        self.__wait = True
        self.__hardware.setFormat(format)
        self.__wait = False
        self.__geom_dirty = True

    def resizeEvent(self, event):
        self.__geom_dirty = True

    def wheelEvent(self, event):
        delta = 0
        if event.source() == QtCore.Qt.MouseEventSynthesizedBySystem:
            delta = event.pixelDelta().y()
        else:
            delta = event.angleDelta().y()

        if delta == 0:
            return

        pixelWidth, pixelHeight = self.__hardware.pixelSize()
        if pixelWidth <= 0 or pixelHeight <= 0:
            return

        old_scale = self.__scale
        if delta > 0:
            new_scale = old_scale * 1.1
        else:
            new_scale = old_scale * 0.9

        new_scale = max(0.02, min(1000.0, new_scale))
        dpos = event.position() * self.devicePixelRatio()
        spos = QtCore.QPointF(dpos.x() - (pixelWidth * 0.5), dpos.y() - (pixelHeight * 0.5))
        self.__img_pos = spos - (spos - self.__img_pos) * (new_scale / max(1e-12, old_scale))
        self.__scale = new_scale
        self.__geom_dirty = True

    def getAimPixel(self):
        if self.__aim_pixel:
            colors = self.__tex_shader.getPixelValues(*self.__aim_pixel)
        else:
            colors = [(0, 0, 0, 0)] * 25

        return (self.__aim_pixel, colors)

    def __checkAim(self):
        if self.__aim_pixel:
            iWidth, iHeight = self.__tex_shader.imageSize()
            if iWidth <= 0 or iHeight <= 0:
                self.__aim_pixel = None
                return

            nx = int(min(max(0, int(self.__aim_pixel[0])), iWidth - 1))
            ny = int(min(max(0, int(self.__aim_pixel[1])), iHeight - 1))

            if nx != self.__aim_pixel[0] or ny != self.__aim_pixel[1]:
                self.__aim_pixel = (nx, ny)
                self.aimPositionChanged.emit()

    def __setAim(self, pos):
        pixelWidth, pixelHeight = self.__hardware.pixelSize()
        if pixelWidth <= 0 or pixelHeight <= 0:
            return

        iWidth, iHeight = self.__tex_shader.imageSize()
        if iWidth <= 0 or iHeight <= 0:
            return

        dpos = pos * self.devicePixelRatio()
        sx = dpos.x() - (pixelWidth * 0.5)
        sy = dpos.y() - (pixelHeight * 0.5)

        x0 = (iWidth * -0.5) * self.__scale + self.__img_pos.x()
        y0 = (iHeight * -0.5) * self.__scale + self.__img_pos.y()

        u = (sx - x0) / max(1e-12, (iWidth * self.__scale))
        v = (sy - y0) / max(1e-12, (iHeight * self.__scale))

        ix = u * iWidth
        iy = v * iHeight

        self.__aim_pixel = (
            int(min(max(0, int(ix)), iWidth - 1)),
            int(min(max(0, int(iy)), iHeight - 1))
        )

        self.__geom_dirty = True
        self.aimPositionChanged.emit()

    def mousePressEvent(self, event):
        pos = event.position()

        if event.button() == QtCore.Qt.MiddleButton or event.modifiers() == QtCore.Qt.AltModifier:
            self.__move_anchor = pos

        elif event.button() == QtCore.Qt.LeftButton:
            self.__aim_move = True
            self.__aim_pixel = None
            self.__setAim(pos)

    def mouseReleaseEvent(self, event):
        self.__aim_move = False
        self.__move_anchor = None

    def mouseMoveEvent(self, event):
        if self.__aim_move:
            self.__setAim(event.position())

        elif self.__move_anchor is not None:
            self.__img_pos += event.position() - self.__move_anchor
            self.__move_anchor = event.position()
            self.__geom_dirty = True

    def __updateGeometry(self, batch):
        self.__vertices.updateGeometry(batch, *(self.__hardware.pixelSize()), *(self.__tex_shader.imageSize()), self.__img_pos.x(), self.__img_pos.y(), self.__scale)

    def __updateAim(self, batch):
        self.__aim.updateGeometry(batch, *self.__aim_pixel, *(self.__hardware.pixelSize()), *(self.__tex_shader.imageSize()), self.__img_pos.x(), self.__img_pos.y(), self.__scale)

    def render(self):
        if self.__wait:
            return

        if not self.isExposed():
            return

        if not self.__hardware.readyToRender():
            return

        tex_dirty = self.__tex_shader.isDirty()
        if tex_dirty:
            self.__checkAim()
            self.__geom_dirty = True

        if not tex_dirty and not self.__geom_dirty:
            return

        if self.__hardware.beginFrame() != QtGui.QRhi.FrameOpSuccess:
            return

        batch = self.__hardware.rhi().nextResourceUpdateBatch()
        if tex_dirty:
            self.__tex_shader.updateTexture(batch)
            self.aimPositionChanged.emit()

        if self.__geom_dirty:
            self.__updateGeometry(batch)

            if self.__aim_pixel is not None:
                self.__updateAim(batch)

        cbuffer = self.__hardware.cbuffer()
        rtarget = self.__hardware.rtarget()

        cbuffer.beginPass(rtarget,
            QtGui.QColor.fromRgbF(
                0.125,
                0.125,
                0.125,
                1.0
            ),
            QtGui.QRhiDepthStencilClearValue(
                1.0,
                0
            ),
            batch)

        cbuffer.setViewport(QtGui.QRhiViewport(0, 0, rtarget.pixelSize().width(), rtarget.pixelSize().height()))

        self.__tex_shader.acceptCommandBuffer(cbuffer)
        self.__vertices.acceptCommandBuffer(cbuffer)
        cbuffer.draw(6)

        if self.__aim_pixel is not None:
            self.__aim_shader.acceptCommandBuffer(cbuffer)
            self.__aim.acceptCommandBuffer(cbuffer)
            cbuffer.draw(12)

        cbuffer.endPass()

        self.__hardware.endFrame()
        self.__geom_dirty = False

    def fit(self):
        ww, wh = self.__hardware.pixelSize()
        iw, ih = self.__tex_shader.imageSize()

        if ww > wh:
            ih = max(2, ih - 2)
            self.__scale = wh / ih
        else:
            iw = max(2, iw - 2)
            self.__scale = ww / iw

        self.__img_pos = QtCore.QPointF()
        self.__geom_dirty = True

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F:
            self.fit()


class OFnUIFormatSwitcher(QtWidgets.QComboBox):
    formatChanged = QtCore.Signal(QtGui.QRhiSwapChain.Format)

    def __init__(self, parent=None):
        super(OFnUIFormatSwitcher, self).__init__(parent=parent)
        self.addItems(["SDR", "HDR10"])
        self.setMaximumWidth(100)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.currentIndexChanged.connect(self.__formatChanged)

    def __formatChanged(self, *args):
        self.formatChanged.emit(QtGui.QRhiSwapChain.Format.HDR10 if self.currentText() == "HDR10" else QtGui.QRhiSwapChain.Format.SDR)


class OFnUIViewport(QtWidgets.QWidget):
    aimPositionChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super(OFnUIViewport, self).__init__(parent=parent)
        self.__view = OFnUIView()
        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QtWidgets.QWidget.createWindowContainer(self.__view))

        self.__view.aimPositionChanged.connect(self.aimPositionChanged)

    def fit(self):
        self.__view.fit()

    def setFormat(self, format):
        self.__view.setFormat(format)

    def getAimPixel(self):
        return self.__view.getAimPixel()


class OFnUIPixelDraw(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(OFnUIPixelDraw, self).__init__(parent=parent)
        self.setFixedSize(150, 150)
        self.__default_colors = [QtGui.QColor.fromRgbF(0.42, 0.42, 0.42)] * 25
        self.__colors = self.__default_colors[:]

    def setColors(self, colors):
        self.__colors = [QtGui.QColor.fromRgbF(*x[:3], min(1.0, x[3])) for x in colors]

    def reset(self):
        self.__colors = self.__default_colors[:]

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        for r in range(5):
            for c in range(5):
                x = c * 30
                y = r * 30
                painter.fillRect(x, y, 30, 30, self.__colors[r * 5 + c])

        painter.setPen(QtGui.QPen(QtCore.Qt.red))
        painter.drawLine(50, 75, 100, 75)
        painter.drawLine(75, 50, 75, 100)

        painter.end()


class OFnUIPixelInspector(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super(OFnUIPixelInspector, self).__init__(parent=parent)
        layout = QtWidgets.QGridLayout(self)
        self.__draw = OFnUIPixelDraw(parent=self)
        self.__px = QtWidgets.QLabel("------", parent=self)
        self.__py = QtWidgets.QLabel("------", parent=self)
        self.__r = QtWidgets.QLabel("------", parent=self)
        self.__g = QtWidgets.QLabel("------", parent=self)
        self.__b = QtWidgets.QLabel("------", parent=self)
        self.__a = QtWidgets.QLabel("------", parent=self)

        layout.addWidget(QtWidgets.QLabel("Pixel Inspector", parent=self), 0, 0)
        layout.addWidget(self.__draw, 1, 0)

        sl = QtWidgets.QHBoxLayout()
        sl.addWidget(QtWidgets.QLabel("X :", parent=self))
        sl.addWidget(self.__px)
        sl.addStretch(1)
        layout.addLayout(sl, 2, 0)
        sl = QtWidgets.QHBoxLayout()
        sl.addWidget(QtWidgets.QLabel("Y :", parent=self))
        sl.addWidget(self.__py)
        sl.addStretch(1)
        layout.addLayout(sl, 3, 0)
        sl = QtWidgets.QHBoxLayout()
        sl.addWidget(QtWidgets.QLabel("R :", parent=self))
        sl.addWidget(self.__r)
        sl.addStretch(1)
        layout.addLayout(sl, 4, 0)
        sl = QtWidgets.QHBoxLayout()
        sl.addWidget(QtWidgets.QLabel("G :", parent=self))
        sl.addWidget(self.__g)
        sl.addStretch(1)
        layout.addLayout(sl, 5, 0)
        sl = QtWidgets.QHBoxLayout()
        sl.addWidget(QtWidgets.QLabel("B :", parent=self))
        sl.addWidget(self.__b)
        sl.addStretch(1)
        layout.addLayout(sl, 6, 0)
        sl = QtWidgets.QHBoxLayout()
        sl.addWidget(QtWidgets.QLabel("A :", parent=self))
        sl.addWidget(self.__a)
        sl.addStretch(1)
        layout.addLayout(sl, 7, 0)

    def setPixel(self, x, y, colors):
        oncolor = [str(round(x, 4)) for x in colors[12]]
        self.__px.setText(str(x))
        self.__py.setText(str(y))
        self.__r.setText(oncolor[0])
        self.__g.setText(oncolor[1])
        self.__b.setText(oncolor[2])
        self.__a.setText(oncolor[3])
        self.__draw.setColors(colors)
        self.__draw.update()

    def reset(self):
        self.__px.setText("------")
        self.__py.setText("------")
        self.__r.setText("------")
        self.__g.setText("------")
        self.__b.setText("------")
        self.__draw.reset()


class OFnUIViewportSettings(QtWidgets.QWidget):
    formatChanged = QtCore.Signal(QtGui.QRhiSwapChain.Format)

    def __init__(self, parent=None):
        super(OFnUIViewportSettings, self).__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.__format_switcher = OFnUIFormatSwitcher(parent=self)
        self.__inspector = OFnUIPixelInspector(parent=self)
        layout.addWidget(self.__format_switcher)
        layout.addWidget(self.__inspector)
        layout.addStretch(1)
        self.__format_switcher.formatChanged.connect(self.formatChanged.emit)

    def setPixel(self, x, y, colors):
        self.__inspector.setPixel(x, y, colors)

    def resetInspector(self):
        self.__inspector.reset()
