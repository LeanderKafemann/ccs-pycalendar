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

# iCalendar UTC Offset value
from typing import Any
from io import StringIO
from pycalendar import xmldefinitions
from pycalendar.value import Value

class UTCOffsetValue(Value):
    mValue: int

    def __init__(self, value: int = 0) -> None:
        self.mValue = value

    def duplicate(self) -> "UTCOffsetValue":
        return UTCOffsetValue(self.mValue)

    def getType(self) -> int:
        return Value.VALUETYPE_UTC_OFFSET

    def parse(self, data: str, variant: Any) -> None:
        fullISO = (variant == "vcard")
        datalen = len(data)
        if datalen not in ((6, 9,) if fullISO else (5, 7,)):
            self.mValue = 0
            raise ValueError("UTCOffset: invalid format")
        if data[0] not in ('+', '-'):
            raise ValueError("UTCOffset: does not start with '+' or '-'")
        plus = (data[0] == '+')
        hours = int(data[1:3])
        index = 4 if fullISO else 3
        mins = int(data[index:index + 2])
        secs = 0
        if datalen > 6:
            index = 7 if fullISO else 5
            secs = int(data[index:])
        self.mValue = ((hours * 60) + mins) * 60 + secs
        if not plus:
            self.mValue = -self.mValue

    def generate(self, os: Any, fullISO: bool = False) -> None:
        try:
            abs_value = self.mValue
            if abs_value < 0:
                sign = "-"
                abs_value = -self.mValue
            else:
                sign = "+"
            secs = abs_value % 60
            mins = (abs_value // 60) % 60
            hours = abs_value // (60 * 60)
            s = ("%s%02d:%02d" if fullISO else "%s%02d%02d") % (sign, hours, mins,)
            if (secs != 0):
                s = ("%s:%02d" if fullISO else "%s%02d") % (s, secs,)
            os.write(s)
        except Exception:
            pass

    def writeXML(self, node: Any, namespace: Any) -> None:
        os = StringIO()
        self.generate(os)
        text = os.getvalue()
        text = text[:-2] + ":" + text[-2:]
        value = self.getXMLNode(node, namespace)
        value.text = text

    def parseJSONValue(self, jobject: Any) -> None:
        self.parse(str(jobject), variant="vcard")

    def writeJSONValue(self, jobject: list) -> None:
        os = StringIO()
        self.generate(os, fullISO=True)
        text = os.getvalue()
        jobject.append(text)

    def getValue(self) -> int:
        return self.mValue

    def setValue(self, value: int) -> None:
        self.mValue = value

Value.registerType(Value.VALUETYPE_UTC_OFFSET, UTCOffsetValue, xmldefinitions.value_utc_offset)