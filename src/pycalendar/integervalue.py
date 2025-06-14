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
from pycalendar import xmldefinitions
from pycalendar.value import Value

class IntegerValue(Value):
    mValue: int

    def __init__(self, value: int = None) -> None:
        self.mValue: int = value if value is not None else 0

    def duplicate(self) -> "IntegerValue":
        return IntegerValue(self.mValue)

    def getType(self) -> int:
        return Value.VALUETYPE_INTEGER

    def parse(self, data: Any, variant: Any) -> None:
        self.mValue = int(data)

    def generate(self, os: Any) -> None:
        try:
            os.write(str(self.mValue))
        except Exception:
            pass

    def writeXML(self, node: Any, namespace: Any) -> None:
        value = self.getXMLNode(node, namespace)
        value.text = str(self.mValue)

    def parseJSONValue(self, jobject: Any) -> None:
        self.mValue = int(jobject)

    def writeJSONValue(self, jobject: list) -> None:
        jobject.append(self.mValue)

    def getValue(self) -> int:
        return self.mValue

    def setValue(self, value: int) -> None:
        self.mValue = value

Value.registerType(Value.VALUETYPE_INTEGER, IntegerValue, xmldefinitions.value_integer)