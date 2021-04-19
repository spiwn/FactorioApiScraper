from collections import OrderedDict
from enum import Flag, auto, Enum

class Flags(Flag):
    Struct = 1
    Dummy = 2

    def toJson(self):
        return self.name

class Types(Enum):
    Simple = 1
    Array = 2
    Union = 3
    Table = 4
    Function = 5

    def toJson(self):
        return self.name

class DataMeta(type):
    def __new__(mcs, name, bases, d):
        parent = None if not bases else bases[0]

        allAttributes = dict() if (not parent) else dict(parent.__allAttributes)
        #currentAttributes = { i : None if type(attributes) != dict else attributes[i] for i in attributes}

        currentAttributes = {}
        whitelist = d.get("_attributes")
        for k,v in d.items():
            if whitelist:
                if k in whitelist:
                    currentAttributes[k] = v
            else:
                if not k.startswith("_"):
                    currentAttributes[k] = v

        allAttributes.update(currentAttributes)
        def init(self, **kwargs):
            if parent:
                parent.__init__(self, **kwargs)
            for key,value in  currentAttributes.items():
                self.__setattr__(key, kwargs.get(key) or value and value())

        def setter(self, k, v):
            if k not in allAttributes:
                raise Exception("Unknown attribute: " + k)
            object.__setattr__(self, k, v)

        def strMethod(self):
            result = [name, "("]
            for key in allAttributes:
                value = getattr(self, key)
                if value:
                    result.append(k)
                    result.append("=")
                    result.append(str(value))
            result.append(")")
            return " ".join(result)

            return name + " " + " ".join((k + "=" + getattr(self, k) for k in allAttributes))

        def toJson(self):
            return {k: getattr(self, k) for k in allAttributes if getattr(self, k, None) is not None}

        for k in currentAttributes:
            d.pop(k)

        d["__init__"] = init
        d["__setattr__"] = setter #TODO: comment this out, it is just for development/testing
        d["__str__"] = strMethod
        if "toJson" in d:
            d["_toJson"] = toJson
        else:
            d["toJson"] = toJson

        resultClass = type(name, bases, d)
        resultClass.__allAttributes = allAttributes
        return resultClass

class DocObject(metaclass = DataMeta):
    name = None
    shortDesc = None
    desc = None
    url = None
    def __init__(self, **kwargs):
        pass

class DefinesGroup(DocObject, metaclass = DataMeta):
    defines = OrderedDict
    def __init__(self, **kwargs):
        pass

class ObjectType(metaclass = DataMeta):
    value = None
    type = None
    def __init__(self, **kwargs):
        pass

class Event(DocObject, metaclass = DataMeta):
    contains = list
    def __init__(self, **kwargs):
        pass

class Attribute(DocObject, metaclass = DataMeta):
    type = None
    optional = False
    def __init__(self, **kwargs):
        pass

class Field(Attribute, metaclass = DataMeta):
    mode = None
    _attributes = ("mode",)
    def __init__(self, **kwargs):
        pass

    def toJson(self):
        result = self._toJson()
        result['attribute_type'] = 'field'
        return result

class Parameter(Attribute, metaclass = DataMeta):
    optional = bool
    def __init__(self, **kwargs):
        pass

class FunctionObject(DocObject, metaclass = DataMeta):
    parameters = None
    returnObject = None
    additionalTypes = None
    _attributes = ("parameters", "returnObject", "additionalTypes")

    def __init__(self, **kwargs):
        pass

    def toJson(self):
        result = self._toJson()
        result['attribute_type'] = 'function'
        return result

class ClassObject(DocObject, metaclass = DataMeta):
    attributes = None
    inherits = None
    parents = None
    flags = lambda: Flags(0)
    #TODO: Rename
    _attributes = ("attributes", "inherits", "flags", "parents")

    def __init__(self, **kwargs):
        pass

    def setFlag(self, flag):
        self.flags = self.flags | flag

    def unsetFlag(self, flag):
        self.flags = self.flags & ~flag

    def hasFlag(self, flag):
        return bool(self.flags & flag)

    def toJson(self):
        result = self._toJson()
        if self.flags.value == 0:
            result.pop("flags")
            pass
        return result

class AliasType(DocObject, metaclass = DataMeta):
    type = None
    def __init(self, **kwargs):
        pass