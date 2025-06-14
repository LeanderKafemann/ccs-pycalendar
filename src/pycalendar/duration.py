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

from typing import Any, TextIO
from pycalendar.parser import ParserContext
from pycalendar.stringutils import strtoul
from pycalendar.valueutils import ValueMixin

class Duration(ValueMixin):
    mForward: bool
    mWeeks: int
    mDays: int
    mHours: int
    mMinutes: int
    mSeconds: int

    def __init__(
        self,
        duration: Any = None,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0
    ) -> None:
        self.mForward = True
        self.mWeeks = 0
        self.mDays = 0
        self.mHours = 0
        self.mMinutes = 0
        self.mSeconds = 0

        if duration is None:
            duration = (((weeks * 7 + days) * 24 + hours) * 60 + minutes) * 60 + seconds
        self.setDuration(duration)

    def duplicate(self) -> "Duration":
        other = Duration(None)
        other.mForward = self.mForward
        other.mWeeks = self.mWeeks
        other.mDays = self.mDays
        other.mHours = self.mHours
        other.mMinutes = self.mMinutes
        other.mSeconds = self.mSeconds
        return other

    def __hash__(self) -> int:
        return hash(self.getTotalSeconds())

    def __eq__(self, comp: Any) -> bool:
        return self.getTotalSeconds() == comp.getTotalSeconds()

    def __gt__(self, comp: Any) -> bool:
        return self.getTotalSeconds() > comp.getTotalSeconds()

    def __lt__(self, comp: Any) -> bool:
        return self.getTotalSeconds() < comp.getTotalSeconds()

    def getTotalSeconds(self) -> int:
        return [1, -1][not self.mForward] * (
            self.mSeconds + (self.mMinutes + (self.mHours + (self.mDays + (self.mWeeks * 7)) * 24) * 60) * 60
        )

    def setDuration(self, seconds: int) -> None:
        self.mForward = seconds >= 0

        remainder = seconds
        if remainder < 0:
            remainder = -remainder

        if remainder % (7 * 24 * 60 * 60) == 0:
            self.mWeeks = remainder // (7 * 24 * 60 * 60)
            self.mDays = 0
            self.mHours = 0
            self.mMinutes = 0
            self.mSeconds = 0
        else:
            self.mSeconds = remainder % 60
            remainder -= self.mSeconds
            remainder //= 60

            self.mMinutes = remainder % 60
            remainder -= self.mMinutes
            remainder //= 60

            self.mHours = remainder % 24
            remainder -= self.mHours
            self.mDays = remainder // 24
            self.mWeeks = 0

    def getForward(self) -> bool:
        return self.mForward

    def getWeeks(self) -> int:
        return self.mWeeks

    def getDays(self) -> int:
        return self.mDays

    def getHours(self) -> int:
        return self.mHours

    def getMinutes(self) -> int:
        return self.mMinutes

    def getSeconds(self) -> int:
        return self.mSeconds

    @classmethod
    def parseText(cls, data: str) -> "Duration":
        dur = cls()
        dur.parse(data)
        return dur

    def parse(self, data: str) -> None:
        try:
            offset = 0
            maxoffset = len(data)
            self.mForward = True
            if data[offset] in ('-', '+'):
                self.mForward = data[offset] == '+'
                offset += 1

            if data[offset] != "P":
                raise ValueError("Duration: missing 'P'")
            offset += 1

            if data[offset] != "T":
                num, offset = strtoul(data, offset)
                if data[offset] == "W":
                    self.mWeeks = num
                    offset += 1
                    if offset != maxoffset:
                        if ParserContext.INVALID_DURATION_VALUE != ParserContext.PARSER_RAISE:
                            return
                        raise ValueError("Duration: extra data after 'W'")
                    return
                elif data[offset] == "D":
                    self.mDays = num
                    offset += 1
                    if offset == maxoffset:
                        return
                    if data[offset] != "T":
                        raise ValueError("Duration: no 'T' after 'D'")
                else:
                    raise ValueError("Duration: need 'D' or 'W'")

            offset += 1

            if offset == maxoffset:
                if ParserContext.INVALID_DURATION_VALUE == ParserContext.PARSER_RAISE:
                    raise ValueError("Duration: need number after 'T'")
                else:
                    return
            num, offset = strtoul(data, offset)

            if data[offset] == "H":
                self.mHours = num
                offset += 1
                if offset == maxoffset:
                    return
                num, offset = strtoul(data, offset)

            if data[offset] == "M":
                self.mMinutes = num
                offset += 1
                if offset == maxoffset:
                    return
                num, offset = strtoul(data, offset)

            if data[offset] == "S":
                self.mSeconds = num
                offset += 1
                if offset == maxoffset:
                    return

            raise ValueError("Duration: invalid data after 'T'")

        except IndexError:
            raise ValueError("Duration: index error")

    def generate(self, os: TextIO) -> None:
        try:
            if not self.mForward and (self.mWeeks or self.mDays or self.mHours or self.mMinutes or self.mSeconds):
                os.write("-")
            os.write("P")

            if self.mWeeks != 0:
                os.write("%dW" % (self.mWeeks,))
            else:
                if self.mDays != 0:
                    os.write("%dD" % (self.mDays,))

                if (self.mHours != 0) or (self.mMinutes != 0) or (self.mSeconds != 0):
                    os.write("T")

                    if self.mHours != 0:
                        os.write("%dH" % (self.mHours,))

                    if (self.mMinutes != 0) or ((self.mHours != 0) and (self.mSeconds != 0)):
                        os.write("%dM" % (self.mMinutes,))

                    if self.mSeconds != 0:
                        os.write("%dS" % (self.mSeconds,))
                elif self.mDays == 0:
                    os.write("T0S")
        except Exception:
            pass

    def writeXML(self, node: Any, namespace: Any) -> None:
        node.text = self.getText()

    def parseJSON(self, jobject: Any) -> None:
        self.parse(str(jobject))

    def writeJSON(self, jobject: list) -> None:
        jobject.append(self.getText())