from common import *

def _parseBuiltins(soup, context):
    bl = soup.find("body")
    for div in bl.findChildren("div", "element", recursive = False):
        name = div.get("id")
        content = div.findChild("div", "element-content", recursive = False)
        doc = md.handleDocString(content)
        context.builtinTypes[name] = DocObject(name = name, desc = doc)

def parse_builtin_types(context):
    soupObject = context.retriever.get(builtinTypesURL)
    _parseBuiltins(soupObject, context)