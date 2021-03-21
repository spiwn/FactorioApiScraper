from common import *
from .Attribute import parse_attribute_doc

def _parseIndexPage(soup, context : Context):
    fl = soup.find("ul", "field-list")
    if not fl:
        raise Exception("Global classes description not found")
    for listItem in fl.findChildren("li", recursive = False):
        paramName = listItem.findChild("span", "param-name", recursive = False).get_text(strip = True)
        pt = listItem.findChild("span", "param-type", recursive=False)
        if pt:
            anchor = pt.findChild("a", recursive=False)
            if anchor:
                paramType = anchor.get_text(strip=True)
            else:
                raise Exception("No anchor for global class " + paramName)
        else:
            raise Exception("No parameter type fro global class " + paramName)
        context.globalClasses[paramName] = paramType

def parse_index_page(context):
    soup = context.retriever.get(indexURL)
    _parseIndexPage(soup, context)