import re
import PyOpenColorIO as ocio
from ofne import plugin


RAW_CONFIG = ocio.Config.CreateRaw()
BUILTIN_CONFIGS = []
for it in ocio.BuiltinConfigRegistry().getBuiltinConfigs():
    BUILTIN_CONFIGS.append(f"builtin:{it[0]}")

ROLES = {
    "role:aces_interchange": ocio.ROLE_INTERCHANGE_SCENE,
    "role:cie_xyz_d65_interchange": ocio.ROLE_INTERCHANGE_DISPLAY,
    "role:color_picking": ocio.ROLE_COLOR_PICKING,
    "role:color_timing": ocio.ROLE_COLOR_TIMING,
    "role:compositing_log": ocio.ROLE_COMPOSITING_LOG,
    "role:data": ocio.ROLE_DATA,
    "role:matte_paint": ocio.ROLE_MATTE_PAINT,
    "role:scene_linear": ocio.ROLE_SCENE_LINEAR,
    "role:texture_paint": ocio.ROLE_TEXTURE_PAINT
}

AKA = {
    "aka:ap0": ["lin_ap0"],
    "aka:ap1": ["lin_ap1"],
    "aka:cc": ["acescc_ap1"],
    "aka:cct": ["acescct_ap1"],
    "aka:srgb": ["srgb_tx"],
    "aka:srgb_linear": ["lin_srgb"],
    "aka:xyzd65": ["cie_xyz_d65_display", "cie_xyz_d65"]
}

INTERP_MAP = {
    "best": ocio.INTERP_BEST,
    "cubic": ocio.INTERP_CUBIC,
    "default": ocio.INTERP_DEFAULT,
    "linear": ocio.INTERP_LINEAR,
    "nearest": ocio.INTERP_NEAREST,
    "tetrahedral": ocio.INTERP_TETRAHEDRAL
}

BUILTIN_TRANSFORMS = [x[0] for x in ocio.BuiltinTransformRegistry().getBuiltins()]


def _validPacketData(data):
    shape = data.shape
    if len(shape) != 3:
        return False

    if shape[2] not in (3, 4):
        return False

    return True


def _getOCIO(path):
    if re.match(r"^builtin\:", path):
        path = re.sub(r"^builtin\:", "", path)
        return ocio.Config.CreateFromBuiltinConfig(path)
    else:
        return ocio.Config.CreateFromFile(path)


def _getColorSpaceName(config, inpt):
    global AKA

    if inpt in AKA:
        for al in AKA[inpt]:
            cs = config.getColorSpace(al)
            if cs:
                return cs.getName()

    return inpt


class OCIOMatrixTransform(plugin.OFnOp):
    def __init__(self):
        super(OCIOMatrixTransform, self).__init__()

    def params(self):
        return [
            plugin.OFnParamFloat("m00", default=1.0),
            plugin.OFnParamFloat("m01", default=0.0),
            plugin.OFnParamFloat("m02", default=0.0),
            plugin.OFnParamFloat("m03", default=0.0),
            plugin.OFnParamFloat("m10", default=0.0),
            plugin.OFnParamFloat("m11", default=1.0),
            plugin.OFnParamFloat("m12", default=0.0),
            plugin.OFnParamFloat("m13", default=0.0),
            plugin.OFnParamFloat("m20", default=0.0),
            plugin.OFnParamFloat("m21", default=0.0),
            plugin.OFnParamFloat("m22", default=1.0),
            plugin.OFnParamFloat("m23", default=0.0),
            plugin.OFnParamFloat("m30", default=0.0),
            plugin.OFnParamFloat("m31", default=0.0),
            plugin.OFnParamFloat("m32", default=0.0),
            plugin.OFnParamFloat("m33", default=1.0),
            plugin.OFnParamFloat("offset0", default=0.0),
            plugin.OFnParamFloat("offset1", default=0.0),
            plugin.OFnParamFloat("offset2", default=0.0),
            plugin.OFnParamFloat("offset3", default=0.0),
            plugin.OFnParamBool("inverse", False)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        d = packetArray.packet(0).data()

        if not _validPacketData(d):
            return plugin.OFnPacket()

        matrix = [
            params.get("m00"),
            params.get("m01"),
            params.get("m02"),
            params.get("m03"),
            params.get("m10"),
            params.get("m11"),
            params.get("m12"),
            params.get("m13"),
            params.get("m20"),
            params.get("m21"),
            params.get("m22"),
            params.get("m23"),
            params.get("m30"),
            params.get("m31"),
            params.get("m32"),
            params.get("m33")
        ]
        offset = [
            params.get("offset0"),
            params.get("offset1"),
            params.get("offset2"),
            params.get("offset3")
        ]

        direction = ocio.TRANSFORM_DIR_INVERSE if params.get("inverse") else ocio.TRANSFORM_DIR_FORWARD
        proc = RAW_CONFIG.getProcessor(
            ocio.MatrixTransform(
                matrix=matrix,
                offset=offset,
                direction=direction
            )
        ).getDefaultCPUProcessor()

        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)


