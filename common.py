from DocumentationData import *
import md
from collections import OrderedDict
import argparse
from pathlib import Path
import os

httpPrefix = "https://"
baseURL = "lua-api.factorio.com"
suffix = "/latest/"
apiHome = httpPrefix + baseURL + suffix
md.setAnchorBase(apiHome)

outputDir = "output"

classesURL = "Classes.html"
definesURL = "defines.html"
eventsURL = "events.html"
commonURL = "Common.html"
conceptsURL = "Concepts.html"
indexURL = "index.html"
builtinTypesURL = "Builtin-Types.html"

modeTranslation = {
    "[Read-only]" : "[R]",
    "[Read-Write]" : "[RW]",
    "[Write-only]" : "[W]",
}

def clear_cache(cacheDirParam):
    cachePath = Path(cacheDirParam)
    for file in cachePath.glob("*.html"):
        os.remove(file)
        pass

_argParser = argparse.ArgumentParser()
_argParser.add_argument("-c", "--cache", type = str, help ="Specify a folder to use as a cache", action ="store")
_argParser.add_argument("--clear", help ="remove previously saved html files", action ="store_true")
_argParser.add_argument("--intermediate", help ="store the intermediate representation as a file", action ="store_true")
_argParser.add_argument("--json", help ="write the intermediate representation as json to a file", action ="store_true")
_argParser.add_argument("--skip_generation", help ="skip generating the output", action ="store_true")
arguments = _argParser.parse_args()
arguments.cache = arguments.cache or "cached"

cacheDir = arguments.cache
if arguments.clear:
    clear_cache(cacheDir)

class Context:
    def __init__(self, retriever):
        self.conceptTypes = OrderedDict()
        self.classes = OrderedDict()
        self.defines = DefinesGroup(name = "defines")
        self.commonClassAttributes = {}
        self.commonClasses = OrderedDict()
        self.globalClasses = OrderedDict()
        self.commonEventParameters = None
        self.builtinTypes = OrderedDict()

        self.retriever = retriever
        self.breadcrumbs = []
        self.clazz = None

    def clear_transient(self):
        del self.breadcrumbs
        del self.retriever
        del self.clazz

    def toJson(self):
        attributes = (
            'conceptTypes',
            'classes',
            'defines',
            'commonClassAttributes',
            'commonClasses',
            'globalClasses',
            'commonEventParameters',
            'builtinTypes')
        return {k : self.__dict__[k] for k in attributes}
