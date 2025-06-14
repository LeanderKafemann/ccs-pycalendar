#!/usr/bin/env python
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
from __future__ import with_statement
from __future__ import print_function

from typing import Dict, Any, Set, List, Optional, Union
from pycalendar.icalendar.calendar import Calendar
from xml.etree.cElementTree import ParseError as XMLParseError
import io as StringIO
import getopt
import os
import rule
import sys
import tarfile
import urllib
import xml.etree.cElementTree as XML
import zone

__all__ = (
    "tzconvert",
)

class tzconvert(object):

    rules: Dict[str, rule.RuleSet]
    zones: Dict[str, "zone.Zone"]
    links: Dict[str, str]
    verbose: bool

    def __init__(self, verbose: bool = False) -> None:
        self.rules: Dict[str, rule.RuleSet] = {}
        self.zones: Dict[str, "zone.Zone"] = {}
        self.links: Dict[str, str] = {}
        self.verbose: bool = verbose

    def getZoneNames(self) -> Set[str]:
        return set(self.zones.keys())

    def parse(self, file: str) -> None:
        try:
            with open(file, "r") as f:
                ctr = 0
                for line in f:
                    ctr += 1
                    line = line[:-1]
                    while True:
                        if line.startswith("#") or len(line) == 0:
                            break
                        elif line.startswith("Rule"):
                            self.parseRule(line)
                            break
                        elif line.startswith("Zone"):
                            line = self.parseZone(line, f)
                            if line is None:
                                break
                        elif line.startswith("Link"):
                            self.parseLink(line)
                            break
                        elif len(line.strip()) != 0:
                            assert False, "Could not parse line %d from tzconvert file: '%s'" % (ctr, line,)
                        else:
                            break
        except Exception:
            print("Failed to parse file %s" % (file,))
            raise

    def parseRule(self, line: str) -> None:
        ruleitem = rule.Rule()
        ruleitem.parse(line)
        self.rules.setdefault(ruleitem.name, rule.RuleSet()).rules.append(ruleitem)

    def parseZone(self, line: str, f: Any) -> Optional[str]:
        osbuf = StringIO.StringIO()
        osbuf.write(line)
        last_line: Optional[str] = None
        for nextline in f:
            nextline = nextline[:-1]
            if nextline.startswith("\t") or nextline.startswith(" "):
                osbuf.write("\n")
                osbuf.write(nextline)
            elif nextline.startswith("#") or len(nextline) == 0:
                continue
            else:
                last_line = nextline
                break

        zoneitem = zone.Zone()
        zoneitem.parse(osbuf.getvalue())
        self.zones[zoneitem.name] = zoneitem

        return last_line

    def parseLink(self, line: str) -> None:
        splits = line.split()
        linkFrom = splits[1]
        linkTo = splits[2]
        self.links[linkTo] = linkFrom

    def parseWindowsAliases(self, aliases: str) -> None:
        try:
            with open(aliases) as xmlfile:
                xmlroot = XML.ElementTree(file=xmlfile).getroot()
        except (IOError, XMLParseError):
            raise ValueError("Unable to open or read windows alias file: {}".format(aliases))

        try:
            for elem in xmlroot.findall("./windowsZones/mapTimezones/mapZone"):
                if elem.get("territory", "") == "001":
                    if elem.get("other") not in self.links:
                        self.links[elem.get("other")] = elem.get("type")
                    else:
                        print("Ignoring duplicate Windows alias: {}".format(elem.get("other")))
        except (ValueError, KeyError):
            raise ValueError("Unable to parse windows alias file: {}".format(aliases))

    def expandZone(self, zonename: str, minYear: int, maxYear: int = 2018) -> List[Any]:
        """
        Expand a zones transition dates up to the specified year.
        """
        zoneobj = self.zones[zonename]
        expanded = zoneobj.expand(self.rules, minYear, maxYear)
        return [(item[0], item[1], item[2],) for item in expanded]

    def vtimezones(
        self,
        minYear: int,
        maxYear: int = 2018,
        filterzones: Optional[Union[List[str], Set[str]]] = None
    ) -> str:
        """
        Generate iCalendar data for all VTIMEZONEs or just those specified
        """
        cal = Calendar()
        for tzzone in self.zones.values():
            if filterzones and tzzone.name not in filterzones:
                continue
            vtz = tzzone.vtimezone(cal, self.rules, minYear, maxYear)
            cal.addComponent(vtz)

        return cal.getText()

    def generateZoneinfoFiles(
        self,
        outputdir: str,
        minYear: int,
        maxYear: int = 2018,
        links: bool = True,
        windowsAliases: Optional[str] = None,
        filterzones: Optional[Union[List[str], Set[str]]] = None
    ) -> None:

        try:
            for root, dirs, files in os.walk(outputdir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        except OSError:
            pass

        for tzzone in self.zones.values():
            if filterzones and tzzone.name not in filterzones:
                continue
            cal = Calendar()
            vtz = tzzone.vtimezone(cal, self.rules, minYear, maxYear)
            cal.addComponent(vtz)

            icsdata = cal.getText()
            fpath = os.path.join(outputdir, tzzone.name + ".ics")
            if not os.path.exists(os.path.dirname(fpath)):
                os.makedirs(os.path.dirname(fpath))
            with open(fpath, "w") as f:
                f.write(icsdata)
            if self.verbose:
                print("Write path: %s" % (fpath,))

        if links:
            if windowsAliases is not None:
                self.parseWindowsAliases(windowsAliases)

            link_list: List[str] = []
            for linkTo, linkFrom in sorted(self.links.items(), key=lambda x: x[0]):

                fromPath = os.path.join(outputdir, linkFrom + ".ics")
                if not os.path.exists(fromPath):
                    print("Missing link from: %s to %s" % (linkFrom, linkTo,))
                    continue

                with open(fromPath) as f:
                    icsdata = f.read()
                icsdata = icsdata.replace(linkFrom, linkTo)

                toPath = os.path.join(outputdir, linkTo + ".ics")
                if not os.path.exists(os.path.dirname(toPath)):
                    os.makedirs(os.path.dirname(toPath))
                with open(toPath, "w") as f:
                    f.write(icsdata)
                if self.verbose:
                    print("Write link: %s" % (linkTo,))

                link_list.append("%s\t%s" % (linkTo, linkFrom,))

            linkPath = os.path.join(outputdir, "links.txt")
            with open(linkPath, "w") as f:
                f.write("\n".join(link_list))


def usage(error_msg: Optional[str] = None) -> None:
    if error_msg:
        print(error_msg)

    print("""Usage: tzconvert [options] [DIR]
Options:
    -h            Print this help and exit
    --prodid      PROD-ID string to use
    --start       Start year
    --end         End year

Arguments:
    DIR      Directory containing an Olson tzdata directory to read, also
             where zoneinfo data will be written

Description:
    This utility convert Olson-style timezone data in iCalendar.
    VTIMEZONE objects, one .ics file per-timezone.

""")

    if error_msg:
        raise ValueError(error_msg)
    else:
        sys.exit(0)