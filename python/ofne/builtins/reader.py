from ofne import plugin
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

        if not path or not os.path.isfile(path):
            return plugin.OFnPacket()

        try:
            buf = oiio.ImageBuf(path)
        except:
            return plugin.OFnPacket()

        return plugin.OFnPacket(data=buf.get_pixels(format=oiio.FLOAT))
