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

"""
ICalendar parameter.

The parameter can consist of one or more values, all string.
"""
from typing import Any, List
from pycalendar import xmldefinitions, xmlutils
from pycalendar.utils import encodeParameterValue
import xml.etree.cElementTree as XML

class Parameter(object):
    mName: str
    mValues: List[str]

    def __init__(self, name: str, value: Any = None) -> None:
        self.mName = name
        if value is None:
            self.mValues = []
        elif isinstance(value, str):
            self.mValues = [value]
        else:
            self.mValues = value

    def duplicate(self) -> "Parameter":
        other = Parameter(self.mName)
        other.mValues = self.mValues[:]
        return other

    def __hash__(self) -> int:
        return hash((self.mName.upper(), tuple(self.mValues)))

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Parameter):
            return False
        return self.mName.upper() == other.mName.upper() and self.mValues == other.mValues

    def getName(self) -> str:
        return self.mName

    def setName(self, name: str) -> None:
        self.mName = name

    def getFirstValue(self) -> str:
        return self.mValues[0]

    def getValues(self) -> List[str]:
        return self.mValues

    def setValues(self, values: List[str]) -> None:
        self.mValues = values

    def addValue(self, value: str) -> None:
        self.mValues.append(value)

    def removeValue(self, value: str) -> int:
        self.mValues.remove(value)
        return len(self.mValues)

    def generate(self, os: Any) -> None:
        try:
            os.write(self.mName)
            if self.mValues:
                os.write("=")
                first = True
                for s in sorted(self.mValues):
                    if first:
                        first = False
                    else:
                        os.write(",")
                    self.generateValue(os, s)
        except Exception:
            pass

    def generateValue(self, os: Any, s: str) -> None:
        s = encodeParameterValue(s)
        if ":" in s or ";" in s or "," in s:
            os.write("\"%s\"" % (s,))
        else:
            os.write(s)

    def writeXML(self, node: Any, namespace: Any) -> None:
        param = XML.SubElement(node, xmlutils.makeTag(namespace, self.getName()))
        for value in self.getValues():
            text = XML.SubElement(param, xmlutils.makeTag(namespace, xmldefinitions.value_text))
            text.text = value

    def writeJSON(self, jobject: dict) -> None:
        jobject[self.getName().lower()] = self.mValues if len(self.mValues) != 1 else self.mValues[0]