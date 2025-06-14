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

# Helpers for value classes
from typing import Any, IO, Type, TypeVar, Generic
from io import StringIO

T = TypeVar("T")

class ValueMixin(object):
    """
    Mix-in für Operationen, die für Value- und value-spezifische Klassen gemeinsam sind.
    """

    def __str__(self) -> str:
        return self.getText()

    @classmethod
    def parseText(cls: Type[T], data: str) -> T:
        value = cls()
        value.parse(data)
        return value

    def parse(self, data: str) -> None:
        raise NotImplementedError

    def generate(self, os: IO[str]) -> None:
        raise NotImplementedError

    def getText(self) -> str:
        os = StringIO()
        self.generate(os)
        return os.getvalue()

    def writeXML(self, node: Any, namespace: Any) -> None:
        raise NotImplementedError

    def parseJSON(self, jobject: Any) -> None:
        raise NotImplementedError

    def writeJSON(self, jobject: Any) -> None:
        raise NotImplementedError


class WrapperValue(object):
    """
    Mix-in für Value-abgeleitete Klassen, die eine value-spezifische Klasse wrappen.
    """

    _wrappedClass: Any = None
    _wrappedType: Any = None
    mValue: Any

    def __init__(self, value: Any = None) -> None:
        self.mValue = value if value is not None else self._wrappedClass()

    def getType(self) -> Any:
        return self._wrappedType

    def duplicate(self) -> "WrapperValue":
        return self.__class__(self.mValue.duplicate())

    def parse(self, data: str, variant: Any = None) -> None:
        self.mValue.parse(data)

    def generate(self, os: IO[str]) -> None:
        self.mValue.generate(os)

    def writeXML(self, node: Any, namespace: Any) -> None:
        value = self.getXMLNode(node, namespace)
        value.text = self.mValue.writeXML()

    def parseJSONValue(self, jobject: Any) -> None:
        self.mValue.parseJSON(jobject)

    def writeJSONValue(self, jobject: Any) -> None:
        self.mValue.writeJSON(jobject)

    def getValue(self) -> Any:
        return self.mValue

    def setValue(self, value: Any) -> None:
        self.mValue = value