class OCIOAllocationUniformTransform(plugin.OFnOp):
    def __init__(self):
        super(OCIOAllocationUniformTransform, self).__init__()

    def params(self):
        return [
            plugin.OFnParamFloat("min", 0.0),
            plugin.OFnParamFloat("max", 1.0),
            plugin.OFnParamBool("inverse", False)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        d = packetArray.packet(0).data()

        if not _validPacketData(d):
            return plugin.OFnPacket()

        direction = ocio.TRANSFORM_DIR_INVERSE if params.get("inverse") else ocio.TRANSFORM_DIR_FORWARD
        proc = RAW_CONFIG.getProcessor(
            ocio.AllocationTransform(
                ocio.ALLOCATION_UNIFORM,
                vars=[
                    params.get("min"),
                    params.get("max")
                ],
                direction=direction
            )
        ).getDefaultCPUProcessor()

        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)


class OCIOAllocationLog2Transform(plugin.OFnOp):
    def __init__(self):
        super(OCIOAllocationLog2Transform, self).__init__()

    def params(self):
        return [
            plugin.OFnParamFloat("min", 0.0),
            plugin.OFnParamFloat("max", 1.0),
            plugin.OFnParamFloat("offset", 0.0),
            plugin.OFnParamBool("inverse", False)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        d = packetArray.packet(0).data()

        if not _validPacketData(d):
            return plugin.OFnPacket()

        direction = ocio.TRANSFORM_DIR_INVERSE if params.get("inverse") else ocio.TRANSFORM_DIR_FORWARD
        proc = RAW_CONFIG.getProcessor(
            ocio.AllocationTransform(
                ocio.ALLOCATION_LG2,
                vars=[
                    params.get("min"),
                    params.get("max"),
                    params.get("offset")
                ],
                direction=direction
            )
        ).getDefaultCPUProcessor()

        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)


class OCIOFileTransform(plugin.OFnOp):
    def __init__(self):
        super(OCIOFileTransform, self).__init__()

    def params(self):
        return [
            plugin.OFnParamStr("src", ""),
            plugin.OFnParamStr("cccId", ""),
            plugin.OFnParamStr("interpolation", "linear", valueList=list(INTERP_MAP.keys()), enforceValueList=True),
            plugin.OFnParamBool("inverse", False)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        d = packetArray.packet(0).data()

        if not _validPacketData(d):
            return plugin.OFnPacket()

        direction = ocio.TRANSFORM_DIR_INVERSE if params.get("inverse") else ocio.TRANSFORM_DIR_FORWARD
        proc = RAW_CONFIG.getProcessor(
            ocio.FileTransform(
                src=params.get("src"),
                cccId=params.get("cccId"),
                interpolation=INTERP_MAP[params.get("interpolation")],
                direction=direction
            )
        ).getDefaultCPUProcessor()

        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)


class OCIOExponentTransform(plugin.OFnOp):
    def __init__(self):
        super(OCIOExponentTransform, self).__init__()

    def params(self):
        return [
            plugin.OFnParamFloat("gamma", 1.0),
            plugin.OFnParamBool("inverse", False)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        d = packetArray.packet(0).data()

        if not _validPacketData(d):
            return plugin.OFnPacket()

        gamma = params.get("gamma")
        direction = ocio.TRANSFORM_DIR_INVERSE if params.get("inverse") else ocio.TRANSFORM_DIR_FORWARD
        proc = RAW_CONFIG.getProcessor(ocio.ExponentTransform(value=[gamma, gamma, gamma, 1.0], negativeStyle=ocio.NEGATIVE_CLAMP, direction=direction)).getDefaultCPUProcessor()

        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)


class OCIOExponentWithLinearTransform(plugin.OFnOp):
    def __init__(self):
        super(OCIOExponentWithLinearTransform, self).__init__()

    def params(self):
        return [
            plugin.OFnParamFloat("gamma", 1.0, min=0.0, max=4.0),
            plugin.OFnParamFloat("offset", 0.0, min=0.0, max=0.9),
            plugin.OFnParamBool("inverse", False)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        d = packetArray.packet(0).data()

        if not _validPacketData(d):
            return plugin.OFnPacket()

        gamma = params.get("gamma")
        offset = params.get("offset")
        direction = ocio.TRANSFORM_DIR_INVERSE if params.get("inverse") else ocio.TRANSFORM_DIR_FORWARD
        proc = RAW_CONFIG.getProcessor(ocio.ExponentWithLinearTransform(gamma=[gamma, gamma, gamma, 1], offset=[offset, offset, offset, 0], negativeStyle=ocio.NEGATIVE_LINEAR, direction=direction)).getDefaultCPUProcessor()

        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)


