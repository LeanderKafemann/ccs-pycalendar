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

from pycalendar.timezone import Timezone
from pycalendar.valueutils import ValueMixin
from typing import Optional, Any


class DateTime(ValueMixin):
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6

    FULLDATE = 0
    ABBREVDATE = 1
    NUMERICDATE = 2
    FULLDATENOYEAR = 3
    ABBREVDATENOYEAR = 4
    NUMERICDATENOYEAR = 5

    mYear: int
    mMonth: int
    mDay: int
    mHours: int
    mMinutes: int
    mSeconds: int
    mDateOnly: bool
    mTZUTC: bool
    mTZID: Optional[str]  # Kann auch int sein, siehe getText(), daher ggf. Union[str, int]
    mTZOffset: Optional[int]
    mPosixTimeCached: bool
    mPosixTime: int

    def __init__(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        hours: Optional[int] = None,
        minutes: Optional[int] = None,
        seconds: Optional[int] = None,
        tzid: Optional[Any] = None,
        utcoffset: Optional[int] = None
    ) -> None:
        if (year is not None) and (month is not None) and (day is not None):
            self.mYear = year
            self.mMonth = month
            self.mDay = day

            if (hours is not None) and (minutes is not None) and (seconds is not None):
                self.mHours = hours
                self.mMinutes = minutes
                self.mSeconds = seconds
                self.mDateOnly = False
            else:
                self.mHours = 0
                self.mMinutes = 0
                self.mSeconds = 0
                self.mDateOnly = True

            if tzid:
                self.mTZUTC = tzid.getUTC()
                self.mTZID = tzid.getTimezoneID()
            else:
                self.mTZUTC = False
                self.mTZID = None
            self.mTZOffset = None

        else:
            self.mYear = 1970
            self.mMonth = 1
            self.mDay = 1

            self.mHours = 0
            self.mMinutes = 0
            self.mSeconds = 0

            self.mDateOnly = False

            self.mTZUTC = False
            self.mTZID = None
            self.mTZOffset = None

        self.mPosixTimeCached = False
        self.mPosixTime = 0

    def duplicate(self) -> "DateTime":
        other = DateTime(self.mYear, self.mMonth, self.mDay, self.mHours, self.mMinutes, self.mSeconds)
        other.mDateOnly = self.mDateOnly
        other.mTZUTC = self.mTZUTC
        other.mTZID = self.mTZID
        other.mTZOffset = self.mTZOffset
        other.mPosixTimeCached = self.mPosixTimeCached
        other.mPosixTime = self.mPosixTime
        return other

    def duplicateAsUTC(self) -> "DateTime":
        other = self.duplicate()
        other.adjustToUTC()
        return other

    def __repr__(self) -> str:
        return "DateTime: %s" % (self.getText(),)

    def __hash__(self) -> int:
        return hash(self.getPosixTime())

    # ... (restliche Methoden wie gehabt, ggf. mit passenden Typannotationen)

    def getTimezoneID(self) -> Optional[str]:
        return self.mTZID

    def setTimezoneID(self, tzid: Optional[str]) -> None:
        self.mTZUTC = False
        self.mTZID = tzid
        self.changed()

    def getTimezone(self) -> "Timezone":
        return Timezone(utc=self.mTZUTC, tzid=self.mTZID)

    def setTimezone(self, tzid: "Timezone") -> None:
        self.mTZUTC = tzid.getUTC()
        self.mTZID = tzid.getTimezoneID()
        self.changed()

    def timeZoneSecondsOffset(self, relative_to_utc: bool = False) -> int:
        if self.mTZUTC:
            return 0
        if self.mTZOffset is None:
            tz = Timezone(utc=self.mTZUTC, tzid=self.mTZID)
            self.mTZOffset = tz.timeZoneSecondsOffset(self, relative_to_utc)
        return self.mTZOffset

    # ... (weitere Methoden wie gehabt)
