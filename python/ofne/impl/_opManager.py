import os
import re
import inspect
import traceback
import importlib.util


RE_PY = re.compile(r"\.py$", re.IGNORECASE)


class _OFnOpManagerImpl(object):
    def __init__(self, opClass):
        super(_OFnOpManagerImpl, self).__init__()
        self.__opClass = opClass
        self.__plugins = {}
        self.reloadPlugins()

    def reloadPlugins(self):
        self.__plugins = {}
        builtins = os.path.abspath(os.path.join(__file__, "../../builtins"))
        for path in [builtins] + os.environ.get("OFNE_PLUGIN_PATH", "").split(os.pathsep):
            if not path:
                continue

            path = os.path.normpath(os.path.abspath(path))

            if not os.path.isdir(path):
                continue

            for f in os.listdir(path):
                fp = os.path.join(path, f)
                fp = os.path.normpath(os.path.abspath(fp))
                if not os.path.isfile(fp):
                    continue

                if not RE_PY.search(f):
                    continue

                mdl = None
                try:
                    spec = importlib.util.spec_from_file_location(f"_ofne_plugin{os.path.splitext(f)[0]}", fp)
                    mdl = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mdl)
                except Exception as e:
                    traceback.print_exc()
                    print(f"WARNING : Failed to load the file {fp}")

                if not mdl:
                    continue

                classes = inspect.getmembers(mdl, inspect.isclass)
                objs = [x[1]() for x in classes if issubclass(x[1], self.__opClass) and x[1] != self.__opClass]
                for obj in objs:
                    self.registerOp(obj)

    def listOps(self):
        return sorted(self.__plugins.keys())

    def getOp(self, opName):
        return self.__plugins.get(opName)

    def registerOp(self, op):
        if not isinstance(op, self.__opClass):
            print(f"WARNING : {op} is not a {self.__opClass} object")
            return False

        if op.type() in self.__plugins:
            print(f"WARNING : {op.type()} is registered already, ignored")
            return False

        self.__plugins[op.type()] = op

        return True

    def deregisterOp(self, op):
        if op.type() not in self.__plugins:
            return False

        if op != self.__plugins[op.type()]:
            return False

        self.__plugins.pop(op.type())

        return True
