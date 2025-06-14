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
from typing import Any, List, Dict, Tuple, Union
from pycalendar.datetime import DateTime
from pycalendar.icalendar import definitions
from pycalendar.icalendar.property import Property
from pycalendar.icalendar.vtimezone import VTimezone
from pycalendar.icalendar.vtimezonedaylight import Daylight
from pycalendar.icalendar.vtimezonestandard import Standard
from pycalendar.utcoffsetvalue import UTCOffsetValue
import rule
import utils

__all__ = (
    "Zone",
    "ZoneRule",
)

class Zone(object):
    name: str
    rules: List["ZoneRule"]

    def __init__(self) -> None:
        self.name: str = ""
        self.rules: List["ZoneRule"] = []

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
        line = splitlines[0]
        splits = [x for x in line.expandtabs(1).split(" ") if len(x) > 0]
        self.name = splits[1]
        rule_obj = ZoneRule(self)
        rule_obj.parse(line, 0)
        self.rules.append(rule_obj)
        for line in splitlines[1:]:
            if len(line) == 0:
                continue
            rule_obj = ZoneRule(self)
            rule_obj.parse(line, 2)
            if rule_obj.gmtoff != "#":
                self.rules.append(rule_obj)

    def generate(self) -> str:
        lines: List[str] = []
        for count, tzrule in enumerate(self.rules):
            if count == 0:
                items = (
                    "Zone " + self.name,
                    tzrule.generate(),
                )
            else:
                items = (
                    "",
                    "",
                    "",
                    tzrule.generate(),
                )
            lines.append("\t".join(items))
        return "\n".join(lines)

    def expand(
        self,
        rules: Dict[str, rule.RuleSet],
        minYear: int,
        maxYear: int
    ) -> List[Tuple[DateTime, int, int, "ZoneRule", Any]]:
        start = DateTime(year=1800, month=1, day=1, hours=0, minutes=0, seconds=0)
        start_offset = self.rules[0].getUTCOffset()
        start_stdoffset = self.rules[0].getUTCOffset()
        startdt = start.duplicate()

        transitions: List[Tuple[DateTime, int, "ZoneRule", Any]] = []
        lastUntilDateUTC = start.duplicate()
        last_offset = start_offset
        last_stdoffset = start_stdoffset
        first = True
        for zonerule in self.rules:
            last_offset, last_stdoffset = zonerule.expand(
                rules, transitions, lastUntilDateUTC, last_offset, last_stdoffset, maxYear
            )
            lastUntilDate = zonerule.getUntilDate()
            lastUntilDateUTC = lastUntilDate.getUTC(last_offset, last_stdoffset)
            if first and len(self.rules) > 1:
                transitions = []
                first = False

        transitions.sort(key=lambda x: x[0])
        results: List[Tuple[DateTime, int, int, "ZoneRule", Any]] = []
        last_transition: Tuple[DateTime, int, int] = (startdt, start_offset, start_offset)
        for transition in transitions:
            dtutc, to_offset, zonerule, rule = transition
            dt = dtutc.duplicate()
            dt.offsetSeconds(last_transition[1])

            if dtutc.getYear() >= minYear:
                if dt > last_transition[0]:
                    results.append((dt, last_transition[1], to_offset, zonerule, rule))
                elif dt <= last_transition[0]:
                    if len(results):
                        results[-1] = ((results[-1][0], results[-1][1], to_offset, zonerule, None))
                    else:
                        results.append((last_transition[0], last_transition[1], last_transition[2], zonerule, None))
            last_transition = (dt, to_offset, last_transition[2], rule)

        return results

    def vtimezone(
        self,
        calendar: Any,
        rules: Dict[str, rule.RuleSet],
        minYear: int,
        maxYear: int
    ) -> VTimezone:
        vtz = VTimezone(parent=calendar)
        vtz.addProperty(Property(definitions.cICalProperty_TZID, self.name))
        vtz.addProperty(Property("X-LIC-LOCATION", self.name))
        transitions = self.expand(rules, minYear, maxYear)
        lastZoneRule = None
        ruleorder: List[Any] = []
        rulemap: Dict[Any, List[Tuple[DateTime, int, int]]] = {}

        def _generateRuleData() -> None:
            for tzrule in ruleorder:
                if tzrule:
                    lastOffsetPair = (rulemap[tzrule][0][1], rulemap[tzrule][0][2],)
                    startIndex = 0
                    for index in range(len(rulemap[tzrule])):
                        offsetPair = (rulemap[tzrule][index][1], rulemap[tzrule][index][2],)
                        if offsetPair != lastOffsetPair:
                            tzrule.vtimezone(
                                vtz,
                                lastZoneRule,
                                rulemap[tzrule][startIndex][0],
                                rulemap[tzrule][index - 1][0],
                                rulemap[tzrule][startIndex][1],
                                rulemap[tzrule][startIndex][2],
                                index - startIndex,
                            )
                            lastOffsetPair = (rulemap[tzrule][index][1], rulemap[tzrule][index][2],)
                            startIndex = index

                    tzrule.vtimezone(
                        vtz,
                        lastZoneRule,
                        rulemap[tzrule][startIndex][0],
                        rulemap[tzrule][index][0],
                        rulemap[tzrule][startIndex][1],
                        rulemap[tzrule][startIndex][2],
                        len(rulemap[tzrule]),
                    )
                else:
                    lastZoneRule.vtimezone(
                        vtz,
                        lastZoneRule,
                        rulemap[tzrule][0][0],
                        rulemap[tzrule][-1][0],
                        rulemap[tzrule][0][1],
                        rulemap[tzrule][0][2],
                    )
            del ruleorder[:]
            rulemap.clear()

        for dt, offsetfrom, offsetto, zonerule, tzrule in transitions:
            if zonerule.format != "LMT":
                if lastZoneRule and lastZoneRule != zonerule:
                    _generateRuleData()
                if tzrule not in ruleorder:
                    ruleorder.append(tzrule)
                rulemap.setdefault(tzrule, []).append((dt, offsetfrom, offsetto,))
            lastZoneRule = zonerule

        _generateRuleData()
        self._compressRDateComponents(vtz)
        vtz.finalise()
        return vtz

    def _compressRDateComponents(self, vtz: VTimezone) -> None:
        similarMap: Dict[Any, List[Any]] = {}
        for item in vtz.mComponents:
            item.finalise()
            key = (
                item.getType(),
                item.getTZName(),
                item.getUTCOffset(),
                item.getUTCOffsetFrom(),
            )
            if item.hasProperty(definitions.cICalProperty_RDATE):
                similarMap.setdefault(key, []).append(item)
        for values in similarMap.values():
            if len(values) > 1:
                mergeTo = values[0]
                for mergeFrom in values[1:]:
                    prop = mergeFrom.getProperties()[definitions.cICalProperty_RDATE][0]
                    mergeTo.addProperty(prop)
                    vtz.mComponents.remove(mergeFrom)

