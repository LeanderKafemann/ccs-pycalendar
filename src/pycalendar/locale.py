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


from typing import List

LONG: int = 0
SHORT: int = 1
ABBREVIATED: int = 2

cLongDays: List[str] = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
cShortDays: List[str] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
cAbbrevDays: List[str] = ["S", "M", "T", "W", "T", "F", "S"]

cLongMonths: List[str] = ["", "January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]
cShortMonths: List[str] = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
cAbbrevMonths: List[str] = ["", "J", "F", "M", "A", "M", "J",
                            "J", "A", "S", "O", "N", "D"]

s24HourTime: bool = False
sDDMMDate: bool = False

def getDay(day: int, strl: int) -> str:
    return {LONG: cLongDays[day], SHORT: cShortDays[day], ABBREVIATED: cAbbrevDays[day]}[strl]

def getMonth(month: int, strl: int) -> str:
    return {LONG: cLongMonths[month], SHORT: cShortMonths[month], ABBREVIATED: cAbbrevMonths[month]}[strl]

def use24HourTime() -> bool:
    # TODO: get 24 hour option from system prefs
    return s24HourTime

def useDDMMDate() -> bool:
    # TODO: get 24 hour option from system prefs
    return sDDMMDate