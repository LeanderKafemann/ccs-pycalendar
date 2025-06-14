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

from typing import Any, Dict, Optional, Tuple

class OutputFilter(object):
    mType: Any
    mAllSubComponents: bool
    mSubComponents: Optional[Dict[Any, "OutputFilter"]]
    mAllProperties: bool
    mProperties: Optional[Dict[Any, Any]]

    def __init__(self, type: Any) -> None:
        self.mType = type
        self.mAllSubComponents = False
        self.mSubComponents: Optional[Dict[Any, "OutputFilter"]] = None
        self.mAllProperties = False
        self.mProperties: Optional[Dict[Any, Any]] = None

    def getType(self) -> Any:
        return self.mType

    def testComponent(self, oftype: Any) -> bool:
        return self.mType == oftype

    def isAllSubComponents(self) -> bool:
        return self.mAllSubComponents

    def setAllSubComponents(self) -> None:
        self.mAllSubComponents = True
        self.mSubComponents = None

    def addSubComponent(self, comp: "OutputFilter") -> None:
        if self.mSubComponents is None:
            self.mSubComponents = {}
        self.mSubComponents[comp.getType()] = comp

    def testSubComponent(self, oftype: Any) -> bool:
        return self.mAllSubComponents or (self.mSubComponents is not None and oftype in self.mSubComponents)

    def hasSubComponentFilters(self) -> bool:
        return self.mSubComponents is not None

    def getSubComponentFilter(self, type: Any) -> Optional["OutputFilter"]:
        if self.mSubComponents is not None:
            return self.mSubComponents.get(type, None)
        else:
            return None

    def isAllProperties(self) -> bool:
        return self.mAllProperties

    def setAllProperties(self) -> None:
        self.mAllProperties = True
        self.mProperties = None

    def addProperty(self, name: Any, no_value: Any) -> None:
        if self.mProperties is None:
            self.mProperties = {}
        self.mProperties[name] = no_value

    def hasPropertyFilters(self) -> bool:
        return self.mProperties is not None

    def testPropertyValue(self, name: Any) -> Tuple[bool, Any]:
        if self.mAllProperties:
            return True, False
        if self.mProperties is None:
            return False, False
        result = self.mProperties.get(name, None)
        return result is not None, result