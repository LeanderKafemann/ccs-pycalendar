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
from typing import Tuple, List
from pycalendar.datetime import DateTime
from pycalendar.icalendar import definitions
from pycalendar.icalendar import itipdefinitions
from pycalendar.icalendar.componentrecur import ComponentRecur
from pycalendar.icalendar.property import Property
from pycalendar.icalendar.validation import ICALENDAR_VALUE_CHECKS
import io as StringIO

class VToDo(ComponentRecur):

    OVERDUE: int = 0
    DUE_NOW: int = 1
    DUE_LATER: int = 2
    DONE: int = 3
    CANCELLED: int = 4

    @staticmethod
    def sort_for_display(e1: "VToDo", e2: "VToDo") -> bool:
        s1 = e1.getMaster()
        s2 = e2.getMaster()
        # ... (Rest bleibt unverändert)

    propertyCardinality_1: Tuple[str, ...] = (
        definitions.cICalProperty_DTSTAMP,
        definitions.cICalProperty_UID,
    )

    propertyCardinality_0_1: Tuple[str, ...] = (
        definitions.cICalProperty_CLASS,
        definitions.cICalProperty_COMPLETED,
        definitions.cICalProperty_CREATED,
        definitions.cICalProperty_DESCRIPTION,
        definitions.cICalProperty_DTSTART,
        definitions.cICalProperty_GEO,
        definitions.cICalProperty_LAST_MODIFIED,
        definitions.cICalProperty_LOCATION,
        definitions.cICalProperty_ORGANIZER,
        definitions.cICalProperty_PERCENT_COMPLETE,
        definitions.cICalProperty_PRIORITY,
        definitions.cICalProperty_RECURRENCE_ID,
        definitions.cICalProperty_SEQUENCE,
        # definitions.cICalProperty_STATUS, # Special fix done for multiple STATUS
        definitions.cICalProperty_SUMMARY,
        definitions.cICalProperty_URL,
        definitions.cICalProperty_RRULE,
        definitions.cICalProperty_DUE,
        definitions.cICalProperty_DURATION,
    )

    propertyValueChecks = ICALENDAR_VALUE_CHECKS

    def __init__(self, parent: ComponentRecur = None) -> None:
        super(VToDo, self).__init__(parent=parent)
        self.mPriority: int = 0
        self.mStatus: int = definitions.eStatus_VToDo_None
        self.mPercentComplete: int = 0
        self.mCompleted: DateTime = DateTime()
        self.mHasCompleted: bool = False

    def duplicate(self, parent: ComponentRecur = None) -> "VToDo":
        other: VToDo = super(VToDo, self).duplicate(parent=parent)
        other.mPriority = self.mPriority
        other.mStatus = self.mStatus
        other.mPercentComplete = self.mPercentComplete
        other.mCompleted = self.mCompleted.duplicate()
        other.mHasCompleted = self.mHasCompleted
        return other

    def getType(self) -> str:
        return definitions.cICalComponent_VTODO

    def getMimeComponentName(self) -> str:
        return itipdefinitions.cICalMIMEComponent_VTODO

    def addComponent(self, comp: ComponentRecur) -> None:
        pass

    def getStatus(self) -> int:
        return self.mStatus

    def setStatus(self, status: int) -> None:
        self.mStatus = status

    def getStatusText(self) -> str:
        sout = StringIO.StringIO()
        # ...
        return sout.toString()

    def getCompletionState(self) -> int:
        # ...
        # Rückgabewerte sind die Klassenversionen (int)
        pass

    def getPriority(self) -> int:
        return self.mPriority

    def setPriority(self, priority: int) -> None:
        self.mPriority = priority

    def getCompleted(self) -> DateTime:
        return self.mCompleted

    def hasCompleted(self) -> bool:
        return self.mHasCompleted

    def finalise(self) -> None:
        pass

    def validate(self, doFix: bool = False) -> Tuple[List[str], List[str]]:
        pass

    def editStatus(self, status: int) -> None:
        pass

    def editCompleted(self, completed: DateTime) -> None:
        pass

    def sortedPropertyKeyOrder(self) -> Tuple[str, ...]:
        return (
            definitions.cICalProperty_UID,
            definitions.cICalProperty_RECURRENCE_ID,
            definitions.cICalProperty_DTSTART,
            definitions.cICalProperty_DURATION,
            definitions.cICalProperty_DUE,
            definitions.cICalProperty_COMPLETED,
        )