class ZoneRule(object):
    zone: Zone
    gmtoff: Union[str, int]
    rule: str
    format: str
    until: Union[str, None]
    _cached_until: Any
    _cached_utc_offset: Any

    def __init__(self, zone: Zone) -> None:
        self.zone = zone
        self.gmtoff: Union[str, int] = 0
        self.rule: str = ""
        self.format: str = ""
        self.until: Union[str, None] = None
        self._cached_until: Any = None
        self._cached_utc_offset: Any = None

    def __str__(self) -> str:
        return self.generate()

    def __eq__(self, other: Any) -> bool:
        return other and (
            self.gmtoff == other.gmtoff and
            self.rule == other.rule and
            self.format == other.format and
            self.until == other.until
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def parse(self, line: str, offset: int) -> None:
        splits = [x for x in line.expandtabs(1).split(" ") if len(x) > 0]
        assert len(splits) + offset >= 5, "Help: %s" % (line,)
        self.gmtoff = splits[2 - offset]
        self.rule = splits[3 - offset]
        self.format = splits[4 - offset]
        if len(splits) >= 6 - offset:
            self.until = " ".join(splits[5 - offset:])

    def generate(self) -> str:
        items = (
            self.gmtoff,
            self.rule,
            self.format,
        )
        if self.until:
            items = items + (self.until,)
        return "\t".join(items)

    def getUntilDate(self) -> Any:
        if self._cached_until is None:
            year = 9999
            month = 12
            day = 1
            hours = 0
            minutes = 0
            seconds = 0
            mode = None
            if self.until and not self.until.startswith("#"):
                splits = self.until.split(" ")
                year = int(splits[0])
                month = 1
                day = 1
                hours = 0
                minutes = 0
                seconds = 0
                mode = None
                if len(splits) > 1 and not splits[1].startswith("#"):
                    month = int(rule.Rule.MONTH_NAME_TO_POS[splits[1]])
                    if len(splits) > 2 and not splits[2].startswith("#"):
                        if splits[2] == "lastSun":
                            dt = DateTime(year=year, month=month, day=1)
                            dt.setDayOfWeekInMonth(-1, DateTime.SUNDAY)
                            splits[2] = dt.getDay()
                        elif splits[2] == "lastSat":
                            dt = DateTime(year=year, month=month, day=1)
                            dt.setDayOfWeekInMonth(-1, DateTime.SATURDAY)
                            splits[2] = dt.getDay()
                        elif splits[2] == "Sun>=1":
                            dt = DateTime(year=year, month=month, day=1)
                            dt.setNextDayOfWeek(1, DateTime.SUNDAY)
                            splits[2] = dt.getDay()
                        elif splits[2] == "Sun>=8":
                            dt = DateTime(year=year, month=month, day=1)
                            dt.setNextDayOfWeek(8, DateTime.SUNDAY)
                            splits[2] = dt.getDay()
                        day = int(splits[2])
                        if len(splits) > 3 and not splits[3].startswith("#"):
                            splits_time = splits[3].split(":")
                            hours = int(splits_time[0])
                            minutes = int(splits_time[1][:2])
                            if len(splits_time[1]) > 2:
                                mode = splits_time[1][2:]
                            else:
                                mode = None
                            if len(splits_time) > 2:
                                seconds = int(splits_time[2])
            dt = DateTime(year=year, month=month, day=day, hours=hours, minutes=minutes, seconds=seconds)
            self._cached_until = utils.DateTime(dt, mode)
        return self._cached_until

    def getUTCOffset(self) -> int:
        if self._cached_utc_offset is None:
            splits = self.gmtoff.split(":")
            hours = int(splits[0] if splits[0][0] != "-" else splits[0][1:])
            minutes = int(splits[1]) if len(splits) > 1 else 0
            seconds = int(splits[2]) if len(splits) > 2 else 0
            negative = splits[0][0] == "-"
            self._cached_utc_offset = ((hours * 60) + minutes) * 60 + seconds
            if negative:
                self._cached_utc_offset = -1 * self._cached_utc_offset
        return self._cached_utc_offset

    def expand(
        self,
        rules: Dict[str, rule.RuleSet],
        results: List[Tuple[Any, ...]],
        lastUntilUTC: DateTime,
        lastOffset: int,
        lastStdOffset: int,
        maxYear: int
    ) -> Tuple[int, int]:
        assert self.isNumericOffset() or self.rule in rules, "No rule '%s' found in cache. %s for %s" % (self.rule, self, self.zone,)
        if self.isNumericOffset():
            return self.expand_norule(results, lastUntilUTC, maxYear)
        else:
            tempresults: List[Tuple[Any, ...]] = []
            ruleset = rules[self.rule]
            ruleset.expand(tempresults, self, maxYear)
            tempresults.sort(key=lambda x: x[0])
            found_one = False
            found_start = False
            last_offset = lastOffset
            last_stdoffset = lastStdOffset
            last_tzrule = None
            finalUntil = self.getUntilDate()
            for dt, to_offset, tzrule in tempresults:
                dtutc = dt.getUTC(last_offset, last_stdoffset)
                if dtutc >= lastUntilUTC:
                    if not found_start and dtutc != lastUntilUTC:
                        if not found_one:
                            last_offset = self.getUTCOffset()
                            last_stdoffset = self.getUTCOffset()
                            dtutc = dt.getUTC(last_offset, last_stdoffset)
                        results.append((lastUntilUTC, last_offset, self, last_tzrule))
                    found_start = True
                    if dtutc >= finalUntil.getUTC(last_offset, last_stdoffset):
                        break
                    results.append((dtutc, to_offset, self, tzrule))
                last_offset = to_offset
                last_stdoffset = self.getUTCOffset()
                last_tzrule = tzrule
                found_one = True
            if found_start == 0:
                results.append((lastUntilUTC, last_offset, self, None))
            return last_offset, last_stdoffset

    def expand_norule(
        self,
        results: List[Tuple[Any, ...]],
        lastUntil: DateTime,
        maxYear: int
    ) -> Tuple[int, int]:
        to_offset = self.getNumericOffset()
        results.append((lastUntil, self.getUTCOffset() + to_offset, self, None))
        return (self.getUTCOffset() + to_offset, self.getUTCOffset())

    def isNumericOffset(self) -> bool:
        if self.rule == "-":
            return True
        elif self.rule and (self.rule[0].isdigit() or (self.rule[0] == "-" and self.rule[1].isdigit())):
            return True
        else:
            return False

    def getNumericOffset(self) -> int:
        offset = 0
        if self.rule != "-":
            splits = self.rule.split(":")
            offset = 60 * 60 * int(splits[0])
            if len(splits) > 1:
                offset += 60 * int(splits[1])
        return offset

    def vtimezone(
        self,
        vtz: VTimezone,
        zonerule: "ZoneRule",
        start: DateTime,
        end: DateTime,
        offsetfrom: int,
        offsetto: int
    ) -> None:
        if self.isNumericOffset() and self.getNumericOffset() != 0:
            comp = Daylight(parent=vtz)
        else:
            comp = Standard(parent=vtz)
        tzoffsetfrom = UTCOffsetValue(offsetfrom)
        tzoffsetto = UTCOffsetValue(offsetto)
        comp.addProperty(Property(definitions.cICalProperty_TZOFFSETFROM, tzoffsetfrom))
        comp.addProperty(Property(definitions.cICalProperty_TZOFFSETTO, tzoffsetto))
        if self.format.find("%") != -1:
            tzname = self.format % ("S",)
        else:
            tzname = self.format
        comp.addProperty(Property(definitions.cICalProperty_TZNAME, tzname))
        comp.addProperty(Property(definitions.cICalProperty_DTSTART, start))
        comp.addProperty(Property(definitions.cICalProperty_RDATE, start))
        comp.finalise()
        vtz.addComponent(comp)