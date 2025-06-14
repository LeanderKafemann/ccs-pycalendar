from io import StringIO
from pycalendar import xmldefinitions, xmlutils
from pycalendar.datetimevalue import DateTimeValue
from pycalendar.periodvalue import PeriodValue
from pycalendar.value import Value
import xml.etree.cElementTree as XML
from pycalendar.exceptions import InvalidComponent, ErrorBase
from typing import (
    Self, Optional, Any, Callable, Dict, List, Tuple, Union
)

class ComponentBase(object):
    propertyCardinality_1: Tuple[str, ...] = ()
    propertyCardinality_1_Fix_Empty: Tuple[str, ...] = ()
    propertyCardinality_0_1: Tuple[str, ...] = ()
    propertyCardinality_1_More: Tuple[str, ...] = ()

    propertyValueChecks: Optional[Dict[str, Callable[[Any], bool]]] = None

    sortSubComponents: bool = True

    sComponentType: Any = None
    sPropertyType: Any = None

    mParentComponent: Optional["ComponentBase"]
    mComponents: List["ComponentBase"]
    mProperties: Dict[str, List[Any]]
    cardinalityChecks: Tuple[
        Callable[[List[str], List[str], bool], None],
        Callable[[List[str], List[str], bool], None],
        Callable[[List[str], List[str], bool], None],
        Callable[[List[str], List[str], bool], None],
    ]

    def __init__(self, parent: Optional["ComponentBase"] = None) -> None:
        self.mParentComponent: Optional["ComponentBase"] = parent
        self.mComponents: List["ComponentBase"] = []
        self.mProperties: Dict[str, List[Any]] = {}

        self.cardinalityChecks = (
            self.check_cardinality_1,
            self.check_cardinality_1_Fix_Empty,
            self.check_cardinality_0_1,
            self.check_cardinality_1_More,
        )

    def duplicate(self, **args) -> Self:
        other = self.__class__(**args)
        for component in self.mComponents:
            other.addComponent(component.duplicate(parent=other))
        other.mProperties = {}
        for propname, props in self.mProperties.items():
            other.mProperties[propname] = [i.duplicate() for i in props]
        return other

    def __str__(self) -> str:
        return self.getText()

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ComponentBase):
            return False
        return (
            self.getType() == other.getType()
            and self.compareProperties(other)
            and self.compareComponents(other)
        )

    def getType(self) -> str:
        raise NotImplementedError

    def getBeginDelimiter(self) -> str:
        return "BEGIN:" + self.getType()

    def getEndDelimiter(self) -> str:
        return "END:" + self.getType()

    def getSortKey(self) -> str:
        return ""

    def getParentComponent(self) -> Optional["ComponentBase"]:
        return self.mParentComponent

    def setParentComponent(self, parent: Optional["ComponentBase"]) -> None:
        self.mParentComponent = parent

    def compareComponents(self, other: "ComponentBase") -> bool:
        mine = set(self.mComponents)
        theirs = set(other.mComponents)
        for item in mine:
            for another in theirs:
                if item == another:
                    theirs.remove(another)
                    break
            else:
                return False
        return len(theirs) == 0

    def getComponents(self, compname: Optional[str] = None) -> List["ComponentBase"]:
        compname = compname.upper() if compname else None
        return [
            component
            for component in self.mComponents
            if compname is None or component.getType().upper() == compname
        ]

    def getComponentByKey(self, key: Any) -> Optional["ComponentBase"]:
        for component in self.mComponents:
            if component.getMapKey() == key:
                return component
        return None

    def removeComponentByKey(self, key: Any) -> None:
        for component in self.mComponents:
            if component.getMapKey() == key:
                self.removeComponent(component)
                return

    def addComponent(self, component: "ComponentBase") -> None:
        self.mComponents.append(component)

    def hasComponent(self, compname: str) -> bool:
        return self.countComponents(compname) != 0

    def countComponents(self, compname: str) -> int:
        return len(self.getComponents(compname))

    def removeComponent(self, component: "ComponentBase") -> None:
        self.mComponents.remove(component)

    def removeAllComponent(self, compname: Optional[str] = None) -> None:
        if compname:
            compname = compname.upper()
            for component in tuple(self.mComponents):
                if component.getType().upper() == compname:
                    self.removeComponent(component)
        else:
            self.mComponents = []

    def sortedComponentNames(self) -> Tuple[str, ...]:
        return ()

    def compareProperties(self, other: "ComponentBase") -> bool:
        mine = set()
        for props in self.mProperties.values():
            mine.update(props)
        theirs = set()
        for props in other.mProperties.values():
            theirs.update(props)
        return mine == theirs

    def getProperties(self, propname: Optional[str] = None) -> Union[Dict[str, List[Any]], List[Any]]:
        return self.mProperties.get(propname.upper(), []) if propname else self.mProperties

    def setProperties(self, props: Dict[str, List[Any]]) -> None:
        self.mProperties = props

    def addProperty(self, prop: Any) -> None:
        self.mProperties.setdefault(prop.getName().upper(), []).append(prop)

    def hasProperty(self, propname: str) -> bool:
        return propname.upper() in self.mProperties

    def countProperty(self, propname: str) -> int:
        return len(self.mProperties.get(propname.upper(), []))

    def findFirstProperty(self, propname: str) -> Optional[Any]:
        return self.mProperties.get(propname.upper(), [None])[0]

    def removeProperty(self, prop: Any) -> None:
        key = prop.getName().upper()
        if key in self.mProperties:
            self.mProperties[key].remove(prop)
            if len(self.mProperties[key]) == 0:
                del self.mProperties[key]

    def removeProperties(self, propname: str) -> None:
        if propname.upper() in self.mProperties:
            del self.mProperties[propname.upper()]

    def getPropertyInteger(self, prop: str, type: Optional[Any] = None) -> Optional[int]:
        return self.loadValueInteger(prop, type)

    def getPropertyString(self, prop: str) -> Optional[str]:
        return self.loadValueString(prop)

    def getProperty(self, prop: str, value: Any) -> Any:
        return self.loadValue(prop, value)

    def finalise(self) -> None:
        raise NotImplemented

    def validate(self, doFix: bool = False) -> Tuple[List[str], List[str]]:
        fixed: List[str] = []
        unfixed: List[str] = []
        for check in self.cardinalityChecks:
            check(fixed, unfixed, doFix)
        if self.propertyValueChecks is not None:
            for properties in self.mProperties.values():
                for property in properties:
                    propname = property.getName().upper()
                    if propname in self.propertyValueChecks:
                        if not self.propertyValueChecks[propname](property):
                            logProblem = "[%s] Property value incorrect: %s" % (self.getType(), propname,)
                            unfixed.append(logProblem)
        for component in self.mComponents:
            morefixed, moreunfixed = component.validate(doFix)
            fixed.extend(morefixed)
            unfixed.extend(moreunfixed)
        return fixed, unfixed

    def check_cardinality_1(self, fixed: List[str], unfixed: List[str], doFix: bool) -> None:
        for propname in self.propertyCardinality_1:
            if self.countProperty(propname) != 1:
                logProblem = "[%s] Missing or too many required property: %s" % (self.getType(), propname)
                unfixed.append(logProblem)

    def check_cardinality_1_Fix_Empty(self, fixed: List[str], unfixed: List[str], doFix: bool) -> None:
        for propname in self.propertyCardinality_1_Fix_Empty:
            if self.countProperty(propname) > 1:
                logProblem = "[%s] Too many required property: %s" % (self.getType(), propname)
                unfixed.append(logProblem)
            elif self.countProperty(propname) == 0:
                logProblem = "[%s] Missing required property: %s" % (self.getType(), propname)
                if doFix:
                    self.addProperty(self.sPropertyType(propname, ""))
                    fixed.append(logProblem)
                else:
                    unfixed.append(logProblem)

    def check_cardinality_0_1(self, fixed: List[str], unfixed: List[str], doFix: bool) -> None:
        for propname in self.propertyCardinality_0_1:
            if self.countProperty(propname) > 1:
                logProblem = "[%s] Too many properties present: %s" % (self.getType(), propname)
                unfixed.append(logProblem)

    def check_cardinality_1_More(self, fixed: List[str], unfixed: List[str], doFix: bool) -> None:
        for propname in self.propertyCardinality_1_More:
            if not self.countProperty(propname) > 0:
                logProblem = "[%s] Missing required property: %s" % (self.getType(), propname)
                unfixed.append(logProblem)

    def getText(self) -> str:
        s = StringIO()
        self.generate(s)
        return s.getvalue()

    def generate(self, os: Any) -> None:
        os.write(self.getBeginDelimiter())
        os.write("\r\n")
        self.writeProperties(os)
        self.writeComponents(os)
        os.write(self.getEndDelimiter())
        os.write("\r\n")

    def generateFiltered(self, os: Any, filter: Any) -> None:
        os.write(self.getBeginDelimiter())
        os.write("\r\n")
        self.writePropertiesFiltered(os, filter)
        self.writeComponentsFiltered(os, filter)
        os.write(self.getEndDelimiter())
        os.write("\r\n")

    def writeXML(self, node: Any, namespace: Any) -> None:
        comp = XML.SubElement(node, xmlutils.makeTag(namespace, self.getType()))
        self.writePropertiesXML(comp, namespace)
        self.writeComponentsXML(comp, namespace)

    def writeXMLFiltered(self, node: Any, namespace: Any, filter: Any) -> None:
        comp = XML.SubElement(node, xmlutils.makeTag(namespace, self.getType()))
        self.writePropertiesFilteredXML(comp, namespace, filter)
        self.writeComponentsFilteredXML(comp, namespace, filter)

    @classmethod
    def parseJSON(cls, jobject: list, parent: Any, comp: Optional[Any] = None) -> Any:
        try:
            if comp is None:
                comp = cls.sComponentType.makeComponent(jobject[0].upper(), parent)
            for prop in jobject[1]:
                comp.addProperty(cls.sPropertyType.parseJSON(prop))
            for subcomp in jobject[2]:
                comp.addComponent(cls.sComponentType.parseJSON(subcomp, comp))
            comp.finalise()
            return comp
        except ErrorBase:
            raise
        except Exception as e:
            raise InvalidComponent("Invalid component: {}".format(e), jobject)

    def writeJSON(self, jobject: list) -> None:
        comp = [self.getType().lower(), [], []]
        self.writePropertiesJSON(comp[1])
        self.writeComponentsJSON(comp[2])
        jobject.append(comp)

    def writeJSONFiltered(self, jobject: list, filter: Any) -> None:
        comp = [self.getType().lower(), [], []]
        self.writePropertiesFilteredJSON(comp[1], filter)
        self.writeComponentsFilteredJSON(comp[2], filter)
        jobject.append(comp)

    def sortedComponents(self) -> List["ComponentBase"]:
        components = self.mComponents[:]
        sortedcomponents: List["ComponentBase"] = []
        orderedNames = self.sortedComponentNames()
        for name in orderedNames:
            namedcomponents = []
            for component in tuple(components):
                if component.getType().upper() == name:
                    namedcomponents.append(component)
                    components.remove(component)
            for component in sorted(namedcomponents, key=lambda x: x.getSortKey()):
                sortedcomponents.append(component)
        if self.sortSubComponents:
            remainder = sorted(components, key=lambda x: (x.getType().upper(), x.getSortKey(),))
        else:
            remainder = components
        for component in remainder:
            sortedcomponents.append(component)
        return sortedcomponents

    def writeComponents(self, os: Any) -> None:
        for component in self.sortedComponents():
            component.generate(os)

    def writeComponentsFiltered(self, os: Any, filter: Any) -> None:
        if filter.isAllSubComponents():
            self.writeComponents(os)
        elif filter.hasSubComponentFilters():
            for subcomp in self.sortedcomponents():
                subfilter = filter.getSubComponentFilter(subcomp.getType())
                if subfilter is not None:
                    subcomp.generateFiltered(os, subfilter)

    def writeComponentsXML(self, node: Any, namespace: Any) -> None:
        if self.mComponents:
            comps = XML.SubElement(node, xmlutils.makeTag(namespace, xmldefinitions.components))
            for component in self.sortedComponents():
                component.writeXML(comps, namespace)

    def writeComponentsFilteredXML(self, node: Any, namespace: Any, filter: Any) -> None:
        if self.mComponents:
            comps = XML.SubElement(node, xmlutils.makeTag(namespace, xmldefinitions.components))
            if filter.isAllSubComponents():
                self.writeXML(comps, namespace)
            elif filter.hasSubComponentFilters():
                for subcomp in self.sortedcomponents():
                    subfilter = filter.getSubComponentFilter(subcomp.getType())
                    if subfilter is not None:
                        subcomp.writeXMLFiltered(comps, namespace, subfilter)

    def writeComponentsJSON(self, jobject: list) -> None:
        if self.mComponents:
            for component in self.sortedComponents():
                component.writeJSON(jobject)

    def writeComponentsFilteredJSON(self, jobject: list, filter: Any) -> None:
        if self.mComponents:
            if filter.isAllSubComponents():
                self.writeJSON(jobject)
            elif filter.hasSubComponentFilters():
                for subcomp in self.sortedcomponents():
                    subfilter = filter.getSubComponentFilter(subcomp.getType())
                    if subfilter is not None:
                        subcomp.writeJSONFiltered(jobject, subfilter)

    def loadValue(self, value_name: str) -> Optional[Any]:
        if self.hasProperty(value_name):
            return self.findFirstProperty(value_name)
        return None

    def loadValueInteger(self, value_name: str, type: Optional[Any] = None) -> Optional[int]:
        if type:
            if self.hasProperty(value_name):
                if type == Value.VALUETYPE_INTEGER:
                    ivalue = self.findFirstProperty(value_name).getIntegerValue()
                    if ivalue is not None:
                        return ivalue.getValue()
                elif type == Value.VALUETYPE_UTC_OFFSET:
                    uvalue = self.findFirstProperty(value_name).getUTCOffsetValue()
                    if uvalue is not None:
                        return uvalue.getValue()
            return None
        else:
            return self.loadValueInteger(value_name, Value.VALUETYPE_INTEGER)

    def loadValueString(self, value_name: str) -> Optional[str]:
        if self.hasProperty(value_name):
            tvalue = self.findFirstProperty(value_name).getTextValue()
            if tvalue is not None:
                return tvalue.getValue()
        return None

    def loadValueDateTime(self, value_name: str) -> Optional[Any]:
        if self.hasProperty(value_name):
            dtvalue = self.findFirstProperty(value_name).getDateTimeValue()
            if dtvalue is not None:
                return dtvalue.getValue()
        return None

    def loadValueDuration(self, value_name: str) -> Optional[Any]:
        if self.hasProperty(value_name):
            dvalue = self.findFirstProperty(value_name).getDurationValue()
            if dvalue is not None:
                return dvalue.getValue()
        return None

    def loadValuePeriod(self, value_name: str) -> Optional[Any]:
        if self.hasProperty(value_name):
            pvalue = self.findFirstProperty(value_name).getPeriodValue()
            if pvalue is not None:
                return pvalue.getValue()
        return None

    def loadValueRRULE(self, value_name: str, value: Any, add: bool) -> bool:
        if self.hasProperty(value_name):
            items = self.getProperties()[value_name]
            for iter in items:
                rvalue = iter.getRecurrenceValue()
                if rvalue is not None:
                    if add:
                        value.addRule(rvalue.getValue())
                    else:
                        value.subtractRule(rvalue.getValue())
            return True
        else:
            return False

    def loadValueRDATE(self, value_name: str, value: Any, add: bool) -> bool:
        if self.hasProperty(value_name):
            for iter in self.getProperties(value_name):
                mvalue = iter.getMultiValue()
                if mvalue is not None:
                    for obj in mvalue.getValues():
                        if isinstance(obj, DateTimeValue):
                            if add:
                                value.addDT(obj.getValue())
                            else:
                                value.subtractDT(obj.getValue())
                        elif isinstance(obj, PeriodValue):
                            if add:
                                value.addPeriod(obj.getValue().getStart())
                            else:
                                value.subtractPeriod(obj.getValue().getStart())
            return True
        else:
            return False

    def sortedPropertyKeys(self) -> List[str]:
        keys = list(self.mProperties.keys())
        keys.sort()
        results: List[str] = []
        for skey in self.sortedPropertyKeyOrder():
            if skey in keys:
                results.append(skey)
                keys.remove(skey)
        results.extend(keys)
        return results

    def sortedPropertyKeyOrder(self) -> Tuple[str, ...]:
        return ()

    def writeProperties(self, os: Any) -> None:
        keys = self.sortedPropertyKeys()
        for key in keys:
            props = self.mProperties[key]
            for prop in props:
                prop.generate(os)

    def writePropertiesFiltered(self, os: Any, filter: Any) -> None:
        keys = self.sortedPropertyKeys()
        if filter.isAllProperties():
            for key in keys:
                for prop in self.getProperties(key):
                    prop.generate(os)
        elif filter.hasPropertyFilters():
            for key in keys:
                for prop in self.getProperties(key):
                    prop.generateFiltered(os, filter)

    def writePropertiesXML(self, node: Any, namespace: Any) -> None:
        properties = XML.SubElement(node, xmlutils.makeTag(namespace, xmldefinitions.properties))
        keys = self.sortedPropertyKeys()
        for key in keys:
            props = self.mProperties[key]
            for prop in props:
                prop.writeXML(properties, namespace)

    def writePropertiesFilteredXML(self, node: Any, namespace: Any, filter: Any) -> None:
        props = XML.SubElement(node, xmlutils.makeTag(namespace, xmldefinitions.properties))
        keys = self.sortedPropertyKeys()
        if filter.isAllProperties():
            for key in keys:
                for prop in self.getProperties(key):
                    prop.writeXML(props, namespace)
        elif filter.hasPropertyFilters():
            for key in keys:
                for prop in self.getProperties(key):
                    prop.writeXMLFiltered(props, namespace, filter)

    def writePropertiesJSON(self, jobject: list) -> None:
        keys = self.sortedPropertyKeys()
        for key in keys:
            props = self.mProperties[key]
            for prop in props:
                prop.writeJSON(jobject)

    def writePropertiesFilteredJSON(self, jobject: list, filter: Any) -> None:
        keys = self.sortedPropertyKeys()
        if filter.isAllProperties():
            for key in keys:
                for prop in self.getProperties(key):
                    prop.writeJSON(jobject)
        elif filter.hasPropertyFilters():
            for key in keys:
                for prop in self.getProperties(key):
                    prop.writeJSONFiltered(jobject, filter)

    def loadPrivateValue(self, value_name: str) -> Optional[str]:
        result = self.loadValueString(value_name)
        if result is not None:
            self.removeProperties(value_name)
        return result

    def writePrivateProperty(self, os: Any, key: str, value: Any) -> None:
        prop = self.sPropertyType(name=key, value=value)
        prop.generate(os)

    def editProperty(self, propname: str, propvalue: Any) -> None:
        self.removeProperties(propname)
        if propvalue:
            self.addProperty(self.sPropertyType(name=propname, value=propvalue))