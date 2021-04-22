from pathlib import Path
from common import *

encoding = "utf8"

def openForWriting(directory, filename):
    return open(directory.joinpath(filename), 'w', encoding=encoding)

def escapeName(name):
    return name.replace(" ", "_")

def writeMetaHeader(w):
    w.write("---@meta\n\n")

def writeDesc(desc, w):
    for line in desc.split("\n"):
        w.write("---")
        w.write(line.strip())
        w.write("\n")

def writeFullDesc(shortDesc, desc, w):
    if shortDesc:
        if desc and desc != shortDesc and not desc.startswith(shortDesc):
            writeDesc(shortDesc, w)
    if desc:
        writeDesc(desc, w)

counter = [0, 0, 0, 0]

def writeObjectType(objectType, w):
    if objectType is None:
        w.write("any")
    if isinstance(objectType, str):
        w.write(objectType)
        return
    if objectType.value is None and objectType.type is None:
        counter[3] += 1
        w.write("any")
        return
    if objectType.type == Types.Function:
        #TODO: Search for a meaningful way to document these - so far there is none
        w.write("fun():nil")
        return
    if objectType.type is None or objectType.type == Types.Simple:
        if isinstance(objectType.value, list):
            writeObjectType(objectType.value[0], w)
        else:
            #TODO: count and remove
            writeObjectType(objectType.value, w)
        return
    if objectType.type == Types.Union:
        notFirst = False
        for t in objectType.value:
            if notFirst:
                w.write("|")
            writeObjectType(t, w)
            notFirst = True
        return
    if objectType.type == Types.Array:
        if type(objectType.value) in (list, tuple):
            writeObjectType(objectType.value[0], w)
        else:
            writeObjectType(objectType.value, w)
        w.write("[]")
        return
    if objectType.type == Types.Table:
        w.write("table<")
        writeObjectType(objectType.value[0], w)
        w.write(",")
        writeObjectType(objectType.value[1], w)
        w.write(">")
        return
    raise Exception("Unknown object type: " + objectType.type)

def writeFunctionObject(functionObject, escapedName, w):
    w.write("\n")

    if functionObject.additionalTypes:
        for clazz in functionObject.additionalTypes:
            writeClass(clazz, w)
            w.write("\n")

    writeFullDesc(functionObject.shortDesc, functionObject.desc, w)
    w.write("---\n")
    if functionObject.parameters:
        for _, parameter in functionObject.parameters.items():
            w.write("---@param ")
            w.write(parameter.name)
            if parameter.optional:
                w.write("?")
            w.write(" ")
            writeObjectType(parameter.type, w)
            if parameter.desc or parameter.shortDesc:
                w.write(" ")
                w.write(parameter.desc or parameter.shortDesc)
            w.write("\n")
            w.write("---\n")
    returnObject = functionObject.returnObject
    if returnObject:
        if not isinstance(returnObject, str) and functionObject.returnObject.desc:
            writeDesc(functionObject.returnObject.desc, w)
        w.write("---@return ")
        if isinstance(returnObject, str):
            # TODO: all returnObjects should be instances of Attribute?
            w.write(returnObject)
        else:
            writeObjectType(functionObject.returnObject.type, w)
        w.write("\n")
    w.write(escapedName)
    w.write(".")
    w.write(functionObject.name)
    w.write(" = function(")
    if functionObject.parameters:
        count = 0
        for _, parameter in functionObject.parameters.items():
            if count > 0:
                w.write(", ")
            w.write(parameter.name)
            count += 1
    w.write(") end\n")

def writeClass(clazz, w):
    escapedName = escapeName(clazz.name)
    writeFullDesc(clazz.shortDesc, clazz.desc, w)
    w.write("---@class ")
    w.write(escapedName)

    if clazz.parents:
        w.write(":")
        writeComma = False
        for parent in clazz.parents:
            if writeComma:
                w.write(", ")
            w.write(parent)
            writeComma = True

    w.write("\n")

    hasMethods = False

    if clazz.attributes:
        for k, attribute in clazz.attributes.items():
            if isinstance(attribute, FunctionObject):
                hasMethods = True
                continue
            w.write("---\n")
            writeFullDesc(attribute.shortDesc, attribute.desc, w)
            w.write("---")
            w.write("@field ")
            w.write(attribute.name)
            w.write(" ")
            writeObjectType(attribute.type, w)
            w.write("\n")

    if not hasMethods and not clazz.attributes and not clazz.parents and not clazz.desc and not clazz.shortDesc:
        #print("What it is my purpose?: ", clazz.name)
        pass

    if hasMethods:

        #maybe the local variable name has a prefix
        w.write("local ")
        w.write(escapedName)
        w.write(" = {}\n")

        for k, attribute in clazz.attributes.items():
            if not isinstance(attribute, FunctionObject):
                continue
            writeFunctionObject(attribute, escapedName, w)


