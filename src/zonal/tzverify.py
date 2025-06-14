#!/usr/bin/env python
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
from typing import Any, List, Set, Tuple, Sequence
from pycalendar.datetime import DateTime
from pycalendar.exceptions import InvalidData
from pycalendar.icalendar.calendar import Calendar
from tzconvert import tzconvert
import getopt
import os
import sys
from pycalendar.icalendar import definitions

def loadCalendarFromZoneinfo(
    zoneinfopath: str,
    skips: Sequence[str] = (),
    only: Sequence[str] = (),
    verbose: bool = False,
    quiet: bool = False
) -> "CalendarZonesWrapper":
    if not quiet:
        print("Scanning for calendar data in: %s" % (zoneinfopath,))
    paths: List[str] = []

    def scanForICS(dirpath: str) -> None:
        for fname in os.listdir(dirpath):
            fpath = os.path.join(dirpath, fname)
            if os.path.isdir(fpath):
                scanForICS(fpath)
            elif fname.endswith(".ics"):
                if only:
                    for item in only:
                        if item in fpath:
                            if verbose:
                                print("Found calendar data: %s" % (fpath,))
                            paths.append(fpath)
                else:
                    for skip in skips:
                        if skip in fpath:
                            break
                    else:
                        if verbose:
                            print("Found calendar data: %s" % (fpath,))
                        paths.append(fpath)
    scanForICS(zoneinfopath)

    if not quiet:
        print("Parsing calendar data in: %s" % (zoneinfopath,))
    return loadCalendar(paths, verbose)

def loadCalendar(files: Sequence[str], verbose: bool) -> "CalendarZonesWrapper":
    cal = Calendar()
    for file in files:
        if verbose:
            print("Parsing calendar data: %s" % (file,))
        with open(file, "r") as fin:
            try:
                cal.parse(fin)
            except InvalidData as e:
                print("Failed to parse bad data: %s" % (e.mData,))
                raise
    return CalendarZonesWrapper(calendar=cal)

def parseTZData(zonedir: str, zonefiles: Sequence[str]) -> "CalendarZonesWrapper":
    parser = tzconvert()
    for file in zonefiles:
        zonefile = os.path.join(zonedir, file)
        if not os.path.exists(zonefile):
            print("Zone file '%s' does not exist." % (zonefile,))
        parser.parse(zonefile)
    return CalendarZonesWrapper(zones=parser)

class CalendarZonesWrapper(object):
    calendar: Any
    zones: Any

    def __init__(self, calendar: Any = None, zones: Any = None) -> None:
        self.calendar = calendar
        self.zones = zones
        assert self.calendar is not None or self.zones is not None

    def getTZIDs(self) -> Set[str]:
        if self.calendar:
            return getTZIDs(self.calendar)
        elif self.zones:
            return self.zones.getZoneNames()
        return set()

    def expandTransitions(self, tzid: str, start: DateTime, end: DateTime) -> List[Tuple[Any, ...]]:
        if self.calendar:
            return getExpandedDates(self.calendar, tzid, start, end)
        elif self.zones:
            return self.zones.expandZone(tzid, start.getYear(), end.getYear())
        return []

def compareCalendars(
    calendar1: CalendarZonesWrapper,
    calendar2: CalendarZonesWrapper,
    start: DateTime,
    end: DateTime,
    filterTzids: Sequence[str] = (),
    verbose: bool = False,
    quiet: bool = False
) -> None:
    tzids1 = calendar1.getTZIDs()
    tzids2 = calendar2.getTZIDs()

    missing = tzids1.difference(tzids2)
    if missing:
        print("""TZIDs in calendar 1 not in calendar 2 files: %s
These cannot be checked.""" % (", ".join(sorted(missing)),))

    for tzid in sorted(tzids1.intersection(tzids2)):
        if filterTzids and tzid not in filterTzids:
            continue
        if not quiet:
            print("\nChecking TZID: %s" % (tzid,))
        calendardates1 = calendar1.expandTransitions(tzid, start, end)
        calendardates2 = calendar2.expandTransitions(tzid, start, end)
        if verbose:
            print("Calendar 1 dates: %s" % (formattedExpandedDates(calendardates1),))
            print("Calendar 2 dates: %s" % (formattedExpandedDates(calendardates2),))
        set1 = set(calendardates1)
        set2 = set(calendardates2)
        d1 = set1.difference(set2)
        for i in set(d1):
            if i[0] == start:
                d1.discard(i)
                break
            if i[2] == i[3]:
                d1.discard(i)
        d2 = set2.difference(set1)
        for i in set(d2):
            if i[2] == i[3]:
                d2.discard(i)
        if d1:
            print("In calendar 1 but not in calendar 2 tzid=%s: %s" % (tzid, formattedExpandedDates(d1),))
        if d2:
            print("In calendar 2 but not in calendar 1 tzid=%s: %s" % (tzid, formattedExpandedDates(d2),))
        if not d1 and not d2 and not quiet:
            print("Matched: %s" % (tzid,))

