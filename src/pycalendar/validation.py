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
from typing import Any, Callable, Dict
from pycalendar.plaintextvalue import PlainTextValue

def partial(func: Callable, *args: Any, **keywords: Any) -> Callable:
    def newfunc(*fargs: Any, **fkeywords: Any) -> Any:
        newkeywords = keywords.copy()
        newkeywords.update(fkeywords)
        return func(*(args + fargs), **newkeywords)
    newfunc.func = func
    newfunc.args = args
    newfunc.keywords = keywords
    return newfunc

class PropertyValueChecks(object):
    @staticmethod
    def stringValue(text: str, property: Any) -> bool:
        value = property.getValue()
        if value and isinstance(value, PlainTextValue):
            value = value.getValue()
            return value.lower() == text.lower()
        return False

    @staticmethod
    def alwaysUTC(property: Any) -> bool:
        value = property.getDateTimeValue()
        if value:
            value = value.getValue()
            return value.utc()
        return False

    @staticmethod
    def numericRange(low: int, high: int, property: Any) -> bool:
        value = property.getIntegerValue()
        if value:
            value = value.getValue()
            return low <= value <= high
        return False

    @staticmethod
    def positiveIntegerOrZero(property: Any) -> bool:
        value = property.getIntegerValue()
        if value:
            value = value.getValue()
            return value >= 0
        return False