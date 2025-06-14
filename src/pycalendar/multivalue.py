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

from typing import Any, List
from pycalendar.value import Value

class MultiValue(Value):
    mType: int
    mValues: List[Value]

    def __init__(self, type: int) -> None:
        self.mType = type
        self.mValues: List[Value] = []

    def __hash__(self) -> int:
        return hash(tuple(self.mValues))

    def duplicate(self) -> "MultiValue":
        other = MultiValue(self.mType)
        other.mValues = [i.duplicate() for i in self.mValues]
        return other

    def getType(self) -> int:
        return self.mType

    def getRealType(self) -> int:
        return Value.VALUETYPE_MULTIVALUE

    def getValue(self) -> List[Value]:
        return self.mValues

    def getValues(self) -> List[Value]:
        return self.mValues

    def addValue(self, value: Value) -> None:
        self.mValues.append(value)

    def setValue(self, value: List[Any]) -> None:
        newValues: List[Value] = []
        for v in value:
            val = Value.createFromType(self.mType)
            val.setValue(v)
            newValues.append(val)
        self.mValues = newValues

    def parse(self, data: str, variant: Any) -> None:
        if "," in data:
            tokens = data.split(",")
        else:
            tokens = (data,)
        for token in tokens:
            value = Value.createFromType(self.mType)
            value.parse(token, variant)
            self.mValues.append(value)

    def generate(self, os: Any) -> None:
        try:
            first = True
            for iter in self.mValues:
                if first:
                    first = False
                else:
                    os.write(",")
                iter.generate(os)
        except Exception:
            pass

    def writeXML(self, node: Any, namespace: Any) -> None:
        for iter in self.mValues:
            iter.writeXML(node, namespace)

    def parseJSONValue(self, jobject: Any) -> None:
        for jvalue in jobject:
            value = Value.createFromType(self.mType)
            value.parseJSONValue(jvalue)
            self.mValues.append(value)

    def writeJSONValue(self, jobject: list) -> None:
        for iter in self.mValues:
            iter.writeJSONValue(jobject)

Value.registerType(Value.VALUETYPE_MULTIVALUE, MultiValue, None)