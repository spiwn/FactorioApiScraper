from common import *
import re

definesIdRe = re.compile("defines\\..+")

def _extractIdAndProperties(data, context, idString = None):
    if idString:
        idText = idString.split(".")
    else:
        idText = data["id"].split(".")

    if idText[1] == "events":
        define = Event(name=idText[-1])
    else:
        define = DocObject(name=idText[-1])

    td = data.find_next_sibling("td")
    if td:
        doc = md.handleDocString(td)
        if doc:
            define.shortDesc = doc

    return define

def _extractTd(parent, context, group):
    tables = parent.findChildren("table", "brief-members")
    for table in tables:
        for tr in table.findChildren("tr"):
            td = tr.findChild("td")
            idText = td.get_text(strip = True)
            define = _extractIdAndProperties(td, context, idText)
            group.defines[define.name] = define


def _parseDefineGroup(element, context, group):
    ec = element.findChild("div", "element-content", recursive=False)

    # Get Doc of defines group
    doc = []
    for child in ec.children:
        if child.name in ("table", "div"):
            break
        temp = md.handleDocString(child)
        if temp:
            doc.append(temp)

    name = element.get("id").split(".")[-1]
    defineGroup = DefinesGroup(name = name)
    if doc:
        defineGroup.desc = md.lineBreak.join(doc)

    group.defines[name] = defineGroup
    # check if group
    children = list(ec.findChildren("div", "element", id = definesIdRe, recursive = False))
    if children:
        for child in  children:
            _parseDefineGroup(child, context, defineGroup)
    else:
        _extractTd(ec, context, defineGroup)
    pass

def _parseDefines(soup, context):
    briefListing = soup.find("div", "brief-listing")
    for element in briefListing.find_next_siblings("div", "element", id = definesIdRe):
        _parseDefineGroup(element, context, context.defines)

def parse_defines(context):
    source = context.retriever.get(definesURL)
    _parseDefines(source, context)