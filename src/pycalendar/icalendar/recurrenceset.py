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
from pycalendar.icalendar.exceptions import TooManyInstancesError
from pycalendar.utils import set_difference

class RecurrenceSet(object):
    mRrules: List[Any]
    mExrules: List[Any]
    mRdates: List[Any]
    mExdates: List[Any]
    mRperiods: List[Any]
    mExperiods: List[Any]

    def __init__(self) -> None:
        self.mRrules = []
        self.mExrules = []
        self.mRdates = []
        self.mExdates = []
        self.mRperiods = []
        self.mExperiods = []

    def duplicate(self) -> "RecurrenceSet":
        other = RecurrenceSet()
        other.mRrules = [i.duplicate() for i in self.mRrules]
        other.mExrules = [i.duplicate() for i in self.mExrules]
        other.mRdates = [i.duplicate() for i in self.mRdates]
        other.mExdates = [i.duplicate() for i in self.mExdates]
        other.mRperiods = [i.duplicate() for i in self.mRperiods]
        other.mExperiods = [i.duplicate() for i in self.mExperiods]
        return other

    def hasRecurrence(self) -> bool:
        return (
            (len(self.mRrules) != 0) or (len(self.mRdates) != 0) or (len(self.mRperiods) != 0) or
            (len(self.mExrules) != 0) or (len(self.mExdates) != 0) or
            (len(self.mExperiods) != 0)
        )

    def equals(self, comp: "RecurrenceSet") -> bool:
        if not self.equalsRules(self.mRrules, comp.mRrules):
            return False
        if not self.equalsRules(self.mExrules, comp.mExrules):
            return False
        if not self.equalsDates(self.mRdates, comp.mRdates):
            return False
        if not self.equalsPeriods(self.mRperiods, comp.mRperiods):
            return False
        if not self.equalsDates(self.mExdates, comp.mExdates):
            return False
        if not self.equalsPeriods(self.mExperiods, comp.mExperiods):
            return False
        return True

    def equalsRules(self, rules1: List[Any], rules2: List[Any]) -> bool:
        if len(rules1) != len(rules2):
            return False
        elif len(rules1) == 0:
            return True
        temp2 = rules2[:]
        for r1 in rules1:
            found = False
            for r2 in temp2:
                if r1.equals(r2):
                    temp2.remove(r2)
                    found = True
                    break
            if not found:
                return False
        return True

    def equalsDates(self, dates1: List[Any], dates2: List[Any]) -> bool:
        if len(dates1) != len(dates2):
            return False
        elif len(dates1) == 0:
            return True
        dt1 = dates1[:]
        dt2 = dates2[:]
        dt1.sort(key=lambda x: x.getPosixTime())
        dt2.sort(key=lambda x: x.getPosixTime())
        return dt1 == dt2

    def equalsPeriods(self, periods1: List[Any], periods2: List[Any]) -> bool:
        if len(periods1) != len(periods2):
            return False
        elif len(periods1) == 0:
            return True
        p1 = periods1[:]
        p2 = periods2[:]
        p1.sort()
        p2.sort()
        return p1 == p2

    def addRule(self, rule: Any) -> None:
        self.mRrules.append(rule)

    def subtractRule(self, rule: Any) -> None:
        self.mExrules.append(rule)

    def addDT(self, dt: Any) -> None:
        self.mRdates.append(dt)

    def subtractDT(self, dt: Any) -> None:
        self.mExdates.append(dt)

    def addPeriod(self, p: Any) -> None:
        self.mRperiods.append(p)

    def subtractPeriod(self, p: Any) -> None:
        self.mExperiods.append(p)

    def getRules(self) -> List[Any]:
        return self.mRrules

    def getExrules(self) -> List[Any]:
        return self.mExrules

    def getDates(self) -> List[Any]:
        return self.mRdates

    def getExdates(self) -> List[Any]:
        return self.mExdates

    def getPeriods(self) -> List[Any]:
        return self.mRperiods

    def getExperiods(self) -> List[Any]:
        return self.mExperiods

    def expand(self, start: Any, range: Any, items: List[Any], float_offset: int = 0, maxInstances: Any = None) -> bool:
        limited: bool = False
        include: List[Any] = []
        if range.isDateWithinPeriod(start):
            include.append(start)
        else:
            limited = True
        for iter in self.mRrules:
            if iter.expand(start, range, include, float_offset=float_offset, maxInstances=maxInstances):
                limited = True
        for iter in self.mRdates:
            if range.isDateWithinPeriod(iter):
                include.append(iter)
                if maxInstances and len(include) > maxInstances:
                    raise TooManyInstancesError("Too many instances")
            else:
                limited = True
        for iter in self.mRperiods:
            if range.isPeriodOverlap(iter):
                include.append(iter.getStart())
                if maxInstances and len(include) > maxInstances:
                    raise TooManyInstancesError("Too many instances")
            else:
                limited = True
        include = [x for x in set(include)]
        include.sort(key=lambda x: x.getPosixTime())
        exclude: List[Any] = []
        for iter in self.mExrules:
            iter.expand(start, range, exclude, float_offset=float_offset)
        for iter in self.mExdates:
            if range.isDateWithinPeriod(iter):
                exclude.append(iter)
        for iter in self.mExperiods:
            if range.isPeriodOverlap(iter):
                exclude.append(iter.getStart())
        exclude = [x for x in set(exclude)]
        exclude.sort(key=lambda x: x.getPosixTime())
        items.extend(set_difference(include, exclude))
        return limited

    def changed(self) -> None:
        for iter in self.mRrules:
            iter.clear()
        for iter in self.mExrules:
            iter.clear()

    def excludeFutureRecurrence(self, exclude: Any) -> None:
        for iter in self.mRrules:
            iter.excludeFutureRecurrence(exclude)
        self.mRdates = [dt for dt in self.mRdates if dt < exclude]
        self.mRperiods = [iter for iter in self.mRperiods if iter <= exclude]

    def isSimpleUI(self) -> bool:
        if ((len(self.mRrules) > 1) or (len(self.mExrules) > 0) or
                (len(self.mRdates) > 0) or (len(self.mRperiods) > 0)):
            return False
        elif len(self.mRrules) == 1:
            return self.mRrules[0].isSimpleRule()
        else:
            return True

    def isAdvancedUI(self) -> bool:
        if ((len(self.mRrules) > 1) or (len(self.mExrules) > 0) or
                (len(self.mRdates) > 0) or (len(self.mRperiods) > 0)):
            return False
        elif len(self.mRrules) == 1:
            return self.mRrules[0].isAdvancedRule()
        else:
            return True

    def getUIRecurrence(self) -> Any:
        if len(self.mRrules) == 1:
            return self.mRrules[0]
        else:
            return None

    def getUIDescription(self) -> str:
        if not self.hasRecurrence():
            return "No Recurrence"
        if ((len(self.mRrules) == 1) and (len(self.mExrules) == 0) and (len(self.mRdates) == 0) and
                (len(self.mExdates) == 0) and (len(self.mRperiods) == 0) and
                (len(self.mExperiods) == 0)):
            return self.mRrules[0].getUIDescription()
        return "Multiple recurrence rules, dates or exclusions"