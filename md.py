import re

#lineBreak = "  \n"
lineBreak = "\n"

_anchorBase = ""

#TODO: Rework this: instead of the absolute path, this module should insert a
# placeholder that should be replaced later, by the exporting code
def setAnchorBase(url):
    global _anchorBase
    _anchorBase = url

def emphasis(s):
    return "_" + s + "_"

def strong(s):
    return "**" + s + "**"

def code(s):
    return '```' + s + '```'

def shortCode(s):
    return '`' + s + '`'

_indentationCache = { i : " " * i for i in range(20)}
_listCharacters = ["*", "+", "-"]
_whitespaceRe = re.compile("^\\s+$")

def docMapFunction(x, isList, listChar, doIndent = False, indent = 0):
    indentation = ""
    if doIndent:
        indentation = _indentationCache[indent]
    x = x.strip()
    if isList:
        return indentation + _listCharacters[listChar] + " " + x
    return indentation + x

def handleDocString(node, sep = " ", isList = False, listChar = -1, maxDepth = None, currentDepth = 1, doIndent = False, indent = 0):
    if maxDepth and currentDepth > maxDepth:
        return None
    if isinstance(node, str):
        return node.strip()
    children = node.children
    if not children:
        return node.get_text(strip = True)
    nextDepth = currentDepth + 1
    result = []
    for child in node.children:
        name = child.name
        if not name:
            result.append(child.string.strip())
            continue
        if name == "code":
            codeText = handleDocString(child, maxDepth = 1)
            if "\n" in codeText:
                result.append(code(codeText))
            else:
                result.append(shortCode(codeText))
        elif name == "em":
            result.append(emphasis(handleDocString(child, maxDepth = 1)))
        elif name == "strong":
            result.append(strong(handleDocString(child, maxDepth = 1)))
        elif name == "br":
            result.append(lineBreak)
        elif name == "span":
            result.append(handleDocString(child, listChar = listChar, maxDepth = maxDepth))
        elif name == "a":
            result.append("[" + child.get_text(strip = True) + "](" + _anchorBase + child["href"] + ")")
        elif name == "ul":
            nextListChar = (listChar + 1) % len(_listCharacters)
            t = handleDocString(child, sep = lineBreak, isList = True, listChar = nextListChar,
                            maxDepth = maxDepth, currentDepth = nextDepth, indent = indent + 2, doIndent = True)
            if t:
                result.append(lineBreak + t + lineBreak)
        elif name == "li":
            result.append(handleDocString(child, listChar = listChar, maxDepth = maxDepth, currentDepth = nextDepth, indent = indent))
        elif name == "p":
            result.append(handleDocString(child, listChar = listChar, maxDepth = maxDepth) + lineBreak)
        elif name == "div":
            result.append(handleDocString(child, listChar = listChar, maxDepth = maxDepth, currentDepth = nextDepth, indent = indent))
        else:
            print(child.prettify())
            raise Exception("Unknown html tag: " + name)
    temp = sep.join(map(lambda x: docMapFunction(x, isList, listChar, doIndent, indent), filter(lambda x: x and not _whitespaceRe.match(x), result)))

    return temp