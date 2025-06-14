##
#    Copyright (c) 2007-2019 Cyrus Daboo. All rights reserved.
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
from typing import Any, List, Tuple, Dict, Union
from pycalendar.datetime import DateTime
from pycalendar.icalendar import definitions
from pycalendar.icalendar.property import Property
from pycalendar.icalendar.recurrence import Recurrence
from pycalendar.icalendar.vtimezonedaylight import Daylight
from pycalendar.icalendar.vtimezonestandard import Standard
from pycalendar.utcoffsetvalue import UTCOffsetValue
from pycalendar.utils import daysInMonth
import utils

__all__ = (
    "Rule",
    "RuleSet",
)

class RuleSet(object):
    """
    A set of tzdata rules tied to a specific Rule name
    """

    name: str
    rules: List["Rule"]

    def __init__(self) -> None:
        self.name: str = ""
        self.rules: List["Rule"] = []

    def __str__(self) -> str:
        return self.generate()

    def __eq__(self, other: Any) -> bool:
        return other and (
            self.name == other.name and
            self.rules == other.rules
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def parse(self, lines: str) -> None:
        splitlines = lines.split("\n")
        for line in splitlines:
            splits = line.expandtabs(1).split(" ")
            name = splits[1]
            assert name, "Must have a zone name: '%s'" % (lines,)
            if not self.name:
                self.name = name
            assert self.name == name, "Different zone names %s and %s: %s" % (self.name, name, line,)
            rule = Rule()
            rule.parse(line)
            self.rules.append(rule)

    def generate(self) -> str:
        items = [rule.generate() for rule in self.rules]
        return "\n".join(items)

    def expand(self, results: List[Any], zoneinfo: Any, maxYear: int) -> None:
        for rule in self.rules:
            rule.expand(results, zoneinfo, maxYear)

class Rule(object):
    """
    A tzdata Rule
    """

    LASTDAY_NAME_TO_DAY: Dict[str, int] = {
        "lastSun": DateTime.SUNDAY,
        "lastMon": DateTime.MONDAY,
        "lastTue": DateTime.TUESDAY,
        "lastWed": DateTime.WEDNESDAY,
        "lastThu": DateTime.THURSDAY,
        "lastFri": DateTime.FRIDAY,
        "lastSat": DateTime.SATURDAY,
    }

    DAY_NAME_TO_DAY: Dict[str, int] = {
        "Sun": DateTime.SUNDAY,
        "Mon": DateTime.MONDAY,
        "Tue": DateTime.TUESDAY,
        "Wed": DateTime.WEDNESDAY,
        "Thu": DateTime.THURSDAY,
        "Fri": DateTime.FRIDAY,
        "Sat": DateTime.SATURDAY,
    }

    LASTDAY_NAME_TO_RDAY: Dict[str, int] = {
        "lastSun": definitions.eRecurrence_WEEKDAY_SU,
        "lastMon": definitions.eRecurrence_WEEKDAY_MO,
        "lastTue": definitions.eRecurrence_WEEKDAY_TU,
        "lastWed": definitions.eRecurrence_WEEKDAY_WE,
        "lastThu": definitions.eRecurrence_WEEKDAY_TH,
        "lastFri": definitions.eRecurrence_WEEKDAY_FR,
        "lastSat": definitions.eRecurrence_WEEKDAY_SA,
    }

    DAY_NAME_TO_RDAY: Dict[int, int] = {
        DateTime.SUNDAY: definitions.eRecurrence_WEEKDAY_SU,
        DateTime.MONDAY: definitions.eRecurrence_WEEKDAY_MO,
        DateTime.TUESDAY: definitions.eRecurrence_WEEKDAY_TU,
        DateTime.WEDNESDAY: definitions.eRecurrence_WEEKDAY_WE,
        DateTime.THURSDAY: definitions.eRecurrence_WEEKDAY_TH,
        DateTime.FRIDAY: definitions.eRecurrence_WEEKDAY_FR,
        DateTime.SATURDAY: definitions.eRecurrence_WEEKDAY_SA,
    }

    MONTH_NAME_TO_POS: Dict[str, int] = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }

    MONTH_POS_TO_NAME: Tuple[str, ...] = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

    name: str
    fromYear: str
    toYear: str
    type: str
    inMonth: str
    onDay: str
    atTime: str
    saveTime: str
    letter: str
    dt_cache: Union[None, List[Any]]

    def __init__(self) -> None:
        self.name: str = ""
        self.fromYear: str = ""
        self.toYear: str = ""
        self.type: str = "-"
        self.inMonth: str = ""
        self.onDay: str = ""
        self.atTime: str = ""
        self.saveTime: str = ""
        self.letter: str = ""
        self.dt_cache: Union[None, List[Any]] = None

    def __str__(self) -> str:
        return self.generate()

    def __eq__(self, other: Any) -> bool:
        return other and (
            self.name == other.name and
            self.fromYear == other.fromYear and
            self.toYear == other.toYear and
            self.type == other.type and
            self.inMonth == other.inMonth and
            self.onDay == other.onDay and
            self.atTime == other.atTime and
            self.saveTime == other.saveTime and
            self.letter == other.letter
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def parse(self, line: str) -> None:
        splits = [x for x in line.expandtabs(1).split(" ") if len(x) > 0]
        assert len(splits) >= 10, "Wrong number of fields in Rule: '%s'" % (line,)
        self.name = splits[1]
        self.fromYear = splits[2]
        self.toYear = splits[3]
        self.type = splits[4]
        self.inMonth = splits[5]
        self.onDay = splits[6]
        self.atTime = splits[7]
        self.saveTime = splits[8]
        self.letter = splits[9]

    def generate(self) -> str:
        items = (
            "Rule",
            self.name,
            self.fromYear,
            self.toYear,
            self.type,
            self.inMonth,
            self.onDay,
            self.atTime,
            self.saveTime,
            self.letter,
        )
        return "\t".join(items)

    def getOffset(self) -> int:
        splits = self.saveTime.split(":")
        hours = int(splits[0])
        if len(splits) == 2:
            minutes = int(splits[1])
        else:
            minutes = 0
        negative = hours < 0
        if negative:
            return -((-hours * 60) + minutes) * 60
        else:
            return ((hours * 60) + minutes) * 60

    def startYear(self) -> int:
        return int(self.fromYear)

    def endYear(self) -> int:
        if self.toYear == "only":
            return self.startYear()
        elif self.toYear == "max":
            return 9999
        else:
            return int(self.toYear)

    def datetimeForYear(self, year: int) -> Tuple[DateTime, str]:
        dt = DateTime()
        dt.setYear(year)
        dt.setMonth(Rule.MONTH_NAME_TO_POS[self.inMonth])
        dt.setDay(1)
        splits = self.atTime.split(":")
        if len(splits) == 1:
            splits.append("0")
        assert len(splits) == 2, "atTime format is wrong: %s, %s" % (self.atTime, self,)
        hours = int(splits[0])
        if len(splits[1]) > 2:
            minutes = int(splits[1][:2])
            special = splits[1][2:]
        else:
            minutes = int(splits[1])
            special = ""
        if hours == 24 and minutes == 0:
            dt.setHours(23)
            dt.setMinutes(59)
            dt.setSeconds(59)
        else:
            dt.setHours(hours)
            dt.setMinutes(minutes)
        if self.onDay in Rule.LASTDAY_NAME_TO_DAY:
            dt.setDayOfWeekInMonth(-1, Rule.LASTDAY_NAME_TO_DAY[self.onDay])
        elif self.onDay.find(">=") != -1:
            splits = self.onDay.split(">=")
            dt.setNextDayOfWeek(int(splits[1]), Rule.DAY_NAME_TO_DAY[splits[0]])
        else:
            try:
                day = int(self.onDay)
                dt.setDay(day)
            except:
                assert False, "onDay value is not recognized: %s" % (self.onDay,)
        return dt, special

    def getOnDayDetails(self, start: DateTime, indicatedDay: int, indicatedOffset: int) -> Tuple[int, int, Union[None, List[int]]]:
        month = start.getMonth()
        year = start.getYear()
        dayOfWeek = start.getDayOfWeek()
        if indicatedDay != dayOfWeek:
            difference = dayOfWeek - indicatedDay
            if difference in (1, -6,):
                indicatedOffset += 1
                if start.getDay() == 1:
                    month -= 1
                    if month < 1:
                        month = 12
            elif difference in (-1, 6,):
                assert indicatedOffset != 1, "Bad RRULE adjustment"
                indicatedOffset -= 1
            elif difference in (-5,):
                pass
            else:
                assert False, "Unknown RRULE adjustment"
        try:
            day = Rule.DAY_NAME_TO_RDAY[dayOfWeek]
            offset = indicatedOffset
            bymday = None
            if offset == 1:
                offset = 1
            elif offset == 8:
                offset = 2
            elif offset == 15:
                offset = 3
            elif offset == 22:
                offset = 4
            else:
                days_in_month = daysInMonth(month, year)
                if days_in_month - offset == 6:
                    offset = -1
                elif days_in_month - offset == 13:
                    offset = -2
                elif days_in_month - offset == 20:
                    offset = -3
                else:
                    bymday = [offset + i for i in range(7) if (offset + i) <= days_in_month]
                    offset = 0
        except:
            assert False, "onDay value is not recognized: %s" % (self.onDay,)
        return offset, day, bymday

    def expand(self, results: List[Any], zoneinfo: Any, maxYear: int) -> None:
        if self.startYear() >= maxYear:
            return
        self.fullExpand(maxYear)
        zoneoffset = zoneinfo.getUTCOffset()
        offset = self.getOffset()
        for dt in self.dt_cache:
            results.append((dt, zoneoffset + offset, self))

    def fullExpand(self, maxYear: int) -> None:
        if self.dt_cache is None:
            start = self.startYear()
            end = self.endYear()
            if end > maxYear:
                end = maxYear - 1
            self.dt_cache = []
            for year in range(start, end + 1):
                dt = utils.DateTime(*self.datetimeForYear(year))
                self.dt_cache.append(dt)

    def vtimezone(
        self,
        vtz: Any,
        zonerule: Any,
        start: DateTime,
        end: DateTime,
        offsetfrom: int,
        offsetto: int,
        instanceCount: int
    ) -> None:
        dstoffset = self.getOffset()
        if dstoffset == 0:
            comp = Standard(parent=vtz)
        else:
            comp = Daylight(parent=vtz)
        tzoffsetfrom = UTCOffsetValue(offsetfrom)
        tzoffsetto = UTCOffsetValue(offsetto)
        comp.addProperty(Property(definitions.cICalProperty_TZOFFSETFROM, tzoffsetfrom))
        comp.addProperty(Property(definitions.cICalProperty_TZOFFSETTO, tzoffsetto))
        if zonerule.format.find("%") != -1:
            tzname = zonerule.format % (self.letter if self.letter != "-" else "",)
        elif "/" in zonerule.format:
            split_format = zonerule.format.split("/")
            tzname = split_format[0] if dstoffset == 0 else split_format[1]
        else:
            tzname = zonerule.format
        comp.addProperty(Property(definitions.cICalProperty_TZNAME, tzname))
        comp.addProperty(Property(definitions.cICalProperty_DTSTART, start))
        if start == end:
            instanceCount = 1
        if self.toYear != "only" and instanceCount != 1:
            rrule = Recurrence()
            rrule.setFreq(definitions.eRecurrence_YEARLY)
            rrule.setByMonth((Rule.MONTH_NAME_TO_POS[self.inMonth],))
            if self.onDay in Rule.LASTDAY_NAME_TO_RDAY:
                dayOfWeek = start.getDayOfWeek()
                indicatedDay = Rule.LASTDAY_NAME_TO_DAY[self.onDay]
                if dayOfWeek == indicatedDay:
                    rrule.setByDay(((-1, Rule.LASTDAY_NAME_TO_RDAY[self.onDay]),))
                elif dayOfWeek < indicatedDay or dayOfWeek == 6 and indicatedDay == 0:
                    fakeOffset = daysInMonth(start.getMonth(), start.getYear()) - 6
                    offset, rday, bymday = self.getOnDayDetails(start, indicatedDay, fakeOffset)
                    if bymday:
                        rrule.setByMonthDay(bymday)
                    rrule.setByDay(((offset, rday),))
                else:
                    rrule.setByMonth(())
                    daysBackStartOfMonth = (
                        365, 334, 306, 275, 245, 214, 184, 153, 122, 92, 61, 31, 0
                    )
                    rrule.setByYearDay([-(daysBackStartOfMonth[Rule.MONTH_NAME_TO_POS[self.inMonth]] + i) for i in range(7)])
                    rrule.setByDay(
                        ((0, divmod(Rule.LASTDAY_NAME_TO_DAY[self.onDay] + 1, 7)[1]),),
                    )
            elif self.onDay.find(">=") != -1:
                indicatedDay, dayoffset = self.onDay.split(">=")
                dayOfWeek = start.getDayOfWeek()
                indicatedDay = Rule.DAY_NAME_TO_DAY[indicatedDay]
                if dayOfWeek == indicatedDay:
                    offset, rday, bymday = self.getOnDayDetails(start, indicatedDay, int(dayoffset))
                    if bymday:
                        rrule.setByMonthDay(bymday)
                    rrule.setByDay(((offset, rday),))
                elif dayoffset == 1 and divmod(dayoffset - indicatedDay, 7)[1] == 6:
                    rrule.setByMonth(())
                    daysBackStartOfMonth = (
                        365, 334, 306, 275, 245, 214, 184, 153, 122, 92, 61, 31, 0
                    )
                    rrule.setByYearDay([-(daysBackStartOfMonth[Rule.MONTH_NAME_TO_POS[self.inMonth]] + i) for i in range(7)])
                    rrule.setByDay(
                        ((0, divmod(indicatedDay + 1, 7)[1]),),
                    )
                else:
                    offset, rday, bymday = self.getOnDayDetails(start, indicatedDay, int(dayoffset))
                    if bymday:
                        rrule.setByMonthDay(bymday)
                    rrule.setByDay(((offset, rday),))
            else:
                try:
                    int(self.onDay)
                except:
                    assert False, "onDay value is not recognized: %s" % (self.onDay,)
            if zonerule.getUntilDate().dt.getYear() < 9999 or self.endYear() < 9999:
                until = end.duplicate()
                until.offsetSeconds(-offsetfrom)
                until.setTimezoneUTC(True)
                rrule.setUseUntil(True)
                rrule.setUntil(until)
            comp.addProperty(Property(definitions.cICalProperty_RRULE, rrule))
        else:
            comp.addProperty(Property(definitions.cICalProperty_RDATE, start))
        comp.finalise()
        vtz.addComponent(comp)