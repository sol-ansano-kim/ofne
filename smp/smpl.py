from ofne.core import packet
from ofne.core import op
from ofne.core import param
import numpy as np


class PlusOp(op.OFnOp):
    def __init__(self):
        super(PlusOp, self).__init__()

    def params(self):
        return []

    def needs(self):
        return 2

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        return packet.OFnPacket(data=packetArray.packet(0).data() + packetArray.packet(1).data())


class MakeNums(op.OFnOp):
    def __init__(self):
        super(MakeNums, self).__init__()

    def params(self):
        return [
            param.OFnParamInt("count", min=0),
            param.OFnParamFloat("num", 0.0)
        ]

    def needs(self):
        return 0

    def packetable(self):
        return True

    def operate(self, params, packetArray):
        return packet.OFnPacket(data=np.array([params.get("num")] * params.get("count")))


class Print(op.OFnOp):
    def __init__(self):
        super(Print, self).__init__()

    def needs(self):
        return 1

    def packetable(self):
        return False

    def params(self):
        return []

    def operate(self, params, packetArray):
        print(packetArray.packet(0).data())