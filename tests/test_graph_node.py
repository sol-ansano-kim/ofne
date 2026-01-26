import unittest
import numpy as np


class GraphNode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from ofne.core import packet
        except:
            import sys
            import os
            sys.path.append((os.path.abspath(os.path.join(__file__, "../../python"))))
        finally:
            from ofne.core import abst
            from ofne.core import node as core_node
            from ofne.core import op
            from ofne.core import param
            from ofne.core import packet
            from ofne.graph import node as graph_node
            from ofne import exceptions
            cls.core_node = core_node
            cls.graph_node = graph_node
            cls.exceptions = exceptions
            cls.param = param
            cls.packet = packet

        class DummyScene(abst._SceneBase):
            def __init__(self):
                super(DummyScene)

            def getUniqueName(self, name):
                return name

        class PlusOp(op.OFnOp):
            def __init__(self):
                super(PlusOp, self).__init__()

            def params(self):
                return [
                    cls.param.OFnParamFloat("num")
                ]

            def needs(self):
                return 1

            def packetable(self):
                return True

            def operate(self, params, packetArray):
                GraphNode.count += 1
                return GraphNode.packet.OFnPacket(data=packetArray.packet(0).data() + params.get("num"))

        class MakeNums(op.OFnOp):
            def __init__(self):
                super(MakeNums, self).__init__()

            def params(self):
                return [
                    cls.param.OFnParamInt("count", min=0),
                    cls.param.OFnParamFloat("num")
                ]

            def needs(self):
                return 0

            def packetable(self):
                return True

            def operate(self, params, packetArray):
                GraphNode.count += 1
                return GraphNode.packet.OFnPacket(data=np.array([params.get("num")] * params.get("count")))

        cls.PlusOp = PlusOp
        cls.MakeNums = MakeNums
        cls.scene = DummyScene()
        cls.count = 0

    def test_creation(self):
        op_plus = self.PlusOp()
        op_make = self.MakeNums()
        plus_node = self.core_node.OFnNode(self.scene, op_plus)
        make_node = self.core_node.OFnNode(self.scene, op_make)

        plus = self.graph_node.OFnGraphNode(plus_node)
        make = self.graph_node.OFnGraphNode(make_node)
        self.assertIsNotNone(plus)
        self.assertIsNotNone(make)

        self.assertEqual(plus.node(), plus_node)
        self.assertEqual(make.node(), make_node)

    def test_eval_by_param(self):
        GraphNode.count = 0
        empty_packey_array = self.packet.OFnPacketArray([])

        make_node = self.core_node.OFnNode(self.scene, self.MakeNums())
        make = self.graph_node.OFnGraphNode(make_node)
        self.assertTrue(make.isDirty())
        p = make.packet()
        self.assertEqual(len(p.data()), 0)
        self.assertTrue(make.isDirty())
        self.assertEqual(GraphNode.count, 0)

        self.assertEqual(GraphNode.count, 0)
        make.evaluate(empty_packey_array)
        self.assertEqual(GraphNode.count, 1)
        self.assertFalse(make.isDirty())
        p = make.packet()
        self.assertEqual(len(p.data()), 0)
        self.assertFalse(make.isDirty())

        make_node.setParamValue("count", 1)
        self.assertTrue(make.isDirty())
        p = make.packet()
        self.assertEqual(GraphNode.count, 1)
        self.assertEqual(len(p.data()), 0)
        self.assertEqual(GraphNode.count, 1)
        make.evaluate(empty_packey_array)
        self.assertEqual(GraphNode.count, 2)
        self.assertFalse(make.isDirty())
        p = make.packet()
        self.assertEqual(len(p.data()), 1)
        self.assertEqual(p.data()[0], 0.0)
        self.assertEqual(GraphNode.count, 2)
        make.evaluate(empty_packey_array)
        self.assertEqual(GraphNode.count, 2)
        self.assertEqual(len(p.data()), 1)
        self.assertEqual(p.data()[0], 0.0)

        make_node.setParamValue("num", 1.0)
        self.assertTrue(make.isDirty())
        p = make.packet()
        self.assertEqual(len(p.data()), 1)
        self.assertEqual(p.data()[0], 0.0)
        self.assertEqual(GraphNode.count, 2)
        make.evaluate(empty_packey_array)
        self.assertFalse(make.isDirty())
        self.assertEqual(GraphNode.count, 3)
        p = make.packet()
        self.assertEqual(len(p.data()), 1)
        self.assertEqual(p.data()[0], 1.0)

        self.assertFalse(make.isDirty())
        make_node.setParamValue("count", 3)
        self.assertEqual(GraphNode.count, 3)
        self.assertTrue(make.isDirty())
        make.evaluate(empty_packey_array)
        self.assertFalse(make.isDirty())
        self.assertEqual(GraphNode.count, 4)
        p = make.packet()
        self.assertEqual(len(p.data()), 3)
        self.assertEqual(p.data()[0], 1.0)
        self.assertEqual(p.data()[1], 1.0)
        self.assertEqual(p.data()[2], 1.0)

    def test_eval_by_connection(self):
        GraphNode.count = 0
        empty_packey_array = self.packet.OFnPacketArray([])

        make_node_1 = self.core_node.OFnNode(self.scene, self.MakeNums())
        make_1 = self.graph_node.OFnGraphNode(make_node_1)
        make_node_2 = self.core_node.OFnNode(self.scene, self.MakeNums())
        make_2 = self.graph_node.OFnGraphNode(make_node_2)

        make_node_1.setParamValue("count", 1)
        make_node_1.setParamValue("num", 0.5)
        make_node_2.setParamValue("count", 3)
        make_node_2.setParamValue("num", 1.1)

        plus_node = self.core_node.OFnNode(self.scene, self.PlusOp())
        plus = self.graph_node.OFnGraphNode(plus_node)
        self.assertTrue(plus.isDirty())
        self.assertEqual(GraphNode.count, 0)
        plus.evaluate(empty_packey_array)
        self.assertEqual(GraphNode.count, 1)
        self.assertEqual(len(plus.packet().data()), 0)

        self.assertFalse(plus.isDirty())
        plus.evaluate(empty_packey_array)
        self.assertEqual(GraphNode.count, 1)
        plus_node.connect(make_node_1)
        self.assertTrue(plus.isDirty())
        make_1.evaluate(empty_packey_array)
        self.assertEqual(GraphNode.count, 2)
        plus.evaluate(self.packet.OFnPacketArray([make_1.packet()]))
        self.assertEqual(GraphNode.count, 3)
        plus_packet = plus.packet()
        self.assertEqual(len(plus_packet.data()), 1)
        self.assertEqual(plus_packet.data()[0], 0.5)
        make_1.evaluate(empty_packey_array)
        self.assertEqual(GraphNode.count, 3)
        plus.evaluate(self.packet.OFnPacketArray([make_1.packet()]))
        self.assertEqual(GraphNode.count, 3)
        plus_packet = plus.packet()
        self.assertEqual(len(plus_packet.data()), 1)
        self.assertEqual(plus_packet.data()[0], 0.5)
        self.assertFalse(plus.isDirty())

        plus_node.connect(make_node_2)
        self.assertTrue(plus.isDirty())
        make_2.evaluate(empty_packey_array)
        self.assertEqual(GraphNode.count, 4)
        plus.evaluate(self.packet.OFnPacketArray([make_2.packet()]))
        self.assertEqual(GraphNode.count, 5)
        self.assertFalse(plus.isDirty())
        plus_packet = plus.packet()
        self.assertEqual(len(plus_packet.data()), 3)
        self.assertEqual(plus_packet.data()[0], 1.1)
        self.assertEqual(plus_packet.data()[1], 1.1)
        self.assertEqual(plus_packet.data()[2], 1.1)
        make_2.evaluate(empty_packey_array)
        self.assertEqual(GraphNode.count, 5)
        plus.evaluate(self.packet.OFnPacketArray([make_2.packet()]))
        self.assertEqual(GraphNode.count, 5)
        plus_packet = plus.packet()
        self.assertEqual(len(plus_packet.data()), 3)
        self.assertEqual(plus_packet.data()[0], 1.1)
        self.assertEqual(plus_packet.data()[1], 1.1)
        self.assertEqual(plus_packet.data()[2], 1.1)
        self.assertFalse(plus.isDirty())

        plus_node.connect(make_node_1)
        self.assertTrue(plus.isDirty())
        make_1.evaluate(empty_packey_array)
        self.assertEqual(GraphNode.count, 5)
        plus.evaluate(self.packet.OFnPacketArray([make_1.packet()]))
        self.assertEqual(GraphNode.count, 6)
        plus_packet = plus.packet()
        self.assertEqual(len(plus_packet.data()), 1)
        self.assertEqual(plus_packet.data()[0], 0.5)
        self.assertFalse(plus.isDirty())

        plus_node.connect(make_node_2)
        self.assertTrue(plus.isDirty())
        make_2.evaluate(empty_packey_array)
        self.assertEqual(GraphNode.count, 6)
        plus.evaluate(self.packet.OFnPacketArray([make_2.packet()]))
        self.assertEqual(GraphNode.count, 7)
        self.assertFalse(plus.isDirty())
        plus_packet = plus.packet()
        self.assertEqual(len(plus_packet.data()), 3)
        self.assertEqual(plus_packet.data()[0], 1.1)
        self.assertEqual(plus_packet.data()[1], 1.1)
        self.assertEqual(plus_packet.data()[2], 1.1)
