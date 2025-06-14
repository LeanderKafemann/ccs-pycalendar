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

# vCard ADR value
from typing import Any, Tuple, IO
from pycalendar import utils
from pycalendar.valueutils import ValueMixin

class Adr(ValueMixin):
    """
    mValue is a tuple of seven str or tuples of str
    """

    (
        POBOX,
        EXTENDED,
        STREET,
        LOCALITY,
        REGION,
        POSTALCODE,
        COUNTRY,
        MAXITEMS
    ) = range(8)

    mValue: Tuple[str, str, str, str, str, str, str]

    def __init__(
        self,
        pobox: str = "",
        extended: str = "",
        street: str = "",
        locality: str = "",
        region: str = "",
        postalcode: str = "",
        country: str = ""
    ) -> None:
        self.mValue = (pobox, extended, street, locality, region, postalcode, country)

    def duplicate(self) -> "Adr":
        return Adr(*self.mValue)

    def __hash__(self) -> int:
        return hash(self.mValue)

    def __repr__(self) -> str:
        return "ADR %s" % (self.getText(),)

    def __eq__(self, comp: Any) -> bool:
        return isinstance(comp, Adr) and self.mValue == comp.mValue

    def getPobox(self) -> str:
        return self.mValue[Adr.POBOX]

    def setPobox(self, value: str) -> None:
        self.mValue = self.mValue[:Adr.POBOX] + (value,) + self.mValue[Adr.POBOX+1:]

    def getExtended(self) -> str:
        return self.mValue[Adr.EXTENDED]

    def setExtended(self, value: str) -> None:
        self.mValue = self.mValue[:Adr.EXTENDED] + (value,) + self.mValue[Adr.EXTENDED+1:]

    def getStreet(self) -> str:
        return self.mValue[Adr.STREET]

    def setStreet(self, value: str) -> None:
        self.mValue = self.mValue[:Adr.STREET] + (value,) + self.mValue[Adr.STREET+1:]

    def getLocality(self) -> str:
        return self.mValue[Adr.LOCALITY]

    def setLocality(self, value: str) -> None:
        self.mValue = self.mValue[:Adr.LOCALITY] + (value,) + self.mValue[Adr.LOCALITY+1:]

    def getRegion(self) -> str:
        return self.mValue[Adr.REGION]

    def setRegion(self, value: str) -> None:
        self.mValue = self.mValue[:Adr.REGION] + (value,) + self.mValue[Adr.REGION+1:]

    def getPostalCode(self) -> str:
        return self.mValue[Adr.POSTALCODE]

    def setPostalCode(self, value: str) -> None:
        self.mValue = self.mValue[:Adr.POSTALCODE] + (value,) + self.mValue[Adr.POSTALCODE+1:]

    def getCountry(self) -> str:
        return self.mValue[Adr.COUNTRY]

    def setCountry(self, value: str) -> None:
        self.mValue = self.mValue[:Adr.COUNTRY] + (value,) + self.mValue[Adr.COUNTRY+1:]

    def parse(self, data: str) -> None:
        self.mValue = utils.parseDoubleNestedList(data, Adr.MAXITEMS)

    def generate(self, os: IO[str]) -> None:
        utils.generateDoubleNestedList(os, self.mValue)

    def parseJSON(self, jobject: Any) -> None:
        self.mValue = tuple(map(lambda x: x.encode("utf-8"), jobject))

    def writeJSON(self, jobject: list) -> None:
        jobject.append(list(self.mValue))

    def getValue(self) -> Tuple[str, str, str, str, str, str, str]:
        return self.mValue

    def setValue(self, value: Tuple[str, str, str, str, str, str, str]) -> None:
        self.mValue = value