from common import *
import re
from parsing.SingleClass import parseParameter

conceptTypesTableRe = re.compile("[ai]s a table:?$")
numberOfWaysRe = re.compile("may be specified in one of (the )?(\\w+) ways")

def parseBriefListing(bl):
    types = OrderedDict()
    for div in bl.findChildren("div", recursive = False):
        typeString = next(div.children).strip()  # 'type' or 'struct' what is the difference?
        className = div.findChild("span", "type-name").findChild("a").get_text(strip = True)
        if typeString == "type":
            types[className] = ClassObject(name = className)
        else:
            classFields = OrderedDict()
            for row in div.findChild("table", "brief-members", recursive = False).findChildren("tr", recursive = False):
                td = row.findChild("td", "header")
                fieldName = td.findChild("span", "element-name", recursive = False).findChild("a",
                                                                                            recursive = False).get_text(
                    strip = True)
                shortDescriptionString = row.findChild("td", "description", recursive = False).get_text(strip = True)

                typeString = td.findChild("span", "attribute-type").findChild("span", "param-type").get_text(strip = True)
                modeString = td.find("span", "attribute-mode").get_text(strip = True)

                classFields[fieldName] = Field(name = fieldName, type = typeString, shortDesc = shortDescriptionString,
                                               mode = modeString)
            types[className] = ClassObject(name = className, attributes = classFields, flags = Flags.Struct)
    return types

def _parseConcepts(soup, context):

    bl = soup.find("div", "brief-listing")
    conceptTypes = parseBriefListing(bl)

    for classDiv in bl.find_next_siblings("div", "element"):
        className = classDiv.get("id")
        clazz = conceptTypes[className]

        classDoc = []

        ecDiv = classDiv.findChild("div", "element-content")
        fieldList = ecDiv.findChild("ul", "field-list")
        if clazz.hasFlag(Flags.Struct):
            #TODO: do
            #print("Struct found")
            pass
        elif fieldList is None:
            temp = ecDiv.findChild("p", recursive = False)
            if temp:
                tempText = temp.get_text(strip = True).strip()
                if numberOfWaysRe.search(tempText):
                    ul = temp.findNextSibling("ul")
                    memberTypes = []
                    for li in ul.findChildren("li", recursive = False):
                        children = tuple(li.children)
                        memberTypes.append(children[1].get_text(strip = True))
                        #TODO: research how to add the documentation
                        if len(children) > 2 and children[2]:
                            doc = children[2].strip(": \n")
                    alias = AliasType(
                        name = className,
                        desc = clazz.desc or tempText,
                        shortDesc = clazz.shortDesc,
                        url = clazz.url,
                        type = ObjectType(
                            type = Types.Union,
                            value = memberTypes)
                    )
                    conceptTypes[className] = alias
                    pass
                else:
                    #TODO: these
                    pass

            else:
                raise Exception("Formatting not recognized")
                pass
            classDoc.append(md.handleDocString(ecDiv))
        else:
            previousText = []
            for c in ecDiv.children:
                if c == fieldList:
                    break
                temp = md.handleDocString(c)
                if temp:
                    previousText.append(temp)


            previousText = md.lineBreak.join(previousText)
            if previousText in ("Members:", "Table with the following fields:", "A table:"):
                classDoc.append(previousText)
                attributes = []
                for li in fieldList.children:
                    attributes.append(parseParameter(li, context))
                if attributes:
                    clazz.attributes = OrderedDict()
                    for attribute in attributes:
                        clazz.attributes[attribute.name] = attribute
            elif conceptTypesTableRe.search(previousText) or previousText == "This is an array of tables with the following fields:":
                if "array of" in previousText:
                    attributes = OrderedDict()
                    for li in fieldList.children:
                        p = parseParameter(li, context)
                        attributes[p.name] = p
                    if not attributes:
                        raise Exception()
                    dummyClass = ClassObject(
                        name = "_" + className + "_Helper",
                        attributes = attributes,
                        flags = Flags.Dummy,
                    )
                    alias = AliasType(
                        name = className,
                        desc = clazz.desc or previousText,
                        shortDesc = clazz.shortDesc,
                        url = clazz.url,
                        type = ObjectType(
                            type = Types.Array,
                            value = dummyClass.name)
                    )
                    conceptTypes[dummyClass.name] = dummyClass
                    conceptTypes.move_to_end(className)
                    conceptTypes[className] = alias
                    pass
                else:
                    #print(className)
                    #TODO: handle Resistances type
                    #print(previous)
                    #print(dir(fieldList))
                    classDoc.append(previousText)
                    #TODO: do
            elif "Table with the following fields:" in previousText:
                #TODO: do
                #TODO: handle AutoplaceSpecification
                pass
            elif "Members:" in previousText:
                #print(className, previousText)
                pass
            else:
                #TODO: handle these few exception
                #print(dir(ecDiv))
                #print(className, fieldList.previous.strip())
                #print(ecDiv.prettify(encoding = "utf8"))
                #print(className)
                pass
    context.conceptTypes = conceptTypes

def parse_concepts(context):
    soup = context.retriever.get(conceptsURL)
    _parseConcepts(soup, context)

def main():
    from retriever import SourceRetriever
    retriever = SourceRetriever(
        baseURL,
        useCached = True,
        cacheDir = cacheDir,
        suffix = suffix)
    context = Context(retriever)
    parse_concepts(context)

if __name__ == '__main__':
    main()