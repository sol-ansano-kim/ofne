class _OFnSceneImpl(object):
    def __init__(self, nodeClass, opManager):
        super(_OFnSceneImpl, self).__init__()
        self.__node_class = nodeClass
        self.__op_manager = opManager
        self.__nodes = {}

    def createNode(self, type, name=None):
        op = self.__op_manager.getOp(type)
        if op is None:
            return None

        node = self.__node_class(self, op, name=name)
        self.__nodes[node.id()] = node

        return node

    def __delNode(self, node):
        node.disconnectAll()
        for on in node.outputs():
            indice = []
            for i, io in enumerate(on.inputs()):
                if io == node:
                    indice.append(i)

            for i in indice:
                on.disconnect(i)

        del node

    def deleteNode(self, node):
        if node.id() not in self.__nodes:
            return False

        self.__nodes.pop(node.id())

        self.__delNode(node)

        return True

    def nodes(self):
        return [x for x in self.__nodes.values()]

    def getUniqueName(self, name):
        index = 0

        while (True):
            nname = f"{name}{index}" if index > 0 else name

            used = False
            for n in self.__nodes.values():
                if n.name() == nname:
                    used = True
                    break

            if not used:
                return nname

            index += 1

    def read(self, filepath):
        pass

    def write(self, filepath):
        pass

    def clear(self):
        keys = list(self.__nodes.keys())

        for k in keys:
            v = self.__nodes.pop(k)
            del v

        return True

    def toDict(self):
        d = {
            "nodes": [],
            "connections": []
        }

        for n in self.__nodes.values():
            params = {}
            for pn in n.paramNames():
                params[pn] = n.getParamValue(pn)

            d["nodes"].append(
                {
                    "name": n.name(),
                    "type": n.type(),
                    "id": n.id(),
                    "params": params
                }
            )

            for i, inp in enumerate(n.inputs()):
                if inp is None:
                    continue

                d["connections"].append(
                    {
                        "src": inp.id(),
                        "dst": n.id(),
                        "index": i,
                    }
                )

        return d
