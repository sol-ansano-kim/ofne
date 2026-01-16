import sys
import os
import unittest
import numpy as np


class GraphScene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.pop("OFNE_PLUGIN_PATH", None)

        try:
            from ofne.core import packet
        except:
            sys.path.append((os.path.abspath(os.path.join(__file__, "../../python"))))
        finally:
            from ofne.core import node as core_node
            from ofne.core import scene as core_scene
            from ofne.core import op
            from ofne.core import opManager
            from ofne.core import param
            from ofne.core import packet
            from ofne.graph import node as graph_node
            from ofne.graph import scene as graph_scene
            from ofne import exceptions
            cls.core_node = core_node
            cls.core_scene = core_scene
            cls.graph_node = graph_node
            cls.graph_scene = graph_scene
            cls.exceptions = exceptions
            cls.param = param
            cls.packet = packet
            cls.opManager = opManager

            class PlusOp(op.OFnOp):
                def __init__(self):
                    super(PlusOp, self).__init__()

                def params(self):
                    return {}

                def needs(self):
                    return 2

                def packetable(self):
                    return True

                def operate(self, params, packetArray):
                    GraphScene.count += 1
                    return GraphScene.packet.OFnPacket(data=packetArray.packet(0).data() + packetArray.packet(1).data())

            class MakeNums(op.OFnOp):
                def __init__(self):
                    super(MakeNums, self).__init__()

                def params(self):
                    return {
                        "count": cls.param.OFnParamInt(min=0),
                        "num": cls.param.OFnParamFloat()
                    }

                def needs(self):
                    return 0

                def packetable(self):
                    return True

                def operate(self, params, packetArray):
                    GraphScene.count += 1
                    return GraphScene.packet.OFnPacket(data=np.array([params.get("num")] * params.get("count")))

            class Output(op.OFnOp):
                def __init__(self):
                    super(Output, self).__init__()

                def needs(self):
                    return 1

                def packetable(self):
                    return False

                def params(self):
                    return {}

                def operate(self, params, packetArray):
                    GraphScene.count += 1
                    pass

            cls.PlusOp = PlusOp()
            cls.MakeNums = MakeNums()
            cls.Output = Output()
            cls.count = 0

            opManager.OFnOpManager().reloadPlugins()
            opManager.OFnOpManager().registerOp(cls.PlusOp)
            opManager.OFnOpManager().registerOp(cls.MakeNums)
            opManager.OFnOpManager().registerOp(cls.Output)

    @classmethod
    def tearDownClass(cls):
        cls.opManager.OFnOpManager().deregisterOp(cls.PlusOp)
        cls.opManager.OFnOpManager().deregisterOp(cls.MakeNums)
        cls.opManager.OFnOpManager().deregisterOp(cls.Output)

    def test_graph(self):
        self.assertEqual(len(self.opManager.OFnOpManager().listOps()), 3)
        self.assertIsNotNone(self.opManager.OFnOpManager().getOp("PlusOp"))
        self.assertIsNotNone(self.opManager.OFnOpManager().getOp("MakeNums"))
        self.assertIsNotNone(self.opManager.OFnOpManager().getOp("Output"))

        scn = self.core_scene.OFnScene()
        p1 = scn.createNode("PlusOp")
        m1 = scn.createNode("MakeNums")
        m2 = scn.createNode("MakeNums")
        op = scn.createNode("Output")
        self.assertIsNotNone(p1)
        self.assertIsNotNone(m1)
        self.assertIsNotNone(m2)
        self.assertIsNotNone(op)

        self.assertEqual(GraphScene.count, 0)
        self.assertEqual(len(scn.nodes()), 4)
        m1.setParamValue("num", 1.0)
        m1.setParamValue("count", 1)
        m2.setParamValue("num", 2.0)
        m2.setParamValue("count", 1)

        p1.connect(m1, 0)
        p1.connect(m2, 1)
        op.connect(p1, 0)

        graph_scene = self.graph_scene.OFnGraphScene(scn)
        self.assertIsNotNone(graph_scene)
        self.assertEqual(GraphScene.count, 0)
        graph_scene.packet(m1)
        self.assertEqual(GraphScene.count, 1)
        graph_scene.packet(p1)
        self.assertEqual(GraphScene.count, 3)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 4)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 4)
        m2.setParamValue("num", 3.0)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 7)
        m2.setParamValue("num", 3.0)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 7)
        m2.setParamValue("num", 1.0)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 10)
        m2.setParamValue("num", 2.0)
        graph_scene.packet(p1)
        self.assertEqual(GraphScene.count, 12)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 13)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 13)
        m1.setParamValue("num", 1.0)
        m2.setParamValue("num", 2.0)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 13)
        m1.setParamValue("num", 2.0)
        m2.setParamValue("num", 3.0)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 17)
        m3 = scn.createNode("MakeNums")
        m3.setParamValue("num", 3.0)
        m3.setParamValue("count", 1)
        self.assertEqual(m2.getParamValue("num"), m3.getParamValue("num"))
        self.assertEqual(m2.getParamValue("count"), m3.getParamValue("count"))
        p1.connect(m3, 1)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 20)
        p1.connect(m3, 0)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 22)
        m1.setParamValue("num", 5.0)
        p1.connect(m1, 0)
        p1.connect(m1, 1)
        graph_scene.packet(op)
        self.assertEqual(GraphScene.count, 25)
