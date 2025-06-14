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
from typing import Any, ClassVar, Optional, Union
from pycalendar import stringutils
from pycalendar.timezonedb import TimezoneDatabase

class Timezone(object):
    """
    Wrapper around a timezone specification. There are three options:

    UTC - when mUTC is True
    TZID - when mUTC is False and tzid is a str
    UTCOFFSET - when mUTC is False and tzid is an int
    """

    sDefaultTimezone: ClassVar[Optional["Timezone"]] = None
    UTCTimezone: ClassVar[Optional["Timezone"]] = None

    mUTC: bool
    mTimezone: Union[str, int, None]

    def __init__(self, utc: Optional[bool] = None, tzid: Optional[Union[str, int]] = None) -> None:
        if utc is not None:
            self.mUTC = utc
            self.mTimezone = tzid
        elif tzid is not None:
            if isinstance(tzid, str):
                self.mUTC = tzid.lower() == 'utc'
                self.mTimezone = None if tzid.lower() == 'utc' else tzid
            else:
                self.mUTC = False
                self.mTimezone = tzid
        else:
            self.mUTC = True
            self.mTimezone = None
            if Timezone.sDefaultTimezone is not None:
                self.mUTC = Timezone.sDefaultTimezone.mUTC
                self.mTimezone = Timezone.sDefaultTimezone.mTimezone

    def duplicate(self) -> "Timezone":
        return Timezone(self.mUTC, self.mTimezone)

    def equals(self, comp: "Timezone") -> bool:
        if self.floating() or comp.floating():
            return True
        elif self.mUTC != comp.mUTC:
            return False
        else:
            return self.mUTC or stringutils.compareStringsSafe(self.mTimezone, comp.mTimezone)

    @staticmethod
    def same(utc1: bool, tzid1: Union[str, int, None], utc2: bool, tzid2: Union[str, int, None]) -> bool:
        if Timezone.is_float(utc1, tzid1) or Timezone.is_float(utc2, tzid2):
            return True
        elif utc1 != utc2:
            return False
        else:
            return utc1 or stringutils.compareStringsSafe(tzid1, tzid2)

    @staticmethod
    def is_float(utc: bool, tzid: Union[str, int, None]) -> bool:
        return not utc and not tzid

    def getUTC(self) -> bool:
        return self.mUTC

    def setUTC(self, utc: bool) -> None:
        self.mUTC = utc

    def getTimezoneID(self) -> Union[str, int, None]:
        return self.mTimezone

    def setTimezoneID(self, tzid: Union[str, int, None]) -> None:
        self.mTimezone = tzid

    def floating(self) -> bool:
        return not self.mUTC and self.mTimezone is None

    def hasTZID(self) -> bool:
        return not self.mUTC and self.mTimezone is not None

    def timeZoneSecondsOffset(self, dt: Any, relative_to_utc: bool = False) -> int:
        if self.mUTC:
            return 0
        elif self.mTimezone is None:
            return TimezoneDatabase.getTimezoneOffsetSeconds(Timezone.sDefaultTimezone.getTimezoneID(), dt, relative_to_utc)
        elif isinstance(self.mTimezone, int):
            return self.mTimezone
        else:
            return TimezoneDatabase.getTimezoneOffsetSeconds(self.mTimezone, dt, relative_to_utc)

    def timeZoneDescriptor(self, dt: Any) -> str:
        if self.mUTC:
            return "(UTC)"
        elif self.mTimezone is None:
            return TimezoneDatabase.getTimezoneDescriptor(Timezone.sDefaultTimezone.getTimezoneID(), dt)
        elif isinstance(self.mTimezone, int):
            sign = "-" if self.mTimezone < 0 else "+"
            hours = abs(self.mTimezone) // 3600
            minutes = divmod(abs(self.mTimezone) // 60, 60)[1]
            return "%s%02d%02d" % (sign, hours, minutes,)
        else:
            return TimezoneDatabase.getTimezoneDescriptor(self.mTimezone, dt)

Timezone.sDefaultTimezone = Timezone()
Timezone.UTCTimezone = Timezone(utc=True)