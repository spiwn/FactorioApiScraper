from common import *

def _findClassPages(soup, context):
    classes = context.classes
    bl = soup.find("div", "brief-listing")
    table = bl.findChild("table")
    for tr in table.findChildren("tr"):
        header = tr.findChild("td", "header")
        a = header.findChild("a")
        name = a.get_text(strip = True)
        href = a["href"]
        classes[name] = ClassObject(name = name, url = href)
        #TODO: short desc
        #context.retriever.enqueue(href)

def parse_all_classes(context):
    soupObject = context.retriever.get(classesURL)
    _findClassPages(soupObject, context)