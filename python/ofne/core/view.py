import uuid
from .packet import OFnPacket


class OFnView(object):
    __Instance = None

    def __new__(self):
        if OFnView.__Instance is None:
            OFnView.__Instance = super(OFnView, self).__new__()
            OFnView.__Instance.__packet = OFnPacket()
            OFnView.__Instance.__stamp = uuid.uuid4()

        return OFnView.__Instance

    def __init__(self):
        super(OFnView, self).__init__()

    def dump(self, packet):
        self.__packet = packet.copy()
        self.__stamp = uuid.uuid4()

    def packet(self):
        return self.__packet

    def stamp(self):
        return self.__stamp
