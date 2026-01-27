from ofne import plugin
import numpy as np
import os
import OpenImageIO as oiio


class ReadImage(plugin.OFnOp):
    def __init__(self):
        super(ReadImage, self).__init__()

    def params(self):
        return [
            plugin.OFnParamStr("path", "")
        ]

    def needs(self):
        return 0

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        path = params.get("path")

        if not path:
            return plugin.OFnPacket()

        if not os.path.isfile(path):
            raise Exception("No such image file")

        buf = oiio.ImageBuf(path)

        return plugin.OFnPacket(data=buf.get_pixels(format=oiio.FLOAT))


class ConstantImage(plugin.OFnOp):
    def __init__(self):
        super(ConstantImage, self).__init__()

    def params(self):
        return [
            plugin.OFnParamInt("width", 512, min=2),
            plugin.OFnParamInt("height", 512, min=2),
            plugin.OFnParamFloat("R", 1.0),
            plugin.OFnParamFloat("G", 1.0),
            plugin.OFnParamFloat("B", 1.0),
            plugin.OFnParamFloat("A", 1.0),
        ]

    def needs(self):
        return 0

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        return plugin.OFnPacket(
            data=np.full(
                (
                    params.get("height"),
                    params.get("width"),
                    4
                ),
                [
                    params.get("R"),
                    params.get("G"),
                    params.get("B"),
                    params.get("A")
                ],
                dtype=np.float32
            )
        )
