from . import abst
from . import node
from ..core import packet
from .. import exceptions


class OFnGraphScene(abst._GraphSceneBase):
    def __init__(self, scene):
        super(OFnGraphScene, self).__init__(scene)
        self.__scene = scene
        self.__graph_nodes = {}

    def __track_nodes(self):
        new_nodes = {}

        for sn in self.__scene.nodes():
            n = self.__graph_nodes.get(sn.id(), None)
            if n is None:
                n = node.OFnGraphNode(sn)

            new_nodes[sn.id()] = n

        self.__graph_nodes = new_nodes

    def __inputNetwork(self, nodes):
        cache = set()
        eval_nodes = []

        currents = nodes[:]
        while (currents):
            nexts = []

            for cur in currents:
                if cur not in cache:
                    eval_nodes.append(cur)
                    cache.add(cur)
                    nexts.extend([x for x in cur.inputs() if x is not None])

            currents = nexts

        return [self.__graph_nodes[x.id()] for x in reversed(eval_nodes)]

    def evaluate(self, nodes, force=False):
        self.__track_nodes()

        waiting = self.__inputNetwork(nodes)
        dirty_set = set()

        curs = [x for x in waiting if x.isDirty()]
        while (curs):
            nexts = []
            for cur in curs:
                if cur.node().id() in dirty_set:
                    continue

                cur.dirty()
                dirty_set.add(cur.node().id())
                nexts.extend([self.__graph_nodes[x.id()] for x in cur.node().outputs()])

            curs = nexts

        evaled = set()

        latest_count = None
        while (waiting):
            if len(waiting) == latest_count:
                raise exceptions.OFnGraphEvaluationError("Failed to evaludate the scene graph")

            latest_count = len(waiting)

            pending = []
            for _ in range(latest_count):
                gn = waiting.pop(0)

                if gn.node().id() in evaled:
                    continue

                if not force and not gn.isDirty():
                    continue

                ready = True
                packets = []
                for inn in gn.node().inputs():
                    if inn is not None and self.__graph_nodes[inn.id()].isDirty():
                        ready = False
                        break

                    if inn is None:
                        packets.append(packet.OFnPacket())
                    else:
                        packets.append(self.__graph_nodes[inn.id()].packet())

                if not ready:
                    pending.append(gn)
                    continue

                gn.evaluate(packet.OFnPacketArray(packets))
                evaled.add(gn.node().id())

            waiting = pending + waiting

    def packet(self, node):
        if node.id() not in self.__graph_nodes:
            self.__track_nodes()

        gn = self.__graph_nodes.get(node.id())
        if gn is None:
            return None

        self.evaluate([node])

        return gn.packet()
