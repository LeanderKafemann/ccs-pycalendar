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
from typing import Any, Callable
from pycalendar.datetime import DateTime

class ComponentExpanded(object):
    mOwner: Any
    mInstanceStart: DateTime
    mInstanceEnd: DateTime
    mRecurring: bool

    @staticmethod
    def sort_by_dtstart_allday(e1: "ComponentExpanded", e2: "ComponentExpanded") -> bool:
        if e1.mInstanceStart.isDateOnly() and e2.mInstanceStart.isDateOnly():
            return e1.mInstanceStart < e2.mInstanceStart
        elif e1.mInstanceStart.isDateOnly():
            return True
        elif e2.mInstanceStart.isDateOnly():
            return False
        elif e1.mInstanceStart == e2.mInstanceStart:
            if e1.mInstanceEnd == e2.mInstanceEnd:
                return e1.getOwner().getStamp() < e2.getOwner().getStamp()
            else:
                return e1.mInstanceEnd > e2.mInstanceEnd
        else:
            return e1.mInstanceStart < e2.mInstanceStart

    @staticmethod
    def sort_by_dtstart(e1: "ComponentExpanded", e2: "ComponentExpanded") -> bool:
        if e1.mInstanceStart == e2.mInstanceStart:
            if (
                e1.mInstanceStart.isDateOnly() and not e2.mInstanceStart.isDateOnly() or
                not e1.mInstanceStart.isDateOnly() and e2.mInstanceStart.isDateOnly()
            ):
                return e1.mInstanceStart.isDateOnly()
            else:
                return False
        else:
            return e1.mInstanceStart < e2.mInstanceStart

    def __init__(self, owner: Any, rid: Any) -> None:
        self.mOwner = owner
        self.initFromOwner(rid)

    def duplicate(self) -> "ComponentExpanded":
        other = ComponentExpanded(self.mOwner, None)
        other.mInstanceStart = self.mInstanceStart.duplicate()
        other.mInstanceEnd = self.mInstanceEnd.duplicate()
        other.mRecurring = self.mRecurring
        return other

    def close(self) -> None:
        self.mOwner = None

    def getOwner(self) -> Any:
        return self.mOwner

    def getMaster(self) -> Any:
        return self.mOwner

    def getTrueMaster(self) -> Any:
        return self.mOwner.getMaster()

    def getInstanceStart(self) -> DateTime:
        return self.mInstanceStart

    def getInstanceEnd(self) -> DateTime:
        return self.mInstanceEnd

    def recurring(self) -> bool:
        return self.mRecurring

    def isNow(self) -> bool:
        now = DateTime.getNowUTC()
        return self.mInstanceStart <= now and self.mInstanceEnd > now

    def initFromOwner(self, rid: Any) -> None:
        if rid is None:
            self.mInstanceStart = self.mOwner.getStart()
            self.mInstanceEnd = self.mOwner.getEnd()
            self.mRecurring = False
        elif not self.mOwner.isRecurrenceInstance():
            self.mInstanceStart = rid
            if self.mOwner.hasEnd():
                self.mInstanceEnd = self.mInstanceStart + (self.mOwner.getEnd() - self.mOwner.getStart())
            else:
                self.mInstanceEnd = self.mInstanceStart.duplicate()
            self.mRecurring = True
        elif rid == self.mOwner.getRecurrenceID():
            self.mInstanceStart = self.mOwner.getStart()
            self.mInstanceEnd = self.mOwner.getEnd()
            self.mRecurring = True
        else:
            self.mInstanceStart = rid + (self.mOwner.getStart() - self.mOwner.getRecurrenceID())
            self.mInstanceEnd = self.mInstanceStart + (self.mOwner.getEnd() - self.mOwner.getStart())
            self.mRecurring = True