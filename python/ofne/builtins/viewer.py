import numpy
from ofne import plugin
from ofne.core import resource


class Viewer(plugin.OFnOp):
    def __init__(self):
        super(Viewer, self).__init__()

    def params(self):
        return []

    def needs(self):
        return 1

    def packetable(self):
        return False

    def operate(self, params, packetArray):
        p = packetArray.packet(0)
        d = p.data()
        if d.dtype != numpy.float32:
            if numpy.issubdtype(d.dtype, numpy.integer):
                invf = numpy.float64(1 / float(numpy.iinfo(d.dtype).max))
                resource.OFnViewResource().dump(plugin.OFnPacket(data=(d * invf).astype(numpy.float32), metadata=p.metadata()))
            elif d.dtype == numpy.float64:
                f32 = numpy.finfo(numpy.float32)
                d = numpy.clip(d, f32.min, f32.max)
                resource.OFnViewResource().dump(plugin.OFnPacket(data=d.astype(numpy.float32), metadata=p.metadata()))
            else:
                resource.OFnViewResource().dump(plugin.OFnPacket(data=d.astype(numpy.float32), metadata=p.metadata()))
        else:
            resource.OFnViewResource().dump(p)

    def unique(self):
        return True
