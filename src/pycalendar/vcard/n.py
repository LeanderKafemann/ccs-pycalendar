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

class N(ValueMixin):
    """
    mValue is a tuple of five str
    """

    (
        LAST,
        FIRST,
        MIDDLE,
        PREFIX,
        SUFFIX,
        MAXITEMS
    ) = range(6)

    mValue: Tuple[str, str, str, str, str]

    def __init__(
        self,
        last: str = "",
        first: str = "",
        middle: str = "",
        prefix: str = "",
        suffix: str = ""
    ) -> None:
        self.mValue = (last, first, middle, prefix, suffix)

    def duplicate(self) -> "N":
        return N(*self.mValue)

    def __hash__(self) -> int:
        return hash(self.mValue)

    def __repr__(self) -> str:
        return "N %s" % (self.getText(),)

    def __eq__(self, comp: Any) -> bool:
        return isinstance(comp, N) and self.mValue == comp.mValue

    def getFirst(self) -> str:
        return self.mValue[N.FIRST]

    def setFirst(self, value: str) -> None:
        self.mValue = self.mValue[:N.FIRST] + (value,) + self.mValue[N.FIRST+1:]

    def getLast(self) -> str:
        return self.mValue[N.LAST]

    def setLast(self, value: str) -> None:
        self.mValue = self.mValue[:N.LAST] + (value,) + self.mValue[N.LAST+1:]

    def getMiddle(self) -> str:
        return self.mValue[N.MIDDLE]

    def setMiddle(self, value: str) -> None:
        self.mValue = self.mValue[:N.MIDDLE] + (value,) + self.mValue[N.MIDDLE+1:]

    def getPrefix(self) -> str:
        return self.mValue[N.PREFIX]

    def setPrefix(self, value: str) -> None:
        self.mValue = self.mValue[:N.PREFIX] + (value,) + self.mValue[N.PREFIX+1:]

    def getSuffix(self) -> str:
        return self.mValue[N.SUFFIX]

    def setSuffix(self, value: str) -> None:
        self.mValue = self.mValue[:N.SUFFIX] + (value,) + self.mValue[N.SUFFIX+1:]

    def getFullName(self) -> str:
        def _stringOrList(item: Any) -> str:
            return item if isinstance(item, str) else " ".join(item)
        results = []
        for i in (N.PREFIX, N.FIRST, N.MIDDLE, N.LAST, N.SUFFIX):
            result = _stringOrList(self.mValue[i])
            if result:
                results.append(result)
        return " ".join(results)

    def parse(self, data: str) -> None:
        self.mValue = utils.parseDoubleNestedList(data, N.MAXITEMS)

    def generate(self, os: IO[str]) -> None:
        utils.generateDoubleNestedList(os, self.mValue)

    def parseJSON(self, jobject: Any) -> None:
        self.mValue = tuple(map(lambda x: x.encode("utf-8"), jobject))

    def writeJSON(self, jobject: list) -> None:
        jobject.append(list(self.mValue))

    def getValue(self) -> Tuple[str, str, str, str, str]:
        return self.mValue

    def setValue(self, value: Tuple[str, str, str, str, str]) -> None:
        self.mValue = value