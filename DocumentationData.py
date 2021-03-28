from collections import OrderedDict
from enum import Flag, auto, Enum

class Flags(Flag):
    Struct = auto()
    Dummy = auto()

class Types(Enum):
    Simple = auto()
    Array = auto()
    Union = auto()
    Table = auto()
    Function = auto()

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
            for k,v in  currentAttributes.items():
                self.__setattr__(k, kwargs.get(k) or v and v())

        def setter(self, k, v):
            if k not in allAttributes:
                raise Exception("Unknown attribute: " + k)
            object.__setattr__(self, k, v)

        for k in currentAttributes:
            d.pop(k)

        d["__init__"] = init
        d["__setattr__"] = setter #TODO: comment this out, it is just for development/testing
        result = type(name, bases, d)
        result.__allAttributes = allAttributes
        return result

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
    def __init__(self, **kwargs):
        pass

class Parameter(Attribute, metaclass = DataMeta):
    optional = bool
    def __init__(self, **kwargs):
        pass

class FunctionObject(DocObject, metaclass = DataMeta):
    parameters = None
    returnObject = None
    def __init__(self, **kwargs):
        pass

class ClassObject(DocObject, metaclass = DataMeta):
    attributes = None
    inherits = None
    parents = None
    flags = lambda: Flags(0)
    _attributes = ("attributes", "inherits", "flags", "parents")
    def __init__(self, **kwargs):
        pass

    def setFlag(self, flag):
        self.flags = self.flags | flag

    def unsetFlag(self, flag):
        self.flags = self.flags & ~flag

    def hasFlag(self, flag):
        return bool(self.flags & flag)
