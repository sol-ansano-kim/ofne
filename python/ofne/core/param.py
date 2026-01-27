from . import abst
from .. import exceptions


ParamTypeBool = 0
ParamTypeInt = 1
ParamTypeFloat = 2
ParamTypeStr = 3
ParamTypeCode = 4


class OFnParamBase(abst._ParamBase):
    def __init__(self, name, default, label=None):
        super(OFnParamBase, self).__init__(name, default, label=label)
        self.__name = name
        self.__label = label or name
        self.__value = None
        self.__default = None

        self.set(default)
        self.__default = self.__value

    def name(self):
        return self.__name

    def label(self):
        return self.__label

    def default(self):
        return self.__default

    def get(self):
        return self.__value

    def set(self, value):
        if not self.isValid(value):
            raise exceptions.OFnInvalidParamValueError(self, value)

        self.__value = value

    def type(self):
        raise exceptions.OFnNotImplementedError(self, "type")

    def isValid(self, value):
        raise exceptions.OFnNotImplementedError(self, "isValid")

    def copy(self):
        raise exceptions.OFnNotImplementedError(self, "copy")


class OFnParamBool(OFnParamBase):
    def __init__(self, name, default=False, label=None):
        super(OFnParamBool, self).__init__(name, default, label=label)

    def type(self):
        return ParamTypeBool

    def isValid(self, value):
        return isinstance(value, bool)

    def copy(self):
        n = OFnParamBool(self.name(), self.default(), label=self.label())
        n.set(self.get())

        return n


class OFnParamStr(OFnParamBase):
    def __init__(self, name, default="", label=None, valueList=None, enforceValueList=False):
        self.__value_list = list(valueList) if isinstance(valueList, (list, tuple, set)) else []
        self.__enforce_value_list = enforceValueList if self.__value_list else False

        super(OFnParamStr, self).__init__(name, default, label=label)

    def type(self):
        return ParamTypeStr

    def enforceValueList(self):
        return self.__enforce_value_list

    def valueList(self):
        return self.__value_list[:]

    def isValid(self, value):
        if not isinstance(value, str):
            return False

        if self.__enforce_value_list and value not in self.__value_list:
            return False

        return True

    def copy(self):
        n = OFnParamStr(self.name(), default=self.default(), label=self.label(), valueList=self.__value_list, enforceValueList=self.__enforce_value_list)
        n.set(self.get())

        return n


class OFnParamCode(OFnParamBase):
    def __init__(self, name, default="", label=None):
        super(OFnParamCode, self).__init__(name, default=default, label=None)

    def type(self):
        return ParamTypeCode

    def isValid(self, value):
        if not isinstance(value, str):
            return False

        return True

    def copy(self):
        n = OFnParamCode(self.name(), default=self.default(), label=self.label())
        n.set(self.get())

        return n


class OFnNumericParam(OFnParamBase):
    def __init__(self, name, default=None, label=None, min=None, max=None):
        self.__min = min
        self.__max = max

        super(OFnNumericParam, self).__init__(name, default, label=label)

    def min(self):
        return self.__min

    def max(self):
        return self.__max

    def isValid(self, value):
        if self.__min is not None and value < self.__min:
            return False

        if self.__max is not None and value > self.__max:
            return False

        return True

    def copy(self):
        n = self.__class__(self.name(), default=self.default(), label=self.label(), min=self.__min, max=self.__max)
        n.set(self.get())

        return n


class OFnParamInt(OFnNumericParam):
    def __init__(self, name, default=0, label=None, min=None, max=None):
        super(OFnParamInt, self).__init__(name, default=default, label=label, min=min, max=max)

    def type(self):
        return ParamTypeInt

    def isValid(self, value):
        if not isinstance(value, int):
            return False

        if isinstance(value, bool):
            return False

        return super(OFnParamInt, self).isValid(value)


class OFnParamFloat(OFnNumericParam):
    def __init__(self, name, default=0.0, label=None, min=None, max=None):
        super(OFnParamFloat, self).__init__(name, default=default, label=label, min=min, max=max)

    def type(self):
        return ParamTypeFloat

    def isValid(self, value):
        if not isinstance(value, float):
            return False

        return super(OFnParamFloat, self).isValid(value)


class OFnParams(abst._ParamsBase):
    def __init__(self, paramList):
        super(OFnParams).__init__()
        self.__params = []
        self.__param_map = {}
        for param in paramList:
            cp = param.copy()
            self.__params.append(cp)
            self.__param_map[param.name()] = cp

    def copy(self):
        return OFnParams(self.__params)

    def getParam(self, key):
        if key not in self.__param_map:
            return None

        return self.__param_map[key].copy()

    def get(self, key, default=None):
        if key not in self.__param_map:
            return default

        return self.__param_map[key].get()

    def set(self, key, value):
        if key not in self.__param_map:
            return False

        self.__param_map[key].set(value)
        return True

    def keys(self):
        return [x.name() for x in self.__params]
