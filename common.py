from DocumentationData import *
import md
from collections import OrderedDict

classesURL = "Classes.html"
definesURL = "defines.html"
eventsURL = "events.html"
commonURL = "Common.html"
conceptsURL = "Concepts.html"
indexURL = "index.html"

modeTranslation = {
    "[Read-only]" : "[R]",
    "[Read-Write]" : "[RW]",
    "[Write-only]" : "[W]",
}

class Context:
    def __init__(self, retriever):
        self.retriever = retriever
        self.conceptTypes = OrderedDict()
        self.classes = OrderedDict()
        self.defines = DefinesGroup(name = "defines")
        self.commonClassAttributes = {}
        self.commonClasses = OrderedDict()
        self.globalClasses = OrderedDict()
        self.commonEventParameters = None