import numpy
import OpenImageIO
import PyOpenColorIO
from ofne import plugin


DefaultPythonExpression = """# # Inputs
# # inPackets : A container of input packets
# # oiio : OpenImageIO library
# # ocio : PyOpenColorIO library
# # np : NumPy library
# # Packet : Packet class
# # Output
# # outPacket: A Packet constructed from the processed result
# in_data = inPackets.packet(0).data()
# in_shape = in_data.shape
# random_data = np.random.rand(in_shape[0], in_shape[1], in_shape[2]).astype(np.float32)
# outPacket = Packet(data=in_data + random_data)
outPacket = inPackets.packet(0)
"""


class PythonExpression(plugin.OFnOp):
    def __init__(self):
        super(PythonExpression, self).__init__()

    def params(self):
        return [
            plugin.OFnParamCode("code", default=DefaultPythonExpression)
        ]

    def needs(self):
        return 4

    def packetable(self):
        return True

    def _eval(self, expression, inPackets):
        eval_local = {"inPackets": inPackets, "Packet": plugin.OFnPacket}
        eval_global = {"np": numpy, "oiio": OpenImageIO, "ocio": PyOpenColorIO}

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

        op = self._eval(exp, packetArray)
        if op:
            return op
        else:
            return plugin.OFnPacket()
