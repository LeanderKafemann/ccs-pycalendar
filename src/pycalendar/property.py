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
from typing import Any, Dict, List, Optional
from pycalendar import stringutils, xmlutils, xmldefinitions
from pycalendar.parameter import Parameter
from pycalendar.binaryvalue import BinaryValue
from pycalendar.caladdressvalue import CalAddressValue
from pycalendar.datetimevalue import DateTimeValue
from pycalendar.durationvalue import DurationValue
from pycalendar.exceptions import InvalidProperty
from pycalendar.integervalue import IntegerValue
from pycalendar.multivalue import MultiValue
from pycalendar.periodvalue import PeriodValue
from pycalendar.plaintextvalue import PlainTextValue
from pycalendar.unknownvalue import UnknownValue
from pycalendar.urivalue import URIValue
from pycalendar.utcoffsetvalue import UTCOffsetValue
from pycalendar.utils import decodeParameterValue
from pycalendar.value import Value
import io as StringIO
import xml.etree.cElementTree as XML

class PropertyBase(object):
    sDefaultValueTypeMap: Dict[str, int] = {}
    sAlwaysValueTypes: set[str] = set()
    sValueTypeMap: Dict[str, int] = {}
    sTypeValueMap: Dict[int, str] = {}
    sMultiValues: set[str] = set()
    sSpecialVariants: Dict[str, int] = {}
    sUsesGroup: bool = False
    sVariant: str = "none"
    sValue: Optional[str] = None
    sText: Optional[str] = None

    mName: str
    mParameters: Dict[str, List[Parameter]]
    mValue: Optional[Value]

    def __init__(self, name: Optional[str] = None, value: Any = None, valuetype: Any = None) -> None:
        self.mName: str = name if name is not None else ""
        self.mParameters: Dict[str, List[Parameter]] = {}
        self.mValue: Optional[Value] = None

    def duplicate(self) -> "PropertyBase":
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __eq__(self, other: Any) -> bool:
        raise NotImplementedError

    def __repr__(self) -> str:
        return "Property: %s" % (self.getText(),)

    def __str__(self) -> str:
        return self.getText()

    def getGroup(self) -> Optional[str]:
        return self.mGroup if self.sUsesGroup else None

    def setGroup(self, group: str) -> None:
        if self.sUsesGroup:
            self.mGroup = group

    def getName(self) -> str:
        return self.mName

    def setName(self, name: str) -> None:
        self.mName = name

    def getParameters(self) -> Dict[str, List[Parameter]]:
        return self.mParameters

    def setParameters(self, parameters: Dict[str, List[Parameter]]) -> None:
        self.mParameters = dict([(k.upper(), v) for k, v in parameters.items()])

    def hasParameter(self, attr: str) -> bool:
        return attr.upper() in self.mParameters

    def getParameterValue(self, attr: str) -> Any:
        return self.mParameters[attr.upper()][0].getFirstValue()

    def getParameterValues(self, attr: str) -> Any:
        return self.mParameters[attr.upper()][0].getValues()

    def addParameter(self, attr: Parameter) -> None:
        self.mParameters.setdefault(attr.getName().upper(), []).append(attr)

    def replaceParameter(self, attr: Parameter) -> None:
        self.mParameters[attr.getName().upper()] = [attr]

    def removeParameters(self, attr: str) -> None:
        if attr.upper() in self.mParameters:
            del self.mParameters[attr.upper()]

    def getValue(self) -> Optional[Value]:
        return self.mValue

    def getBinaryValue(self) -> Optional[BinaryValue]:
        if isinstance(self.mValue, BinaryValue):
            return self.mValue
        else:
            return None

    def getCalAddressValue(self) -> Optional[CalAddressValue]:
        if isinstance(self.mValue, CalAddressValue):
            return self.mValue
        else:
            return None

    def getDateTimeValue(self) -> Optional[DateTimeValue]:
        if isinstance(self.mValue, DateTimeValue):
            return self.mValue
        else:
            return None

    def getDurationValue(self) -> Optional[DurationValue]:
        if isinstance(self.mValue, DurationValue):
            return self.mValue
        else:
            return None

    def getIntegerValue(self) -> Optional[IntegerValue]:
        if isinstance(self.mValue, IntegerValue):
            return self.mValue
        else:
            return None

    def getMultiValue(self) -> Optional[MultiValue]:
        if isinstance(self.mValue, MultiValue):
            return self.mValue
        else:
            return None

    def getPeriodValue(self) -> Optional[PeriodValue]:
        if isinstance(self.mValue, PeriodValue):
            return self.mValue
        else:
            return None

    def getTextValue(self) -> Optional[PlainTextValue]:
        if isinstance(self.mValue, PlainTextValue):
            return self.mValue
        else:
            return None

    def getURIValue(self) -> Optional[URIValue]:
        if isinstance(self.mValue, URIValue):
            return self.mValue
        else:
            return None

    def getUTCOffsetValue(self) -> Optional[UTCOffsetValue]:
        if isinstance(self.mValue, UTCOffsetValue):
            return self.mValue
        else:
            return None

    @classmethod
    def registerDefaultValue(cls, propname: str, valuetype: int, always_write_value: bool = False) -> None:
        if propname not in cls.sDefaultValueTypeMap:
            cls.sDefaultValueTypeMap[propname] = valuetype
        if always_write_value:
            cls.sAlwaysValueTypes.add(propname)

    @classmethod
    def parseText(cls, data: str) -> "PropertyBase":
        try:
            prop = cls()
            prop_name, txt = stringutils.strduptokenstr(data, ";:")
            if not prop_name:
                raise InvalidProperty("Invalid property: empty name", data)
            if prop.sUsesGroup:
                splits = prop_name.split(".", 1)
                if len(splits) == 2:
                    prop.mGroup = splits[0]
                    prop.mName = splits[1]
                else:
                    prop.mName = prop_name
            else:
                prop.mName = prop_name
            txt = prop.parseTextParameters(txt, data)
            prop.mValue = None
            value_type = prop.determineValueType()
            if prop.mName.upper() in prop.sMultiValues:
                prop.mValue = MultiValue(value_type)
            else:
                prop.mValue = Value.createFromType(value_type)
            prop.mValue.parse(txt, prop.sVariant)
            prop._postCreateValue(value_type)
            return prop
        except Exception as e:
            raise InvalidProperty("Invalid property: '{}'".format(e), data)

    def parseTextParameters(self, txt: str, data: str) -> str:
        try:
            while txt:
                if txt[0] == ';':
                    txt = txt[1:]
                    parameter_name, txt = stringutils.strduptokenstr(txt, "=")
                    if parameter_name is None:
                        raise InvalidProperty("Invalid property: empty parameter name", data)
                    txt = txt[1:]
                    parameter_value, txt = stringutils.strduptokenstr(txt, ":;,")
                    if parameter_value is None:
                        raise InvalidProperty("Invalid property: empty parameter value", data)
                    attrvalue = Parameter(name=parameter_name, value=decodeParameterValue(parameter_value))
                    self.mParameters.setdefault(parameter_name.upper(), []).append(attrvalue)
                    while txt[0] == ',':
                        txt = txt[1:]
                        parameter_value2, txt = stringutils.strduptokenstr(txt, ":;,")
                        if parameter_value2 is None:
                            raise InvalidProperty("Invalid property: empty parameter multi-value", data)
                        attrvalue.addValue(decodeParameterValue(parameter_value2))
                elif txt[0] == ':':
                    return txt[1:]
                else:
                    raise InvalidProperty("Invalid property: missing value separator", data)
        except IndexError:
            raise InvalidProperty("Invalid property: 'parameter index error'", data)

    def getText(self) -> str:
        os = StringIO.StringIO()
        self.generate(os)
        return os.getvalue()

    def generate(self, os: Any) -> None:
        self.generateValue(os, False)

    def generateFiltered(self, os: Any, filter: Any) -> None:
        test, novalue = filter.testPropertyValue(self.mName.upper())
        if test:
            self.generateValue(os, novalue)

    def generateValue(self, os: Any, novalue: bool) -> None:
        self.setupValueParameter()
        sout = StringIO.StringIO()
        if self.sUsesGroup and hasattr(self, "mGroup") and self.mGroup:
            sout.write(self.mGroup + ".")
        sout.write(self.mName)
        for key in sorted(self.mParameters.keys()):
            for attr in self.mParameters[key]:
                sout.write(";")
                attr.generate(sout)
        sout.write(":")
        if self.mValue and not novalue:
            self.mValue.generate(sout)
        temp = sout.getvalue()
        sout.close()
        if len(temp) < 75:
            os.write(temp)
        else:
            start = 0
            written = 0
            lineWrap = 74
            while written < len(temp):
                offset = start + lineWrap
                if offset >= len(temp):
                    line = temp[start:]
                    os.write(line)
                    written = len(temp)
                else:
                    while (temp[offset] > 0x7F) and ((ord(temp[offset]) & 0xC0) == 0x80):
                        offset -= 1
                    line = temp[start:offset]
                    os.write(line)
                    os.write("\r\n ")
                    lineWrap = 73
                    written += offset - start
                    start = offset
        os.write("\r\n")

    def writeXML(self, node: Any, namespace: Any) -> None:
        self.generateValueXML(node, namespace, False)

    def writeXMLFiltered(self, node: Any, namespace: Any, filter: Any) -> None:
        test, novalue = filter.testPropertyValue(self.mName.upper())
        if test:
            self.generateValueXML(node, namespace, novalue)

    def generateValueXML(self, node: Any, namespace: Any, novalue: bool) -> None:
        prop = XML.SubElement(node, xmlutils.makeTag(namespace, self.getName()))
        if len(self.mParameters):
            params = XML.SubElement(prop, xmlutils.makeTag(namespace, xmldefinitions.parameters))
            for key in sorted(self.mParameters.keys()):
                for attr in self.mParameters[key]:
                    if attr.getName().lower() != "value":
                        attr.writeXML(params, namespace)
        if self.mValue and not novalue:
            self.mValue.writeXML(prop, namespace)

    @classmethod
    def parseJSON(cls, jobject: list) -> "PropertyBase":
        try:
            prop = cls()
            prop.mName = jobject[0].encode("utf-8").upper()
            if jobject[1]:
                for name, value in jobject[1].items():
                    name = name.upper()
                    attrvalue = Parameter(name=name.encode("utf-8"), value=value.encode("utf-8"))
                    prop.mParameters.setdefault(name, []).append(attrvalue)
            value_type = cls.sValueTypeMap.get(jobject[2].upper(), Value.VALUETYPE_UNKNOWN)
            default_type = cls.sDefaultValueTypeMap.get(prop.mName.upper(), Value.VALUETYPE_UNKNOWN)
            if default_type != value_type:
                attrvalue = Parameter(name=cls.sValue, value=jobject[2].encode("utf-8").upper())
                prop.mParameters.setdefault(cls.sValue, []).append(attrvalue)
            value_type = prop.determineValueType()
            values = jobject[3:]
            if prop.mName.upper() in cls.sMultiValues:
                prop.mValue = MultiValue(value_type)
                prop.mValue.parseJSONValue(values)
            else:
                prop.mValue = Value.createFromType(value_type)
                prop.mValue.parseJSONValue(values[0])
            prop._postCreateValue(value_type)
            return prop
        except Exception as e:
            raise InvalidProperty("Invalid property: '{}'".format(e), jobject)

    def writeJSON(self, jobject: list) -> None:
        self.generateValueJSON(jobject, False)

    def writeJSONFiltered(self, jobject: list, filter: Any) -> None:
        test, novalue = filter.testPropertyValue(self.mName.upper())
        if test:
            self.generateValueJSON(jobject, novalue)

    def generateValueJSON(self, jobject: list, novalue: bool) -> None:
        prop = [
            self.getName().lower(),
            {},
        ]
        jobject.append(prop)
        for key in sorted(self.mParameters.keys()):
            for attr in self.mParameters[key]:
                if attr.getName().lower() != "value":
                    attr.writeJSON(prop[1])
        if self.mValue and not novalue:
            self.mValue.writeJSON(prop)

    def determineValueType(self) -> int:
        value_type = self.sDefaultValueTypeMap.get(self.mName.upper(), Value.VALUETYPE_UNKNOWN)
        if self.sValue in self.mParameters:
            attr = self.getParameterValue(self.sValue)
            value_type = self.sValueTypeMap.get(attr, value_type)
        if self.mName.upper() in self.sSpecialVariants:
            if value_type == self.sDefaultValueTypeMap.get(self.mName.upper(), Value.VALUETYPE_UNKNOWN):
                value_type = self.sSpecialVariants[self.mName.upper()]
        return value_type

    def createValue(self, data: Any) -> None:
        self.mValue = None
        value_type = self.determineValueType()
        if self.mName.upper() in self.sMultiValues:
            self.mValue = MultiValue(value_type)
        else:
            self.mValue = Value.createFromType(value_type)
        try:
            self.mValue.parse(data, self.sVariant)
        except ValueError as e:
            raise InvalidProperty("Invalid property value: '{}'".format(e), data)
        self._postCreateValue(value_type)

    def _postCreateValue(self, value_type: int) -> None:
        pass

    def setValue(self, value: Any) -> None:
        self.mValue = None
        value_type = self.sDefaultValueTypeMap.get(self.mName.upper(), Value.VALUETYPE_TEXT)
        if self.sValue in self.mParameters:
            value_type = self.sValueTypeMap.get(self.getParameterValue(self.sValue), value_type)
        if self.mName.upper() in self.sMultiValues:
            self.mValue = MultiValue(value_type)
        else:
            self.mValue = Value.createFromType(value_type)
        self.mValue.setValue(value)
        self._postCreateValue(value_type)

    def setupValueParameter(self) -> None:
        if self.sValue in self.mParameters:
            del self.mParameters[self.sValue]
        if self.mValue is None:
            return
        default_type = self.sDefaultValueTypeMap.get(self.mName.upper())
        if self.mName.upper() in self.sSpecialVariants:
            actual_type = default_type
        else:
            actual_type = self.mValue.getType()
        if default_type is None or default_type != actual_type or self.mName.upper() in self.sAlwaysValueTypes:
            actual_value = self.sTypeValueMap.get(actual_type)
            if actual_value is not None and (default_type is not None or actual_type != Value.VALUETYPE_TEXT):
                self.mParameters.setdefault(self.sValue, []).append(Parameter(name=self.sValue, value=actual_value))

    def _init_attr_value_int(self, ival: int) -> None:
        self.mValue = IntegerValue(value=ival)
        self.setupValueParameter()

    def _init_attr_value_text(self, txt: str, value_type: int) -> None:
        self.mValue = Value.createFromType(value_type)
        if isinstance(self.mValue, PlainTextValue) or isinstance(self.mValue, UnknownValue):
            self.mValue.setValue(txt)
        self.setupValueParameter()

    def _init_attr_value_datetime(self, dt: Any) -> None:
        self.mValue = DateTimeValue(value=dt)
        self.setupValueParameter()

    def _init_attr_value_utcoffset(self, utcoffset: Any) -> None:
        self.mValue = UTCOffsetValue()
        self.mValue.setValue(utcoffset.getValue())
        self.setupValueParameter()