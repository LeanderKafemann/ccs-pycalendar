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
from typing import Any, Dict, List, Optional, Tuple, Union, IO
from pycalendar import xmlutils
from pycalendar.datetime import DateTime
from pycalendar.icalendar import definitions, xmldefinitions
from pycalendar.icalendar.exceptions import TooManyInstancesError
from pycalendar.period import Period
from pycalendar.valueutils import ValueMixin
import io as StringIO
import xml.etree.cElementTree as XML

def WeekDayNumCompare_compare(w1: Tuple[int, int], w2: Tuple[int, int]) -> int:
    if w1[0] < w2[0]:
        return -1
    elif w1[0] > w2[0]:
        return 1
    elif w1[1] < w2[1]:
        return -1
    elif w1[1] > w2[1]:
        return 1
    else:
        return 0

def WeekDayNumSort_less_than(w1: Tuple[int, int], w2: Tuple[int, int]) -> bool:
    return (w1[0] < w2[0]) or (w1[0] == w2[0] and w1[1] < w2[1])

class Recurrence(ValueMixin):
    cFreqMap: Dict[str, int] = {
        definitions.cICalValue_RECUR_SECONDLY: definitions.eRecurrence_SECONDLY,
        definitions.cICalValue_RECUR_MINUTELY: definitions.eRecurrence_MINUTELY,
        definitions.cICalValue_RECUR_HOURLY: definitions.eRecurrence_HOURLY,
        definitions.cICalValue_RECUR_DAILY: definitions.eRecurrence_DAILY,
        definitions.cICalValue_RECUR_WEEKLY: definitions.eRecurrence_WEEKLY,
        definitions.cICalValue_RECUR_MONTHLY: definitions.eRecurrence_MONTHLY,
        definitions.cICalValue_RECUR_YEARLY: definitions.eRecurrence_YEARLY,
    }

    cFreqToXMLMap: Dict[int, str] = {
        definitions.eRecurrence_SECONDLY: xmldefinitions.recur_freq_secondly,
        definitions.eRecurrence_MINUTELY: xmldefinitions.recur_freq_minutely,
        definitions.eRecurrence_HOURLY: xmldefinitions.recur_freq_hourly,
        definitions.eRecurrence_DAILY: xmldefinitions.recur_freq_daily,
        definitions.eRecurrence_WEEKLY: xmldefinitions.recur_freq_weekly,
        definitions.eRecurrence_MONTHLY: xmldefinitions.recur_freq_monthly,
        definitions.eRecurrence_YEARLY: xmldefinitions.recur_freq_yearly,
    }

    cRecurMap: Dict[str, int] = {
        definitions.cICalValue_RECUR_FREQ: definitions.eRecurrence_FREQ,
        definitions.cICalValue_RECUR_UNTIL: definitions.eRecurrence_UNTIL,
        definitions.cICalValue_RECUR_COUNT: definitions.eRecurrence_COUNT,
        definitions.cICalValue_RECUR_INTERVAL: definitions.eRecurrence_INTERVAL,
        definitions.cICalValue_RECUR_BYSECOND: definitions.eRecurrence_BYSECOND,
        definitions.cICalValue_RECUR_BYMINUTE: definitions.eRecurrence_BYMINUTE,
        definitions.cICalValue_RECUR_BYHOUR: definitions.eRecurrence_BYHOUR,
        definitions.cICalValue_RECUR_BYDAY: definitions.eRecurrence_BYDAY,
        definitions.cICalValue_RECUR_BYMONTHDAY: definitions.eRecurrence_BYMONTHDAY,
        definitions.cICalValue_RECUR_BYYEARDAY: definitions.eRecurrence_BYYEARDAY,
        definitions.cICalValue_RECUR_BYWEEKNO: definitions.eRecurrence_BYWEEKNO,
        definitions.cICalValue_RECUR_BYMONTH: definitions.eRecurrence_BYMONTH,
        definitions.cICalValue_RECUR_BYSETPOS: definitions.eRecurrence_BYSETPOS,
        definitions.cICalValue_RECUR_WKST: definitions.eRecurrence_WKST,
    }

    cWeekdayMap: Dict[str, int] = {
        definitions.cICalValue_RECUR_WEEKDAY_SU: definitions.eRecurrence_WEEKDAY_SU,
        definitions.cICalValue_RECUR_WEEKDAY_MO: definitions.eRecurrence_WEEKDAY_MO,
        definitions.cICalValue_RECUR_WEEKDAY_TU: definitions.eRecurrence_WEEKDAY_TU,
        definitions.cICalValue_RECUR_WEEKDAY_WE: definitions.eRecurrence_WEEKDAY_WE,
        definitions.cICalValue_RECUR_WEEKDAY_TH: definitions.eRecurrence_WEEKDAY_TH,
        definitions.cICalValue_RECUR_WEEKDAY_FR: definitions.eRecurrence_WEEKDAY_FR,
        definitions.cICalValue_RECUR_WEEKDAY_SA: definitions.eRecurrence_WEEKDAY_SA,
    }

    cWeekdayRecurMap: Dict[int, str] = dict([(v, k) for k, v in cWeekdayMap.items()])
    cUnknownIndex: int = -1

    mFreq: int
    mUseCount: bool
    mCount: int
    mUseUntil: bool
    mUntil: Optional[DateTime]
    mInterval: int
    mBySeconds: Optional[List[int]]
    mByMinutes: Optional[List[int]]
    mByHours: Optional[List[int]]
    mByDay: Optional[List[Tuple[int, int]]]
    mByMonthDay: Optional[List[int]]
    mByYearDay: Optional[List[int]]
    mByWeekNo: Optional[List[int]]
    mByMonth: Optional[List[int]]
    mBySetPos: Optional[List[int]]
    mWeekstart: int
    mCached: bool
    mCacheStart: Optional[DateTime]
    mCacheUpto: Optional[DateTime]
    mFullyCached: bool
    mRecurrences: Optional[List[Any]]

    def __init__(self) -> None:
        self.init_Recurrence()

    def duplicate(self) -> "Recurrence":
        other = Recurrence()
        other.mFreq = self.mFreq
        other.mUseCount = self.mUseCount
        other.mCount = self.mCount
        other.mUseUntil = self.mUseUntil
        if other.mUseUntil and self.mUntil is not None:
            other.mUntil = self.mUntil.duplicate()
        else:
            other.mUntil = None
        other.mInterval = self.mInterval
        other.mBySeconds = self.mBySeconds[:] if self.mBySeconds is not None else None
        other.mByMinutes = self.mByMinutes[:] if self.mByMinutes is not None else None
        other.mByHours = self.mByHours[:] if self.mByHours is not None else None
        other.mByDay = self.mByDay[:] if self.mByDay is not None else None
        other.mByMonthDay = self.mByMonthDay[:] if self.mByMonthDay is not None else None
        other.mByYearDay = self.mByYearDay[:] if self.mByYearDay is not None else None
        other.mByWeekNo = self.mByWeekNo[:] if self.mByWeekNo is not None else None
        other.mByMonth = self.mByMonth[:] if self.mByMonth is not None else None
        other.mBySetPos = self.mBySetPos[:] if self.mBySetPos is not None else None
        other.mWeekstart = self.mWeekstart
        other.mCached = self.mCached
        other.mCacheStart = self.mCacheStart.duplicate() if self.mCacheStart else None
        other.mCacheUpto = self.mCacheUpto.duplicate() if self.mCacheUpto else None
        other.mFullyCached = self.mFullyCached
        other.mRecurrences = self.mRecurrences[:] if self.mRecurrences else None
        return other

    def init_Recurrence(self) -> None:
        self.mFreq = definitions.eRecurrence_YEARLY
        self.mUseCount = False
        self.mCount = 0
        self.mUseUntil = False
        self.mUntil = None
        self.mInterval = 1
        self.mBySeconds = None
        self.mByMinutes = None
        self.mByHours = None
        self.mByDay = None
        self.mByMonthDay = None
        self.mByYearDay = None
        self.mByWeekNo = None
        self.mByMonth = None
        self.mBySetPos = None
        self.mWeekstart = definitions.eRecurrence_WEEKDAY_MO
        self.mCached = False
        self.mCacheStart = None
        self.mCacheUpto = None
        self.mFullyCached = False
        self.mRecurrences = None

    def __hash__(self) -> int:
        return hash((
            self.mFreq,
            self.mUseCount,
            self.mCount,
            self.mUseUntil,
            self.mUntil,
            self.mInterval,
            tuple(self.mBySeconds) if self.mBySeconds else None,
            tuple(self.mByMinutes) if self.mByMinutes else None,
            tuple(self.mByHours) if self.mByHours else None,
            tuple(self.mByDay) if self.mByDay else None,
            tuple(self.mByMonthDay) if self.mByMonthDay else None,
            tuple(self.mByYearDay) if self.mByYearDay else None,
            tuple(self.mByWeekNo) if self.mByWeekNo else None,
            tuple(self.mByMonth) if self.mByMonth else None,
            tuple(self.mBySetPos) if self.mBySetPos else None,
            self.mWeekstart,
        ))

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Recurrence):
            return False
        return self.equals(other)

    def equals(self, comp: "Recurrence") -> bool:
        return (
            (self.mFreq == comp.mFreq) and
            (self.mUseCount == comp.mUseCount) and (self.mCount == comp.mCount) and
            (self.mUseUntil == comp.mUseUntil) and (self.mUntil == comp.mUntil) and
            (self.mInterval == comp.mInterval) and
            self.equalsNum(self.mBySeconds, comp.mBySeconds) and
            self.equalsNum(self.mByMinutes, comp.mByMinutes) and
            self.equalsNum(self.mByHours, comp.mByHours) and
            self.equalsDayNum(self.mByDay, comp.mByDay) and
            self.equalsNum(self.mByMonthDay, comp.mByMonthDay) and
            self.equalsNum(self.mByYearDay, comp.mByYearDay) and
            self.equalsNum(self.mByWeekNo, comp.mByWeekNo) and
            self.equalsNum(self.mByMonth, comp.mByMonth) and
            self.equalsNum(self.mBySetPos, comp.mBySetPos) and
            (self.mWeekstart == comp.mWeekstart)
        )

    def equalsNum(self, items1: Optional[List[int]], items2: Optional[List[int]]) -> bool:
        if items1 is None:
            items1 = []
        if items2 is None:
            items2 = []
        if len(items1) != len(items2):
            return False
        elif len(items1) == 0:
            return True
        temp1 = items1[:]
        temp2 = items2[:]
        temp1.sort()
        temp2.sort()
        for i in range(0, len(temp1)):
            if temp1[i] != temp2[i]:
                return False
        return True

    def equalsDayNum(self, items1: Optional[List[Tuple[int, int]]], items2: Optional[List[Tuple[int, int]]]) -> bool:
        if items1 is None:
            items1 = []
        if items2 is None:
            items2 = []
        if len(items1) != len(items2):
            return False
        elif len(items1) == 0:
            return True
        temp1 = items1[:]
        temp2 = items2[:]
        temp1.sort()
        temp2.sort()
        for i in range(0, len(temp1)):
            if temp1[i] != temp2[i]:
                return False
        return True

    def _setAndclearIfChanged(self, attr: str, value: Any) -> None:
        if getattr(self, attr) != value:
            self.clear()
            setattr(self, attr, value)

    def getFreq(self) -> int:
        return self.mFreq

    def setFreq(self, freq: int) -> None:
        self._setAndclearIfChanged("mFreq", freq)

    def getUseUntil(self) -> bool:
        return self.mUseUntil

    def setUseUntil(self, use_until: bool) -> None:
        self._setAndclearIfChanged("mUseUntil", use_until)

    def getUntil(self) -> Optional[DateTime]:
        return self.mUntil

    def setUntil(self, until: DateTime) -> None:
        self._setAndclearIfChanged("mUntil", until)

    def getUseCount(self) -> bool:
        return self.mUseCount

    def setUseCount(self, use_count: bool) -> None:
        self._setAndclearIfChanged("mUseCount", use_count)

    def getCount(self) -> int:
        return self.mCount

    def setCount(self, count: int) -> None:
        self._setAndclearIfChanged("mCount", count)

    def getInterval(self) -> int:
        return self.mInterval

    def setInterval(self, interval: int) -> None:
        self._setAndclearIfChanged("mInterval", interval)

    def getByMonth(self) -> Optional[List[int]]:
        return self.mByMonth

    def setByMonth(self, by: List[int]) -> None:
        self._setAndclearIfChanged("mByMonth", by[:])

    def getByMonthDay(self) -> Optional[List[int]]:
        return self.mByMonthDay

    def setByMonthDay(self, by: List[int]) -> None:
        self._setAndclearIfChanged("mByMonthDay", by[:])

    def getByYearDay(self) -> Optional[List[int]]:
        return self.mByYearDay

    def setByYearDay(self, by: List[int]) -> None:
        self._setAndclearIfChanged("mByYearDay", by[:])

    def getByDay(self) -> Optional[List[Tuple[int, int]]]:
        return self.mByDay

    def setByDay(self, by: List[Tuple[int, int]]) -> None:
        self._setAndclearIfChanged("mByDay", by[:])

    def getBySetPos(self) -> Optional[List[int]]:
        return self.mBySetPos

    def setBySetPos(self, by: List[int]) -> None:
        self._setAndclearIfChanged("mBySetPos", by[:])

    # ... (Restliche Methoden bleiben unverändert, können aber bei Bedarf ebenfalls typisiert werden)