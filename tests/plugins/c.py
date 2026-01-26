from ofne.core import op


class MyOpA(op.OFnOp):
    def __init__(self):
        super(MyOpA, self).__init__()

    def needs(self):
        return 0

    def params(self):
        return []

    def packetable(self):
        return False
