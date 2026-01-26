from ofne.core import op
from ofne.core import param


class MyOpA(op.OFnOp):
    def __init__(self):
        super(MyOpA, self).__init__()

    def needs(self):
        return 0

    def params(self):
        return [
            param.OFnParamInt("count", min=0),
            param.OFnParamFloat("num")
        ]

    def packetable(self):
        return True
