from pathlib import Path
from common import *

encoding = "utf8"

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
        writeObjectType(objectType.value[0], w)
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

    if clazz.attributes:
        for k, attribute in clazz.attributes.items():
            if isinstance(attribute, FunctionObject):
                continue
            w.write("---\n")
            writeFullDesc(attribute.shortDesc, attribute.desc, w)
            w.write("---")
            w.write("@field ")
            w.write(attribute.name)
            w.write(" ")
            writeObjectType(attribute.type, w)
            w.write("\n")

    #maybe the local variable name has a prefix
    w.write("local ")
    w.write(escapedName)
    w.write(" = {}\n")

    if clazz.attributes:
        for k, attribute in clazz.attributes.items():
            if not isinstance(attribute, FunctionObject):
                continue
            w.write("\n")
            writeFullDesc(attribute.shortDesc, attribute.desc, w)
            w.write("---\n")
            if attribute.parameters:
                for _, parameter in attribute.parameters.items():
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
            returnObject = attribute.returnObject
            if returnObject:
                if not isinstance(returnObject, str) and attribute.returnObject.desc:
                    writeDesc(attribute.returnObject.desc, w)
                w.write("---@return ")
                if isinstance(returnObject, str):
                    #TODO: all returnObjects should be instances of Attribute
                    w.write(returnObject)
                else:
                    writeObjectType(attribute.returnObject.type, w)
                w.write("\n")
            w.write(escapedName)
            w.write(".")
            w.write(attribute.name)
            w.write(" = function(")
            if attribute.parameters:
                count = 0
                for _, parameter in attribute.parameters.items():
                    if count > 0:
                        w.write(", ")
                    w.write(parameter.name)
                    count += 1
            w.write(") end\n")

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
    writeFullDesc(define.shortDesc, define.desc, w)

    # if isinstance(define, Event):
    #     w.write("---@param parameters ")
    #     w.write(define.contains[-1].name)
    #     w.write("\n")

    w.write(prefix)
    w.write(escapedName)

    if isinstance(define, DefinesGroup) and define.defines:
        w.write(' = "{}"\n')
        newPrefix = prefix + define.name + "."
        for child in define.defines.values():
            writeSingleDefine(child, w, newPrefix)
        w.write("\n")
    if isinstance(define, Event):
        #w.write(' = function(parameters) end\n')
        #w.write(" = number\n")
        w.write(" = ")
        w.write(escapedName)
        w.write("\n")
    elif not isinstance(define, DefinesGroup):
        #w.write(' = "n/a"\n')
        w.write(" = number\n")

def writeDefines(context, directory):
    with open(directory.joinpath("defines.lua"), 'w', encoding = encoding) as w:
        writeMetaHeader(w)
        w.write("---@class defines\n")
        w.write("defines = {}\n\n")

        writeClass(context.commonEventParameters, w)

        writeSingleDefine(context.defines, w, "")
        w.write("return defines\n")

def writeClasses(context, directory):
    classesDirPath = directory.joinpath("classes")
    classesDirPath.mkdir(parents = True, exist_ok = True)

    parentClassesFilePath = classesDirPath.joinpath("Parents.lua")
    with open(parentClassesFilePath, 'w', encoding = encoding) as w:
        for _, clazz in context.commonClasses.items():
            writeClass(clazz, w)
            w.write("\n")

    for _, clazz in context.classes.items():
        classFilePath = classesDirPath.joinpath(clazz.name + ".lua")
        with open(classFilePath, 'w', encoding = encoding) as w:
            writeMetaHeader(w)
            writeClass(clazz, w)
            w.write("\n")

def writeGlobalClasses(context, directory):
    with open(directory.joinpath("globalClasses.lua"), 'w', encoding = encoding) as w:
        for k, v in context.globalClasses.items():
            w.write("---@type ")
            w.write(v)
            w.write("\n")
            w.write(k)
            w.write(" = {}\n")
        w.write("\n")
    pass

def formatDocumentation(context : Context, directory):
    writeDefines(context, directory)
    writeClasses(context, directory)
    writeGlobalClasses(context, directory)
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