def writeSingleDefine(define, w, prefix):
    escapedName = escapeName(define.name)

    if isinstance(define, Event):
        if define.contains:
            for clazz in define.contains:
                w.write("\n")
                writeClass(clazz, w)
        else:
            print(define.name)
            raise Exception("Event with no parameters")
    else:
        writeFullDesc(define.shortDesc, define.desc, w)

    w.write(prefix)
    w.write(escapedName)

    if isinstance(define, DefinesGroup):
        if define.defines:
            w.write(' = {\n')
            #newPrefix = prefix + define.name + "."
            newPrefix = prefix + "  "
            for child in define.defines.values():
                writeSingleDefine(child, w, newPrefix)
            w.write(prefix)
            w.write("}")
            if define.name != "defines":
                w.write(",")
            w.write("\n")
        else:
            w.write(" = {},\n")
    elif isinstance(define, Event):
        #w.write(' = function(parameters) end\n')
        #w.write(" = number\n")
        w.write(" = ")
        #w.write(escapedName)
        w.write("0,")
        w.write("\n")
    elif not isinstance(define, DefinesGroup):
        #w.write(' = "n/a"\n')
        w.write(" = 0,\n")
    else:
        raise Exception("Unknown value type in defines: ", type(DefinesGroup), define.name)

def writeDefines(context, directory):
    with openForWriting(directory, "defines.lua") as w:
        writeMetaHeader(w)

        writeClass(context.commonEventParameters, w)
        w.write("\n")

        writeSingleDefine(context.defines, w, "")

        w.write("\n")
        w.write("return defines\n")

def writeClasses(context, directory):
    classesDirPath = directory.joinpath("classes")
    classesDirPath.mkdir(parents = True, exist_ok = True)

    parentClassesFilePath = classesDirPath.joinpath()
    with openForWriting(classesDirPath, "Parents.lua") as w:
        for _, clazz in context.commonClasses.items():
            writeClass(clazz, w)
            w.write("\n")

    for _, clazz in context.classes.items():
        with openForWriting(classesDirPath, clazz.name + ".lua") as w:
            writeMetaHeader(w)
            writeClass(clazz, w)
            w.write("\n")

def writeGlobalClasses(context, directory):
    with openForWriting(directory, "globalClasses.lua") as w:
        for k, v in context.globalClasses.items():
            w.write("---@type ")
            w.write(v)
            w.write("\n")
            w.write(k)
            w.write(" = {}\n")
        w.write("\n")
    pass

def writeAliasType(alias, w):
    if alias.shortDesc or alias.desc:
        writeFullDesc(alias.shortDesc, alias.desc, w)
    w.write("---@alias ")
    w.write(alias.name)
    w.write(" ")
    writeObjectType(alias.type, w)
    w.write("\n")
    pass

def writeConceptTypes(context, directory):
    with openForWriting(directory, "concepts.lua") as w:
        writeMetaHeader(w)
        for k, v in context.conceptTypes.items():
            if isinstance(v, ClassObject):
                writeClass(v, w)
            elif isinstance(v, AliasType):
                writeAliasType(v, w)
            else:
                raise Exception()
            w.write("\n")
        w.write("\n")
    pass

def writeBuiltintypes(context, directory):
    luaTypeMapping = {
        'float' : 'number',
        'double' : 'number',
        'int' : 'integer',
        'int8' : 'integer',
        'uint' : 'integer',
        'uint8' : 'integer',
        'uint16' : 'integer',
        'uint64' : 'integer',
        'string' : 'string',
        'boolean' : 'boolean',
        'table' : 'table'
    }

    with openForWriting(directory, "builtinTypes.lua") as w:
        writeMetaHeader(w)

        for builtinType in context.builtinTypes.values():
            writeFullDesc(builtinType.shortDesc, builtinType.desc, w)
            w.write("---@alias ")
            w.write(builtinType.name)
            w.write(" ")
            w.write(luaTypeMapping.get(builtinType.name, 'any'))
            w.write("\n\n")


def formatDocumentation(context : Context, directory):
    writeDefines(context, directory)
    writeClasses(context, directory)
    writeConceptTypes(context, directory)
    writeGlobalClasses(context, directory)
    writeBuiltintypes(context, directory)
    print(counter)

def main():
    import pickle
    __outputDirPath = Path("output")
    __outputDirPath.mkdir(parents=True, exist_ok=True)
    with open(__outputDirPath.joinpath("context.txt"), 'rb') as r:
        formatDocumentation(pickle.load(r), __outputDirPath)
    print("Done")

if __name__ == "__main__":
    main()