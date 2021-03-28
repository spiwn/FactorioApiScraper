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
_argParser.add_argument("--intermediate", help ="store the intermediate representation", action ="store_true")
_argParser.add_argument("--skip_generation", help ="skip generating the output", action ="store_true")
arguments = _argParser.parse_args()
arguments.cache = arguments.cache or "cached"

cacheDir = arguments.cache
if arguments.clear:
    clear_cache(cacheDir)

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
        self.breadcrumbs = []