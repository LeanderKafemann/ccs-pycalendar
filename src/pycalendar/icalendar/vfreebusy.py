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
from typing import Any, List, Optional, Tuple
from pycalendar.datetime import DateTime
from pycalendar.icalendar import definitions
from pycalendar.icalendar import itipdefinitions
from pycalendar.icalendar.component import Component
from pycalendar.icalendar.freebusy import FreeBusy
from pycalendar.icalendar.property import Property
from pycalendar.icalendar.validation import ICALENDAR_VALUE_CHECKS
from pycalendar.period import Period
from pycalendar.periodvalue import PeriodValue
from pycalendar.value import Value

class VFreeBusy(Component):
    propertyCardinality_1: Tuple[str, ...] = (
        definitions.cICalProperty_DTSTAMP,
        definitions.cICalProperty_UID,
    )

    propertyCardinality_0_1: Tuple[str, ...] = (
        definitions.cICalProperty_CONTACT,
        definitions.cICalProperty_DTSTART,
        definitions.cICalProperty_DTEND,
        definitions.cICalProperty_ORGANIZER,
        definitions.cICalProperty_URL,
    )

    propertyValueChecks: Any = ICALENDAR_VALUE_CHECKS

    mStart: DateTime
    mHasStart: bool
    mEnd: DateTime
    mHasEnd: bool
    mDuration: bool
    mCachedBusyTime: bool
    mSpanPeriod: Optional[Period]
    mBusyTime: Optional[List[FreeBusy]]

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent=parent)
        self.mStart = DateTime()
        self.mHasStart = False
        self.mEnd = DateTime()
        self.mHasEnd = False
        self.mDuration = False
        self.mCachedBusyTime = False
        self.mSpanPeriod = None
        self.mBusyTime = None

    def duplicate(self, parent: Any = None) -> "VFreeBusy":
        other = super().duplicate(parent=parent)
        other.mStart = self.mStart.duplicate()
        other.mHasStart = self.mHasStart
        other.mEnd = self.mEnd.duplicate()
        other.mHasEnd = self.mHasEnd
        other.mDuration = self.mDuration
        other.mCachedBusyTime = False
        other.mBusyTime = None
        return other

    def getType(self) -> str:
        return definitions.cICalComponent_VFREEBUSY

    def getMimeComponentName(self) -> str:
        return itipdefinitions.cICalMIMEComponent_VFREEBUSY

    def finalise(self) -> None:
        super().finalise()
        temp = self.loadValueDateTime(definitions.cICalProperty_DTSTART)
        self.mHasStart = temp is not None
        if self.mHasStart:
            self.mStart = temp
        temp = self.loadValueDateTime(definitions.cICalProperty_DTEND)
        if temp is None:
            temp = self.loadValueDuration(definitions.cICalProperty_DURATION)
            if temp is not None:
                self.mEnd = self.mStart + temp
                self.mDuration = True
            else:
                self.mEnd = self.mStart
        else:
            self.mHasEnd = True
            self.mDuration = False
            self.mEnd = temp

    def fixStartEnd(self) -> None:
        if self.mHasStart and self.mEnd <= self.mStart:
            self.mEnd = self.mStart.duplicate()
            self.mDuration = False
            if self.mStart.isDateOnly():
                self.mEnd.offsetDay(1)
                self.mDuration = True
            else:
                self.mEnd.offsetDay(1)
                self.mEnd.setHHMMSS(0, 0, 0)

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

    def getSpanPeriod(self) -> Optional[Period]:
        return self.mSpanPeriod

    def getBusyTime(self) -> Optional[List[FreeBusy]]:
        return self.mBusyTime

    def editTiming(self) -> None:
        self.mHasStart = False
        self.mHasEnd = False
        self.mDuration = False
        self.mStart.setToday()
        self.mEnd.setToday()
        self.removeProperties(definitions.cICalProperty_DTSTART)
        self.removeProperties(definitions.cICalProperty_DTEND)
        self.removeProperties(definitions.cICalProperty_DURATION)

    def editTimingStartEnd(self, start: DateTime, end: DateTime) -> None:
        self.mHasStart = self.mHasEnd = True
        self.mStart = start
        self.mEnd = end
        self.mDuration = False
        self.fixStartEnd()
        self.removeProperties(definitions.cICalProperty_DTSTART)
        self.removeProperties(definitions.cICalProperty_DTEND)
        self.removeProperties(definitions.cICalProperty_DURATION)
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

    def expandPeriodComp(self, period: Period, result: List[Any]) -> None:
        if not self.mCachedBusyTime:
            self.cacheBusyTime()
        if (self.mBusyTime is not None) and period.isPeriodOverlap(self.mSpanPeriod):
            result.append(self)

    def expandPeriodFB(self, period: Period, result: List[FreeBusy]) -> None:
        if not self.mCachedBusyTime:
            self.cacheBusyTime()
        if (self.mBusyTime is not None) and period.isPeriodOverlap(self.mSpanPeriod):
            for fb in self.mBusyTime:
                result.append(FreeBusy(fb))

    def cacheBusyTime(self) -> None:
        self.mBusyTime = []
        min_start = DateTime()
        max_end = DateTime()
        props = self.getProperties()
        result = props.get(definitions.cICalProperty_FREEBUSY, ())
        for iter in result:
            type = 0
            is_busy = False
            if iter.hasParameter(definitions.cICalParameter_FBTYPE):
                fbyype = iter.getParameterValue(definitions.cICalParameter_FBTYPE)
                if fbyype.upper() == definitions.cICalParameter_FBTYPE_BUSY:
                    is_busy = True
                    type = FreeBusy.BUSY
                elif fbyype.upper() == definitions.cICalParameter_FBTYPE_BUSYUNAVAILABLE:
                    is_busy = True
                    type = FreeBusy.BUSYUNAVAILABLE
                elif fbyype.upper() == definitions.cICalParameter_FBTYPE_BUSYTENTATIVE:
                    is_busy = True
                    type = FreeBusy.BUSYTENTATIVE
                else:
                    is_busy = False
                    type = FreeBusy.FREE
            else:
                is_busy = True
                type = FreeBusy.BUSY
            if is_busy:
                multi = iter.getMultiValue()
                if (multi is not None) and (multi.getType() == Value.VALUETYPE_PERIOD):
                    for o in multi.getValues():
                        period = None
                        if isinstance(o, PeriodValue):
                            period = o
                        if period is not None:
                            self.mBusyTime.append(FreeBusy(type, period.getValue()))
                            if len(self.mBusyTime) == 1:
                                min_start = period.getValue().getStart()
                                max_end = period.getValue().getEnd()
                            else:
                                if min_start > period.getValue().getStart():
                                    min_start = period.getValue().getStart()
                                if max_end < period.getValue().getEnd():
                                    max_end = period.getValue().getEnd()
        if len(self.mBusyTime) == 0:
            self.mBusyTime = None
        else:
            self.mBusyTime.sort(key=lambda x: x.getPeriod().getStart().getPosixTime())
            start = DateTime()
            end = DateTime()
            if self.mHasStart:
                start = self.mStart
            else:
                start = min_start
            if self.mHasEnd:
                end = self.mEnd
            else:
                end = max_end
            self.mSpanPeriod = Period(start, end)
        self.mCachedBusyTime = True

    def sortedPropertyKeyOrder(self) -> Tuple[str, ...]:
        return (
            definitions.cICalProperty_UID,
            definitions.cICalProperty_DTSTART,
            definitions.cICalProperty_DURATION,
            definitions.cICalProperty_DTEND,
        )

Component.registerComponent(definitions.cICalComponent_VFREEBUSY, VFreeBusy)