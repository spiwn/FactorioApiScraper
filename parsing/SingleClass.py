from common import *
from parsing.Attribute import parse_attribute_doc
import re

#Inherited from LuaControlBehavior: get_circuit_network, type, entity
inheritsRe = re.compile("Inherited from (?P<clname>\\w+)\\s*:\\s*(?P<attributes>(?:(?:\\s*,\\s*)?\\w+)+)")

attributesRe = re.compile("\\s*,\\s*")
bracketRe = re.compile("[{(]")

def getReturnTypes(children, context):
    types = []
    valueType = None
    for e, child in enumerate(children):
        if isinstance(child, str):
            stripped = child.strip()
            if "→" == stripped:
                continue
            if stripped == "dictionary":
                valueType = Types.Table
                types.append(getReturnTypes(tuple(children[e + 1].children), context))
                types.append(getReturnTypes(tuple(children[e + 3].children), context))
                break
            if "array of" == stripped:
                valueType = Types.Array
            elif "or" == stripped:
                #print("zzz", context.breadcrumbs)
                valueType = Types.Union
            elif stripped in {"function()", "function"}:
                valueType = Types.Function
                break
            elif "function(" == stripped:
                #print("c2", children[e + 1:])
                #TODO: I could not find any meaningful way of documenting these parameters
                valueType = Types.Function
                break
            elif stripped:
                #TODO: these are mostly exceptions
                #print("foo", stripped, context.breadcrumbs)
                types.append(stripped)

            else:
                continue

        elif child.name == "span" and "param-type" in child.get("class"):
            types.append(getReturnTypes(list(child.children), context))
        elif child.name == "a":
            types.append(child.get_text(strip = True))
        else:
            #TODO: check if something strange goes through here
            types.append(child.get_text(strip = True))
    if valueType is None and len(types) == 1:
        return types[0]
    return ObjectType(
        type = valueType,
        value = types
    )

def parseDescription(soup, element, className):
    classDoc = []
    h1 = soup.findChild("h1")
    desc = soup.find("body").findChild("div", "brief-description", recursive=False)

    if h1 and h1.get_text(strip = True) == className and desc:
        root = desc
    else:
        root = element.find("div", "element-content", recursive=False)
    if root is None:
        raise Exception("No class info found")

    hasChildren = False
    for e in root.children:
        hasChildren = True
        if isinstance(e, str):
            classDoc.append(e)
        else:
            if e.name == "p":
                classDoc.append(md.handleDocString(e))
            elif e.name == "ul":
                classDoc.append(md.handleDocString(e, isList=True, listChar=0, sep=md.lineBreak))
            elif e.name == "div":
                classes = e.get("class")
                if classes:
                    if "example" in classes:
                        classDoc.append(md.handleDocString(e))
                    elif "notes" in classes:
                        classDoc.append(md.handleDocString(e))
                    elif "element" in classes:
                        #print("element", e.get("id"))
                        pass
                    else:
                        print("Unknown div class", classes)
                else:
                    print("Div does not have a class")
            else:
                print("Unknown element", e.name)
    if not hasChildren:
        print("No description", className)
    return classDoc

def parseShortDescription(soup, clName):
    shortDescriptions = {}
    hasValid = False
    hasHelp = False
    table = soup.find("div", "brief-listing", id = clName + ".brief").findChild("table", recursive = False)
    for tr in table.findChildren("tr", recursive = False):
        nameSpan = tr.findChild("td", "header").findChild("span", "element-name", recursive = False)
        anchorNode = nameSpan.findChild("a", recursive = False)

        if anchorNode:
            name = anchorNode.get_text(strip = True)
            if name == "valid":
                hasValid = True
            elif name == "help":
                hasHelp = True
            else:
                shortDescriptions[name] = md.handleDocString(tr.findChild("td", "description", recursive = False))
                t = shortDescriptions[name]
    return hasHelp, hasValid, shortDescriptions

