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
        self.__batch = None

        with open(os.path.join(os.path.dirname(__file__), "shaders/quad.vert.qsb"), "rb") as f:
            self.__vs = QtGui.QShader.fromSerialized(QtCore.QByteArray(f.read()))
        with open(os.path.join(os.path.dirname(__file__), "shaders/quad.frag.qsb"), "rb") as f:
            self.__fs = QtGui.QShader.fromSerialized(QtCore.QByteArray(f.read()))

        if not (self.__vs.isValid() and self.__fs.isValid()):
            raise Exception("SHADER ERROR")

        self.__sampler = self.__hardware.rhi().newSampler(
            QtGui.QRhiSampler.Linear,
            QtGui.QRhiSampler.Linear,
            QtGui.QRhiSampler.Linear,
            QtGui.QRhiSampler.ClampToEdge,
            QtGui.QRhiSampler.ClampToEdge,
            QtGui.QRhiSampler.ClampToEdge
        )
        self.__sampler.create()

        self.__updateTexture()

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

    def popBatch(self):
        b = self.__batch
        self.__batch = None

        return b

    def binding(self):
        return self.__binding

    def pipeline(self):
        return self.__pipeline

    def imageSize(self):
        s = self.__view.image().size()

        return (s.width(), s.height())

    def isDirty(self):
        if self.__view.isDirty():
            self.__updateTexture()
            return True

        return False

    def __updateTexture(self):
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
        layout.setBindings([QtGui.QRhiVertexInputBinding(16)]) # 4 floats * 4 bytes
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

        self.__batch = self.__hardware.rhi().nextResourceUpdateBatch()
        self.__batch.uploadTexture(self.__texture, self.__view.image())


class OFnUIGeometry(object):
    def __init__(self, hr):
        super(OFnUIGeometry, self).__init__()
        self.__hardware = hr
        self.__vbuffer = self.__hardware.rhi().newBuffer(
            QtGui.QRhiBuffer.Dynamic,
            QtGui.QRhiBuffer.VertexBuffer,
            96 # 6 vertices * 16bytes
        )
        self.__vbuffer.create()

        self.__batch = None

    def __del__(self):
        self.destroy()

    def destroy(self):
        if self.__vbuffer:
            self.__vbuffer.destroy()
            self.__vbuffer = None

    def acceptCommandBuffer(self, cbuffer):
        cbuffer.setVertexInput(0, [(self.__vbuffer, 0)])

    def popBatch(self):
        b = self.__batch
        self.__batch = None

        return b

    def updateGeometry(self, pixelWidth, pixelHeight, iWidth, iHeight, planePosX, planePosY, scale):
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
            (*p00, *uv00), (*p10, *uv10), (*p11, *uv11),
            (*p00, *uv00), (*p11, *uv11), (*p01, *uv01),
        ]
        data = struct.pack("<" + "f" * (4 * 6), *[f for v in verts for f in v])

        self.__batch = self.__hardware.rhi().nextResourceUpdateBatch()
        self.__batch.updateDynamicBuffer(self.__vbuffer, 0, len(data), data)


class OFnUIView(QtGui.QWindow):
    def __init__(self):
        super(OFnUIView, self).__init__()
        self.__test_switch = False

        # TODO : other platform
        rhi_impl = QtGui.QRhi.D3D11
        if sys.platform == "darwin":
            self.setSurfaceType(QtGui.QSurface.MetalSurface)
            rhi_impl = QtGui.QRhi.Metal

        self.__wait = False
        self.__hardware = OFnUIHardwareResources(self, rhi_impl)
        self.__tex_shader = OFnUITextureShader(self.__hardware)
        self.__vertices = OFnUIGeometry(self.__hardware)
        self.__scale = 1.0
        self.__move_anchor = None
        self.__img_pos = QtCore.QPointF(0, 0)
        self.__geom_dirty = True

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

        if delta > 0:
            self.__scale *= 1.05
        else:
            self.__scale *= 0.95

        self.__geom_dirty = True

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.__move_anchor = event.position()

    def mouseReleaseEvent(self, event):
        self.__move_anchor = None

    def mouseMoveEvent(self, event):
        if self.__move_anchor is not None:
            self.__img_pos += event.position() - self.__move_anchor
            self.__move_anchor = event.position()
            self.__geom_dirty = True

    def __updateGeometry(self):
        self.__vertices.updateGeometry(*(self.__hardware.pixelSize()), *(self.__tex_shader.imageSize()), self.__img_pos.x(), self.__img_pos.y(), self.__scale)

    def render(self):
        if self.__wait:
            return

        if not self.isExposed():
            return

        if not self.__hardware.readyToRender():
            return

        tex_dirty = self.__tex_shader.isDirty()
        if tex_dirty:
            self.__geom_dirty = True

        if not tex_dirty and not self.__geom_dirty:
            return

        if self.__hardware.beginFrame() != QtGui.QRhi.FrameOpSuccess:
            return

        if self.__geom_dirty:
            self.__updateGeometry()

        cbuffer = self.__hardware.cbuffer()
        rtarget = self.__hardware.rtarget()

        batch = None
        batch = self.__tex_shader.popBatch()
        gbatch = self.__vertices.popBatch()
        if batch is not None:
            if gbatch is not None:
                batch.merge(gbatch)
        else:
            batch = gbatch

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

        self.__geom_dirty = True

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F:
            self.fit()


class OFnUIViewport(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(OFnUIViewport, self).__init__(parent=parent)
        self.__viewer = OFnUIView()
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.__format_selector = QtWidgets.QComboBox(parent=self)
        self.__format_selector.addItems(["SDR", "HDR10"])
        self.__format_selector.setMaximumWidth(100)
        layout.addWidget(QtWidgets.QWidget.createWindowContainer(self.__viewer))
        layout.addWidget(self.__format_selector)
        self.__format_selector.currentIndexChanged.connect(self.__formatChanged)

    def __formatChanged(self, *args):
        self.__viewer.setFormat(QtGui.QRhiSwapChain.Format.HDR10 if self.__format_selector.currentText() == "HDR10" else QtGui.QRhiSwapChain.Format.SDR)

    def fit(self):
        self.__viewer.fit()
