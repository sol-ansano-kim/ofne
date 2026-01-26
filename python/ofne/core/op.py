from . import abst
from .. import exceptions


class OFnOp(abst._OpBase):
    def __init__(self):
        super(OFnOp, self).__init__()

    @classmethod
    def type(cls):
        return cls.__name__

    def needs(self):
        raise exceptions.OFnNotImplementedError(self, "needs")

    def params(self):
        raise exceptions.OFnNotImplementedError(self, "params")

    def packetable(self):
        raise exceptions.OFnNotImplementedError(self, "packetable")

    def operate(self, params, packetArray):
        raise exceptions.OFnNotImplementedError(self, "operate")

    def unique(self):
        return False
