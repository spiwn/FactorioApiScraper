from common import *
import re

spaceRe = re.compile(" {2,}")

def parse_attribute_doc(element):
    attributeDoc = []
    record = False
    for child in element.children:
        if child.name == "span" and child.get("class")[0] in ("param-type", "param-name", "opt"):
            record = True
            attributeDoc = []
            continue
        if not record:
            continue
        temp = md.handleDocString(child)
        if temp:
            attributeDoc.append(spaceRe.sub(" ", temp.strip(": \n")))

    return attributeDoc