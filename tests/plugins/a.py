from ofne.core import op
from ofne.core import param


class MyOpA(op.OFnOp):
    def __init__(self):
        super(MyOpA, self).__init__()

    def needs(self):
        return 0

    def params(self):
        return {
            "count": param.OFnParamInt(min=0),
            "num": param.OFnParamFloat()
        }

    def packetable(self):
        return True
