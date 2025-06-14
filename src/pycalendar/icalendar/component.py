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
from typing import Any, ClassVar, Dict, Optional, Set, Type, Union
from pycalendar import stringutils
from pycalendar.componentbase import ComponentBase
from pycalendar.datetime import DateTime
from pycalendar.icalendar import definitions
from pycalendar.icalendar.property import Property
import os
import time
import uuid

class Component(ComponentBase):
    uid_ctr: ClassVar[int] = 1
    mapper: ClassVar[Dict[str, Type["Component"]]] = {}

    sComponentType: ClassVar[Optional[Type["Component"]]] = None
    sPropertyType: ClassVar[Type[Property]] = Property

    mUID: str
    mSeq: int
    mOriginalSeq: int
    mChanged: bool

    @classmethod
    def registerComponent(cls, name: str, comptype: Type["Component"]) -> None:
        cls.mapper[name] = comptype

    @classmethod
    def makeComponent(cls, compname: str, parent: Any) -> "Component":
        try:
            return cls.mapper[compname](parent=parent)
        except KeyError:
            return cls.mapper[definitions.cICalComponent_UNKNOWN](parent=parent, comptype=compname)

    def __init__(self, parent: Optional[Any] = None) -> None:
        super(Component, self).__init__(parent)
        self.mUID: str = ""
        self.mSeq: int = 0
        self.mOriginalSeq: int = 0
        self.mChanged: bool = False

    def duplicate(self, parent: Optional[Any] = None, **args: Any) -> "Component":
        other = super(Component, self).duplicate(parent=parent, **args)
        other.mUID = self.mUID
        other.mSeq = self.mSeq
        other.mOriginalSeq = self.mOriginalSeq
        other.mChanged = self.mChanged
        return other

    def __repr__(self) -> str:
        return "%s: UID: %s" % (self.getType(), self.getMapKey(),)

    def getMimeComponentName(self) -> str:
        raise NotImplementedError

    def getMapKey(self) -> str:
        if hasattr(self, "mMapKey"):
            return self.mMapKey
        elif self.mUID:
            return self.mUID
        else:
            self.mMapKey = str(uuid.uuid4())
            return self.mMapKey

    def getSortKey(self) -> str:
        return self.getMapKey()

    def getMasterKey(self) -> str:
        return self.mUID

    def getUID(self) -> str:
        return self.mUID

    def setUID(self, uid: Optional[str]) -> None:
        if uid:
            self.mUID = uid
        else:
            lhs_txt = ""
            lhs_txt += str(time.time())
            lhs_txt += "."
            lhs_txt += str(os.getpid())
            lhs_txt += "."
            lhs_txt += str(Component.uid_ctr)
            Component.uid_ctr += 1
            lhs = stringutils.md5digest(lhs_txt)
            rhs = None
            from pycalendar.icalendar.calendar import Calendar
            domain = Calendar.sDomain
            domain += str(Component.uid_ctr)
            rhs = stringutils.md5digest(domain)
            new_uid = lhs
            new_uid += "@"
            new_uid += rhs
            self.mUID = new_uid
        self.removeProperties(definitions.cICalProperty_UID)
        prop = Property(definitions.cICalProperty_UID, self.mUID)
        self.addProperty(prop)

    def getSeq(self) -> int:
        return self.mSeq

    def setSeq(self, seq: int) -> None:
        self.mSeq = seq
        self.removeProperties(definitions.cICalProperty_SEQUENCE)
        prop = Property(definitions.cICalProperty_SEQUENCE, self.mSeq)
        self.addProperty(prop)

    def getOriginalSeq(self) -> int:
        return self.mOriginalSeq

    def getChanged(self) -> bool:
        return self.mChanged

    def setChanged(self, changed: bool) -> None:
        self.mChanged = changed

    def initDTSTAMP(self) -> None:
        self.removeProperties(definitions.cICalProperty_DTSTAMP)
        prop = Property(definitions.cICalProperty_DTSTAMP, DateTime.getNowUTC())
        self.addProperty(prop)

    def updateLastModified(self) -> None:
        self.removeProperties(definitions.cICalProperty_LAST_MODIFIED)
        prop = Property(definitions.cICalProperty_LAST_MODIFIED, DateTime.getNowUTC())
        self.addProperty(prop)

    def finalise(self) -> None:
        temps = self.loadValueString(definitions.cICalProperty_UID)
        if temps is not None:
            self.mUID = temps
        temp = self.loadValueInteger(definitions.cICalProperty_SEQUENCE)
        if temp is not None:
            self.mSeq = temp
        self.mOriginalSeq = self.mSeq

    def canGenerateInstance(self) -> bool:
        return True

    def getTimezones(self, tzids: Set[str]) -> None:
        for props in self.mProperties.values():
            for prop in props:
                dtv = prop.getDateTimeValue()
                if dtv is not None:
                    if dtv.getValue().getTimezoneID():
                        tzids.add(dtv.getValue().getTimezoneID())

Component.sComponentType = Component