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
from typing import Any, List, Set, Tuple
from pycalendar.icalendar import definitions
from pycalendar.icalendar import itipdefinitions
from pycalendar.icalendar.component import Component
from pycalendar.icalendar.validation import ICALENDAR_VALUE_CHECKS

class VAvailability(Component):
    propertyCardinality_1: Tuple[str, ...] = (
        definitions.cICalProperty_DTSTAMP,
        definitions.cICalProperty_UID,
    )

    propertyCardinality_0_1: Tuple[str, ...] = (
        definitions.cICalProperty_BUSYTYPE,
        definitions.cICalProperty_CLASS,
        definitions.cICalProperty_CREATED,
        definitions.cICalProperty_DESCRIPTION,
        definitions.cICalProperty_DTSTART,
        definitions.cICalProperty_LAST_MODIFIED,
        definitions.cICalProperty_ORGANIZER,
        definitions.cICalProperty_SEQUENCE,
        definitions.cICalProperty_SUMMARY,
        definitions.cICalProperty_URL,
        definitions.cICalProperty_RECURRENCE_ID,
        definitions.cICalProperty_DTEND,
        definitions.cICalProperty_DURATION,
    )

    propertyValueChecks: Any = ICALENDAR_VALUE_CHECKS

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent=parent)

    def duplicate(self, parent: Any = None) -> "VAvailability":
        return super().duplicate(parent=parent)

    def getType(self) -> str:
        return definitions.cICalComponent_VAVAILABILITY

    def getMimeComponentName(self) -> str:
        return itipdefinitions.cICalMIMEComponent_VAVAILABILITY

    def finalise(self) -> None:
        super().finalise()

    def validate(self, doFix: bool = False) -> Tuple[List[str], List[str]]:
        fixed, unfixed = super().validate(doFix)
        if self.hasProperty(definitions.cICalProperty_DTEND) and self.hasProperty(definitions.cICalProperty_DURATION):
            logProblem = "[%s] Properties must not both be present: %s, %s" % (
                self.getType(),
                definitions.cICalProperty_DTEND,
                definitions.cICalProperty_DURATION,
            )
            if doFix:
                self.removeProperties(definitions.cICalProperty_DTEND)
                fixed.append(logProblem)
            else:
                unfixed.append(logProblem)
        return fixed, unfixed

    def addComponent(self, comp: Any) -> None:
        if comp.getType() == definitions.cICalComponent_AVAILABLE:
            super().addComponent(comp)
        else:
            raise ValueError("Only 'AVAILABLE' components allowed in 'VAVAILABILITY'")

    def sortedPropertyKeyOrder(self) -> Tuple[str, ...]:
        return (
            definitions.cICalProperty_UID,
            definitions.cICalProperty_DTSTART,
            definitions.cICalProperty_DURATION,
            definitions.cICalProperty_DTEND,
        )

    def getTimezones(self, tzids: Set[str]) -> None:
        super().getTimezones(tzids)
        for available in self.getComponents(definitions.cICalComponent_AVAILABLE):
            available.getTimezones(tzids)

Component.registerComponent(definitions.cICalComponent_VAVAILABILITY, VAvailability)