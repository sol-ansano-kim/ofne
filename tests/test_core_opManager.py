import unittest


class NodeManagerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from ofne.core import opManager
        except:
            import sys
            sys.path.append((os.path.abspath(os.path.join(__file__, "../../python"))))
        finally:
            import os
            from ofne.core import opManager
            from ofne.core import op
            cls.op = op
            cls.opManager = opManager
            cls.orgEnv = os.environ.get("OFNE_PLUGIN_PATH")
            os.environ["OFNE_PLUGIN_PATH"] = os.path.join(__file__, "../plugins")

            class TestOpA(op.OFnOp):
                pass

            class TestOpB(op.OFnOp):
                pass

            cls.TestOpA = TestOpA
            cls.TestOpB = TestOpB

            cls.opManager.OFnOpManager().reloadPlugins()

    @classmethod
    def tearDownClass(cls):
        import os

        if not cls.orgEnv:
            os.environ.pop("OFNE_PLUGIN_PATH", None)
        else:
            os.environ["OFNE_PLUGIN_PATH"] = cls.orgEnv

        cls.opManager.OFnOpManager().reloadPlugins()

    def test_singleton(self):
        a = self.opManager.OFnOpManager()
        self.assertIsNotNone(a)
        b = self.opManager.OFnOpManager()
        self.assertIsNotNone(a)
        self.assertEqual(a, b)
        self.assertEqual(id(a), id(b))

    def test_load(self):
        man = self.opManager.OFnOpManager()
        man.reloadPlugins()
        self.assertTrue("MyOpA" in man.listOps())
        self.assertTrue("MyOpB" in man.listOps())
        op = man.getOp("MyOpA")
        self.assertIsNotNone(op)
        op = man.getOp("MyOpB")
        self.assertIsNotNone(op)
        op = man.getOp("MyOpC")
        self.assertIsNone(op)

    def test_reg_dereg(self):
        man = self.opManager.OFnOpManager()
        init_count = len(man.listOps())
        opa = self.TestOpA()
        opa1 = self.TestOpA()
        opb = self.TestOpB()

        self.assertTrue(man.registerOp(opa))
        self.assertEqual(len(man.listOps()), init_count + 1)
        self.assertEqual(man.getOp("TestOpA"), opa)
        self.assertFalse(man.registerOp(opa))
        self.assertEqual(len(man.listOps()), init_count + 1)
        self.assertFalse(man.registerOp(opa1))
        self.assertNotEqual(man.getOp("TestOpA"), opa1)
        self.assertEqual(len(man.listOps()), init_count + 1)
        self.assertTrue(man.registerOp(opb))
        self.assertEqual(len(man.listOps()), init_count + 2)
        self.assertEqual(man.getOp("TestOpB"), opb)
        self.assertTrue(man.deregisterOp(opb))
        self.assertEqual(len(man.listOps()), init_count + 1)
        self.assertFalse(man.deregisterOp(opb))
        self.assertEqual(len(man.listOps()), init_count + 1)
        self.assertFalse(man.deregisterOp(opa1))
        self.assertEqual(len(man.listOps()), init_count + 1)
        self.assertTrue(man.deregisterOp(opa))
        self.assertEqual(len(man.listOps()), init_count)
