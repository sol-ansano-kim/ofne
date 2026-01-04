class OFnUINode(object):
    def __init__(self, node):
        super(OFnUINode, self).__init__()
        self.__node = node
        self.__pos_x = 0
        self.__pos_y = 0


class OFnUIScene(object):
    def __init__(self, scene):
        super(OFnUIScene, self).__init__()
        self.__scene = scene
        self.__nodes = {}

    def createNode(self, op_type):
        print(op_type)