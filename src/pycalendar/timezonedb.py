##
#    Copyright (c) 2011-2013 Cyrus Daboo. All rights reserved.
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
from typing import Any, ClassVar, Optional, Dict, Set
from pycalendar.exceptions import NoTimezoneInDatabase, InvalidData
import os

class TimezoneDatabase(object):
    """
    On demand timezone database cache. This scans a TZdb directory for .ics files matching a
    TZID and caches the component data in a calendar from whence the actual component is returned.
    """

    sTimezoneDatabase: ClassVar[Optional["TimezoneDatabase"]] = None

    dbpath: Optional[str]
    calendar: Any
    tzcache: Dict[str, Any]
    stdtzcache: Set[str]
    notstdtzcache: Set[str]

    @staticmethod
    def createTimezoneDatabase(dbpath: str) -> None:
        TimezoneDatabase.sTimezoneDatabase = TimezoneDatabase()
        TimezoneDatabase.sTimezoneDatabase.setPath(dbpath)

    @staticmethod
    def clearTimezoneDatabase() -> None:
        if TimezoneDatabase.sTimezoneDatabase is not None:
            TimezoneDatabase.sTimezoneDatabase.clear()

    def __init__(self) -> None:
        from pycalendar.icalendar.calendar import Calendar
        self.dbpath: Optional[str] = None
        self.calendar: Any = Calendar()
        self.tzcache: Dict[str, Any] = {}
        self.stdtzcache: Set[str] = set()
        self.notstdtzcache: Set[str] = set()

    def setPath(self, dbpath: str) -> None:
        self.dbpath = dbpath

    def clear(self) -> None:
        from pycalendar.icalendar.calendar import Calendar
        self.calendar = Calendar()
        self.tzcache.clear()
        self.stdtzcache.clear()
        self.notstdtzcache.clear()

    @staticmethod
    def getTimezoneDatabase() -> "TimezoneDatabase":
        if TimezoneDatabase.sTimezoneDatabase is None:
            TimezoneDatabase.sTimezoneDatabase = TimezoneDatabase()
        return TimezoneDatabase.sTimezoneDatabase

    @staticmethod
    def getTimezone(tzid: str) -> Any:
        return TimezoneDatabase.getTimezoneDatabase()._getTimezone(tzid)

    @staticmethod
    def getTimezoneInCalendar(tzid: str) -> Optional[Any]:
        """
        Return a VTIMEZONE inside a valid VCALENDAR
        """
        tz = TimezoneDatabase.getTimezone(tzid)
        if tz is not None:
            from pycalendar.icalendar.calendar import Calendar
            cal = Calendar()
            cal.addComponent(tz.duplicate(cal))
            return cal
        else:
            return None

    @staticmethod
    def getTimezoneOffsetSeconds(tzid: str, dt: Any, relative_to_utc: bool = False) -> int:
        tz = TimezoneDatabase.getTimezone(tzid)
        if tz is not None:
            return tz.getTimezoneOffsetSeconds(dt, relative_to_utc)
        else:
            return 0

    @staticmethod
    def getTimezoneDescriptor(tzid: str, dt: Any) -> str:
        tz = TimezoneDatabase.getTimezone(tzid)
        if tz is not None:
            return tz.getTimezoneDescriptor(dt)
        else:
            return ""

    @staticmethod
    def isStandardTimezone(tzid: str) -> bool:
        return TimezoneDatabase.getTimezoneDatabase()._isStandardTimezone(tzid)

    def cacheTimezone(self, tzid: str) -> None:
        """
        Load the specified timezone identifier's timezone data from a file and parse it
        into the L{Calendar} used to store timezones used by this object.
        """
        if self.dbpath is None:
            return

        tzpath = os.path.join(self.dbpath, "%s.ics" % (tzid,))
        tzpath = os.path.normpath(tzpath)
        if tzpath.startswith(self.dbpath) and os.path.isfile(tzpath):
            try:
                with open(tzpath) as f:
                    self.calendar.parseComponent(f)
            except (IOError, InvalidData):
                raise NoTimezoneInDatabase(self.dbpath, tzid)
        else:
            raise NoTimezoneInDatabase(self.dbpath, tzid)

    def addTimezone(self, tz: Any) -> None:
        """
        Add the specified VTIMEZONE component to this object's L{Calendar} cache. This component
        is assumed to be a non-standard timezone - i.e., not loaded from the timezone database.
        """
        copy = tz.duplicate(self.calendar)
        self.calendar.addComponent(copy)
        self.tzcache[copy.getID()] = copy

    def _addStandardTimezone(self, tz: Any) -> None:
        """
        Same as L{addTimezone} except that the timezone is marked as a standard timezone. This
        is only meant to be used for testing which happens in the absence of a real standard
        timezone database.
        """
        if tz.getID() not in self.tzcache:
            self.addTimezone(tz)
        self.stdtzcache.add(tz.getID())

    def _isStandardTimezone(self, tzid: str) -> bool:
        """
        Check whether the specified time zone id corresponds to a standard time zone.
        """
        if tzid in self.stdtzcache:
            return True
        elif tzid in self.notstdtzcache:
            return False
        else:
            self._getTimezone(tzid)
            return tzid in self.stdtzcache

    def _getTimezone(self, tzid: str) -> Any:
        """
        Get a timezone matching the specified timezone identifier. Use this object's
        cache - if not in the cache try to load it from a tz database file and store in
        this object's calendar.
        """
        if tzid not in self.tzcache:
            tz = self.calendar.getTimezone(tzid)
            if tz is None:
                try:
                    self.cacheTimezone(tzid)
                except NoTimezoneInDatabase:
                    pass
                tz = self.calendar.getTimezone(tzid)
            self.tzcache[tzid] = tz
            if tz is not None and tzid is not None:
                self.stdtzcache.add(tzid)
            else:
                self.notstdtzcache.add(tzid)
        return self.tzcache[tzid]

    @staticmethod
    def mergeTimezones(cal: Any, tzs: Any) -> None:
        """
        Merge each timezone from other calendar.
        """
        tzdb = TimezoneDatabase.getTimezoneDatabase()
        if cal is tzdb.calendar:
            return
        for tz in tzs:
            tzdb.mergeTimezone(tz)

    def mergeTimezone(self, tz: Any) -> None:
        """
        If the supplied VTIMEZONE is not in our cache then store it in memory.
        """
        if self._getTimezone(tz.getID()) is None:
            self.addTimezone(tz)