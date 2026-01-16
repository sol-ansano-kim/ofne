import unittest


class SceneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from ofne.core import scene
        except:
            import sys
            sys.path.append((os.path.abspath(os.path.join(__file__, "../../python"))))
        finally:
            import os
            from ofne.core import scene
            from ofne.core import opManager
            cls.scene = scene
            cls.opManager = opManager
            cls.orgEnv = os.environ.get("OFNE_PLUGIN_PATH")
            os.environ["OFNE_PLUGIN_PATH"] = os.path.join(__file__, "../plugins")
            cls.opManager.OFnOpManager().reloadPlugins()

        cls.test_ofsn_file = os.path.join(os.path.dirname(__file__), "example")

    @classmethod
    def tearDownClass(cls):
        import os

        if not cls.orgEnv:
            os.environ.pop("OFNE_PLUGIN_PATH", None)
        else:
            os.environ["OFNE_PLUGIN_PATH"] = cls.orgEnv

        cls.opManager.OFnOpManager().reloadPlugins()
        if os.path.isfile(cls.test_ofsn_file):
            os.remove(cls.test_ofsn_file)

    def test_create(self):
        scn = self.scene.OFnScene()
        self.assertIsNotNone(scn)
        self.assertEqual(scn.nodes(), [])
        nodea = scn.createNode("MyOpA")
        self.assertIsNotNone(nodea)
        self.assertEqual(len(scn.nodes()), 1)
        self.assertEqual(nodea.name(), "MyOpA")
        nodeb = scn.createNode("MyOpB")
        self.assertIsNotNone(nodeb)
        self.assertEqual(len(scn.nodes()), 2)
        self.assertEqual(nodeb.name(), "MyOpB")
        nodec = scn.createNode("MyOpC")
        self.assertIsNone(nodec)
        self.assertEqual(len(scn.nodes()), 2)
        nodea2 = scn.createNode("MyOpA")
        self.assertIsNotNone(nodea2)
        self.assertEqual(len(scn.nodes()), 3)
        self.assertEqual(nodea2.name(), "MyOpA1")
        nodea3 = scn.createNode("MyOpA")
        self.assertIsNotNone(nodea3)
        self.assertEqual(len(scn.nodes()), 4)
        self.assertEqual(nodea3.name(), "MyOpA2")

        scn = self.scene.OFnScene()
        n = scn.createNode("MyOpB", name="aaa")
        self.assertEqual(len(scn.nodes()), 1)
        self.assertEqual(n.name(), "aaa")
        n = scn.createNode("MyOpB", name="aaa")
        self.assertEqual(len(scn.nodes()), 2)
        self.assertEqual(n.name(), "aaa1")

    def test_delete(self):
        scn = self.scene.OFnScene()
        a = scn.createNode("MyOpB", name="a")
        b = scn.createNode("MyOpB", name="b")
        c = scn.createNode("MyOpB", name="c")
        self.assertEqual(len(scn.nodes()), 3)
        self.assertTrue(scn.deleteNode(b))
        self.assertEqual(len(scn.nodes()), 2)

        scn2 = self.scene.OFnScene()
        a = scn2.createNode("MyOpB", name="a")
        self.assertEqual(len(scn.nodes()), 2)
        self.assertEqual(len(scn2.nodes()), 1)

        self.assertFalse(scn.deleteNode(a))
        self.assertFalse(scn2.deleteNode(c))
        self.assertEqual(len(scn.nodes()), 2)
        self.assertEqual(len(scn2.nodes()), 1)

        self.assertTrue(scn.deleteNode(c))
        self.assertTrue(scn2.deleteNode(a))
        self.assertEqual(len(scn.nodes()), 1)
        self.assertEqual(len(scn2.nodes()), 0)

    def test_node(self):
        scn = self.scene.OFnScene()
        scn.createNode("MyOpA", name="a")
        scn.createNode("MyOpA", name="a")
        scn.createNode("MyOpB", name="a")
        self.assertEqual([x.name() for x in scn.nodes()], ["a", "a1", "a2"])
        nodes = scn.nodes()
        nodes.pop(1)
        self.assertEqual([x.name() for x in nodes], ["a", "a2"])
        self.assertEqual([x.name() for x in scn.nodes()], ["a", "a1", "a2"])

    def test_clear(self):
        scn = self.scene.OFnScene()
        scn.createNode("MyOpA", name="a")
        scn.createNode("MyOpA", name="a")
        scn.createNode("MyOpB", name="a")
        self.assertEqual([x.name() for x in scn.nodes()], ["a", "a1", "a2"])
        self.assertTrue(scn.clear())
        self.assertEqual([x.name() for x in scn.nodes()], [])

    def test_disconnect_deleted_nodes(self):
        scn = self.scene.OFnScene()
        a1 = scn.createNode("MyOpA")
        a2 = scn.createNode("MyOpA")
        b1 = scn.createNode("MyOpB")
        b2 = scn.createNode("MyOpB")
        self.assertEqual(a1.outputs(), [])
        self.assertEqual(a2.outputs(), [])
        self.assertEqual(b1.inputs(), [None, None])
        self.assertTrue(b1.connect(a1, index=1))
        self.assertTrue(b1.connect(a2, index=0))
        self.assertEqual(a1.outputs(), [b1])
        self.assertEqual(a2.outputs(), [b1])
        self.assertEqual(b1.inputs(), [a2, a1])
        self.assertEqual(b1.outputs(), [])
        self.assertTrue(b2.connect(b1, index=1))
        self.assertTrue(b2.connect(a1, index=0))
        self.assertTrue(b1 in a1.outputs())
        self.assertTrue(b2 in a1.outputs())
        self.assertEqual(b1.outputs(), [b2])
        self.assertEqual(b2.inputs(), [a1, b1])
        self.assertTrue(scn.deleteNode(b1))
        self.assertEqual(a1.outputs(), [b2])
        self.assertEqual(a2.outputs(), [])
        self.assertEqual(b2.inputs(), [a1, None])

    def __read(self):
        try:
            with open(self.test_ofsn_file) as f:
                return eval(f.read())
        except:
            return None

    def test_save_to(self):
        import os

        scn = self.scene.OFnScene()
        a = scn.createNode("MyOpA")
        self.assertFalse(os.path.isfile(self.test_ofsn_file))
        scn.write(self.test_ofsn_file)
        self.assertTrue(os.path.isfile(self.test_ofsn_file))
        d = self.__read()
        self.assertIsNotNone(d)
        self.assertEqual(len(d["nodes"]), 1)
        self.assertEqual(len(d["connections"]), 0)

        b1 = scn.createNode("MyOpB")
        scn.write(self.test_ofsn_file)
        d = self.__read()
        self.assertIsNotNone(d)
        self.assertEqual(len(d["nodes"]), 2)
        self.assertEqual(len(d["connections"]), 0)

        self.assertTrue(b1.connect(a, index=1))
        scn.write(self.test_ofsn_file)
        d = self.__read()
        self.assertIsNotNone(d)
        self.assertEqual(len(d["nodes"]), 2)
        self.assertEqual(len(d["connections"]), 1)

        self.assertTrue(b1.connect(a, index=0))
        scn.write(self.test_ofsn_file)
        d = self.__read()
        self.assertIsNotNone(d)
        self.assertEqual(len(d["nodes"]), 2)
        self.assertEqual(len(d["connections"]), 2)

        b2 = scn.createNode("MyOpB")
        scn.write(self.test_ofsn_file)
        d = self.__read()
        self.assertIsNotNone(d)
        self.assertEqual(len(d["nodes"]), 3)
        self.assertEqual(len(d["connections"]), 2)

        self.assertTrue(b2.connect(b1, index=0))
        scn.write(self.test_ofsn_file)
        d = self.__read()
        self.assertIsNotNone(d)
        self.assertEqual(len(d["nodes"]), 3)
        self.assertEqual(len(d["connections"]), 3)

        self.assertTrue(b2.connect(b1, index=1))
        scn.write(self.test_ofsn_file)
        d = self.__read()
        self.assertIsNotNone(d)
        self.assertEqual(len(d["nodes"]), 3)
        self.assertEqual(len(d["connections"]), 4)

        self.assertTrue(b2.connect(a, index=1))
        scn.write(self.test_ofsn_file)
        d = self.__read()
        self.assertIsNotNone(d)
        self.assertEqual(len(d["nodes"]), 3)
        self.assertEqual(len(d["connections"]), 4)

        scn.deleteNode(b1)
        scn.write(self.test_ofsn_file)
        d = self.__read()
        self.assertIsNotNone(d)
        self.assertEqual(len(d["nodes"]), 2)
        self.assertEqual(len(d["connections"]), 1)
