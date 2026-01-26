from . import abst
from ..core.packet import OFnPacket


class OFnGraphNode(abst._GraphNodeBase):
    def __init__(self, node):
        super(OFnGraphNode, self).__init__(node)
        self.__node = node
        self.__latest_inputs = None
        self.__bypassed_last_time = False
        self.__latest_params = None
        self.__packet = OFnPacket()

    def node(self):
        return self.__node

    def __params(self):
        d = {}
        for p in self.__node.paramNames():
            d[p] = self.__node.getParamValue(p)

        return d

    def __inputs(self):
        inputs = []
        for inp in self.__node.inputs():
            if inp is not None and not inp.getByPassed():
                inp = inp.id()

            inputs.append(inp)

        return inputs

    def dirty(self):
        self.__latest_inputs = None
        self.__latest_params = None

    def isDirty(self):
        if self.__bypassed_last_time != self.__node.getByPassed():
            return True

        if self.__latest_inputs is None or self.__latest_params is None:
            return True

        if self.__latest_inputs != self.__inputs():
            return True

        d = self.__params()
        if len(d) != len(self.__latest_params):
            return True

        for k, v in d.items():
            if self.__latest_params.get(k) != v:
                return True

        return False

    def evaluate(self, packetArray):
        if self.isDirty():
            self.__bypassed_last_time = self.__node.getByPassed()
            self.__latest_inputs = self.__inputs()
            self.__latest_params = self.__params()

            if self.__node.getByPassed():
                self.__packet = packetArray.packet(0)
            else:
                p = self.__node.operate(packetArray)
                if self.__node.packetable():
                    self.__packet = p

    def packet(self):
        return self.__packet