def getTZIDs(cal: Calendar) -> Set[str]:
    results: Set[str] = set()
    for vtz in cal.getComponents(definitions.cICalComponent_VTIMEZONE):
        tzid = vtz.getID()
        results.add(tzid)
    return results

def getExpandedDates(
    cal: Calendar,
    tzid: str,
    start: DateTime,
    end: DateTime
) -> List[Tuple[Any, ...]]:
    return cal.getTimezone(tzid).expandAll(start, end)

def sortedList(setdata: Any) -> List[Any]:
    l = list(setdata)
    l.sort(key=lambda x: x[0])
    return l

def formattedExpandedDates(expanded: Any) -> str:
    items = sortedList([(item[0], item[1], secondsToTime(item[2]), secondsToTime(item[3]),) for item in expanded])
    return ", ".join(["(%s, %s, %s, %s)" % item for item in items])

def secondsToTime(seconds: int) -> str:
    if seconds < 0:
        seconds = -seconds
        negative = "-"
    else:
        negative = ""
    secs = divmod(seconds, 60)[1]
    mins = divmod(seconds // 60, 60)[1]
    hours = divmod(seconds // (60 * 60), 60)[1]
    if secs:
        return "%s%02d:%02d:%02d" % (negative, hours, mins, secs,)
    else:
        return "%s%02d:%02d" % (negative, hours, mins,)

def usage(error_msg: str = None) -> None:
    if error_msg:
        print(error_msg)

    print("""Usage: tzverify [options] DIR1 DIR2
Options:
    -h            Print this help and exit
    -v            Be verbose
    -q            Be quiet
    --start       Start year
    --end         End year

Arguments:
    DIR1          Directories containing two sets of zoneinfo data
    DIR2          to be compared

Description:
    This utility will compare iCalendar zoneinfo hierarchies by expanding
    timezone transitions and comparing.

""")

    if error_msg:
        raise ValueError(error_msg)
    else:
        sys.exit(0)

if __name__ == '__main__':

    verbose: bool = False
    quiet: bool = False
    startYear: int = 1933
    endYear: int = 2018
    zonedir1: str = None
    zonedir2: str = None

    options, args = getopt.getopt(sys.argv[1:], "hvq", ["start=", "end=", ])

    for option, value in options:
        if option == "-h":
            usage()
        elif option == "-v":
            verbose = True
        elif option == "-q":
            quiet = True
        elif option == "--start":
            startYear = int(value)
        elif option == "--end":
            endYear = int(value)
        else:
            usage("Unrecognized option: %s" % (option,))

    # Process arguments
    if len(args) != 2:
        usage("Must have two arguments")
    zonedir1 = os.path.expanduser(args[0])
    zonedir2 = os.path.expanduser(args[1])

    start = DateTime(year=startYear, month=1, day=1)
    end = DateTime(year=endYear, month=1, day=1)

    zonefiles = (
        "northamerica",
        "southamerica",
        "europe",
        "africa",
        "asia",
        "australasia",
        "antarctica",
    )

    skips = (
        # "Europe/Sofia",
        # "Africa/Cairo",
    )

    only = (
        # "Europe/Lisbon",
    )

    checkcalendar1 = loadCalendarFromZoneinfo(zonedir1, skips, only, verbose, quiet)
    checkcalendar2 = loadCalendarFromZoneinfo(zonedir2, skips, only, verbose, quiet)

    compareCalendars(
        checkcalendar1,
        checkcalendar2,
        start,
        end,
        filterTzids=(
            # "America/Goose_Bay",
        ),
        verbose=verbose,
        quiet=quiet,
    )