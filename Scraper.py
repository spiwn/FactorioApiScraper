from retriever import SourceRetriever
from parsing.AllClassesPage import parse_all_classes
from parsing.CommonPage import parse_common
from parsing.Concepts import parse_concepts
from parsing.SingleClass import parse_class
from parsing.Defines import parse_defines
from parsing.Events import parse_events
from parsing.Index import parse_index_page
from common import *

import DocFormatter

useCachedOverride = True

def prettify(f, soup):
    with open("p" + f, 'wb') as w:
        soup.encode("utf8")
        w.write(soup.prettify(encoding = "utf8"))

def parseClasses(context):
    #Used to "parse" only specified classes - for faster testing
    classFilter = [
        #"LuaControlBehavior",
        #"LuaEntityPrototype",
        #"LuaGuiElement",
        #"LuaSurface",
        #"LuaEquipment",
        #"LuaBootstrap"
    ]

    filtered = {}
    if classFilter:
        for i in classFilter:
            filtered[i] = context.classes[i]
    else:
        filtered = context.classes

    for k, v in filtered.items():
        context.retriever.enqueue(v.url)

    for k, v in filtered.items():
        cl = context.retriever.get(v.url)
        parse_class(k, cl, context)

def scrape(retriever):
    startingUrls = [
        commonURL,
        classesURL,
        definesURL,
        eventsURL,
        conceptsURL,
        indexURL]
    for url in startingUrls:
        #retriever.enqueue(url)
        pass

    context = Context(retriever)

    parse_common(context)
    parse_all_classes(context)
    parse_concepts(context)
    parseClasses(context)
    parse_defines(context)
    parse_events(context)
    parse_index_page(context)

    return context



def store_intermediate(context, outputDirPath):
    del context.retriever
    import pickle
    with open(outputDirPath.joinpath("context.txt"), 'wb') as w:
        pickle.dump(context, w)

def go():
    context = scrape(SourceRetriever(
        baseURL,
        useCached = useCachedOverride or arguments.ca,
        cacheDir = cacheDir,
        suffix = suffix))

    outputDirPath = Path(outputDir)
    outputDirPath.mkdir(parents = True, exist_ok = True)

    if arguments.intermediate:
        store_intermediate(context, outputDirPath)

    if not arguments.skip_generation:
        DocFormatter.formatDocumentation(context, outputDirPath)
        pass

    print("Done")

if __name__ == "__main__":
    go()