def parseParameter(parentElement, context):
    paramNameSpan = parentElement.findChild("span", "param-name", recursive = False)
    if not paramNameSpan:
        return None
    argName = paramNameSpan.get_text(strip = True)
    parameterType = None
    typeNode = parentElement.findChild("span", "param-type", recursive = False)
    if typeNode:
        if argName == "peaks":
            print("peaks")
        parameterType = getReturnTypes(tuple(typeNode.children), context)
    else:
        parameterType = "any"
        # TODO: temporary workaround
    fieldListNode = parentElement.findChild("ul", "field-list", recursive = False)
    parameterDoc = parse_attribute_doc(parentElement, fieldListNode)
    if fieldListNode:
        pass

    if parameterDoc:
        # TODO: fix this
        # It seems that beautifulsoup returns a string containing new lines so they must be removed
        # An example is LuaBootstrap.on_event f parameter's description
        parameterDoc = " ".join(map(lambda x: x.replace("\n", " "), filter(lambda x: x, parameterDoc)))
    parameter = Parameter(
        name = argName,
        type = parameterType,
        desc = parameterDoc)
    return parameter

def parseField(row, modeNode, context):
    elementContent = row.findChild("div", "element-content", recursive = False)
    attributeDoc = []
    if elementContent:
        attributeDoc.append(md.handleDocString(elementContent))
        # print(1, doc[-1])
    typeNode = row.findChild("span", "attribute-type")
    if typeNode:
        attributeType = getReturnTypes(tuple(typeNode.findChild("span", "param-type").children), context)
    else:
        # TODO: temporary workaround
        attributeType = "any"
    modeString = modeTranslation[modeNode.get_text(strip = True)]
    tempDoc = " ".join(filter(lambda x: x, attributeDoc))
    attribute = Attribute(
        desc = tempDoc,
        mod = modeString,
        type = attributeType)
    return attribute

nameRe = re.compile("(?P<name>\w+)\s*(?P<bracket>\{|\()(?P<signature>.+?)(?:→(?P<returnType>.+))?")

def parseMethod(row, context):
    returnDesc = None
    returnType = None
    parametersAsTable = False
    attributeDoc = []
    args = OrderedDict()
    elementHeader = row.findChild("div", "element-header", recursive = False)
    nameNode = elementHeader.findChild("span", "element-name", recursive = False)
    methodName = nameNode.get_text(strip = True)
    nameMatch = nameRe.match(methodName)
    methodName = nameMatch.group("name")
    openingBracket = nameMatch.group("bracket")
    if nameMatch:
        #print(nameMatch.group("bracket"))
        pass
    #print(name, callSignature)
    elementContent = row.findChild("div", "element-content", recursive = False)
    attributeDoc.append(md.handleDocString(elementContent, maxDepth = 1))
    returnSpan = row.findChild("span", "return-type")
    if returnSpan:
        pt = returnSpan.findChild("span", "param-type", recursive = False)
        returnType = getReturnTypes(tuple(pt.children), context)
    returnValueDetailFound = False
    additionalTypes = []
    for detail in elementContent.findChildren("div", "detail", recursive = False) or ():
        header = detail.findChild("div", "detail-header")
        if header is None:
            # TODO: check where this happens
            attributeDoc.append(md.handleDocString(detail))
            continue

        headerText = header.get_text(strip = True)

        if headerText == "Parameters":
            # doc.append(md.strong(headerText))
            dc = detail.find("div", "detail-content")
            count = 0
            for div in dc.findChildren("div", recursive = False):
                count += 1
                if not div.findChild("span", "param-name", recursive = False):
                    if not list(div.children):
                        continue

                    fieldListNode = div.findChild("ul", "field-list", recursive = False)
                    doc = parse_attribute_doc(div, fieldListNode)
                    if len(doc) == 1 and "Table with the following fields" == doc[0]:
                        parametersAsTable = True
                        #print(context.breadcrumbs)
                    elif openingBracket == '{':
                        parametersAsTable = True
                    else:
                        print(methodName)
                    subParameters = OrderedDict()
                    for li in fieldListNode.findChildren("li", recursive = False):
                        parameter = parseParameter(li, context)
                        if parameter:
                            subParameters[parameter.name] = parameter

                    if parametersAsTable:
                        dummyClass = ClassObject(
                            name = context.clazz + methodName + "_param",
                            attributes = subParameters,
                            flags = Flags.Dummy)
                        additionalTypes.append(dummyClass)
                        desc = None
                        if doc:
                            desc = " ".join(map(lambda x: x.replace("\n", " "), filter(lambda x: x, doc)))
                        parameter = Parameter(
                            name = dummyClass.name[0].lower() + dummyClass.name[1:],
                            type = dummyClass.name,
                            desc = desc)
                else:
                    parameter = parseParameter(div, context)
                args[parameter.name] = parameter
        elif headerText == "Return value":
            returnValueDetailFound = True
            returnDesc = md.handleDocString(header.find_next_sibling("div", "detail-content"))
        elif headerText == "See also":
            attributeDoc.append(md.strong(headerText))
            attributeDoc.append(md.handleDocString(detail))
        else:
            raise Exception("Unknown headerText: " + headerText)
    if not returnValueDetailFound:
        # print(returnType)
        pass
    tempDoc = " ".join(filter(lambda x: x, attributeDoc))
    returnObject = None
    if returnType:
        returnObject = Attribute(
            type = returnType,
            desc = returnDesc)
    functionObject = FunctionObject(
        desc = tempDoc,
        returnObject = returnObject,
        parameters = args)
    if additionalTypes:
        functionObject.additionalTypes = additionalTypes
    return functionObject

