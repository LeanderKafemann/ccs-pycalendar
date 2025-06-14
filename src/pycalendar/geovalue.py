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

# iCalendar REQUEST-STATUS value

from typing import Any, List
from pycalendar import xmlutils
from pycalendar.exceptions import InvalidData
from pycalendar.icalendar import xmldefinitions
from pycalendar.value import Value
from pycalendar import xmldefinitions as xmldefinitions_top
import xml.etree.cElementTree as XML

class GeoValue(Value):
    """
    The value is a list of 2 floats
    """
    mValue: List[float]

    def __init__(self, value: List[float] = None) -> None:
        self.mValue = value if value is not None else [0.0, 0.0]

    def __hash__(self) -> int:
        return hash(tuple(self.mValue))

    def duplicate(self) -> "GeoValue":
        return GeoValue(self.mValue[:])

    def getType(self) -> int:
        return Value.VALUETYPE_GEO

    def parse(self, data: str, variant: str = "icalendar") -> None:
        splits = data.split(";")
        if len(splits) != 2:
            raise InvalidData("GEO value incorrect", data)
        try:
            self.mValue = [float(splits[0]), float(splits[1])]
        except ValueError:
            if splits[0][-1] == '\\':
                try:
                    self.mValue = [float(splits[0][:-1]), float(splits[1])]
                except ValueError:
                    raise InvalidData("GEO value incorrect", data)
            else:
                raise InvalidData("GEO value incorrect", data)

    def generate(self, os: Any) -> None:
        os.write("%s;%s" % (self.mValue[0], self.mValue[1],))

    def writeXML(self, node: Any, namespace: Any) -> None:
        value = self.getXMLNode(node, namespace)
        latitude = XML.SubElement(value, xmlutils.makeTag(namespace, xmldefinitions.geo_latitude))
        latitude.text = str(self.mValue[0])
        longitude = XML.SubElement(value, xmlutils.makeTag(namespace, xmldefinitions.geo_longitude))
        longitude.text = str(self.mValue[1])

    def parseJSONValue(self, jobject: List[float]) -> None:
        self.mValue = jobject

    def writeJSONValue(self, jobject: list) -> None:
        jobject.append(list(self.mValue))

    def getValue(self) -> List[float]:
        return self.mValue

    def setValue(self, value: List[float]) -> None:
        self.mValue = value

Value.registerType(Value.VALUETYPE_GEO, GeoValue, xmldefinitions.geo, xmldefinitions_top.value_float)