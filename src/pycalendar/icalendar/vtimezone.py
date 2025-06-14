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
from typing import Any, List, Optional, Tuple, Dict, Union
from pycalendar.datetime import DateTime
from pycalendar.icalendar import definitions
from pycalendar.icalendar.component import Component
from pycalendar.icalendar.validation import ICALENDAR_VALUE_CHECKS

class VTimezone(Component):
    propertyCardinality_1: Tuple[str, ...] = (
        definitions.cICalProperty_TZID,
    )

    propertyCardinality_0_1: Tuple[str, ...] = (
        definitions.cICalProperty_LAST_MODIFIED,
        definitions.cICalProperty_TZURL,
    )

    propertyValueChecks: Any = ICALENDAR_VALUE_CHECKS

    UTCOFFSET_CACHE_MAX_ENTRIES: int = 100000
    sortSubComponents: bool = False

    mID: str
    mUTCOffsetSortKey: Optional[float]
    mCachedExpandAllMaxYear: Optional[int]
    mCachedOffsets: Optional[Dict[Any, int]]

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent=parent)
        self.mID = ""
        self.mUTCOffsetSortKey = None
        self.mCachedExpandAllMaxYear = None
        self.mCachedOffsets = None

    def duplicate(self, parent: Any = None) -> "VTimezone":
        other = super().duplicate(parent=parent)
        other.mID = self.mID
        other.mUTCOffsetSortKey = self.mUTCOffsetSortKey
        return other

    def getType(self) -> str:
        return definitions.cICalComponent_VTIMEZONE

    def getMimeComponentName(self) -> None:
        return None

    def addComponent(self, comp: Any) -> None:
        if ((comp.getType() == definitions.cICalComponent_STANDARD) or
                (comp.getType() == definitions.cICalComponent_DAYLIGHT)):
            super().addComponent(comp)
        else:
            raise ValueError("Only 'STANDARD' or 'DAYLIGHT' components allowed in 'VTIMEZONE'")

    def getMapKey(self) -> str:
        return self.mID

    def finalise(self) -> None:
        temp = self.loadValueString(definitions.cICalProperty_TZID)
        if temp is not None:
            self.mID = temp
        self.mComponents.sort(key=lambda x: x.getStart())
        super().finalise()

    def validate(self, doFix: bool = False) -> Tuple[List[str], List[str]]:
        fixed, unfixed = super().validate(doFix)
        for component in self.mComponents:
            if component.getType() in (definitions.cICalComponent_STANDARD, definitions.cICalComponent_DAYLIGHT):
                break
        else:
            logProblem = "[%s] At least one component must be present: %s or %s" % (
                self.getType(),
                definitions.cICalComponent_STANDARD,
                definitions.cICalComponent_DAYLIGHT,
            )
            unfixed.append(logProblem)
        return fixed, unfixed

    def getID(self) -> str:
        return self.mID

    def getUTCOffsetSortKey(self) -> float:
        if self.mUTCOffsetSortKey is None:
            if len(self.mComponents) > 0:
                utc_offset1 = self.mComponents[0].getUTCOffset()
                utc_offset2 = utc_offset1
                if len(self.mComponents) > 1:
                    utc_offset2 = self.mComponents[1].getUTCOffset()
                self.mUTCOffsetSortKey = (utc_offset1 + utc_offset2) / 2
            else:
                self.mUTCOffsetSortKey = 0
        return self.mUTCOffsetSortKey

    def getTimezoneOffsetSeconds(self, dt: DateTime, relative_to_utc: bool = False) -> int:
        temp = dt.duplicate()
        temp.setTimezoneID(None)
        if self.mCachedExpandAllMaxYear is None or temp.mYear >= self.mCachedExpandAllMaxYear:
            cacheMax = temp.duplicate()
            cacheMax.setHHMMSS(0, 0, 0)
            cacheMax.offsetYear(2)
            cacheMax.setMonth(1)
            cacheMax.setDay(1)
            self.mCachedExpandAll = self.expandAll(None, cacheMax)
            self.mCachedExpandAllMaxYear = cacheMax.mYear
            self.mCachedOffsets = {}
        if len(self.mCachedExpandAll):
            cacheKey = (temp.mYear, temp.mMonth, temp.mDay, temp.mHours, temp.mMinutes, relative_to_utc)
            i = self.mCachedOffsets.get(cacheKey) if self.mCachedOffsets is not None else None
            if i is None:
                i = VTimezone.tuple_bisect_right(self.mCachedExpandAll, temp, relative_to_utc)
                if self.mCachedOffsets is not None and len(self.mCachedOffsets) >= self.UTCOFFSET_CACHE_MAX_ENTRIES:
                    self.mCachedOffsets = {}
                if self.mCachedOffsets is not None:
                    self.mCachedOffsets[cacheKey] = i
            if i != 0:
                return self.mCachedExpandAll[i - 1][3]
        return 0

    def getTimezoneDescriptor(self, dt: DateTime) -> str:
        result = ""
        found = self.findTimezoneElement(dt)
        if found is not None:
            if len(found.getTZName()) == 0:
                tzoffset = found.getUTCOffset()
                negative = False
                if tzoffset < 0:
                    tzoffset = -tzoffset
                    negative = True
                result = ("+", "-")[negative]
                hours_offset = tzoffset // (60 * 60)
                if hours_offset < 10:
                    result += "0"
                result += str(hours_offset)
                mins_offset = (tzoffset // 60) % 60
                if mins_offset < 10:
                    result += "0"
                result += str(mins_offset)
            else:
                result = "(" + found.getTZName() + ")"
        return result

    def mergeTimezone(self, tz: Any) -> None:
        pass

    @staticmethod
    def tuple_bisect_right(a: List[Any], x: DateTime, relative_to_utc: bool = False) -> int:
        lo = 0
        hi = len(a)
        while lo < hi:
            mid = (lo + hi) // 2
            if x < a[mid][1 if relative_to_utc else 0]:
                hi = mid
            else:
                lo = mid + 1
        return lo

    def findTimezoneElement(self, dt: DateTime) -> Optional[Any]:
        temp = dt.duplicate()
        temp.setTimezoneID(None)
        found = None
        dt_found = DateTime()
        for item in self.mComponents:
            dt_item = item.expandBelow(temp)
            if temp >= dt_item:
                if found is not None:
                    if dt_item > dt_found:
                        found = item
                        dt_found = dt_item
                else:
                    found = item
                    dt_found = dt_item
        return found

    def expandAll(self, start: Any, end: Any, with_name: bool = False) -> List[Any]:
        results: List[Any] = []
        for item in self.mComponents:
            results.extend(item.expandAll(start, end, with_name))
        utc_results: List[Any] = []
        for items in set(results):
            items = list(items)
            utcdt = items[0].duplicate()
            utcdt.offsetSeconds(-items[1])
            utcdt.setTimezoneUTC(True)
            items.insert(1, utcdt)
            utc_results.append(tuple(items))
        utc_results.sort(key=lambda x: x[0].getPosixTime())
        return utc_results

    def sortedPropertyKeyOrder(self) -> Tuple[str, ...]:
        return (
            definitions.cICalProperty_TZID,
            definitions.cICalProperty_LAST_MODIFIED,
            definitions.cICalProperty_TZURL,
        )

    @staticmethod
    def sortByUTCOffsetComparator(tz1: "VTimezone", tz2: "VTimezone") -> int:
        sort1 = tz1.getUTCOffsetSortKey()
        sort2 = tz2.getUTCOffsetSortKey()
        if sort1 == sort2:
            return tz1.getID().casefold().__cmp__(tz2.getID().casefold())
        else:
            return (1, -1)[sort1 < sort2]

Component.registerComponent(definitions.cICalComponent_VTIMEZONE, VTimezone)