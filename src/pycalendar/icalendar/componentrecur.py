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
from typing import Any, Callable, List, Optional, Tuple, Union
from pycalendar.datetime import DateTime
from pycalendar.icalendar import definitions
from pycalendar.icalendar.component import Component
from pycalendar.icalendar.componentexpanded import ComponentExpanded
from pycalendar.icalendar.property import Property
from pycalendar.icalendar.recurrenceset import RecurrenceSet
from pycalendar.timezone import Timezone
from pycalendar.utils import set_difference
import uuid

class ComponentRecur(Component):
    propertyCardinality_STATUS_Fix: Tuple[str, ...] = (
        definitions.cICalProperty_STATUS,
    )

    mMaster: "ComponentRecur"
    mMapKey: Optional[str]
    mSummary: Optional[str]
    mStamp: DateTime
    mHasStamp: bool
    mStart: DateTime
    mHasStart: bool
    mEnd: DateTime
    mHasEnd: bool
    mDuration: bool
    mHasRecurrenceID: bool
    mAdjustFuture: bool
    mAdjustPrior: bool
    mRecurrenceID: Optional[DateTime]
    mRecurrences: Optional[RecurrenceSet]

    @staticmethod
    def mapKey(uid: str, rid: Optional[str] = None) -> Optional[str]:
        if uid:
            result = "u:" + uid
            if rid is not None:
                result += rid
            return result
        else:
            return None

    @staticmethod
    def sort_by_dtstart_allday(e1: Any, e2: Any) -> bool:
        if e1.self.mStart.isDateOnly() and e2.self.mStart.isDateOnly():
            return e1.self.mStart < e2.self.mStart
        elif e1.self.mStart.isDateOnly():
            return True
        elif e2.self.mStart.isDateOnly():
            return False
        elif e1.self.mStart == e2.self.mStart:
            if e1.self.mEnd == e2.self.mEnd:
                return e1.self.mStamp < e2.self.mStamp
            else:
                return e1.self.mEnd > e2.self.mEnd
        else:
            return e1.self.mStart < e2.self.mStart

    @staticmethod
    def sort_by_dtstart(e1: Any, e2: Any) -> bool:
        if e1.self.mStart == e2.self.mStart:
            if (
                e1.self.mStart.isDateOnly() and e2.self.mStart.isDateOnly() or
                not e1.self.mStart.isDateOnly() and not e2.self.mStart.isDateOnly()
            ):
                return False
            else:
                return e1.self.mStart.isDateOnly()
        else:
            return e1.self.mStart < e2.self.mStart

    def __init__(self, parent: Optional[Any] = None) -> None:
        super(ComponentRecur, self).__init__(parent=parent)
        self.mMaster: ComponentRecur = self
        self.mMapKey: Optional[str] = None
        self.mSummary: Optional[str] = None
        self.mStamp: DateTime = DateTime()
        self.mHasStamp: bool = False
        self.mStart: DateTime = DateTime()
        self.mHasStart: bool = False
        self.mEnd: DateTime = DateTime()
        self.mHasEnd: bool = False
        self.mDuration: bool = False
        self.mHasRecurrenceID: bool = False
        self.mAdjustFuture: bool = False
        self.mAdjustPrior: bool = False
        self.mRecurrenceID: Optional[DateTime] = None
        self.mRecurrences: Optional[RecurrenceSet] = None
        self.cardinalityChecks += (
            self.check_cardinality_STATUS_Fix,
        )

    def duplicate(self, parent: Optional[Any] = None) -> "ComponentRecur":
        other = super(ComponentRecur, self).duplicate(parent=parent)
        other.mMaster = self.mMaster if self.recurring() else self
        other.mMapKey = self.mMapKey
        other.mSummary = self.mSummary
        if (self.mStamp is not None):
            other.mStamp = self.mStamp.duplicate()
        other.mHasStamp = self.mHasStamp
        other.mStart = self.mStart.duplicate()
        other.mHasStart = self.mHasStart
        other.mEnd = self.mEnd.duplicate()
        other.mHasEnd = self.mHasEnd
        other.mDuration = self.mDuration
        other.mHasRecurrenceID = self.mHasRecurrenceID
        other.mAdjustFuture = self.mAdjustFuture
        other.mAdjustPrior = self.mAdjustPrior
        if self.mRecurrenceID is not None:
            other.mRecurrenceID = self.mRecurrenceID.duplicate()
        other._resetRecurrenceSet()
        return other

    def canGenerateInstance(self) -> bool:
        return not self.mHasRecurrenceID

    def recurring(self) -> bool:
        return (self.mMaster is not None) and (self.mMaster is not self)

    def setMaster(self, master: "ComponentRecur") -> None:
        self.mMaster = master
        self.initFromMaster()

    def getMaster(self) -> "ComponentRecur":
        return self.mMaster

    def getMapKey(self) -> str:
        if self.mMapKey is None:
            self.mMapKey = str(uuid.uuid4())
        return self.mMapKey

    def getMasterKey(self) -> Optional[str]:
        return ComponentRecur.mapKey(self.mUID)

    def initDTSTAMP(self) -> None:
        super(ComponentRecur, self).initDTSTAMP()
        temp = self.loadValueDateTime(definitions.cICalProperty_DTSTAMP)
        self.mHasStamp = temp is not None
        if self.mHasStamp:
            self.mStamp = temp

    def getStamp(self) -> DateTime:
        return self.mStamp

    def hasStamp(self) -> bool:
        return self.mHasStamp

    def getStart(self) -> DateTime:
        return self.mStart

    def hasStart(self) -> bool:
        return self.mHasStart

    def getEnd(self) -> DateTime:
        return self.mEnd

    def hasEnd(self) -> bool:
        return self.mHasEnd

    def useDuration(self) -> bool:
        return self.mDuration

    def isRecurrenceInstance(self) -> bool:
        return self.mHasRecurrenceID

    def isAdjustFuture(self) -> bool:
        return self.mAdjustFuture

    def isAdjustPrior(self) -> bool:
        return self.mAdjustPrior

    def getRecurrenceID(self) -> Optional[DateTime]:
        return self.mRecurrenceID

    def isRecurring(self) -> bool:
        return (self.mRecurrences is not None) and self.mRecurrences.hasRecurrence()

    def getRecurrenceSet(self) -> Optional[RecurrenceSet]:
        return self.mRecurrences

    def setUID(self, uid: str) -> None:
        super(ComponentRecur, self).setUID(uid)
        if self.mHasRecurrenceID:
            self.mMapKey = self.mapKey(self.mUID, self.mRecurrenceID.getText())
        else:
            self.mMapKey = self.mapKey(self.mUID)

    def getSummary(self) -> Optional[str]:
        return self.mSummary

    def setSummary(self, summary: str) -> None:
        self.mSummary = summary

    def getDescription(self) -> str:
        txt = self.loadValueString(definitions.cICalProperty_DESCRIPTION)
        if txt is not None:
            return txt
        else:
            return ""

    def getLocation(self) -> str:
        txt = self.loadValueString(definitions.cICalProperty_LOCATION)
        if txt is not None:
            return txt
        else:
            return ""

    def finalise(self) -> None:
        super(ComponentRecur, self).finalise()
        temp = self.loadValueDateTime(definitions.cICalProperty_DTSTAMP)
        self.mHasStamp = temp is not None
        if self.mHasStamp:
            self.mStamp = temp
        temp = self.loadValueDateTime(definitions.cICalProperty_DTSTART)
        self.mHasStart = temp is not None
        if self.mHasStart:
            self.mStart = temp
        temp = self.loadValueDateTime(definitions.cICalProperty_DTEND)
        if temp is None:
            temp = self.loadValueDuration(definitions.cICalProperty_DURATION)
            if temp is not None:
                self.mHasEnd = False
                self.mEnd = self.mStart + temp
                self.mDuration = True
            else:
                self.mHasEnd = False
                self.mEnd = self.mStart.duplicate()
                if self.mEnd.isDateOnly():
                    self.mEnd.offsetDay(1)
                self.mDuration = False
        else:
            self.mHasEnd = True
            self.mEnd = temp
            self.mDuration = False
        temp = self.loadValueString(definitions.cICalProperty_SUMMARY)
        if temp is not None:
            self.mSummary = temp
        self.mHasRecurrenceID = (self.countProperty(definitions.cICalProperty_RECURRENCE_ID) != 0)
        if self.mHasRecurrenceID:
            self.mRecurrenceID = self.loadValueDateTime(definitions.cICalProperty_RECURRENCE_ID)
        if self.mHasRecurrenceID:
            self.mMapKey = self.mapKey(self.mUID, self.mRecurrenceID.getText())
            attrs = self.findFirstProperty(definitions.cICalProperty_RECURRENCE_ID).getParameters()
            if definitions.cICalParameter_RANGE in attrs:
                self.mAdjustFuture = (attrs[definitions.cICalParameter_RANGE][0].getFirstValue() == definitions.cICalParameter_RANGE_THISANDFUTURE)
                self.mAdjustPrior = (attrs[definitions.cICalParameter_RANGE][0].getFirstValue() == definitions.cICalParameter_RANGE_THISANDPRIOR)
            else:
                self.mAdjustFuture = False
                self.mAdjustPrior = False
        else:
            self.mMapKey = self.mapKey(self.mUID)
        self._resetRecurrenceSet()

    def validate(self, doFix: bool = False) -> Tuple[List[str], List[str]]:
        fixed, unfixed = super(ComponentRecur, self).validate(doFix)
        if self.mHasStart and self.mRecurrences:
            dtutc = self.mStart.duplicateAsUTC()
            for rrule in self.mRecurrences.getRules():
                if rrule.getUseUntil():
                    if rrule.getUntil().isDateOnly() ^ self.mStart.isDateOnly():
                        logProblem = "[%s] Value types must match: %s, %s" % (
                            self.getType(),
                            definitions.cICalProperty_DTSTART,
                            definitions.cICalValue_RECUR_UNTIL,
                        )
                        if doFix:
                            rrule.getUntil().setDateOnly(self.mStart.isDateOnly())
                            if not self.mStart.isDateOnly():
                                rrule.getUntil().setHHMMSS(dtutc.getHours(), dtutc.getMinutes(), dtutc.getSeconds())
                                rrule.getUntil().setTimezone(Timezone(utc=True))
                            self.mRecurrences.changed()
                            fixed.append(logProblem)
                        else:
                            unfixed.append(logProblem)
        return fixed, unfixed

    def check_cardinality_STATUS_Fix(self, fixed: List[str], unfixed: List[str], doFix: bool) -> None:
        for propname in self.propertyCardinality_STATUS_Fix:
            if self.countProperty(propname) > 1:
                logProblem = "[%s] Too many properties: %s" % (self.getType(), propname)
                if doFix:
                    for prop in self.getProperties(propname):
                        if prop.getTextValue().getValue().upper() == definitions.cICalProperty_STATUS_CANCELLED:
                            self.removeProperties(propname)
                            self.addProperty(Property(propname, definitions.cICalProperty_STATUS_CANCELLED))
                            fixed.append(logProblem)
                            break
                    else:
                        unfixed.append(logProblem)
                else:
                    unfixed.append(logProblem)

    def _resetRecurrenceSet(self) -> None:
        self.mRecurrences = None
        if (
            (self.countProperty(definitions.cICalProperty_RRULE) != 0) or
            (self.countProperty(definitions.cICalProperty_RDATE) != 0) or
            (self.countProperty(definitions.cICalProperty_EXRULE) != 0) or
            (self.countProperty(definitions.cICalProperty_EXDATE) != 0)
        ):
            self.mRecurrences = RecurrenceSet()
            self.loadValueRRULE(definitions.cICalProperty_RRULE, self.mRecurrences, True)
            self.loadValueRDATE(definitions.cICalProperty_RDATE, self.mRecurrences, True)
            self.loadValueRRULE(definitions.cICalProperty_EXRULE, self.mRecurrences, False)
            self.loadValueRDATE(definitions.cICalProperty_EXDATE, self.mRecurrences, False)

    def FixStartEnd(self) -> None:
        if self.mHasStart and self.mEnd <= self.mStart:
            self.mEnd = self.mStart.duplicate()
            self.mDuration = False
            if self.mStart.isDateOnly():
                self.mEnd.offsetDay(1)
                self.mDuration = True
            else:
                self.mEnd.offsetDay(1)
                self.mEnd.setHHMMSS(0, 0, 0)

    def expandPeriod(self, period: Any, results: List[Any]) -> None:
        if ((self.mRecurrences is not None) and self.mRecurrences.hasRecurrence() and not self.isRecurrenceInstance()):
            items: List[Any] = []
            self.mRecurrences.expand(self.mStart, period, items)
            cal = self.mParentComponent
            if cal is not None:
                recurs: List[Any] = []
                cal.getRecurrenceInstancesIds(definitions.cICalComponent_VEVENT, self.getUID(), recurs)
                recurs.sort()
                if len(recurs) != 0:
                    temp = set_difference(items, recurs)
                    items = temp
                    instances: List[Any] = []
                    cal.getRecurrenceInstancesItems(definitions.cICalComponent_VEVENT, self.getUID(), instances)
                    prior: List[Any] = []
                    future: List[Any] = []
                    for iter in instances:
                        if iter.isAdjustPrior():
                            prior.append(iter)
                        if iter.isAdjustFuture():
                            future.append(iter)
                    if len(prior) + len(future) == 0:
                        for iter in items:
                            results.append(self.createExpanded(self, iter))
                    else:
                        prior.sort(self.sort_by_dtstart)
                        future.sort(self.sort_by_dtstart)
                        for iter1 in items:
                            slave = None
                            for i in range(len(prior) - 1, 0, -1):
                                riter2 = prior[i]
                                if riter2.getStart() > iter1:
                                    slave = riter2
                                    break
                            for i in range(len(future) - 1, 0, -1):
                                riter2 = future[i]
                                if riter2.getStart() < iter1:
                                    slave = riter2
                                    break
                            if slave is None:
                                slave = self
                            results.append(self.createExpanded(slave, iter1))
                else:
                    for iter in items:
                        results.append(self.createExpanded(self, iter))
        elif self.withinPeriod(period):
            if self.isRecurrenceInstance():
                rid = self.mRecurrenceID
            else:
                rid = None
            results.append(ComponentExpanded(self, rid))

    def withinPeriod(self, period: Any) -> bool:
        if ((self.mRecurrences is not None) and self.mRecurrences.hasRecurrence()):
            items: List[Any] = []
            self.mRecurrences.expand(self.mStart, period, items)
            return len(items) != 0
        else:
            if self.mEnd <= period.getStart() or self.mStart >= period.getEnd():
                return False
            else:
                return True

    def changedRecurrence(self) -> None:
        if self.mRecurrences is not None:
            self.mRecurrences.changed()

    def editSummary(self, summary: str) -> None:
        self.mSummary = summary
        self.editProperty(definitions.cICalProperty_SUMMARY, summary)

    def editDetails(self, description: str, location: str) -> None:
        self.editProperty(definitions.cICalProperty_DESCRIPTION, description)
        self.editProperty(definitions.cICalProperty_LOCATION, location)

    def editTiming(self) -> None:
        self.mHasStart = False
        self.mHasEnd = False
        self.mDuration = False
        self.mStart.setToday()
        self.mEnd.setToday()
        self.removeProperties(definitions.cICalProperty_DTSTART)
        self.removeProperties(definitions.cICalProperty_DTEND)
        self.removeProperties(definitions.cICalProperty_DURATION)
        self.removeProperties(definitions.cICalProperty_DUE)

    def editTimingDue(self, due: DateTime) -> None:
        self.mHasStart = False
        self.mHasEnd = True
        self.mDuration = False
        self.mStart = due
        self.mEnd = due
        self.removeProperties(definitions.cICalProperty_DUE)
        self.removeProperties(definitions.cICalProperty_DTSTART)
        self.removeProperties(definitions.cICalProperty_DTEND)
        self.removeProperties(definitions.cICalProperty_DURATION)
        prop = Property(definitions.cICalProperty_DUE, due)
        self.addProperty(prop)

    def editTimingStartEnd(self, start: DateTime, end: DateTime) -> None:
        self.mHasStart = self.mHasEnd = True
        self.mStart = start
        self.mEnd = end
        self.mDuration = False
        self.FixStartEnd()
        self.removeProperties(definitions.cICalProperty_DTSTART)
        self.removeProperties(definitions.cICalProperty_DTEND)
        self.removeProperties(definitions.cICalProperty_DURATION)
        self.removeProperties(definitions.cICalProperty_DUE)
        prop = Property(definitions.cICalProperty_DTSTART, start)
        self.addProperty(prop)
        temp = start.duplicate()
        temp.offsetDay(1)
        if not start.isDateOnly() or end != temp:
            prop = Property(definitions.cICalProperty_DTEND, end)
            self.addProperty(prop)

    def editTimingStartDuration(self, start: DateTime, duration: Any) -> None:
        self.mHasStart = True
        self.mHasEnd = False
        self.mStart = start
        self.mEnd = start + duration
        self.mDuration = True
        self.removeProperties(definitions.cICalProperty_DTSTART)
        self.removeProperties(definitions.cICalProperty_DTEND)
        self.removeProperties(definitions.cICalProperty_DURATION)
        self.removeProperties(definitions.cICalProperty_DUE)
        prop = Property(definitions.cICalProperty_DTSTART, start)
        self.addProperty(prop)
        if (not start.isDateOnly() or (duration.getWeeks() != 0) or (duration.getDays() > 1)):
            prop = Property(definitions.cICalProperty_DURATION, duration)
            self.addProperty(prop)

    def editRecurrenceSet(self, recurs: RecurrenceSet) -> None:
        if self.mRecurrences is None:
            self.mRecurrences = RecurrenceSet()
        self.mRecurrences = recurs
        self.removeProperties(definitions.cICalProperty_RRULE)
        self.removeProperties(definitions.cICalProperty_EXRULE)
        self.removeProperties(definitions.cICalProperty_RDATE)
        self.removeProperties(definitions.cICalProperty_EXDATE)
        for iter in self.mRecurrences.getRules():
            prop = Property(definitions.cICalProperty_RRULE, iter)
            self.addProperty(prop)
        for iter in self.getExrules():
            prop = Property(definitions.cICalProperty_EXRULE, iter)
            self.addProperty(prop)
        for iter in self.mRecurrences.getDates():
            prop = Property(definitions.cICalProperty_RDATE, iter)
            self.addProperty(prop)
        for iter in self.mRecurrences.getExdates():
            prop = Property(definitions.cICalProperty_EXDATE, iter)
            self.addProperty(prop)

    def excludeRecurrence(self, start: DateTime) -> None:
        if self.mRecurrences is None:
            return
        self.mRecurrences.subtract(start)
        prop = Property(definitions.cICalProperty_EXDATE, start)
        self.addProperty(prop)

    def excludeFutureRecurrence(self, start: DateTime) -> None:
        if self.mRecurrences is None:
            return
        self.mRecurrences.excludeFutureRecurrence(start)
        self.removeProperties(definitions.cICalProperty_RRULE)
        self.removeProperties(definitions.cICalProperty_RDATE)
        for iter in self.mRecurrences.getRules():
            prop = Property(definitions.cICalProperty_RRULE, iter)
            self.addProperty(prop)
        for iter in self.mRecurrences.getDates():
            prop = Property(definitions.cICalProperty_RDATE, iter)
            self.addProperty(prop)

    def initFromMaster(self) -> None:
        if self.recurring():
            self.finalise()
            if not self.hasProperty(definitions.cICalProperty_DTSTART):
                self.mStart = self.mRecurrenceID
            if (
                not self.hasProperty(definitions.cICalProperty_DTEND) and
                not self.hasProperty(definitions.cICalProperty_DURATION)
            ):
                self.mEnd = self.mStart + (self.mMaster.getEnd() - self.mMaster.getStart())
            elif (self.hasProperty(definitions.cICalProperty_DURATION) and
                  not self.hasProperty(definitions.cICalProperty_DTSTART)):
                temp = self.loadValueDuration(definitions.cICalProperty_DURATION)
                self.mEnd = self.mStart + temp

    def createExpanded(self, master: Any, recurid: Any) -> ComponentExpanded:
        return ComponentExpanded(master, recurid)