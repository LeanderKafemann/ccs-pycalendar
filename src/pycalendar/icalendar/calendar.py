##
#    Copyright (c) 2007-2013 Cyrus Daboo. All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
##
from typing import Any, Dict, List, Optional, Set, Tuple, Union, IO
from io import StringIO
from pycalendar import xmlutils
from pycalendar.containerbase import ContainerBase
from pycalendar.datetime import DateTime
from pycalendar.exceptions import InvalidData
from pycalendar.icalendar import definitions, xmldefinitions
from pycalendar.icalendar.component import Component
from pycalendar.icalendar.componentexpanded import ComponentExpanded
from pycalendar.icalendar.componentrecur import ComponentRecur
from pycalendar.icalendar.freebusy import FreeBusy
from pycalendar.icalendar.property import Property
from pycalendar.icalendar.validation import ICALENDAR_VALUE_CHECKS
from pycalendar.parser import ParserContext
from pycalendar.period import Period
from pycalendar.utils import readFoldedLine
import collections
import json
import xml.etree.cElementTree as XML

class Calendar(ContainerBase):
    REMOVE_ALL: int = 0
    REMOVE_ONLY_THIS: int = 1
    REMOVE_THIS_AND_FUTURE: int = 2

    FIND_EXACT: int = 0
    FIND_MASTER: int = 1

    ALL_TIMEZONES: int = 0
    NONSTD_TIMEZONES: int = 1
    NO_TIMEZONES: int = 2

    sContainerDescriptor: str = "iCalendar"
    sComponentType: Any = Component
    sPropertyType: Any = Property

    sFormatText: str = "text/calendar"
    sFormatJSON: str = "application/calendar+json"

    propertyCardinality_1: Tuple[str, ...] = (
        definitions.cICalProperty_PRODID,
        definitions.cICalProperty_VERSION,
    )

    propertyCardinality_0_1: Tuple[str, ...] = (
        definitions.cICalProperty_CALSCALE,
        definitions.cICalProperty_METHOD,
    )

    propertyValueChecks: Any = ICALENDAR_VALUE_CHECKS

    mName: str
    mDescription: str
    mMasterComponentsByTypeAndUID: Dict[Any, Dict[Any, Any]]
    mOverriddenComponentsByUID: Dict[Any, List[Any]]

    def __init__(self, parent: Optional[Any] = None, add_defaults: bool = True) -> None:
        super(Calendar, self).__init__(add_defaults=add_defaults)
        self.mName: str = ""
        self.mDescription: str = ""
        self.mMasterComponentsByTypeAndUID: Dict[Any, Dict[Any, Any]] = collections.defaultdict(lambda: collections.defaultdict(list))
        self.mOverriddenComponentsByUID: Dict[Any, List[Any]] = collections.defaultdict(list)

    def __str__(self) -> str:
        return self.getText(includeTimezones=Calendar.NO_TIMEZONES)

    def duplicate(self) -> "Calendar":
        other = super(Calendar, self).duplicate()
        other.mName = self.mName
        other.mDescription = self.mDescription
        return other

    def getType(self) -> str:
        return definitions.cICalComponent_VCALENDAR

    def getName(self) -> str:
        return self.mName

    def setName(self, name: str) -> None:
        self.mName = name

    def editName(self, name: str) -> None:
        if self.mName != name:
            self.mName = name
            self.removeProperties(definitions.cICalProperty_XWRCALNAME)
            if len(name):
                self.addProperty(Property(definitions.cICalProperty_XWRCALNAME, name))

    def getDescription(self) -> str:
        return self.mDescription

    def setDescription(self, description: str) -> None:
        self.mDescription = description

    def editDescription(self, description: str) -> None:
        if self.mDescription != description:
            self.mDescription = description
            self.removeProperties(definitions.cICalProperty_XWRCALDESC)
            if len(description):
                self.addProperty(Property(definitions.cICalProperty_XWRCALDESC, description))

    def getMethod(self) -> str:
        result = ""
        if self.hasProperty(definitions.cICalProperty_METHOD):
            result = self.loadValueString(definitions.cICalProperty_METHOD)
        return result

    def changeUID(self, oldUID: str, newUID: str) -> None:
        for component in self.mComponents:
            if component.getUID() == oldUID:
                component.setUID(newUID)
        if oldUID in self.mOverriddenComponentsByUID:
            self.mOverriddenComponentsByUID[newUID] = self.mOverriddenComponentsByUID[oldUID]
            del self.mOverriddenComponentsByUID[oldUID]
        for ctype in self.mMasterComponentsByTypeAndUID:
            if oldUID in self.mMasterComponentsByTypeAndUID[ctype]:
                self.mMasterComponentsByTypeAndUID[ctype][newUID] = self.mMasterComponentsByTypeAndUID[ctype][oldUID]
                del self.mMasterComponentsByTypeAndUID[ctype][oldUID]

    def finalise(self) -> None:
        temps = self.loadValueString(definitions.cICalProperty_XWRCALNAME)
        if temps is not None:
            self.mName = temps
        temps = self.loadValueString(definitions.cICalProperty_XWRCALDESC)
        if temps is not None:
            self.mDescription = temps

    def sortedComponentNames(self) -> Tuple[str, ...]:
        return (
            definitions.cICalComponent_VTIMEZONE,
            definitions.cICalComponent_VEVENT,
            definitions.cICalComponent_VTODO,
            definitions.cICalComponent_VJOURNAL,
            definitions.cICalComponent_VFREEBUSY,
            definitions.cICalComponent_VAVAILABILITY,
        )

    def sortedPropertyKeyOrder(self) -> Tuple[str, ...]:
        return (
            definitions.cICalProperty_VERSION,
            definitions.cICalProperty_CALSCALE,
            definitions.cICalProperty_METHOD,
            definitions.cICalProperty_PRODID,
        )

    def parse(self, ins: Any) -> Any:
        result = super(Calendar, self).parse(ins)
        from pycalendar.timezonedb import TimezoneDatabase
        TimezoneDatabase.mergeTimezones(self, self.getComponents(definitions.cICalComponent_VTIMEZONE))
        return result

    def parseComponent(self, ins: Any) -> Optional[Any]:
        result: Optional[Any] = None
        LOOK_FOR_VCALENDAR = 0
        GET_PROPERTY_OR_COMPONENT = 1
        GOT_VCALENDAR = 4
        state = LOOK_FOR_VCALENDAR
        lines: List[Optional[str]] = [None, None]
        comp: Any = self
        compend: Optional[str] = None
        componentstack: List[Any] = []
        got_timezone: bool = False
        while readFoldedLine(ins, lines):
            line = lines[0]
            if state == LOOK_FOR_VCALENDAR:
                if line == self.getBeginDelimiter():
                    state = GET_PROPERTY_OR_COMPONENT
                elif len(line) == 0:
                    if ParserContext.BLANK_LINES_IN_DATA == ParserContext.PARSER_RAISE:
                        raise InvalidData("iCalendar data has blank lines")
                else:
                    raise InvalidData("iCalendar data not recognized", line)
            elif state == GET_PROPERTY_OR_COMPONENT:
                if line.startswith("BEGIN:"):
                    componentstack.append((comp, compend,))
                    comp = self.sComponentType.makeComponent(line[6:], comp)
                    compend = comp.getEndDelimiter()
                    if result is None:
                        result = comp
                    if comp.getType() == definitions.cICalComponent_VTIMEZONE:
                        got_timezone = True
                elif line == self.getEndDelimiter():
                    state = GOT_VCALENDAR
                elif line == compend:
                    comp.finalise()
                    componentstack[-1][0].addComponent(comp)
                    comp, compend = componentstack.pop()
                elif len(line) == 0:
                    if ParserContext.BLANK_LINES_IN_DATA == ParserContext.PARSER_RAISE:
                        raise InvalidData("iCalendar data has blank lines")
                elif comp is self:
                    pass
                else:
                    prop = self.sPropertyType.parseText(line)
                    if comp is not self:
                        comp.addProperty(prop)
            if state == GOT_VCALENDAR:
                break
        if got_timezone:
            from pycalendar.timezonedb import TimezoneDatabase
            TimezoneDatabase.mergeTimezones(self, self.getComponents(definitions.cICalComponent_VTIMEZONE))
        return result

    def addComponent(self, component: Any) -> None:
        super(Calendar, self).addComponent(component)
        if isinstance(component, ComponentRecur):
            uid = component.getUID()
            rid = component.getRecurrenceID()
            if rid:
                self.mOverriddenComponentsByUID[uid].append(component)
            else:
                self.mMasterComponentsByTypeAndUID[component.getType()][uid] = component

    def removeComponent(self, component: Any) -> None:
        super(Calendar, self).removeComponent(component)
        if isinstance(component, ComponentRecur):
            uid = component.getUID()
            rid = component.getRecurrenceID()
            if rid:
                self.mOverriddenComponentsByUID[uid].remove(component)
            else:
                del self.mMasterComponentsByTypeAndUID[component.getType()][uid]

    def deriveComponent(self, recurrenceID: DateTime) -> Optional[ComponentRecur]:
        master = self.masterComponent()
        if master is None:
            return None
        newcomp = master.duplicate()
        for propname in (
            definitions.cICalProperty_RRULE,
            definitions.cICalProperty_RDATE,
            definitions.cICalProperty_EXRULE,
            definitions.cICalProperty_EXDATE,
            definitions.cICalProperty_RECURRENCE_ID,
        ):
            newcomp.removeProperties(propname)
        dtstart = newcomp.getStart()
        dtend = newcomp.getEnd()
        oldduration = dtend - dtstart
        newdtstartValue = recurrenceID.duplicate()
        if not dtstart.isDateOnly():
            if dtstart.local():
                newdtstartValue.adjustTimezone(dtstart.getTimezone())
        else:
            newdtstartValue.setDateOnly(True)
        newcomp.removeProperties(definitions.cICalProperty_DTSTART)
        newcomp.removeProperties(definitions.cICalProperty_DTEND)
        prop = Property(definitions.cICalProperty_DTSTART, newdtstartValue)
        newcomp.addProperty(prop)
        if not newcomp.useDuration():
            prop = Property(definitions.cICalProperty_DTEND, newdtstartValue + oldduration)
            newcomp.addProperty(prop)
        newcomp.addProperty(Property("RECURRENCE-ID", newdtstartValue))
        newcomp.finalise()
        return newcomp

    def masterComponent(self) -> Optional[ComponentRecur]:
        for component in self.getComponents():
            if isinstance(component, ComponentRecur):
                rid = component.getRecurrenceID()
                if rid is None:
                    return component
        else:
            return None

    def getText(self, includeTimezones: Optional[int] = None, format: Optional[str] = None) -> str:
        if format is None or format == self.sFormatText:
            s = StringIO()
            self.generate(s, includeTimezones=includeTimezones)
            return s.getvalue()
        elif format == self.sFormatJSON:
            return self.getTextJSON(includeTimezones=includeTimezones)

    def generate(self, os: IO[str], includeTimezones: Optional[int] = None) -> None:
        self.includeMissingTimezones(includeTimezones=includeTimezones)
        super(Calendar, self).generate(os)

    def getTextXML(self, includeTimezones: Optional[int] = None) -> str:
        node = self.writeXML(includeTimezones)
        return xmlutils.toString(node)

    def writeXML(self, includeTimezones: Optional[int] = None) -> Any:
        self.includeMissingTimezones(includeTimezones=includeTimezones)
        root = XML.Element(xmlutils.makeTag(xmldefinitions.iCalendar20_namespace, xmldefinitions.icalendar))
        super(Calendar, self).writeXML(root, xmldefinitions.iCalendar20_namespace)
        return root

    def getTextJSON(self, includeTimezones: Optional[int] = None, sort_keys: bool = False) -> str:
        jobject: List[Any] = []
        self.writeJSON(jobject, includeTimezones)
        return json.dumps(jobject[0], indent=2, separators=(',', ':'), sort_keys=sort_keys)

    def writeJSON(self, jobject: list, includeTimezones: Optional[int] = None) -> None:
        self.includeMissingTimezones(includeTimezones=includeTimezones)
        super(Calendar, self).writeJSON(jobject)

    def getVEvents(self, period: Period, list: List[Any], all_day_at_top: bool = True) -> None:
        for vevent in self.getComponents(definitions.cICalComponent_VEVENT):
            vevent.expandPeriod(period, list)
        if all_day_at_top:
            list.sort(ComponentExpanded.sort_by_dtstart_allday)
        else:
            list.sort(ComponentExpanded.sort_by_dtstart)

    def getVToDos(self, only_due: bool, all_dates: bool, upto_due_date: DateTime, list: List[Any]) -> None:
        minusoneday = DateTime()
        minusoneday.setNowUTC()
        minusoneday.offsetDay(-1)
        today = DateTime()
        today.setToday()
        for vtodo in self.getComponents(definitions.cICalComponent_VTODO):
            if only_due:
                if vtodo.getStatus() == definitions.eStatus_VToDo_Cancelled:
                    continue
                elif (
                    (vtodo.getStatus() == definitions.eStatus_VToDo_Completed) and
                    (not vtodo.hasCompleted() or (vtodo.getCompleted() < minusoneday))
                ):
                    continue
            if not all_dates:
                if vtodo.hasEnd() and (vtodo.getEnd() > upto_due_date):
                    continue
                elif not vtodo.hasEnd() and (today > upto_due_date):
                    continue
            # TODO: fix this
            # list.append(ComponentExpandedShared(ComponentExpanded(vtodo, None)))

    def getRecurrenceInstancesItems(self, type: Any, uid: Any, items: List[Any]) -> None:
        items.extend(self.mOverriddenComponentsByUID.get(uid, ()))

    def getRecurrenceInstancesIds(self, type: Any, uid: Any, ids: List[Any]) -> None:
        ids.extend([comp.getRecurrenceID() for comp in self.mOverriddenComponentsByUID.get(uid, ())])

    def getVFreeBusyList(self, period: Period, list: List[Any]) -> None:
        for vfreebusy in self.getComponents(definitions.cICalComponent_VFREEBUSY):
            vfreebusy.expandPeriod(period, list)

    def getVFreeBusyFB(self, period: Period, fb: List[Any]) -> None:
        # TODO: fix this
        self.getVEvents(period, list)
        if len(list) == 0:
            return
        dtstart: List[Any] = []
        dtend: List[Any] = []
        for dt in list:
            if dt.getInstanceStart().isDateOnly():
                continue
            transp = ""
            if dt.getOwner().getProperty(definitions.cICalProperty_TRANSP, transp) and (transp == definitions.cICalProperty_TRANSPARENT):
                continue
            dtstart.append(dt.getInstanceStart())
            dtend.append(dt.getInstanceEnd())
        list.clear()
        temp = Period(dtstart.front(), dtend.front())
        dtstart_iter = dtstart.iter()
        dtstart_iter.next()
        dtend_iter = dtend.iter()
        dtend_iter.next()
        for _ignore in (None,):
            if dtstart_iter > temp.getEnd():
                fb.addProperty(Property(definitions.cICalProperty_FREEBUSY, temp))
                temp = Period(dtstart_iter, dtend_iter)
            if dtend_iter > temp.getEnd():
                temp = Period(temp.getStart(), dtend_iter)
        fb.addProperty(Property(definitions.cICalProperty_FREEBUSY, temp))

    def getFreeBusy(self, period: Period, fb: List[Any]) -> None:
        list: List[Any] = []
        self.getVEvents(period, list)
        for comp in list:
            if comp.getInstanceStart().isDateOnly():
                continue
            transp = ""
            if comp.getOwner().getProperty(definitions.cICalProperty_TRANSP, transp) and (transp == definitions.cICalProperty_TRANSPARENT):
                continue
            status = comp.getMaster().getStatus()
            if status in (definitions.eStatus_VEvent_None, definitions.eStatus_VEvent_Confirmed):
                fb.append(FreeBusy(FreeBusy.BUSY, Period(comp.getInstanceStart(), comp.getInstanceEnd())))
            elif status == definitions.eStatus_VEvent_Tentative:
                fb.append(FreeBusy(FreeBusy.BUSYTENTATIVE, Period(comp.getInstanceStart(), comp.getInstanceEnd())))
                break
            elif status == definitions.eStatus_VEvent_Cancelled:
                pass
        list2: List[Any] = []
        self.getVFreeBusy(period, list2)
        for comp in list2:
            comp.expandPeriod(period, fb)
        FreeBusy.resolveOverlaps(fb)

    def getTimezoneOffsetSeconds(self, tzid: str, dt: DateTime, relative_to_utc: bool = False) -> int:
        timezone = self.getTimezone(tzid)
        return timezone.getTimezoneOffsetSeconds(dt, relative_to_utc) if timezone else 0

    def getTimezoneDescriptor(self, tzid: str, dt: DateTime) -> str:
        timezone = self.getTimezone(tzid)
        return timezone.getTimezoneDescriptor(dt) if timezone else ""

    def getTimezone(self, tzid: str) -> Optional[Any]:
        for timezone in self.getComponents(definitions.cICalComponent_VTIMEZONE):
            if timezone.getID() == tzid:
                return timezone
        else:
            return None

    def addDefaultProperties(self) -> None:
        self.addProperty(Property(definitions.cICalProperty_PRODID, Calendar.sProdID))
        self.addProperty(Property(definitions.cICalProperty_VERSION, "2.0"))
        self.addProperty(Property(definitions.cICalProperty_CALSCALE, "GREGORIAN"))

    def validProperty(self, prop: Any) -> bool:
        if prop.getName() == definitions.cICalProperty_VERSION:
            tvalue = prop.getTextValue()
            if ((tvalue is None) or (tvalue.getValue() != "2.0")):
                return False
        elif prop.getName() == definitions.cICalProperty_CALSCALE:
            tvalue = prop.getTextValue()
            if ((tvalue is None) or (tvalue.getValue() != "GREGORIAN")):
                return False
        return True

    def includeMissingTimezones(self, includeTimezones: Optional[int] = None) -> None:
        if includeTimezones == Calendar.NO_TIMEZONES:
            return
        if includeTimezones is None:
            includeTimezones = Calendar.NONSTD_TIMEZONES
        tzids: Set[str] = set()
        for component in self.mComponents:
            if component.getType() != definitions.cICalComponent_VTIMEZONE:
                component.getTimezones(tzids)
        from pycalendar.timezonedb import TimezoneDatabase
        for tzid in tzids:
            if includeTimezones == Calendar.NONSTD_TIMEZONES and TimezoneDatabase.isStandardTimezone(tzid):
                continue
            tz = self.getTimezone(tzid)
            if tz is None:
                tz = TimezoneDatabase.getTimezone(tzid)
                if tz is not None:
                    dup = tz.duplicate()
                    self.addComponent(dup)

    def stripStandardTimezones(self) -> bool:
        from pycalendar.timezonedb import TimezoneDatabase
        changed = False
        for component in self.getComponents(definitions.cICalComponent_VTIMEZONE):
            tz = TimezoneDatabase.getTimezone(component.getID())
            if tz is not None and TimezoneDatabase.isStandardTimezone(component.getID()):
                self.removeComponent(component)
                changed = True
        return changed