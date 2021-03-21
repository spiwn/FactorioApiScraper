from common import *
import re

conceptTypesTableRe = re.compile("[ai]s a table:?$")
numberOfWaysRe = re.compile("may be specified in one of (the )?(\\w+) ways")

def _parseConcepts(soup, context):
    types = OrderedDict()
    bl = soup.find("div", "brief-listing")
    for div in bl.findChildren("div", recursive = False):
        typeString = next(div.children).strip() # 'type' or 'struct' what is the difference?
        className = div.findChild("span", "type-name").findChild("a").get_text(strip = True)
        if typeString == "type":
            types[className] = ClassObject(name = className)
        else:
            classFields = OrderedDict()
            for row in div.findChild("table", "brief-members", recursive = False).findChildren("tr", recursive = False):
                td = row.findChild("td", "header")
                fieldName = td.findChild("span", "element-name", recursive = False).findChild("a", recursive = False).get_text(strip = True)
                shortDescriptionString = row.findChild("td", "description", recursive = False).get_text(strip = True)

                typeString = td.findChild("span", "attribute-type").findChild("span", "param-type").get_text(strip=True)
                modeString = td.find("span", "attribute-mode").get_text(strip=True)

                classFields[fieldName] = Field(name = fieldName, type = typeString, shortDesc = shortDescriptionString, mode = modeString)
            types[className] = ClassObject(name = className, attributes = classFields, flags = Flags.Struct)

    for classDiv in bl.find_next_siblings("div", "element"):
        className = classDiv.get("id")
        clazz = types[className]

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
                temp = temp.get_text(strip = True).strip()
                if numberOfWaysRe.search(temp):
                    #TODO: these union types
                    pass
                else:

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

                pp = fieldList.parent
                for ee in pp.children:
                    # print(type(ee), ee.name)
                    # print(md.handleDocString(ee))
                    pass
                #TODO: do
                pass
            elif conceptTypesTableRe.search(previousText) or previousText == "This is an array of tables with the following fields:":
                if "array of" in previousText:
                    #print(previous)
                    # TODO: do
                    pass
                else:
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

def parse_concepts(context):
    soup = context.retriever.get(conceptsURL)
    _parseConcepts(soup, context)