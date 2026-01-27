import unittest


class ParamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from ofne.core import packet
        except:
            import sys
            import os
            sys.path.append((os.path.abspath(os.path.join(__file__, "../../python"))))
        finally:
            from ofne.core import param
            from ofne import exceptions
            cls.param = param
            cls.exceptions = exceptions

    def test_bool(self):
        b1 = self.param.OFnParamBool("b")
        self.assertIsNotNone(b1)
        self.assertEqual(b1.type(), self.param.ParamTypeBool)
        self.assertEqual(b1.default(), False)
        self.assertEqual(b1.get(), False)
        b1.set(True)
        self.assertEqual(b1.get(), True)
        self.assertEqual(b1.default(), False)
        self.assertFalse(b1.isValid(1))
        self.assertFalse(b1.isValid(1.23))
        self.assertFalse(b1.isValid("on"))
        self.assertFalse(b1.isValid("false"))
        self.assertTrue(b1.isValid(True))
        self.assertTrue(b1.isValid(False))

        b2 = b1.copy()
        b2.set(False)
        self.assertNotEqual(b2.get(), b1.get())
        self.assertEqual(b2.get(), False)
        self.assertEqual(b2.default(), False)
        self.assertFalse(b2.isValid(1))
        self.assertFalse(b2.isValid(1.23))
        self.assertFalse(b2.isValid("on"))
        self.assertFalse(b2.isValid("false"))
        self.assertTrue(b2.isValid(True))
        self.assertTrue(b2.isValid(False))

        b3 = self.param.OFnParamBool("b", default=True)
        self.assertEqual(b3.default(), True)
        self.assertEqual(b3.get(), True)

        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            b1.set(1)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            b1.set(1.23)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            b1.set("on")

    def test_int(self):
        i1 = self.param.OFnParamInt("i")
        self.assertIsNotNone(i1)
        self.assertEqual(i1.type(), self.param.ParamTypeInt)
        self.assertEqual(i1.default(), 0)
        self.assertEqual(i1.get(), 0)
        i1.set(123)
        self.assertEqual(i1.get(), 123)
        self.assertEqual(i1.default(), 0)
        self.assertFalse(i1.isValid(True))
        self.assertFalse(i1.isValid(1.23))
        self.assertFalse(i1.isValid("1"))
        self.assertFalse(i1.isValid("123"))
        self.assertTrue(i1.isValid(4))
        self.assertTrue(i1.isValid(-1))

        i2 = i1.copy()
        i2.set(456)
        self.assertEqual(i2.get(), 456)
        self.assertEqual(i2.default(), 0)
        self.assertFalse(i2.isValid(True))
        self.assertFalse(i2.isValid(1.23))
        self.assertFalse(i2.isValid("1"))
        self.assertFalse(i2.isValid("123"))
        self.assertTrue(i2.isValid(4))
        self.assertTrue(i2.isValid(-1))

        i3 = self.param.OFnParamInt("i", default=789)
        self.assertEqual(i3.default(), 789)
        self.assertEqual(i3.get(), 789)

        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            i1.set(True)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            i1.set(1.23)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            i1.set("on")

        i4 = self.param.OFnParamInt("i", default=0, min=0, max=100)
        self.assertFalse(i4.isValid(-1))
        self.assertFalse(i4.isValid(101))
        self.assertTrue(i4.isValid(1))
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            i4.set(-1)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            i4.set(101)

        i4.set(5)
        self.assertEqual(i4.get(), 5)

    def test_float(self):
        f1 = self.param.OFnParamFloat("f")
        self.assertIsNotNone(f1)
        self.assertEqual(f1.type(), self.param.ParamTypeFloat)
        self.assertEqual(f1.default(), 0.0)
        self.assertEqual(f1.get(), 0.0)
        f1.set(123.0)
        self.assertEqual(f1.get(), 123.0)
        self.assertEqual(f1.default(), 0.0)
        self.assertFalse(f1.isValid(True))
        self.assertFalse(f1.isValid(1))
        self.assertFalse(f1.isValid("1"))
        self.assertFalse(f1.isValid("123"))
        self.assertTrue(f1.isValid(4.0))
        self.assertTrue(f1.isValid(-1.234))

        f2 = f1.copy()
        f2.set(456.0)
        self.assertEqual(f2.get(), 456.0)
        self.assertEqual(f2.default(), 0.0)
        self.assertFalse(f2.isValid(True))
        self.assertFalse(f2.isValid(1))
        self.assertFalse(f2.isValid("1"))
        self.assertFalse(f2.isValid("123"))
        self.assertTrue(f2.isValid(4.0))
        self.assertTrue(f2.isValid(-1.234))

        f3 = self.param.OFnParamFloat("f", default=789.0)
        self.assertEqual(f3.default(), 789.0)
        self.assertEqual(f3.get(), 789.0)

        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            f1.set(True)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            f1.set(1)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            f1.set("on")

        f4 = self.param.OFnParamFloat("f", default=0.0, min=0.0, max=100.0)
        self.assertFalse(f4.isValid(-0.00001))
        self.assertFalse(f4.isValid(100.1))
        self.assertTrue(f4.isValid(1.0))
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            f4.set(-0.00001)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            f4.set(100.1)

        f4.set(5.0)
        self.assertEqual(f4.get(), 5.0)

    def test_str(self):
        s1 = self.param.OFnParamStr("s")
        self.assertIsNotNone(s1)
        self.assertEqual(s1.type(), self.param.ParamTypeStr)
        self.assertEqual(s1.default(), "")
        self.assertEqual(s1.get(), "")
        s1.set("abc")
        self.assertEqual(s1.get(), "abc")
        self.assertEqual(s1.default(), "")
        self.assertFalse(s1.isValid(True))
        self.assertFalse(s1.isValid(1))
        self.assertFalse(s1.isValid(0.123))
        self.assertTrue(s1.isValid("123"))
        self.assertTrue(s1.isValid("abc"))

        s2 = s1.copy()
        s2.set("def")
        self.assertEqual(s2.get(), "def")
        self.assertEqual(s2.default(), "")
        self.assertFalse(s1.isValid(True))
        self.assertFalse(s1.isValid(1))
        self.assertFalse(s1.isValid(0.123))
        self.assertTrue(s1.isValid("123"))
        self.assertTrue(s1.isValid("abc"))

        s3 = self.param.OFnParamStr("s", default="ghi")
        self.assertEqual(s3.default(), "ghi")
        self.assertEqual(s3.get(), "ghi")

        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            s1.set(True)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            s1.set(1)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            s1.set(-0.123)

        s4 = self.param.OFnParamStr("s", default="a", valueList=["a", "b", "c"], enforceValueList=True)
        self.assertEqual(s4.valueList(), ["a", "b", "c"])
        self.assertFalse(s4.isValid("d"))
        self.assertFalse(s4.isValid("A"))
        self.assertTrue(s4.isValid("b"))
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            s4.set("d")
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            s4.set("A")

        s4.set("b")
        self.assertEqual(s4.get(), "b")
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            self.param.OFnParamStr("s", default="A", valueList=["a", "b", "c"], enforceValueList=True)

        s5 = self.param.OFnParamStr("s", default="a", valueList=["a", "b", "c"], enforceValueList=False)
        self.assertEqual(s5.valueList(), ["a", "b", "c"])
        self.assertTrue(s5.isValid("d"))
        self.assertTrue(s5.isValid("A"))
        self.assertTrue(s5.isValid("b"))
        s5.set("any")
        self.assertEqual(s5.get(), "any")

    def test_code(self):
        s1 = self.param.OFnParamCode("s")
        self.assertIsNotNone(s1)
        self.assertEqual(s1.type(), self.param.ParamTypeCode)
        self.assertEqual(s1.default(), "")
        self.assertEqual(s1.get(), "")
        s1.set("abc")
        self.assertEqual(s1.get(), "abc")
        self.assertEqual(s1.default(), "")
        self.assertFalse(s1.isValid(True))
        self.assertFalse(s1.isValid(1))
        self.assertFalse(s1.isValid(0.123))
        self.assertTrue(s1.isValid("123"))
        self.assertTrue(s1.isValid("abc"))

        s2 = s1.copy()
        s2.set("def")
        self.assertEqual(s2.get(), "def")
        self.assertEqual(s2.default(), "")
        self.assertFalse(s1.isValid(True))
        self.assertFalse(s1.isValid(1))
        self.assertFalse(s1.isValid(0.123))
        self.assertTrue(s1.isValid("123"))
        self.assertTrue(s1.isValid("abc"))

        s3 = self.param.OFnParamCode("s", default="ghi")
        self.assertEqual(s3.default(), "ghi")
        self.assertEqual(s3.get(), "ghi")

        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            s1.set(True)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            s1.set(1)
        with self.assertRaises(self.exceptions.OFnInvalidParamValueError):
            s1.set(-0.123)

    def test_label(self):
        p = self.param.OFnParamBool("b")
        self.assertEqual(p.name(), "b")
        self.assertEqual(p.label(), "b")
        p = self.param.OFnParamFloat("f")
        self.assertEqual(p.name(), "f")
        self.assertEqual(p.label(), "f")
        p = self.param.OFnParamInt("i")
        self.assertEqual(p.name(), "i")
        self.assertEqual(p.label(), "i")
        p = self.param.OFnParamStr("s")
        self.assertEqual(p.name(), "s")
        self.assertEqual(p.label(), "s")

        p = self.param.OFnParamBool("b", label="bool")
        self.assertEqual(p.name(), "b")
        self.assertEqual(p.label(), "bool")
        p = self.param.OFnParamFloat("f", label="float")
        self.assertEqual(p.name(), "f")
        self.assertEqual(p.label(), "float")
        p = self.param.OFnParamInt("i", label="int")
        self.assertEqual(p.name(), "i")
        self.assertEqual(p.label(), "int")
        p = self.param.OFnParamStr("s", label="str")
        self.assertEqual(p.name(), "s")
        self.assertEqual(p.label(), "str")

    def test_params(self):
        params = self.param.OFnParams([])
        self.assertIsNotNone(params)
        self.assertEqual(params.keys(), [])
        test = [
            self.param.OFnParamBool("bool"),
            self.param.OFnParamInt("int"),
            self.param.OFnParamFloat("float"),
            self.param.OFnParamStr("str")
        ]

        params = self.param.OFnParams(test)
        self.assertEqual(len(params.keys()), 4)
        test.pop(0)
        self.assertEqual(len(test), 3)
        self.assertEqual(len(params.keys()), 4)

        test = [
            self.param.OFnParamBool("bool"),
            self.param.OFnParamInt("int"),
            self.param.OFnParamFloat("float"),
            self.param.OFnParamStr("str")
        ]

        params = self.param.OFnParams(test)
        self.assertEqual(test[0].get(), params.get("bool"))
        self.assertEqual(test[1].get(), params.get("int"))
        self.assertEqual(test[2].get(), params.get("float"))
        self.assertEqual(test[3].get(), params.get("str"))

        self.assertFalse(test[0].get())
        test[0].set(True)
        self.assertTrue(test[0].get())
        self.assertFalse(params.get("bool"))
        self.assertTrue(params.set("bool", True))
        self.assertEqual(test[0].get(), params.get("bool"))

        self.assertTrue(params.set("int", 2))
        self.assertNotEqual(test[1].get(), params.get("int"))
        test[1].set(2)
        self.assertEqual(test[1].get(), params.get("int"))

        self.assertEqual(params.get("float"), 0)
        self.assertEqual(params.get("float", 1), 0)
        self.assertEqual(params.get("float2"), None)
        self.assertEqual(params.get("float2", 1), 1)

        cparams = params.copy()
        self.assertEqual(cparams.get("bool"), params.get("bool"))
        self.assertEqual(cparams.get("int"), params.get("int"))
        self.assertEqual(cparams.get("float"), params.get("float"))
        self.assertEqual(cparams.get("str"), params.get("str"))

        cparams.set("float", 1.2)
        self.assertEqual(cparams.get("bool"), params.get("bool"))
        self.assertEqual(cparams.get("int"), params.get("int"))
        self.assertNotEqual(cparams.get("float"), params.get("float"))
        self.assertEqual(cparams.get("str"), params.get("str"))
