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
from typing import Any, List, Optional

class FreeBusy(object):
    FREE: int = 0
    BUSYTENTATIVE: int = 1
    BUSYUNAVAILABLE: int = 2
    BUSY: int = 3

    mType: int
    mPeriod: Any

    def __init__(self, type: Optional[int] = None, period: Optional[Any] = None) -> None:
        self.mType: int = type if type is not None else FreeBusy.FREE
        self.mPeriod: Any = period.duplicate() if period is not None else None

    def duplicate(self) -> "FreeBusy":
        return FreeBusy(self.mType, self.mPeriod)

    def setType(self, type: int) -> None:
        self.mType = type

    def getType(self) -> int:
        return self.mType

    def setPeriod(self, period: Any) -> None:
        self.mPeriod = period.duplicate()

    def getPeriod(self) -> Any:
        return self.mPeriod

    def isPeriodOverlap(self, period: Any) -> bool:
        return self.mPeriod.isPeriodOverlap(period)

    @staticmethod
    def resolveOverlaps(fb: List["FreeBusy"]) -> None:
        # TODO:
        pass