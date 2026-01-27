import numpy
from ofne import plugin


DefaultPythonExpression = """# in_data = inPacket.data()
# in_shape = in_data.shape
# random_data = numpy.random.rand(in_shape[0], in_shape[1], in_shape[2]).astype(numpy.float32)
# outPacket = Packet(data=in_data + random_data)
outPacket = inPacket
"""


class PythonExpression(plugin.OFnOp):
    def __init__(self):
        super(PythonExpression, self).__init__()

    def params(self):
        return [
            plugin.OFnParamCode("code", default=DefaultPythonExpression)
        ]

    def needs(self):
        return 1

    def packetable(self):
        return True

    def _eval(self, expression, inPacket):
        eval_local = {"inPacket": inPacket, "Packet": plugin.OFnPacket}
        eval_global = {"numpy": numpy}

        exec(expression, eval_global, eval_local)

        op = eval_local.get("outPacket")
        if isinstance(op, plugin.OFnPacket):
            return op
        else:
            return None

    def operate(self, params, packetArray):
        exp = params.get("code")

        if not exp:
            return plugin.OFnPacket()

        op = self._eval(exp, packetArray.packet(0))
        if op:
            return op
        else:
            return plugin.OFnPacket()
