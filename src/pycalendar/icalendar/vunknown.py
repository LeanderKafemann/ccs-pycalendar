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
from typing import Any, Tuple
from pycalendar.icalendar import definitions
from pycalendar.icalendar.component import Component
from pycalendar.icalendar.validation import ICALENDAR_VALUE_CHECKS
import uuid

class UnknownComponent(Component):

    propertyValueChecks = ICALENDAR_VALUE_CHECKS

    def __init__(self, parent: Any = None, comptype: str = "") -> None:
        super(UnknownComponent, self).__init__(parent=parent)
        self.mType: str = comptype
        self.mMapKey: str = str(uuid.uuid4())

    def duplicate(self, parent: Any = None) -> "UnknownComponent":
        return super(UnknownComponent, self).duplicate(parent=parent, comptype=self.mType)

    def getType(self) -> str:
        return self.mType

    def getBeginDelimiter(self) -> str:
        return "BEGIN:" + self.mType

    def getEndDelimiter(self) -> str:
        return "END:" + self.mType

    def getMimeComponentName(self) -> str:
        return "unknown"

    def getMapKey(self) -> str:
        return self.mMapKey

    def getSortKey(self) -> str:
        """
        We do not want unknown components sorted.
        """
        return ""

    def sortedPropertyKeyOrder(self) -> Tuple[str, ...]:
        return (
            definitions.cICalProperty_UID,
        )

Component.registerComponent(definitions.cICalComponent_UNKNOWN, UnknownComponent)