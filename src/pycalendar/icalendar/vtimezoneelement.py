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
from typing import Any, List, Optional, Tuple, Union
from bisect import bisect_right
from pycalendar.datetime import DateTime
from pycalendar.icalendar import definitions
from pycalendar.icalendar.component import Component
from pycalendar.icalendar.recurrenceset import RecurrenceSet
from pycalendar.icalendar.validation import ICALENDAR_VALUE_CHECKS
from pycalendar.period import Period
from pycalendar.value import Value

class VTimezoneElement(Component):
    propertyCardinality_1: Tuple[str, ...] = (
        definitions.cICalProperty_DTSTART,
        definitions.cICalProperty_TZOFFSETTO,
        definitions.cICalProperty_TZOFFSETFROM,
    )

    propertyCardinality_0_1: Tuple[str, ...] = (
        definitions.cICalProperty_RRULE,
    )

    propertyValueChecks: Any = ICALENDAR_VALUE_CHECKS

    mStart: DateTime
    mTZName: str
    mUTCOffset: int
    mUTCOffsetFrom: int
    mRecurrences: RecurrenceSet
    mCachedExpandBelow: Optional[DateTime]
    mCachedExpandBelowItems: Optional[List[DateTime]]

    def __init__(self, parent: Any = None, dt: Optional[DateTime] = None, offset: Optional[int] = None) -> None:
        super().__init__(parent=parent)
        self.mStart = dt if dt is not None else DateTime()
        self.mTZName = ""
        self.mUTCOffset = offset if offset is not None else 0
        self.mUTCOffsetFrom = 0
        self.mRecurrences = RecurrenceSet()
        self.mCachedExpandBelow = None
        self.mCachedExpandBelowItems = None

    def duplicate(self, parent: Any = None) -> "VTimezoneElement":
        other = super().duplicate(parent=parent)
        other.mStart = self.mStart.duplicate()
        other.mTZName = self.mTZName
        other.mUTCOffset = self.mUTCOffset
        other.mUTCOffsetFrom = self.mUTCOffsetFrom
        other.mRecurrences = self.mRecurrences.duplicate()
        other.mCachedExpandBelow = None
        other.mCachedExpandBelowItems = None
        return other

    def finalise(self) -> None:
        temp = self.loadValueDateTime(definitions.cICalProperty_DTSTART)
        if temp is not None:
            self.mStart = temp
        temp = self.loadValueInteger(definitions.cICalProperty_TZOFFSETTO, Value.VALUETYPE_UTC_OFFSET)
        if temp is not None:
            self.mUTCOffset = temp
        temp = self.loadValueInteger(definitions.cICalProperty_TZOFFSETFROM, Value.VALUETYPE_UTC_OFFSET)
        if temp is not None:
            self.mUTCOffsetFrom = temp
        temps = self.loadValueString(definitions.cICalProperty_TZNAME)
        if temps is not None:
            self.mTZName = temps
        self.loadValueRRULE(definitions.cICalProperty_RRULE, self.mRecurrences, True)
        self.loadValueRDATE(definitions.cICalProperty_RDATE, self.mRecurrences, True)
        super().finalise()

    def getSortKey(self) -> str:
        return ""

    def getStart(self) -> DateTime:
        return self.mStart

    def getUTCOffset(self) -> int:
        return self.mUTCOffset

    def getUTCOffsetFrom(self) -> int:
        return self.mUTCOffsetFrom

    def getTZName(self) -> str:
        return self.mTZName

    def expandBelow(self, below: DateTime) -> DateTime:
        if not self.mRecurrences.hasRecurrence() or self.mStart > below:
            return self.mStart
        else:
            temp = DateTime(below.getYear(), 1, 1, 0, 0, 0)
            if self.mCachedExpandBelowItems is None:
                self.mCachedExpandBelowItems = []
            if self.mCachedExpandBelow is None:
                self.mCachedExpandBelow = self.mStart.duplicate()
            if temp > self.mCachedExpandBelow:
                self.mCachedExpandBelowItems = []
                period = Period(self.mStart, temp)
                self.mRecurrences.expand(self.mStart, period, self.mCachedExpandBelowItems, float_offset=self.mUTCOffsetFrom)
                self.mCachedExpandBelow = temp
            if len(self.mCachedExpandBelowItems) != 0:
                i = bisect_right(self.mCachedExpandBelowItems, below)
                if i != 0:
                    return self.mCachedExpandBelowItems[i - 1]
                return self.mCachedExpandBelowItems[0]
            return self.mStart

    def expandAll(self, start: Optional[DateTime], end: DateTime, with_name: bool) -> Union[Tuple[Tuple[Any, ...], ...], Tuple[()]]:
        if start is None:
            start = self.mStart
        offsetto = self.loadValueInteger(definitions.cICalProperty_TZOFFSETTO, Value.VALUETYPE_UTC_OFFSET)
        offsetfrom = self.loadValueInteger(definitions.cICalProperty_TZOFFSETFROM, Value.VALUETYPE_UTC_OFFSET)
        if self.mStart > end:
            return ()
        elif not self.mRecurrences.hasRecurrence():
            if self.mStart >= start:
                result: Tuple[Any, ...] = (self.mStart, offsetfrom, offsetto)
                if with_name:
                    result += (self.getTZName(),)
                return (result,)
            else:
                return ()
        else:
            temp = DateTime(end.getYear(), 1, 1, 0, 0, 0)
            if self.mCachedExpandBelowItems is None:
                self.mCachedExpandBelowItems = []
            if self.mCachedExpandBelow is None:
                self.mCachedExpandBelow = self.mStart.duplicate()
            if temp > self.mCachedExpandBelow:
                self.mCachedExpandBelowItems = []
                period = Period(self.mStart, end)
                self.mRecurrences.expand(self.mStart, period, self.mCachedExpandBelowItems, float_offset=self.mUTCOffsetFrom)
                self.mCachedExpandBelow = temp
            if len(self.mCachedExpandBelowItems) != 0:
                results: List[Tuple[Any, ...]] = []
                for dt in self.mCachedExpandBelowItems:
                    if dt >= start and dt < end:
                        result: Tuple[Any, ...] = (dt, offsetfrom, offsetto)
                        if with_name:
                            result += (self.getTZName(),)
                        results.append(result)
                return tuple(results)
            return ()