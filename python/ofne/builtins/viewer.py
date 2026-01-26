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
        resource.OFnViewResource().dump(packetArray.packet(0))

    def unique(self):
        return True
