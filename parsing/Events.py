from common import *
from .Attribute import parse_attribute_doc

def _getEventParamType(element):
    pt = element.findChild("span", "param-type", recursive = False)
    if pt:
        anchor = pt.findChild("a", recursive = False)
        if anchor:
            return anchor.get_text(strip = True)
        else:
            nextP = pt.findChild("span", "param-type", recursive = False)
            if nextP:
                nextAnchor = nextP.findChild("a", recursive = False)
                if nextAnchor:
                    first = list(pt.children)[0]
                    prefix = ""
                    if isinstance(first, str):
                        if "array of" == first.lower():
                            # TODO: better representation of this
                            # like {type, ...}
                            prefix = "Array of "
                    return prefix + nextAnchor.get_text(strip = True)
                else:
                    return nextP.get_text(strip = True)
            return None

    return None

def parseAttribute(d, idText, event):
    paramName = d.findChild("span", "param-name", recursive = False).get_text(strip = True)
    optional = False
    desc = None

    paramType = _getEventParamType(d)
    if paramType is None:
        if idText == "on_permission_group_edited" and paramName == "action":
            paramType = "defines.input_action"
        elif paramName == "selected_prototype":
            # TODO: Custom Input Events.selected_prototype
            fl = d.findChild("ul", "field-list")
            attributes = OrderedDict()
            for li in fl.findChildren(recursive = False):
                temp = parseAttribute(li, idText, event)
                attributes[temp.name] = temp
            paramType = idText + "_selected_prototype"
            event.contains.append(
                ClassObject(
                    name = paramType,
                    flags = Flags.Dummy,
                    attributes = attributes))
        else:
            raise Exception("Unhandled event parameter")

    if d.findChild("span", "opt", recursive = False):
        optional = True

    attributeDoc = parse_attribute_doc(d)
    if attributeDoc:
        desc = " ".join(attributeDoc)
    return Attribute(
        name = paramName,
        type = ObjectType(value = paramType),
        optional = optional,
        desc = desc)


allEventsKey = "All events"
customInputsKey = "Custom Input Events"
def _parseEvents(soup, context):
    allEvents = context.defines.defines["events"]
    events = allEvents.defines
    events[allEventsKey] = allEvents

    commonEventAttributes = OrderedDict()

    commonEventAttributes["name"] = Attribute(
        name = "name",
        type = "defines.events",
        desc = "Identifier of the event"
    )
    #commonEventAttributes["name"] = "name :: defines.events: Identifier of the event"
    commonEventAttributes["tick"] = Attribute(
        name = "tick",
        type = "uint",
        desc = "Tick the event was generated"
    )

    context.commonEventParameters = ClassObject(name = "_All_Event_Parameters",
                attributes = commonEventAttributes)
    #commonEventAttributes["tick"] = "tick :: uint: Tick the event was generated"

    lookingIn = soup.find("div", "brief-listing")
    table = lookingIn.findChild("table", "brief-members", recursive = False)
    for tr in table.findChildren("tr", recursive = False):
        name = tr.findChild("td", "header", recursive = False).findChild("a", recursive = False).get_text(strip = True)
        shortDesc = md.handleDocString(tr.findChild("td", "description", recursive = False))
        # for child in tr.findChild("td", "description", recursive = False).children:
        #     shortDesc.append(md.handleDocString(child))
        # if shortDesc:
        #     shortDesc = " ".join(shortDesc)
        # else:
        #     shortDesc = None
        event = events.get(name)
        if not event:
            if name == customInputsKey:
                events[name] = Event(name = name)
                events.move_to_end(name, last = False)
            else:
                raise Exception("New event that is not in defines found: " + name)
        events[name].shortDesc = shortDesc
    for divElement in lookingIn.find_next_siblings("div", "element"):
        element = divElement.findChild("div", "element")
        #TODO: parse all the events!!!!!!!!!!!!!!!!!
        #TODO: check for short desc
        idText = element.findChild("div", "element-header").get_text(strip = True)
        event = events[idText]

        eventDoc = []
        for p in element.findChildren("p"):
            text = md.handleDocString(p)
            if text:
                eventDoc.append(text)
        eventDesc = md.lineBreak.join(eventDoc)

        attributes = OrderedDict()
        #attributes.update(commonEventAttributes)

        detail = element.findChild("div", "detail-content")
        if detail is not None:
            for d in detail.findChildren("div", recursive = False):
                temp = parseAttribute(d, idText, event)
                attributes[temp.name] = temp

        if idText != allEventsKey:
            event.contains.append(
                ClassObject(
                    #name = event.name + "_parameter",
                    name = event.name,
                    parents = ["_All_Event_Parameters"],
                    attributes = attributes,
                    desc = eventDesc,
                    flags = Flags.Dummy
                ))


        events[idText] = event

    events.pop(allEventsKey)

def parse_events(context):
    soup = context.retriever.get(eventsURL)
    _parseEvents(soup, context)