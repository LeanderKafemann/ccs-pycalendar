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
from typing import Any, Optional
from pycalendar import xmldefinitions, xmlutils
from pycalendar.datetime import DateTime
from pycalendar.duration import Duration
from pycalendar.valueutils import ValueMixin
import xml.etree.cElementTree as XML

class Period(ValueMixin):
    mStart: DateTime
    mEnd: Optional[DateTime]
    mDuration: Optional[Duration]
    mUseDuration: bool

    def __init__(self, start: Optional[DateTime] = None, end: Optional[DateTime] = None, duration: Optional[Duration] = None) -> None:
        self.mStart = start if start is not None else DateTime()
        if end is not None:
            self.mEnd = end
            self.mDuration = None
            self.mUseDuration = False
        elif duration is not None:
            self.mDuration = duration
            self.mEnd = None
            self.mUseDuration = True
        else:
            self.mEnd = self.mStart.duplicate()
            self.mDuration = None
            self.mUseDuration = False

    def duplicate(self) -> "Period":
        if self.mUseDuration:
            other = Period(start=self.mStart.duplicate(), duration=self.mDuration.duplicate() if self.mDuration else None)
        else:
            other = Period(start=self.mStart.duplicate(), end=self.mEnd.duplicate() if self.mEnd else None)
        return other

    def __hash__(self) -> int:
        return hash((self.mStart, self.getEnd(),))

    def __repr__(self) -> str:
        return "Period %s" % (self.getText(),)

    def __str__(self) -> str:
        return self.getText()

    def __eq__(self, comp: Any) -> bool:
        return self.mStart == comp.mStart and self.getEnd() == comp.getEnd()

    def __gt__(self, comp: Any) -> bool:
        return self.mStart > comp

    def __lt__(self, comp: Any) -> bool:
        return self.mStart < comp.mStart or (self.mStart == comp.mStart and self.getEnd() < comp.getEnd())

    @classmethod
    def parseText(cls, data: str) -> "Period":
        period = cls()
        period.parse(data)
        return period

    def parse(self, data: str, fullISO: bool = False) -> None:
        try:
            splits = data.split('/', 1)
            if len(splits) == 2:
                start = splits[0]
                end = splits[1]
                self.mStart.parse(start, fullISO)
                if end[0] == 'P':
                    self.mDuration = Duration.parseText(end)
                    self.mUseDuration = True
                    self.mEnd = None
                else:
                    self.mEnd.parse(end, fullISO)
                    self.mUseDuration = False
                    self.mDuration = None
            else:
                raise ValueError("Period: wrong number of '/' components")
        except IndexError:
            raise ValueError("Period: index error")

    def generate(self, os: Any) -> None:
        try:
            self.mStart.generate(os)
            os.write("/")
            if self.mUseDuration:
                if self.mDuration:
                    self.mDuration.generate(os)
            else:
                if self.mEnd:
                    self.mEnd.generate(os)
        except Exception:
            pass

    def writeXML(self, node: Any, namespace: Any) -> None:
        start = XML.SubElement(node, xmlutils.makeTag(namespace, xmldefinitions.period_start))
        start.text = self.mStart.getXMLText()
        if self.mUseDuration:
            duration = XML.SubElement(node, xmlutils.makeTag(namespace, xmldefinitions.period_duration))
            if self.mDuration:
                duration.text = self.mDuration.getText()
        else:
            end = XML.SubElement(node, xmlutils.makeTag(namespace, xmldefinitions.period_end))
            if self.mEnd:
                end.text = self.mEnd.getXMLText()

    def parseJSON(self, jobject: Any) -> None:
        self.parse("%s/%s" % tuple(jobject), True)

    def writeJSON(self, jobject: list) -> None:
        value = [self.mStart.getXMLText()]
        if self.mUseDuration:
            if self.mDuration:
                value.append(self.mDuration.getText())
        else:
            if self.mEnd:
                value.append(self.mEnd.getXMLText())
        jobject.append(value)

    def getStart(self) -> DateTime:
        return self.mStart

    def getEnd(self) -> DateTime:
        if self.mEnd is None:
            self.mEnd = self.mStart + self.mDuration
        return self.mEnd

    def getDuration(self) -> Duration:
        if self.mDuration is None:
            self.mDuration = self.mEnd - self.mStart
        return self.mDuration

    def getUseDuration(self) -> bool:
        return self.mUseDuration

    def setUseDuration(self, use: bool) -> None:
        self.mUseDuration = use
        if self.mUseDuration and self.mDuration is None:
            self.getDuration()
        elif not self.mUseDuration and self.mEnd is None:
            self.getEnd()

    def isDateWithinPeriod(self, dt: DateTime) -> bool:
        return dt >= self.mStart and dt < self.getEnd()

    def isDateBeforePeriod(self, dt: DateTime) -> bool:
        return dt < self.mStart

    def isDateAfterPeriod(self, dt: DateTime) -> bool:
        return dt >= self.getEnd()

    def isPeriodOverlap(self, p: "Period") -> bool:
        return not (self.mStart >= p.getEnd() or self.getEnd() <= p.mStart)

    def adjustToUTC(self) -> None:
        self.mStart.adjustToUTC()
        self.getEnd().adjustToUTC()

    def describeDuration(self) -> str:
        return ""