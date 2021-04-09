from common import *
import re

spaceRe = re.compile(" {2,}")

def parse_attribute_doc(element, stopAt = None):
    attributeDoc = []
    record = False
    for child in element.children:
        if child.name == "span" and child.get("class")[0] in ("param-type", "param-name", "opt"):
            attributeDoc = []
            continue
        if stopAt and child.name == stopAt.name and child.get("class") == stopAt.get("class"):
            break
        temp = md.handleDocString(child)
        if temp:
            attributeDoc.append(spaceRe.sub(" ", temp.strip(": \n")))

    return attributeDoc