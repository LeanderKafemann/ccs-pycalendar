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

# iCalendar float value

from typing import Any
from pycalendar import xmldefinitions
from pycalendar.value import Value

class FloatValue(Value):
    mValue: float

    def __init__(self, value: float = None) -> None:
        self.mValue: float = value if value is not None else 0.0

    def duplicate(self) -> "FloatValue":
        return FloatValue(self.mValue)

    def getType(self) -> int:
        return Value.VALUETYPE_FLOAT

    def parse(self, data: Any, variant: Any) -> None:
        self.mValue = float(data)

    def generate(self, os: Any) -> None:
        try:
            os.write(str(self.mValue))
        except Exception:
            pass

    def writeXML(self, node: Any, namespace: Any) -> None:
        value = self.getXMLNode(node, namespace)
        value.text = str(self.mValue)

    def parseJSONValue(self, jobject: Any) -> None:
        self.mValue = float(jobject)

    def writeJSONValue(self, jobject: list) -> None:
        jobject.append(self.mValue)

    def getValue(self) -> float:
        return self.mValue

    def setValue(self, value: float) -> None:
        self.mValue = value

Value.registerType(Value.VALUETYPE_FLOAT, FloatValue, xmldefinitions.value_float)
