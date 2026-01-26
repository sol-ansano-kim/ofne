from ..exceptions import OFnNotImplementedError


class _GraphNodeBase(object):
    def __init__(self, node):
        super(_GraphNodeBase, self).__init__()

    def node(self):
        raise OFnNotImplementedError(self, "node")

    def dirty(self):
        raise OFnNotImplementedError(self, "dirty")

    def isDirty(self):
        raise OFnNotImplementedError(self, "isDirty")

    def evaluate(self, packetArray):
        raise OFnNotImplementedError(self, "evaluate")

    def packet(self):
        raise OFnNotImplementedError(self, "packet")

    def result(self):
        raise OFnNotImplementedError(self, "result")

    def errorMessage(self):
        raise OFnNotImplementedError(self, "errorMessage")


class _GraphSceneBase(object):
    def __init__(self, scene):
        super(_GraphSceneBase, self).__init__()

    def evaluate(self, nodes, force=False):
        raise OFnNotImplementedError(self, "evaluate")

    def packet(self, nodes):
        raise OFnNotImplementedError(self, "packet")

    def failedNodes(self):
        raise OFnNotImplementedError(self, "failedNodes")

    def errorMessage(self, node):
        raise OFnNotImplementedError(self, "errorMessage")
