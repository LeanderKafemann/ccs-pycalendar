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

# iCalendar generic text-like value
from typing import Any
from pycalendar.value import Value

class PlainTextValue(Value):
    mValue: str

    def __init__(self, value: str = '') -> None:
        self.mValue = value

    def duplicate(self) -> "PlainTextValue":
        return self.__class__(self.mValue)

    def parse(self, data: str, variant: Any) -> None:
        # No decoding required
        self.mValue = data

    def generate(self, os: Any) -> None:
        try:
            os.write(self.mValue)
        except Exception:
            pass

    def writeXML(self, node: Any, namespace: Any) -> None:
        value = self.getXMLNode(node, namespace)
        value.text = self.mValue

    def parseJSONValue(self, jobject: Any) -> None:
        self.mValue = jobject.encode("utf-8")

    def writeJSONValue(self, jobject: list) -> None:
        jobject.append(self.mValue)

    def getValue(self) -> str:
        return self.mValue

    def setValue(self, value: str) -> None:
        self.mValue = value