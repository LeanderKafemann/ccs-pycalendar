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
from typing import Any, Dict, List, Type, Union
from pycalendar.parameter import Parameter
from pycalendar.datetime import DateTime
from pycalendar.duration import Duration
from pycalendar.icalendar import definitions
from pycalendar.icalendar.component import Component
from pycalendar.icalendar.property import Property
from pycalendar.icalendar.validation import ICALENDAR_VALUE_CHECKS
from pycalendar.value import Value

class VAlarm(Component):
    sActionMap: Dict[str, int] = {
        definitions.cICalProperty_ACTION_AUDIO: definitions.eAction_VAlarm_Audio,
        definitions.cICalProperty_ACTION_DISPLAY: definitions.eAction_VAlarm_Display,
        definitions.cICalProperty_ACTION_EMAIL: definitions.eAction_VAlarm_Email,
        definitions.cICalProperty_ACTION_PROCEDURE: definitions.eAction_VAlarm_Procedure,
        definitions.cICalProperty_ACTION_URI: definitions.eAction_VAlarm_URI,
        definitions.cICalProperty_ACTION_NONE: definitions.eAction_VAlarm_None,
    }

    sActionValueMap: Dict[int, str] = {
        definitions.eAction_VAlarm_Audio: definitions.cICalProperty_ACTION_AUDIO,
        definitions.eAction_VAlarm_Display: definitions.cICalProperty_ACTION_DISPLAY,
        definitions.eAction_VAlarm_Email: definitions.cICalProperty_ACTION_EMAIL,
        definitions.eAction_VAlarm_Procedure: definitions.cICalProperty_ACTION_PROCEDURE,
        definitions.eAction_VAlarm_URI: definitions.cICalProperty_ACTION_URI,
        definitions.eAction_VAlarm_None: definitions.cICalProperty_ACTION_NONE,
    }

    class VAlarmAction(object):
        propertyCardinality_1: tuple = ()
        propertyCardinality_1_Fix_Empty: tuple = ()
        propertyCardinality_0_1: tuple = ()
        propertyCardinality_1_More: tuple = ()

        mType: int

        def __init__(self, type: int) -> None:
            self.mType = type

        def duplicate(self) -> "VAlarm.VAlarmAction":
            return VAlarm.VAlarmAction(self.mType)

        def load(self, valarm: "VAlarm") -> None:
            pass

        def add(self, valarm: "VAlarm") -> None:
            pass

        def remove(self, valarm: "VAlarm") -> None:
            pass

        def getType(self) -> int:
            return self.mType

    class VAlarmAudio(VAlarmAction):
        propertyCardinality_1: tuple = (
            definitions.cICalProperty_ACTION,
            definitions.cICalProperty_TRIGGER,
        )
        propertyCardinality_0_1: tuple = (
            definitions.cICalProperty_DURATION,
            definitions.cICalProperty_REPEAT,
            definitions.cICalProperty_ATTACH,
            definitions.cICalProperty_ACKNOWLEDGED,
        )
        mSpeakText: str

        def __init__(self, speak: str = "") -> None:
            super().__init__(type=definitions.eAction_VAlarm_Audio)
            self.mSpeakText = speak

        def duplicate(self) -> "VAlarm.VAlarmAudio":
            return VAlarm.VAlarmAudio(self.mSpeakText)

        def load(self, valarm: "VAlarm") -> None:
            self.mSpeakText = valarm.loadValueString(definitions.cICalProperty_ACTION_X_SPEAKTEXT)

        def add(self, valarm: "VAlarm") -> None:
            self.remove(valarm)
            prop = Property(definitions.cICalProperty_ACTION_X_SPEAKTEXT, self.mSpeakText)
            valarm.addProperty(prop)

        def remove(self, valarm: "VAlarm") -> None:
            valarm.removeProperties(definitions.cICalProperty_ACTION_X_SPEAKTEXT)

        def isSpeakText(self) -> bool:
            return len(self.mSpeakText) != 0

        def getSpeakText(self) -> str:
            return self.mSpeakText

    class VAlarmDisplay(VAlarmAction):
        propertyCardinality_1: tuple = (
            definitions.cICalProperty_ACTION,
            definitions.cICalProperty_TRIGGER,
        )
        propertyCardinality_1_Fix_Empty: tuple = (
            definitions.cICalProperty_DESCRIPTION,
        )
        propertyCardinality_0_1: tuple = (
            definitions.cICalProperty_DURATION,
            definitions.cICalProperty_REPEAT,
            definitions.cICalProperty_ACKNOWLEDGED,
        )
        mDescription: str

        def __init__(self, description: str = "") -> None:
            super().__init__(type=definitions.eAction_VAlarm_Display)
            self.mDescription = description

        def duplicate(self) -> "VAlarm.VAlarmDisplay":
            return VAlarm.VAlarmDisplay(self.mDescription)

        def load(self, valarm: "VAlarm") -> None:
            self.mDescription = valarm.loadValueString(definitions.cICalProperty_DESCRIPTION)

        def add(self, valarm: "VAlarm") -> None:
            self.remove(valarm)
            prop = Property(definitions.cICalProperty_DESCRIPTION, self.mDescription)
            valarm.addProperty(prop)

        def remove(self, valarm: "VAlarm") -> None:
            valarm.removeProperties(definitions.cICalProperty_DESCRIPTION)

        def getDescription(self) -> str:
            return self.mDescription

    class VAlarmEmail(VAlarmAction):
        propertyCardinality_1: tuple = (
            definitions.cICalProperty_ACTION,
            definitions.cICalProperty_TRIGGER,
        )
        propertyCardinality_1_Fix_Empty: tuple = (
            definitions.cICalProperty_DESCRIPTION,
            definitions.cICalProperty_SUMMARY,
        )
        propertyCardinality_0_1: tuple = (
            definitions.cICalProperty_DURATION,
            definitions.cICalProperty_REPEAT,
            definitions.cICalProperty_ACKNOWLEDGED,
        )
        propertyCardinality_1_More: tuple = (
            definitions.cICalProperty_ATTENDEE,
        )
        mDescription: str
        mSummary: str
        mAttendees: List[str]

        def __init__(self, description: str = "", summary: str = "", attendees: Union[List[str], None] = None) -> None:
            super().__init__(type=definitions.eAction_VAlarm_Email)
            self.mDescription = description
            self.mSummary = summary
            self.mAttendees = attendees if attendees is not None else []

        def duplicate(self) -> "VAlarm.VAlarmEmail":
            return VAlarm.VAlarmEmail(self.mDescription, self.mSummary, self.mAttendees[:])

        def load(self, valarm: "VAlarm") -> None:
            self.mDescription = valarm.loadValueString(definitions.cICalProperty_DESCRIPTION)
            self.mSummary = valarm.loadValueString(definitions.cICalProperty_SUMMARY)
            self.mAttendees = []
            if valarm.hasProperty(definitions.cICalProperty_ATTENDEE):
                range = valarm.getProperties().get(definitions.cICalProperty_ATTENDEE, ())
                for iter in range:
                    attendee = iter.getCalAddressValue()
                    if attendee is not None:
                        self.mAttendees.append(attendee.getValue())

        def add(self, valarm: "VAlarm") -> None:
            self.remove(valarm)
            prop = Property(definitions.cICalProperty_DESCRIPTION, self.mDescription)
            valarm.addProperty(prop)
            prop = Property(definitions.cICalProperty_SUMMARY, self.mSummary)
            valarm.addProperty(prop)
            for iter in self.mAttendees:
                prop = Property(definitions.cICalProperty_ATTENDEE, iter, Value.VALUETYPE_CALADDRESS)
                valarm.addProperty(prop)

        def remove(self, valarm: "VAlarm") -> None:
            valarm.removeProperties(definitions.cICalProperty_DESCRIPTION)
            valarm.removeProperties(definitions.cICalProperty_SUMMARY)
            valarm.removeProperties(definitions.cICalProperty_ATTENDEE)

        def getDescription(self) -> str:
            return self.mDescription

        def getSummary(self) -> str:
            return self.mSummary

        def getAttendees(self) -> List[str]:
            return self.mAttendees

    class VAlarmUnknown(VAlarmAction):
        propertyCardinality_1: tuple = (
            definitions.cICalProperty_ACTION,
            definitions.cICalProperty_TRIGGER,
        )
        propertyCardinality_0_1: tuple = (
            definitions.cICalProperty_DURATION,
            definitions.cICalProperty_REPEAT,
            definitions.cICalProperty_ACKNOWLEDGED,
        )

        def __init__(self) -> None:
            super().__init__(type=definitions.eAction_VAlarm_Unknown)

        def duplicate(self) -> "VAlarm.VAlarmUnknown":
            return VAlarm.VAlarmUnknown()

    class VAlarmURI(VAlarmAction):
        propertyCardinality_1: tuple = (
            definitions.cICalProperty_ACTION,
            definitions.cICalProperty_TRIGGER,
            definitions.cICalProperty_URL,
        )
        propertyCardinality_0_1: tuple = (
            definitions.cICalProperty_DURATION,
            definitions.cICalProperty_REPEAT,
            definitions.cICalProperty_ACKNOWLEDGED,
        )
        mURI: str

        def __init__(self, uri: str = "") -> None:
            super().__init__(type=definitions.eAction_VAlarm_URI)
            self.mURI = uri

        def duplicate(self) -> "VAlarm.VAlarmURI":
            return VAlarm.VAlarmURI(self.mURI)

        def load(self, valarm: "VAlarm") -> None:
            self.mURI = valarm.loadValueString(definitions.cICalProperty_URL)

        def add(self, valarm: "VAlarm") -> None:
            self.remove(valarm)
            prop = Property(definitions.cICalProperty_URL, self.mURI)
            valarm.addProperty(prop)

        def remove(self, valarm: "VAlarm") -> None:
            valarm.removeProperties(definitions.cICalProperty_URL)

        def getURI(self) -> str:
            return self.mURI

    class VAlarmNone(VAlarmAction):
        propertyCardinality_1: tuple = (
            definitions.cICalProperty_ACTION,
        )

        def __init__(self) -> None:
            super().__init__(type=definitions.eAction_VAlarm_None)

        def duplicate(self) -> "VAlarm.VAlarmNone":
            return VAlarm.VAlarmNone()

    sActionToAlarmMap: Dict[int, Type["VAlarmAction"]] = {
        definitions.eAction_VAlarm_Audio: VAlarmAudio,
        definitions.eAction_VAlarm_Display: VAlarmDisplay,
        definitions.eAction_VAlarm_Email: VAlarmEmail,
        definitions.eAction_VAlarm_URI: VAlarmURI,
        definitions.eAction_VAlarm_None: VAlarmNone,
    }

    propertyValueChecks: Any = ICALENDAR_VALUE_CHECKS

    mAction: int
    mTriggerAbsolute: bool
    mTriggerOnStart: bool
    mTriggerOn: DateTime
    mTriggerBy: Duration
    mRepeats: int
    mRepeatInterval: Duration
    mStatusInit: bool
    mAlarmStatus: int
    mLastTrigger: DateTime
    mNextTrigger: DateTime
    mDoneCount: int
    mActionData: "VAlarmAction"

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent=parent)
        self.mAction = definitions.eAction_VAlarm_Display
        self.mTriggerAbsolute = False
        self.mTriggerOnStart = True
        self.mTriggerOn = DateTime()
        self.mTriggerBy = Duration()
        self.mTriggerBy.setDuration(60 * 60)
        self.mRepeats = 0
        self.mRepeatInterval = Duration()
        self.mRepeatInterval.setDuration(5 * 60)
        self.mStatusInit = False
        self.mAlarmStatus = definitions.eAlarm_Status_Pending
        self.mLastTrigger = DateTime()
        self.mNextTrigger = DateTime()
        self.mDoneCount = 0
        self.mActionData = VAlarm.VAlarmDisplay("")

    def duplicate(self, parent: Any = None) -> "VAlarm":
        other = super().duplicate(parent=parent)
        other.mAction = self.mAction
        other.mTriggerAbsolute = self.mTriggerAbsolute
        other.mTriggerOn = self.mTriggerOn.duplicate()
        other.mTriggerBy = self.mTriggerBy.duplicate()
        other.mTriggerOnStart = self.mTriggerOnStart
        other.mRepeats = self.mRepeats
        other.mRepeatInterval = self.mRepeatInterval.duplicate()
        other.mAlarmStatus = self.mAlarmStatus
        if self.mLastTrigger is not None:
            other.mLastTrigger = self.mLastTrigger.duplicate()
        if self.mNextTrigger is not None:
            other.mNextTrigger = self.mNextTrigger.duplicate()
        other.mDoneCount = self.mDoneCount
        other.mActionData = self.mActionData.duplicate()
        return other

    def getMimeComponentName(self) -> Union[str, None]:
        return None

    def getType(self) -> str:
        return definitions.cICalComponent_VALARM

    def getAction(self) -> int:
        return self.mAction

    def getActionData(self) -> "VAlarmAction":
        return self.mActionData

    def isTriggerAbsolute(self) -> bool:
        return self.mTriggerAbsolute

    def getTriggerOn(self) -> DateTime:
        return self.mTriggerOn

    def getTriggerDuration(self) -> Duration:
        return self.mTriggerBy

    def isTriggerOnStart(self) -> bool:
        return self.mTriggerOnStart

    def getRepeats(self) -> int:
        return self.mRepeats

    def getInterval(self) -> Duration:
        return self.mRepeatInterval

    def added(self) -> None:
        super().added()

    def removed(self) -> None:
        super().removed()

    def changed(self) -> None:
        self.mStatusInit = False

    def finalise(self) -> None:
        super().finalise()
        temp = self.loadValueString(definitions.cICalProperty_ACTION)
        if temp is not None:
            self.mAction = VAlarm.sActionMap.get(temp, definitions.eAction_VAlarm_Unknown)
            self.loadAction()
        if self.hasProperty(definitions.cICalProperty_TRIGGER):
            temp1 = self.loadValueDateTime(definitions.cICalProperty_TRIGGER)
            temp2 = self.loadValueDuration(definitions.cICalProperty_TRIGGER)
            if temp1 is not None:
                self.mTriggerAbsolute = True
                self.mTriggerOn = temp1
            elif temp2 is not None:
                self.mTriggerAbsolute = False
                self.mTriggerBy = temp2
                prop = self.findFirstProperty(definitions.cICalProperty_TRIGGER)
                if prop.hasParameter(definitions.cICalParameter_RELATED):
                    temp = prop.getParameterValue(definitions.cICalParameter_RELATED)
                    if temp == definitions.cICalParameter_RELATED_START:
                        self.mTriggerOnStart = True
                    elif temp == definitions.cICalParameter_RELATED_END:
                        self.mTriggerOnStart = False
                else:
                    self.mTriggerOnStart = True
        temp = self.loadValueInteger(definitions.cICalProperty_REPEAT)
        if temp is not None:
            self.mRepeats = temp
        temp = self.loadValueDuration(definitions.cICalProperty_DURATION)
        if temp is not None:
            self.mRepeatInterval = temp
        self.mMapKey = "%s:%s" % (self.mAction, self.mTriggerOn if self.mTriggerAbsolute else self.mTriggerBy,)
        status = self.loadValueString(definitions.cICalProperty_ALARM_X_ALARMSTATUS)
        if status is not None:
            if status == definitions.cICalProperty_ALARM_X_ALARMSTATUS_PENDING:
                self.mAlarmStatus = definitions.eAlarm_Status_Pending
            elif status == definitions.cICalProperty_ALARM_X_ALARMSTATUS_COMPLETED:
                self.mAlarmStatus = definitions.eAlarm_Status_Completed
            elif status == definitions.cICalProperty_ALARM_X_ALARMSTATUS_DISABLED:
                self.mAlarmStatus = definitions.eAlarm_Status_Disabled
            else:
                self.mAlarmStatus = definitions.eAlarm_Status_Pending
        temp = self.loadValueDateTime(definitions.cICalProperty_ALARM_X_LASTTRIGGER)
        if temp is not None:
            self.mLastTrigger = temp

    def validate(self, doFix: bool = False) -> Any:
        self.propertyCardinality_1 = self.mActionData.propertyCardinality_1
        self.propertyCardinality_1_Fix_Empty = self.mActionData.propertyCardinality_1_Fix_Empty
        self.propertyCardinality_0_1 = self.mActionData.propertyCardinality_0_1
        self.propertyCardinality_1_More = self.mActionData.propertyCardinality_1_More
        fixed, unfixed = super().validate(doFix)
        if self.hasProperty(definitions.cICalProperty_DURATION) ^ self.hasProperty(definitions.cICalProperty_REPEAT):
            logProblem = "[%s] Properties must be present together: %s, %s" % (
                self.getType(),
                definitions.cICalProperty_DURATION,
                definitions.cICalProperty_REPEAT,
            )
            unfixed.append(logProblem)
        return fixed, unfixed

    def editStatus(self, status: int) -> None:
        self.removeProperties(definitions.cICalProperty_ALARM_X_ALARMSTATUS)
        self.mAlarmStatus = status
        status_txt = ""
        if self.mAlarmStatus == definitions.eAlarm_Status_Pending:
            status_txt = definitions.cICalProperty_ALARM_X_ALARMSTATUS_PENDING
        elif self.mAlarmStatus == definitions.eAlarm_Status_Completed:
            status_txt = definitions.cICalProperty_ALARM_X_ALARMSTATUS_COMPLETED
        elif self.mAlarmStatus == definitions.eAlarm_Status_Disabled:
            status_txt = definitions.cICalProperty_ALARM_X_ALARMSTATUS_DISABLED
        self.addProperty(Property(definitions.cICalProperty_ALARM_X_ALARMSTATUS, status_txt))

    def editAction(self, action: int, data: "VAlarmAction") -> None:
        self.removeProperties(definitions.cICalProperty_ACTION)
        self.mActionData.remove(self)
        self.mActionData = None
        self.mAction = action
        self.mActionData = data
        action_txt = VAlarm.sActionValueMap.get(self.mAction, definitions.cICalProperty_ACTION_PROCEDURE)
        prop = Property(definitions.cICalProperty_ACTION, action_txt)
        self.addProperty(prop)
        self.mActionData.add(self)

    def editTriggerOn(self, dt: DateTime) -> None:
        self.removeProperties(definitions.cICalProperty_TRIGGER)
        self.mTriggerAbsolute = True
        self.mTriggerOn = dt
        prop = Property(definitions.cICalProperty_TRIGGER, dt)
        self.addProperty(prop)

    def editTriggerBy(self, duration: Duration, trigger_start: bool) -> None:
        self.removeProperties(definitions.cICalProperty_TRIGGER)
        self.mTriggerAbsolute = False
        self.mTriggerBy = duration
        self.mTriggerOnStart = trigger_start
        prop = Property(definitions.cICalProperty_TRIGGER, duration)
        attr = Parameter(
            definitions.cICalParameter_RELATED,
            (
                definitions.cICalParameter_RELATED_START,
                definitions.cICalParameter_RELATED_END
            )[not trigger_start]
        )
        prop.addParameter(attr)
        self.addProperty(prop)

    def editRepeats(self, repeat: int, interval: Duration) -> None:
        self.removeProperties(definitions.cICalProperty_REPEAT)
        self.removeProperties(definitions.cICalProperty_DURATION)
        self.mRepeats = repeat
        self.mRepeatInterval = interval
        if self.mRepeats > 0:
            self.addProperty(Property(definitions.cICalProperty_REPEAT, repeat))
            self.addProperty(Property(definitions.cICalProperty_DURATION, interval))

    def getAlarmStatus(self) -> int:
        return self.mAlarmStatus

    def getNextTrigger(self, dt: DateTime) -> None:
        if not self.mStatusInit:
            self.initNextTrigger()
        dt.copy(self.mNextTrigger)

    def alarmTriggered(self, dt: DateTime) -> bool:
        self.removeProperties(definitions.cICalProperty_ALARM_X_LASTTRIGGER)
        self.removeProperties(definitions.cICalProperty_ALARM_X_ALARMSTATUS)
        self.mLastTrigger.copy(dt)
        if self.mDoneCount < self.mRepeats:
            self.mNextTrigger = self.mLastTrigger + self.mRepeatInterval
            dt.copy(self.mNextTrigger)
            self.mDoneCount += 1
            self.mAlarmStatus = definitions.eAlarm_Status_Pending
        else:
            self.mAlarmStatus = definitions.eAlarm_Status_Completed
        self.addProperty(Property(definitions.cICalProperty_ALARM_X_LASTTRIGGER, dt))
        status = ""
        if self.mAlarmStatus == definitions.eAlarm_Status_Pending:
            status = definitions.cICalProperty_ALARM_X_ALARMSTATUS_PENDING
        elif self.mAlarmStatus == definitions.eAlarm_Status_Completed:
            status = definitions.cICalProperty_ALARM_X_ALARMSTATUS_COMPLETED
        elif self.mAlarmStatus == definitions.eAlarm_Status_Disabled:
            status = definitions.cICalProperty_ALARM_X_ALARMSTATUS_DISABLED
        self.addProperty(Property(definitions.cICalProperty_ALARM_X_ALARMSTATUS, status))
        return self.mAlarmStatus == definitions.eAlarm_Status_Pending

    def loadAction(self) -> None:
        self.mActionData = None
        self.mActionData = VAlarm.sActionToAlarmMap.get(self.mAction, VAlarm.VAlarmUnknown)()
        self.mActionData.load(self)

    def initNextTrigger(self) -> None:
        if self.mAlarmStatus == definitions.eAlarm_Status_Completed:
            return
        self.mStatusInit = True
        nowutc = DateTime.getNowUTC()
        self.mDoneCount = 0
        trigger = DateTime()
        self.getFirstTrigger(trigger)
        while self.mDoneCount < self.mRepeats:
            next_trigger = trigger + self.mRepeatInterval
            if next_trigger > nowutc:
                break
            self.mDoneCount += 1
            trigger = next_trigger
        if trigger == self.mLastTrigger or (nowutc - trigger).getTotalSeconds() > 24 * 60 * 60:
            if self.mDoneCount == self.mRepeats:
                self.mAlarmStatus = definitions.eAlarm_Status_Completed
                return
            else:
                trigger = trigger + self.mRepeatInterval
                self.mDoneCount += 1
        self.mNextTrigger = trigger

    def getFirstTrigger(self, dt: DateTime) -> None:
        if self.isTriggerAbsolute():
            dt.copy(self.getTriggerOn())
        else:
            owner = self.getEmbedder()
            if owner is not None:
                trigger = (owner.getStart(), owner.getEnd())[not self.isTriggerOnStart()]
                dt.copy(trigger + self.getTriggerDuration())

Component.registerComponent(definitions.cICalComponent_VALARM, VAlarm)