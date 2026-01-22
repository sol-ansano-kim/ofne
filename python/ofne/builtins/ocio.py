import PyOpenColorIO as ocio
from ofne import plugin


RAW_CONFIG = ocio.Config.CreateRaw()


class Exponent(plugin.OFnOp):
    def __init__(self):
        super(Exponent, self).__init__()

    def params(self):
        return {
            "gamma": plugin.OFnParamFloat(2.4, min=0.0, max=4.0),
            "offset": plugin.OFnParamFloat(0.055, min=0.0, max=0.9),
            "inverse": plugin.OFnParamBool(True)
        }

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        gamma = params.get("gamma")
        offset = params.get("offset")
        direction = ocio.TRANSFORM_DIR_INVERSE if params.get("inverse") else ocio.TRANSFORM_DIR_FORWARD
        proc = RAW_CONFIG.getProcessor(ocio.ExponentWithLinearTransform(gamma=[gamma, gamma, gamma, 1], offset=[offset, offset, offset, 0], negativeStyle=ocio.NEGATIVE_LINEAR, direction=direction)).getDefaultCPUProcessor()

        d = packetArray.packet(0).data()
        # TODO : sure?
        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)

# MEmO
# for it in ocio.BuiltinConfigRegistry().getBuiltinConfigs():
#     print(it[0])
# config = ocio.Config.CreateFromBuiltinConfig("cg-config-v1.0.0_aces-v1.3_ocio-v2.1")

# for it in ocio.BuiltinTransformRegistry().getBuiltins():
#     print(it)

# srcColorSpace: PyOpenColorIO.PyOpenColorIO.ColorSpace, dstColorSpace: PyOpenColorIO.PyOpenColorIO.ColorSpace
# srcColorSpaceName: str, dstColorSpaceName: str
# srcColorSpaceName: str, display: str, view: str, direction: PyOpenColorIO.PyOpenColorIO.TransformDirection
# namedTransform: PyOpenColorIO.PyOpenColorIO.NamedTransform, direction: PyOpenColorIO.PyOpenColorIO.TransformDirection
# namedTransformName: str, direction: PyOpenColorIO.PyOpenColorIO.TransformDirection
# transform: PyOpenColorIO.PyOpenColorIO.Transform, direction: PyOpenColorIO.PyOpenColorIO.TransformDirection
