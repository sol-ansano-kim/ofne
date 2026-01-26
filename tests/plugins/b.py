from ofne.core import op


class MyOpB(op.OFnOp):
    def __init__(self):
        super(MyOpB, self).__init__()

    def needs(self):
        return 2

    def params(self):
        return []

    def packetable(self):
        return True


class MyOpC(object):
    pass
