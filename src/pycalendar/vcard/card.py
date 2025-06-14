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

from typing import Any, List, ClassVar, Tuple
from io import StringIO
from pycalendar.containerbase import ContainerBase
from pycalendar.exceptions import InvalidData
from pycalendar.parser import ParserContext
from pycalendar.utils import readFoldedLine
from pycalendar.vcard import definitions
from pycalendar.vcard.definitions import VCARD, Property_VERSION, Property_PRODID, Property_UID
from pycalendar.vcard.property import Property
from pycalendar.vcard.validation import VCARD_VALUE_CHECKS
import json

class Card(ContainerBase):
    sContainerDescriptor: ClassVar[str] = "vCard"
    sComponentType: ClassVar[Any] = None
    sPropertyType: ClassVar[Any] = Property

    sFormatText: ClassVar[str] = "text/vcard"
    sFormatJSON: ClassVar[str] = "application/vcard+json"

    propertyCardinality_1: ClassVar[Tuple[str, ...]] = (
        definitions.Property_VERSION,
        definitions.Property_N,
    )

    propertyCardinality_0_1: ClassVar[Tuple[str, ...]] = (
        definitions.Property_BDAY,
        definitions.Property_PRODID,
        definitions.Property_REV,
        definitions.Property_UID,
    )

    propertyCardinality_1_More: ClassVar[Tuple[str, ...]] = (
        definitions.Property_FN,
    )

    propertyValueChecks: ClassVar[Any] = VCARD_VALUE_CHECKS

    def duplicate(self) -> "Card":
        return super(Card, self).duplicate()

    def getType(self) -> str:
        return VCARD

    def sortedPropertyKeyOrder(self) -> Tuple[str, ...]:
        return (
            Property_VERSION,
            Property_PRODID,
            Property_UID,
        )

    @classmethod
    def parseMultipleData(cls, data: Any, format: str) -> List["Card"]:
        if format == cls.sFormatText:
            return cls.parseMultipleTextData(data)
        elif format == cls.sFormatJSON:
            return cls.parseMultipleJSONData(data)
        return []

    @classmethod
    def parseMultipleTextData(cls, ins: Any) -> List["Card"]:
        if isinstance(ins, str):
            ins = StringIO(ins)

        results: List[Card] = []
        card: Card = cls(add_defaults=False)

        LOOK_FOR_VCARD = 0
        GET_PROPERTY = 1
        state = LOOK_FOR_VCARD
        lines: List[Any] = [None, None]

        while readFoldedLine(ins, lines):
            line = lines[0]
            if state == LOOK_FOR_VCARD:
                if line == card.getBeginDelimiter():
                    state = GET_PROPERTY
                elif len(line) == 0:
                    if ParserContext.BLANK_LINES_IN_DATA == ParserContext.PARSER_RAISE:
                        raise InvalidData("vCard data has blank lines")
                else:
                    raise InvalidData("vCard data not recognized", line)
            elif state == GET_PROPERTY:
                if line == card.getEndDelimiter():
                    card.finalise()
                    if not card.hasProperty("VERSION"):
                        raise InvalidData("vCard missing VERSION", "")
                    results.append(card)
                    card = Card(add_defaults=False)
                    state = LOOK_FOR_VCARD
                elif len(line) == 0:
                    if ParserContext.BLANK_LINES_IN_DATA == ParserContext.PARSER_RAISE:
                        raise InvalidData("vCard data has blank lines")
                else:
                    prop = Property.parseText(line)
                    if not card.validProperty(prop):
                        raise InvalidData("Invalid property", str(prop))
                    else:
                        card.addProperty(prop)
        if state != LOOK_FOR_VCARD:
            raise InvalidData("vCard data not complete")
        return results

    @classmethod
    def parseMultipleJSONData(cls, data: Any) -> List["Card"]:
        if not isinstance(data, str):
            data = data.read()
        try:
            jobjects = json.loads(data)
        except ValueError as e:
            raise InvalidData("JSON error: '{}'".format(e), data)
        results: List[Card] = []
        for jobject in jobjects:
            results.append(cls.parseJSON(jobject, None, cls(add_defaults=False)))
        return results

    def addDefaultProperties(self) -> None:
        self.addProperty(Property(definitions.Property_PRODID, Card.sProdID))
        self.addProperty(Property(definitions.Property_VERSION, "3.0"))

    def validProperty(self, prop: Property) -> bool:
        if prop.getName() == definitions.Property_VERSION:
            tvalue = prop.getValue()
            if ((tvalue is None) or (tvalue.getValue() != "3.0")):
                return False
        return True