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
from typing import Any, Dict, List, Optional, Tuple, Union, IO
from pycalendar import stringutils
from pycalendar.parameter import Parameter
from pycalendar.datetime import DateTime
from pycalendar.exceptions import InvalidProperty
from pycalendar.parser import ParserContext
from pycalendar.property import PropertyBase
from pycalendar.utcoffsetvalue import UTCOffsetValue
from pycalendar.utils import decodeParameterValue
from pycalendar.value import Value
from pycalendar.vcard import definitions
from pycalendar.vcard.adr import Adr
from pycalendar.vcard.adrvalue import AdrValue
from pycalendar.vcard.n import N
from pycalendar.vcard.nvalue import NValue
from pycalendar.vcard.orgvalue import OrgValue
import io as StringIO

handleOptions: Tuple[str, ...] = ("allow", "ignore", "fix", "raise")
missingParameterValues: str = "fix"

class Property(PropertyBase):
    sDefaultValueTypeMap: Dict[str, int] = {
        definitions.Property_SOURCE: Value.VALUETYPE_URI,
        definitions.Property_NAME: Value.VALUETYPE_TEXT,
        definitions.Property_PROFILE: Value.VALUETYPE_TEXT,
        definitions.Property_FN: Value.VALUETYPE_TEXT,
        definitions.Property_N: Value.VALUETYPE_TEXT,
        definitions.Property_NICKNAME: Value.VALUETYPE_TEXT,
        definitions.Property_PHOTO: Value.VALUETYPE_BINARY,
        definitions.Property_BDAY: Value.VALUETYPE_DATE,
        definitions.Property_ADR: Value.VALUETYPE_TEXT,
        definitions.Property_LABEL: Value.VALUETYPE_TEXT,
        definitions.Property_TEL: Value.VALUETYPE_TEXT,
        definitions.Property_EMAIL: Value.VALUETYPE_TEXT,
        definitions.Property_MAILER: Value.VALUETYPE_TEXT,
        definitions.Property_TZ: Value.VALUETYPE_UTC_OFFSET,
        definitions.Property_GEO: Value.VALUETYPE_FLOAT,
        definitions.Property_TITLE: Value.VALUETYPE_TEXT,
        definitions.Property_ROLE: Value.VALUETYPE_TEXT,
        definitions.Property_LOGO: Value.VALUETYPE_BINARY,
        definitions.Property_AGENT: Value.VALUETYPE_VCARD,
        definitions.Property_ORG: Value.VALUETYPE_TEXT,
        definitions.Property_CATEGORIES: Value.VALUETYPE_TEXT,
        definitions.Property_NOTE: Value.VALUETYPE_TEXT,
        definitions.Property_PRODID: Value.VALUETYPE_TEXT,
        definitions.Property_REV: Value.VALUETYPE_DATETIME,
        definitions.Property_SORT_STRING: Value.VALUETYPE_TEXT,
        definitions.Property_SOUND: Value.VALUETYPE_BINARY,
        definitions.Property_UID: Value.VALUETYPE_TEXT,
        definitions.Property_URL: Value.VALUETYPE_URI,
        definitions.Property_VERSION: Value.VALUETYPE_TEXT,
        definitions.Property_CLASS: Value.VALUETYPE_TEXT,
        definitions.Property_KEY: Value.VALUETYPE_BINARY,
    }

    sValueTypeMap: Dict[str, int] = {
        definitions.Value_BINARY: Value.VALUETYPE_BINARY,
        definitions.Value_BOOLEAN: Value.VALUETYPE_BOOLEAN,
        definitions.Value_DATE: Value.VALUETYPE_DATE,
        definitions.Value_DATE_TIME: Value.VALUETYPE_DATETIME,
        definitions.Value_FLOAT: Value.VALUETYPE_FLOAT,
        definitions.Value_INTEGER: Value.VALUETYPE_INTEGER,
        definitions.Value_TEXT: Value.VALUETYPE_TEXT,
        definitions.Value_TIME: Value.VALUETYPE_TIME,
        definitions.Value_URI: Value.VALUETYPE_URI,
        definitions.Value_UTCOFFSET: Value.VALUETYPE_UTC_OFFSET,
        definitions.Value_VCARD: Value.VALUETYPE_VCARD,
    }

    sTypeValueMap: Dict[int, str] = {
        Value.VALUETYPE_ADR: definitions.Value_TEXT,
        Value.VALUETYPE_BINARY: definitions.Value_BINARY,
        Value.VALUETYPE_BOOLEAN: definitions.Value_BOOLEAN,
        Value.VALUETYPE_DATE: definitions.Value_DATE,
        Value.VALUETYPE_DATETIME: definitions.Value_DATE_TIME,
        Value.VALUETYPE_FLOAT: definitions.Value_FLOAT,
        Value.VALUETYPE_GEO: definitions.Value_FLOAT,
        Value.VALUETYPE_INTEGER: definitions.Value_INTEGER,
        Value.VALUETYPE_N: definitions.Value_TEXT,
        Value.VALUETYPE_ORG: definitions.Value_TEXT,
        Value.VALUETYPE_TEXT: definitions.Value_TEXT,
        Value.VALUETYPE_TIME: definitions.Value_TIME,
        Value.VALUETYPE_URI: definitions.Value_URI,
        Value.VALUETYPE_UTC_OFFSET: definitions.Value_UTCOFFSET,
        Value.VALUETYPE_VCARD: definitions.Value_VCARD,
    }

    sMultiValues: set = set((
        definitions.Property_NICKNAME,
        definitions.Property_CATEGORIES,
    ))

    sSpecialVariants: Dict[str, int] = {
        definitions.Property_ADR: Value.VALUETYPE_ADR,
        definitions.Property_GEO: Value.VALUETYPE_GEO,
        definitions.Property_N: Value.VALUETYPE_N,
        definitions.Property_ORG: Value.VALUETYPE_ORG,
    }

    sUsesGroup: bool = True
    sVariant: str = "vcard"
    sValue: str = definitions.Parameter_VALUE
    sText: str = definitions.Value_TEXT

    mGroup: Optional[str]

    def __init__(self, group: Optional[str] = None, name: Optional[str] = None, value: Any = None, valuetype: Any = None) -> None:
        super(Property, self).__init__(name, value, valuetype)
        self.mGroup = group
        if value is None:
            pass
        if isinstance(value, int):
            self._init_attr_value_int(value)
        elif isinstance(value, str):
            self._init_attr_value_text(value, valuetype if valuetype else self.sDefaultValueTypeMap.get(self.mName.upper(), Value.VALUETYPE_TEXT))
        elif isinstance(value, DateTime):
            self._init_attr_value_datetime(value)
        elif isinstance(value, Adr):
            self._init_attr_value_adr(value)
        elif isinstance(value, N):
            self._init_attr_value_n(value)
        elif isinstance(value, list) or isinstance(value, tuple):
            if name and name.upper() == definitions.Property_ORG:
                self._init_attr_value_org(value)
            elif name and name.upper() == definitions.Property_GEO:
                self._init_attr_value_geo(value)
            else:
                self._init_attr_value_text_list(value)
        elif isinstance(value, UTCOffsetValue):
            self._init_attr_value_utcoffset(value)

    def duplicate(self) -> "Property":
        other = Property(self.mGroup, self.mName)
        for attrname, attrs in self.mParameters.items():
            other.mParameters[attrname] = [i.duplicate() for i in attrs]
        other.mValue = self.mValue.duplicate()
        return other

    def __hash__(self) -> int:
        return hash((
            self.mGroup,
            self.mName,
            tuple([tuple(self.mParameters[attrname]) for attrname in sorted(self.mParameters.keys())]),
            self.mValue,
        ))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Property):
            return False
        return (
            self.mGroup == other.mGroup and
            self.mName == other.mName and
            self.mValue == other.mValue and
            self.mParameters == other.mParameters
        )

    def parseTextParameters(self, txt: str, data: str) -> Optional[str]:
        try:
            stripValueSpaces = False
            while txt:
                if txt[0] == ';':
                    txt = txt[1:]
                    parameter_name, txt = stringutils.strduptokenstr(txt, "=:;")
                    if parameter_name is None:
                        raise InvalidProperty("Invalid property: empty parameter name", data)
                    if txt[0] != "=":
                        if ParserContext.VCARD_2_NO_PARAMETER_VALUES == ParserContext.PARSER_RAISE:
                            raise InvalidProperty("Invalid property parameter", data)
                        elif ParserContext.VCARD_2_NO_PARAMETER_VALUES == ParserContext.PARSER_ALLOW:
                            parameter_value = None
                        else:
                            parameter_name = None
                        if parameter_name and parameter_name.upper() == "BASE64" and ParserContext.VCARD_2_BASE64 == ParserContext.PARSER_FIX:
                            parameter_name = definitions.Parameter_ENCODING
                            parameter_value = definitions.Parameter_Value_ENCODING_B
                            stripValueSpaces = True
                    else:
                        txt = txt[1:]
                        parameter_value, txt = stringutils.strduptokenstr(txt, ":;,")
                        if parameter_value is None:
                            raise InvalidProperty("Invalid property: empty parameter name", data)
                    if parameter_name is not None:
                        attrvalue = Parameter(name=parameter_name, value=decodeParameterValue(parameter_value))
                        self.mParameters.setdefault(parameter_name.upper(), []).append(attrvalue)
                    while txt[0] == ',':
                        txt = txt[1:]
                        parameter_value2, txt = stringutils.strduptokenstr(txt, ":;,")
                        if parameter_value2 is None:
                            raise InvalidProperty("Invalid property: empty parameter multi-value", data)
                        attrvalue.addValue(decodeParameterValue(parameter_value2))
                elif txt[0] == ':':
                    txt = txt[1:]
                    if stripValueSpaces:
                        txt = txt.replace(" ", "")
                    return txt
        except IndexError:
            raise InvalidProperty("Invalid property: index error", data)

    def generateValue(self, os: IO[str], novalue: bool) -> None:
        if self.mName.upper() == "PHOTO" and self.mValue.getType() == Value.VALUETYPE_BINARY:
            self.setupValueParameter()
            sout = StringIO.StringIO()
            if self.mGroup:
                sout.write(self.mGroup + ".")
            sout.write(self.mName)
            for key in sorted(self.mParameters.keys()):
                for attr in self.mParameters[key]:
                    sout.write(";")
                    attr.generate(sout)
            sout.write(":")
            sout.write("\r\n")
            value = self.mValue.getText()
            value_len = len(value)
            offset = 0
            while value_len > 72:
                sout.write(" ")
                sout.write(value[offset:offset + 72])
                sout.write("\r\n")
                value_len -= 72
                offset += 72
            sout.write(" ")
            sout.write(value[offset:])
            os.write(sout.getvalue())
            os.write("\r\n")
        else:
            super(Property, self).generateValue(os, novalue)

    def _init_attr_value_adr(self, reqstatus: Any) -> None:
        self.mValue = AdrValue(reqstatus)
        self.setupValueParameter()

    def _init_attr_value_n(self, reqstatus: Any) -> None:
        self.mValue = NValue(reqstatus)
        self.setupValueParameter()

    def _init_attr_value_org(self, reqstatus: Any) -> None:
        self.mValue = OrgValue(reqstatus)
        self.setupValueParameter()