class OCIOExposureContrastTransform(plugin.OFnOp):
    def __init__(self):
        super(OCIOExposureContrastTransform, self).__init__()

    def params(self):
        return [
            plugin.OFnParamFloat("exposure", 0.0),
            plugin.OFnParamFloat("contrast", 1.0),
            plugin.OFnParamFloat("gamma", 1.0),
            plugin.OFnParamFloat("pivot", 0.18),
            plugin.OFnParamFloat("logExposureStep", 0.088),
            plugin.OFnParamFloat("logMidGray", 0.435),
            plugin.OFnParamBool("inverse", False)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        ocio.ExposureContrastTransform()
        d = packetArray.packet(0).data()

        if not _validPacketData(d):
            return plugin.OFnPacket()

        trn = ocio.ExposureContrastTransform(
            exposure=params.get("exposure"),
            contrast=params.get("contrast"),
            gamma=params.get("gamma"),
            pivot=params.get("pivot"),
            logExposureStep=params.get("logExposureStep"),
            logMidGray=params.get("logMidGray"),
            direction=ocio.TRANSFORM_DIR_INVERSE if params.get("inverse") else ocio.TRANSFORM_DIR_FORWARD
        )
        proc = RAW_CONFIG.getProcessor(trn).getDefaultCPUProcessor()

        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)


class OCIOColorSpaceTransform(plugin.OFnOp):
    def __init__(self):
        super(OCIOColorSpaceTransform, self).__init__()

    def params(self):
        return [
            plugin.OFnParamPath("config", "", valueList=["${OCIO}"] + BUILTIN_CONFIGS),
            plugin.OFnParamStr("from", "", valueList=list(AKA.keys()), enforceValueList=False),
            plugin.OFnParamStr("to", "", valueList=list(AKA.keys()), enforceValueList=False)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        d = packetArray.packet(0).data()

        if not _validPacketData(d):
            return plugin.OFnPacket()

        config_path = params.get("config")
        src = params.get("from")
        dst = params.get("to")

        if not config_path or not src or not dst:
            return plugin.OFnPacket()

        config = _getOCIO(config_path)
        src = _getColorSpaceName(config, src)
        dst = _getColorSpaceName(config, dst)
        proc = config.getProcessor(src, dst).getDefaultCPUProcessor()

        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)


class OCIODisplayViewTransform(plugin.OFnOp):
    def __init__(self):
        super(OCIODisplayViewTransform, self).__init__()

    def params(self):
        return [
            plugin.OFnParamPath("config", "", valueList=["${OCIO}"] + BUILTIN_CONFIGS),
            plugin.OFnParamStr("from", "", valueList=list(AKA.keys()), enforceValueList=False),
            plugin.OFnParamStr("display", ""),
            plugin.OFnParamStr("view", ""),
            plugin.OFnParamBool("inverse", False)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        d = packetArray.packet(0).data()

        if not _validPacketData(d):
            return plugin.OFnPacket()

        config_path = params.get("config")
        src = params.get("from")
        display = params.get("display")
        view = params.get("view")
        direction = ocio.TRANSFORM_DIR_INVERSE if params.get("inverse") else ocio.TRANSFORM_DIR_FORWARD
        if not config_path or not src or not display or not view:
            return plugin.OFnPacket()

        config = _getOCIO(config_path)
        src = _getColorSpaceName(config, src)
        proc = None
        proc = config.getProcessor(src, display, view, direction).getDefaultCPUProcessor()

        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)


class OCIONamedTransform(plugin.OFnOp):
    def __init__(self):
        super(OCIONamedTransform, self).__init__()

    def params(self):
        return [
            plugin.OFnParamPath("config", "", valueList=["${OCIO}"] + BUILTIN_CONFIGS),
            plugin.OFnParamStr("name", ""),
            plugin.OFnParamBool("inverse", False)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        d = packetArray.packet(0).data()

        if not _validPacketData(d):
            return plugin.OFnPacket()

        config_path = params.get("config")
        name = params.get("name")
        direction = ocio.TRANSFORM_DIR_INVERSE if params.get("inverse") else ocio.TRANSFORM_DIR_FORWARD

        if not config_path or not name:
            return plugin.OFnPacket()

        config = _getOCIO(config_path)
        if config is None:
            return plugin.OFnPacket()

        nt = config.getNamedTransform(name)
        proc = config.getProcessor(nt, direction).getDefaultCPUProcessor()

        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)


class OCIOBuiltinTransform(plugin.OFnOp):
    def __init__(self):
        super(OCIOBuiltinTransform, self).__init__()

    def params(self):
        return [
            plugin.OFnParamStr("name", BUILTIN_TRANSFORMS[0], valueList=BUILTIN_TRANSFORMS, enforceValueList=True),
            plugin.OFnParamBool("inverse", False)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        d = packetArray.packet(0).data()

        if not _validPacketData(d):
            return plugin.OFnPacket()

        name = params.get("name")
        direction = ocio.TRANSFORM_DIR_INVERSE if params.get("inverse") else ocio.TRANSFORM_DIR_FORWARD

        if not name:
            return plugin.OFnPacket()

        proc = RAW_CONFIG.getProcessor(ocio.BuiltinTransform(name), direction).getDefaultCPUProcessor()

        func = proc.applyRGB if d.shape[2] == 3 else proc.applyRGBA
        func(d)

        return plugin.OFnPacket(data=d)
