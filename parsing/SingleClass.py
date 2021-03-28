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

def _parseClass(clazz, soup, context):
    clName = clazz.name
    context.breadcrumbs.append(clName)
    #print(clName)

    attributeRe = re.compile(clName + "\\.\\w+")
    element = soup.find("div", "element", id = clName)

    classDoc = []
    h1 = soup.findChild("h1")
    desc = soup.find("body").find("div", "brief-description")
    if h1 and h1.get_text(strip = True) == clName and desc:
        hasChildren = False
        for e in desc.children:
            hasChildren = True
            if isinstance(e, str):
                classDoc.append(e)
            else:
                if e.name == "p":
                    classDoc.append(md.handleDocString(e))
                elif e.name == "ul":
                    classDoc.append(md.handleDocString(e, isList = True, listChar = 0, sep = md.lineBreak))
                elif e.name == "div":
                    classes = e.get("class")
                    if classes:
                        if "example" in classes:
                            classDoc.append(md.handleDocString(e))
                        elif "notes" in classes:
                            classDoc.append(md.handleDocString(e))
                            pass
                        else:
                            print("Unknown div class", classes)
                    else:
                        print("Div does not have a class")
                else:
                    print("Unknown element", e.name)
        if not hasChildren:
            print("No description", clName)
    else:
        content = element.find("div", "element-content", recursive = False)
        if content:
            for e in content.children:
                if isinstance(e, str):
                    classDoc.append(e)
                else:
                    if e.name == "p":
                        classDoc.append(md.handleDocString(e))
                    elif e.name == "div":
                        classes = e.get("class")
                        if classes:
                            if "notes" in classes:
                                classDoc.append(md.handleDocString(e))
                            elif "element" in classes:
                                pass
                            else:
                                print("Unknown div class", classes)
                        else:
                            print("Div does not have a class")
                    else:
                        print("Unknown element", e.name)

            # print(clName)
            for p in content.findChildren("p", recursive=False) or ():
                # classDoc.append(md.handleDocString(p))
                pass
            notes = element.findChild("div", "notes", recursive=False)
            if notes:
                for note in notes.findChildren("div", "note", recursive=False):
                    # classDoc.append(md.handleDocString(note))
                    pass
        else:
            print("no content")

    hasValid = False
    hasHelp = False

    shortDescriptions = {}

    for tr in soup.find("div", "brief-listing", id = clName + ".brief").findChild("table", recursive = False).findChildren("tr", recursive = False):
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
                if t:
                    #print(t)
                    pass

    attributes = OrderedDict()
    #addCommonAttributes(attributes, context, hasHelp, hasValid)

    for row in element.findChildren("div", "element", id = attributeRe):
        args = {}
        attributeDoc = []

        name = row.findChild("span", "element-name").get_text(strip = True)
        match = bracketRe.search(name)
        if match:
            name = name[ : match.start()]

        context.breadcrumbs.append(name)

        returnDesc = None
        modeString = None

        returnType = None
        attributeType = None

        elementContent = row.findChild("div", "element-content", recursive = False)

        modeNode = row.find("span", "attribute-mode")
        if modeNode:
            typeNode = row.findChild("span", "attribute-type")
            if elementContent:
                attributeDoc.append(md.handleDocString(elementContent))
                #print(1, doc[-1])
            if typeNode:
                attributeType = getReturnTypes(tuple(typeNode.findChild("span", "param-type").children), context)
            else:
                #TODO: temporary workaround
                attributeType = "any"
            modeString = modeTranslation[modeNode.get_text(strip = True)]
        else:
            attributeDoc.append(md.handleDocString(elementContent, maxDepth = 1))
            returnSpan = row.findChild("span", "return-type")
            if returnSpan:
                pt = returnSpan.findChild("span", "param-type", recursive = False)
                if name == "calculate_tile_properties":
                    #print("asd")
                    #Just for testing
                    pass
                returnType = getReturnTypes(tuple(pt.children), context)

            returnValueDetailFound = False
            for detail in elementContent.findChildren("div", "detail", recursive = False) or ():
                header = detail.findChild("div", "detail-header")
                if header is None:
                    #TODO: check where this happens
                    attributeDoc.append(md.handleDocString(detail))
                    continue

                headerText = header.get_text(strip = True)

                if headerText == "Parameters":
                    #doc.append(md.strong(headerText))
                    dc = detail.find("div", "detail-content")
                    count = 0
                    for div in dc.findChildren("div", recursive = False):
                        count += 1
                        if not div.findChild("span", "param-name"):
                            continue

                        argName = div.findChild("span", "param-name").get_text(strip = True)
                        parameterType = None
                        typeNode = div.findChild("span", "param-type")
                        if typeNode:
                            parameterType = getReturnTypes(tuple(typeNode.children), context)
                        else:
                            parameterType = "any"
                            #TODO: temporary workaround

                        parameterDoc = parse_attribute_doc(div)

                        if parameterDoc:
                            #TODO: fix this
                            #It seems that beautifulsoup returns a string containing new lines so they must be removed
                            #An example is LuaBootstrap.on_event f parameter description
                            parameterDoc = " ".join(map(lambda x: x.replace("\n", " "), filter(lambda x: x, parameterDoc)))

                        args[argName] = Parameter(
                            name = argName,
                            type = parameterType,
                            desc = parameterDoc)
                elif headerText == "Return value":
                    returnValueDetailFound = True
                    returnDesc = md.handleDocString(header.find_next_sibling("div", "detail-content"))
                elif headerText == "See also":
                    attributeDoc.append(md.strong(headerText))
                    attributeDoc.append(md.handleDocString(detail))
                else:
                    raise Exception("Unknown headerText: " + headerText)
            if not returnValueDetailFound:
                #print(returnType)
                pass

        if modeNode:
            tempDoc = " ".join(filter(lambda x: x, attributeDoc))
            attribute = Attribute(
                name = name,
                shortDesc = shortDescriptions.get(name),
                desc = tempDoc,
                mod = modeString,
                type = attributeType)
        else:
            tempDoc = " ".join(filter(lambda x: x, attributeDoc))
            returnObject = None
            if returnType:
                returnObject = Attribute(
                    type = returnType,
                    desc = returnDesc)
            attribute = FunctionObject(
                name = name,
                shortDesc = shortDescriptions.get(name),
                desc = tempDoc,
                returnObject = returnObject,
                parameters = args)

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
    className = "LuaBootstrap"
    from retriever import SourceRetriever
    retriever = SourceRetriever(
        baseURL,
        useCached=True,
        cacheDir=cacheDir,
        suffix=suffix)
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