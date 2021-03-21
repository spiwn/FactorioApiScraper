from common import *

def _parseCommon(soup, context):
    context.commonClassAttributes = {}
    bl = soup.find("div", "brief-listing", id = "Common.brief")
    table = bl.findChild("table", recursive = False)
    trs = table.findChildren("tr")
    for tr in trs:
        headerTd = tr.findChild("td", "header", recursive = False)
        elementNameNode = headerTd.findChild("span", "element-name", recursive = False)
        aNode = elementNameNode.findChild("a", recursive = False)
        name = aNode.get_text(strip = True)
        returnTypeNode = elementNameNode.findChild("span", "return-type", recursive = False)
        #returnTypeString = None
        function = False
        mode = None
        if returnTypeNode:
            returnTypeString = returnTypeNode.findChild("span", "param-type", recursive = False).findChild("a", recursive = False).get_text(strip = True)
            function = True
        else:
            returnTypeString = headerTd.findChild("span", "attribute-type", recursive = False)\
                .findChild("span", "param-type", recursive = False)\
                .findChild("a", recursive = False)\
                .get_text(strip = True)
            mode = headerTd.findChild("span", "attribute-mode").get_text(strip = True)
        description = tr.findChild("td", "description", recursive = False)

        desc = description.get_text(strip = True)

        #result = None
        if function:
            result = FunctionObject(name = name, returnObject = returnTypeString, desc = desc)
        else:
            result = Attribute(name = name, mode = mode, type = returnTypeString, desc = desc)
        context.commonClassAttributes[name] = result


    for clazz in (
            ClassObject(name = "LuaObject",
                        attributes = OrderedDict({"object_name" : context.commonClassAttributes["object_name"]})),
            ClassObject(name = "LuaObjectHelp",
                        parents = ["LuaObject"],
                        attributes = OrderedDict({"help": context.commonClassAttributes["help"]})),
            ClassObject(name = "LuaObjectValid",
                        parents = ["LuaObject"],
                        attributes = OrderedDict({"valid": context.commonClassAttributes["valid"]}))):
        context.commonClasses[clazz.name] = clazz

def parse_common(context):
    soup = context.retriever.get(commonURL)
    _parseCommon(soup, context)