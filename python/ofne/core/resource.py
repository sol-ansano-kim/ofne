import uuid
from .packet import OFnPacket


class OFnViewResource(object):
    __Instance = None

    def __new__(self):
        if OFnViewResource.__Instance is None:
            OFnViewResource.__Instance = super(OFnViewResource, self).__new__(self)
            OFnViewResource.__Instance.__packet = OFnPacket()
            OFnViewResource.__Instance.__stamp = uuid.uuid4()

        return OFnViewResource.__Instance

    def __init__(self):
        super(OFnViewResource, self).__init__()

    def dump(self, packet):
        self.__packet = packet
        self.__stamp = uuid.uuid4()

    def packet(self):
        return self.__packet

    def stamp(self):
        return self.__stamp