def _parseClass(clazz, soup, context):
    clName = clazz.name
    context.breadcrumbs.append(clName)
    context.clazz = clName
    #print(clName)

    attributeRe = re.compile(clName + "\\.\\w+")
    element = soup.find("div", "element", id = clName)

    classDoc = parseDescription(soup, element, clName)

    hasHelp, hasValid, shortDescriptions = parseShortDescription(soup, clName)

    attributes = OrderedDict()
    #addCommonAttributes(attributes, context, hasHelp, hasValid)

    for row in element.findChildren("div", "element", id = attributeRe):
        name = row.findChild("span", "element-name").get_text(strip = True)
        match = bracketRe.search(name)
        if match:
            name = name[ : match.start()]

        context.breadcrumbs.append(name)

        modeNode = row.find("span", "attribute-mode")
        if modeNode:
            attribute = parseField(row, modeNode, context)
            attribute.name = name
            attribute.shortDesc = shortDescriptions.get(name)
        else:
            attribute = parseMethod(row, context)
            attribute.name = name
            attribute.shortDesc = shortDescriptions.get(name)

        attributes[name] = attribute
        context.breadcrumbs.pop()

    clazz.attributes = attributes

    bl = soup.find("div", "brief-listing", id = clName + ".brief")
    parents = []#OrderedDict()
    for inherit in bl.findChildren("div", "brief-inherited"):
        line = inherit.get_text(" ", strip = True)
        match = inheritsRe.match(line)
        parentCl = match.group("clname")
        #attrs = m.group("attributes")
        #attrs = attributesRe.split(attrs)
        parents.append(parentCl)
        #inherits[parentCl] = attrs
    if not parents and hasHelp == False and hasValid == False:
        parents.append("LuaObject")
    else:
        if hasHelp:
            parents.append("LuaObjectHelp")
        if hasValid:
            parents.append("LuaObjectValid")
    if parents: #TODO: it is always true
        #clazz.inherits = inherits
        clazz.parents = parents

    clazz.desc = md.lineBreak.join(classDoc)

    #print("qwe", inherits)

def parse_class(className, soupObject, context):
    context.breadcrumbs.clear()
    context.breadcrumbs.append("class")
    clazz = context.classes[className]
    _parseClass(clazz, soupObject, context)

def main():
    #className = "LuaSurface"
    #className = "LuaBootstrap"
    className = "LuaControl"
    from retriever import SourceRetriever
    retriever = SourceRetriever(
        baseURL,
        useCached = True,
        cacheDir = cacheDir,
        suffix = suffix)
    context = Context(retriever)
    co = ClassObject(
        name = className,
        shortDesc = "Testing class",
        url = apiHome + className + ".html"
    )
    so = retriever.get(className + ".html")

    _parseClass(co, so, context)

if __name__ == '__main__':
    main()