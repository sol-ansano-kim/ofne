import unittest


class ImplNode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from ofne.core import packet
        except:
            import sys
            import os
            sys.path.append((os.path.abspath(os.path.join(__file__, "../../python"))))
        finally:
            from ofne.impl import _node
            from ofne.core import op
            from ofne.core import param
            from ofne import exceptions
            cls._node = _node
            cls.exceptions = exceptions
            cls.param = param

        class OneInputs(op.OFnOp):
            def __init__(self):
                super(OneInputs, self).__init__()

            def params(self):
                return []

            def needs(self):
                return 1

            def packetable(self):
                return True

        class ZeroInputs(op.OFnOp):
            def __init__(self):
                super(ZeroInputs, self).__init__()

            def params(self):
                return []

            def needs(self):
                return 0

            def packetable(self):
                return True

        class TwoInputs(op.OFnOp):
            def __init__(self):
                super(TwoInputs, self).__init__()

            def params(self):
                return []

            def needs(self):
                return 2

            def packetable(self):
                return False

        class TwoInputsPacketable(op.OFnOp):
            def __init__(self):
                super(TwoInputsPacketable, self).__init__()

            def params(self):
                return []

            def needs(self):
                return 2

            def packetable(self):
                return True

        class ParamTester(op.OFnOp):
            def __init__(self):
                super(ParamTester, self).__init__()

            def params(self):
                return [
                    cls.param.OFnParamInt("int"),
                    cls.param.OFnParamBool("bool"),
                    cls.param.OFnParamFloat("float"),
                    cls.param.OFnParamStr("str"),
                ]

            def needs(self):
                return 0

            def packetable(self):
                return True

        cls.OneInputs = OneInputs
        cls.ZeroInputs = ZeroInputs
        cls.TwoInputs = TwoInputs
        cls.ParamTester = ParamTester
        cls.TwoInputsPacketable = TwoInputsPacketable

    def test_op(self):
        i0 = self.ZeroInputs()
        i1 = self.OneInputs()
        i2 = self.TwoInputs()

        self.assertIsNotNone(i0)
        self.assertIsNotNone(i1)
        self.assertIsNotNone(i2)

        self.assertEqual(i0.type(), "ZeroInputs")
        self.assertEqual(i1.type(), "OneInputs")
        self.assertEqual(i2.type(), "TwoInputs")

        self.assertEqual(i0.needs(), 0)
        self.assertEqual(i1.needs(), 1)
        self.assertEqual(i2.needs(), 2)

        self.assertTrue(i0.packetable())
        self.assertTrue(i1.packetable())
        self.assertFalse(i2.packetable())

    def test_connect(self):
        i0 = self._node._OFnNodeImpl(self.ZeroInputs(), None)
        i1 = self._node._OFnNodeImpl(self.OneInputs(), None)

        self.assertTrue(i1.connectInput(0, i0))
        self.assertEqual(len([x for x in i1.inputs() if x]), 1)
        inputs = i1.inputs()
        inputs.pop(0)
        self.assertTrue(len(inputs) == 0)
        self.assertEqual(len([x for x in i1.inputs() if x]), 1)
        self.assertEqual(i1.inputs()[0], i0)
        self.assertEqual(len(i0.outputs()), 1)
        outputs = i0.outputs()
        outputs.pop(0)
        self.assertTrue(len(outputs) == 0)
        self.assertEqual(len(i0.outputs()), 1)
        self.assertEqual(i0.outputs()[0], i1)
        self.assertTrue(i1.connectInput(0, i0))
        self.assertEqual(len([x for x in i1.inputs() if x]), 1)
        self.assertEqual(i1.inputs()[0], i0)
        self.assertEqual(len(i0.outputs()), 1)
        self.assertEqual(i0.outputs()[0], i1)

        self.assertTrue(i1.disconnectInput(0))
        self.assertEqual(len([x for x in i1.inputs() if x]), 0)
        self.assertEqual(len(i0.outputs()), 0)
        self.assertFalse(i1.disconnectInput(0))

        with self.assertRaises(self.exceptions.OFnIndexError):
            self.assertTrue(i1.connectInput(1, i0))
        with self.assertRaises(self.exceptions.OFnIndexError):
            self.assertTrue(i1.disconnectInput(1))

        i2 = self._node._OFnNodeImpl(self.TwoInputs(), None)
        self.assertTrue(i1.connectInput(0, i0))
        self.assertFalse(i1.connectInput(0, i2))
        self.assertEqual(len([x for x in i1.inputs() if x]), 1)
        self.assertEqual(i1.inputs()[0], i0)

        i01 = self._node._OFnNodeImpl(self.ZeroInputs(), None)
        i02 = self._node._OFnNodeImpl(self.ZeroInputs(), None)
        i1 = self._node._OFnNodeImpl(self.OneInputs(), None)
        i11 = self._node._OFnNodeImpl(self.OneInputs(), None)
        i2 = self._node._OFnNodeImpl(self.TwoInputs(), None)

        self.assertTrue(i1.connectInput(0, i01))
        self.assertEqual(len([x for x in i1.inputs() if x]), 1)
        self.assertEqual(len(i01.outputs()), 1)
        self.assertEqual(len(i02.outputs()), 0)
        self.assertTrue(i1.connectInput(0, i02))
        self.assertEqual(len([x for x in i1.inputs() if x]), 1)
        self.assertEqual(len(i01.outputs()), 0)
        self.assertEqual(len(i02.outputs()), 1)

        self.assertTrue(i2.connectInput(0, i02))
        self.assertEqual(len([x for x in i2.inputs() if x]), 1)
        self.assertTrue(i2.connectInput(1, i11))
        self.assertEqual(len([x for x in i2.inputs() if x]), 2)
        self.assertEqual(len(i02.outputs()), 2)
        self.assertEqual(len(i11.outputs()), 1)

        i2.disconnectAllInputs()
        self.assertEqual(len([x for x in i2.inputs() if x]), 0)
        self.assertEqual(len(i02.outputs()), 1)
        self.assertEqual(len(i1.outputs()), 0)
        i1.disconnectAllInputs()
        self.assertEqual(len(i02.outputs()), 0)
        self.assertEqual(len([x for x in i1.inputs() if x]), 0)

    def test_params(self):
        pt = self.ParamTester()
        pt1 = self._node._OFnNodeImpl(pt, None)
        self.assertEqual(sorted(pt1.paramNames()), ["bool", "float", "int", "str"])
        bp = pt1.getParam("bool")
        self.assertEqual(bp.get(), pt1.getParamValue("bool"))
        self.assertFalse(pt1.getParamValue("bool"))
        bp.set(True)
        self.assertTrue(bp.get())
        self.assertNotEqual(bp.get(), pt1.getParamValue("bool"))
        self.assertFalse(pt1.getParamValue("bool"))
        self.assertIsNone(pt1.getParam("Abc"))
        self.assertEqual(pt1.getParamValue("int"), 0)
        pt1.setParamValue("int", 1)
        self.assertEqual(pt1.getParamValue("int"), 1)
        ip = pt1.getParam("int")
        self.assertEqual(ip.get(), pt1.getParamValue("int"))
        pt1.setParamValue("int", 2)
        self.assertNotEqual(ip.get(), pt1.getParamValue("int"))
        ip.set(2)
        self.assertEqual(ip.get(), pt1.getParamValue("int"))

    def test_cycle(self):
        one1 = self._node._OFnNodeImpl(self.OneInputs(), None)
        one2 = self._node._OFnNodeImpl(self.OneInputs(), None)
        one3 = self._node._OFnNodeImpl(self.OneInputs(), None)
        self.assertTrue(one1.connectInput(0, one2))
        self.assertFalse(one2.connectInput(0, one1))
        self.assertTrue(one2.connectInput(0, one3))
        self.assertFalse(one3.connectInput(0, one1))

        two1 = self._node._OFnNodeImpl(self.TwoInputsPacketable(), None)
        two2 = self._node._OFnNodeImpl(self.TwoInputsPacketable(), None)
        one1 = self._node._OFnNodeImpl(self.OneInputs(), None)
        one2 = self._node._OFnNodeImpl(self.OneInputs(), None)
        one3 = self._node._OFnNodeImpl(self.OneInputs(), None)
        self.assertTrue(one1.connectInput(0, two1))
        self.assertFalse(two1.connectInput(0, one1))
        self.assertFalse(two1.connectInput(1, one1))
        self.assertTrue(two1.connectInput(0, two2))
        self.assertTrue(two1.connectInput(1, two2))
        self.assertTrue(two2.connectInput(0, one2))
        self.assertTrue(two2.connectInput(0, one2))
        self.assertFalse(one2.connectInput(0, one1))
