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
from typing import Any, List, Tuple, IO, Sequence, Union
from pycalendar.parser import ParserContext
import io as StringIO

def readFoldedLine(ins: IO[str], lines: List[Union[str, None]]) -> bool:
    if lines[1] is not None:
        lines[0] = lines[1]
    else:
        try:
            myline = ins.readline()
            if len(myline) == 0:
                raise ValueError("Folding: empty first line")
            if myline[-1] == "\n":
                if myline[-2] == "\r":
                    lines[0] = myline[:-2]
                else:
                    lines[0] = myline[:-1]
            elif myline[-1] == "\r":
                lines[0] = myline[:-1]
            else:
                lines[0] = myline
        except IndexError:
            lines[0] = ""
        except Exception:
            lines[0] = None
            return False
    while True:
        try:
            myline = ins.readline()
            if len(myline) == 0:
                raise ValueError("Folding: empty next line")
            if myline[-1] == "\n":
                if myline[-2] == "\r":
                    lines[1] = myline[:-2]
                else:
                    lines[1] = myline[:-1]
            elif myline[-1] == "\r":
                lines[1] = myline[:-1]
            else:
                lines[1] = myline
        except IndexError:
            lines[1] = ""
        except Exception:
            lines[1] = None
            return True
        if not lines[1]:
            return True
        if lines[1][0].isspace():
            lines[0] = lines[0] + lines[1][1:]
        else:
            break
    return True

def find_first_of(text: str, tokens: str, offset: int) -> int:
    for ctr, c in enumerate(text[offset:]):
        if c in tokens:
            return offset + ctr
    return -1

def escapeTextValue(value: str) -> str:
    os = StringIO.StringIO()
    writeTextValue(os, value)
    return os.getvalue()

def writeTextValue(os: IO[str], value: str) -> None:
    try:
        start_pos = 0
        end_pos = find_first_of(value, "\r\n;\\,", start_pos)
        if end_pos != -1:
            while True:
                os.write(value[start_pos:end_pos])
                os.write("\\")
                c = value[end_pos]
                if c == '\r':
                    os.write("r")
                elif c == '\n':
                    os.write("n")
                elif c == ';':
                    os.write(";")
                elif c == '\\':
                    os.write("\\")
                elif c == ',':
                    os.write(",")
                start_pos = end_pos + 1
                end_pos = find_first_of(value, "\r\n;\\,", start_pos)
                if end_pos == -1:
                    os.write(value[start_pos:])
                    break
        else:
            os.write(value)
    except Exception:
        pass

def decodeTextValue(value: str) -> str:
    os = StringIO.StringIO()
    start_pos = 0
    end_pos = find_first_of(value, "\\", start_pos)
    size_pos = len(value)
    if end_pos != -1:
        while True:
            os.write(value[start_pos:end_pos])
            end_pos += 1
            if end_pos >= size_pos:
                break
            c = value[end_pos]
            if c == 'r':
                os.write('\r')
            elif c == 'n':
                os.write('\n')
            elif c == 'N':
                os.write('\n')
            elif c == '':
                os.write('')
            elif c == '\\':
                os.write('\\')
            elif c == ',':
                os.write(',')
            elif c == ';':
                os.write(';')
            elif c == ':':
                if ParserContext.INVALID_COLON_ESCAPE_SEQUENCE == ParserContext.PARSER_RAISE:
                    raise ValueError("TextValue: '\\:' not allowed")
                elif ParserContext.INVALID_COLON_ESCAPE_SEQUENCE == ParserContext.PARSER_FIX:
                    os.write(':')
            elif ParserContext.INVALID_ESCAPE_SEQUENCES == ParserContext.PARSER_RAISE:
                raise ValueError("TextValue: '\\{}' not allowed".format(c))
            elif ParserContext.INVALID_ESCAPE_SEQUENCES == ParserContext.PARSER_FIX:
                os.write(c)
            start_pos = end_pos + 1
            if start_pos >= size_pos:
                break
            end_pos = find_first_of(value, "\\", start_pos)
            if end_pos == -1:
                os.write(value[start_pos:])
                break
    else:
        os.write(value)
    return os.getvalue()

def encodeParameterValue(value: str) -> str:
    encode = False
    for c in "\r\n\"^":
        if c in value:
            encode = True
    if encode:
        encoded: List[str] = []
        last = ''
        for c in value:
            if c in "\r\n\"^":
                if c == '\r':
                    encoded.append("^n")
                elif c == '\n':
                    if last != '\r':
                        encoded.append("^n")
                elif c == '"':
                    encoded.append("^'")
                elif c == '^':
                    encoded.append("^^")
            else:
                encoded.append(c)
            last = c
        return "".join(encoded)
    else:
        return value

def decodeParameterValue(value: str) -> str:
    if value is not None and "^" in value:
        decoded: List[str] = []
        last = ''
        for c in value:
            if last == '^':
                if c == 'n':
                    decoded.append('\n')
                elif c == '\'':
                    decoded.append('"')
                elif c == '^':
                    decoded.append('^')
                    c = ''
                else:
                    decoded.append('^')
                    decoded.append(c)
            elif c != '^':
                decoded.append(c)
            last = c
        if last == '^':
            decoded.append('^')
        return "".join(decoded)
    else:
        return value

def parseTextList(data: str, sep: str = ';', always_list: bool = False) -> Union[Tuple[str, ...], str]:
    results: List[str] = []
    item: List[str] = []
    pre_s = ''
    for s in data:
        if s == sep and pre_s != '\\':
            results.append(decodeTextValue("".join(item)))
            item = []
        else:
            item.append(s)
        pre_s = s
    results.append(decodeTextValue("".join(item)))
    return tuple(results) if len(results) > 1 or always_list else (results[0] if len(results) else "")

def generateTextList(os: IO[str], data: Union[str, Sequence[str]], sep: str = ';') -> None:
    try:
        if isinstance(data, str):
            data = (data,)
        results = [escapeTextValue(value) for value in data]
        os.write(sep.join(results))
    except Exception:
        pass

def parseDoubleNestedList(data: str, maxsize: int) -> Tuple[Any, ...]:
    results: List[Any] = []
    items: List[str] = [""]
    pre_s = ''
    for s in data:
        if s == ';' and pre_s != '\\':
            if len(items) > 1:
                results.append(tuple([decodeTextValue(item) for item in items]))
            elif len(items) == 1:
                results.append(decodeTextValue(items[0]))
            else:
                results.append("")
            items = [""]
        elif s == ',' and pre_s != '\\':
            items.append("")
        else:
            items[-1] += s
        pre_s = s
    if len(items) > 1:
        results.append(tuple([decodeTextValue(item) for item in items]))
    elif len(items) == 1:
        results.append(decodeTextValue(items[0]))
    else:
        results.append("")
    for _ignore in range(maxsize - len(results)):
        results.append("")
    if len(results) > maxsize:
        if ParserContext.INVALID_ADR_N_VALUES == ParserContext.PARSER_FIX:
            results = results[:maxsize]
        elif ParserContext.INVALID_ADR_N_VALUES == ParserContext.PARSER_RAISE:
            raise ValueError("ADR: too many components in value")
    return tuple(results)

def generateDoubleNestedList(os: IO[str], data: Sequence[Any]) -> None:
    try:
        def _writeElement(item: Any) -> None:
            if isinstance(item, str):
                writeTextValue(os, item)
            else:
                if item:
                    writeTextValue(os, item[0])
                    for bit in item[1:]:
                        os.write(",")
                        writeTextValue(os, bit)
        for item in data[:-1]:
            _writeElement(item)
            os.write(";")
        _writeElement(data[-1])
    except Exception:
        pass

days_in_month: Tuple[int, ...] = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
days_in_month_leap: Tuple[int, ...] = (0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

def daysInMonth(month: int, year: int) -> int:
    if isLeapYear(year):
        return days_in_month_leap[month]
    else:
        return days_in_month[month]

days_upto_month: Tuple[int, ...] = (0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
days_upto_month_leap: Tuple[int, ...] = (0, 0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335)

def daysUptoMonth(month: int, year: int) -> int:
    if isLeapYear(year):
        return days_upto_month_leap[month]
    else:
        return days_upto_month[month]

cachedLeapYears: dict[int, bool] = {}

def isLeapYear(year: int) -> bool:
    try:
        return cachedLeapYears[year]
    except KeyError:
        if year <= 1752:
            result = (year % 4 == 0)
        else:
            result = ((year % 4 == 0) and (year % 100 != 0)) or (year % 400 == 0)
        cachedLeapYears[year] = result
        return result

cachedLeapDaysSince1970: dict[int, int] = {}

def leapDaysSince1970(year_offset: int) -> int:
    try:
        return cachedLeapDaysSince1970[year_offset]
    except KeyError:
        if year_offset > 2:
            result = (year_offset + 1) // 4
        elif year_offset < -1:
            result = (year_offset + 1) // 4
        else:
            result = 0
        cachedLeapDaysSince1970[year_offset] = result
        return result

def packDate(year: int, month: int, day: int) -> int:
    return (year << 16) | (month << 8) | (day + 128)

def unpackDate(data: int, unpacked: List[int]) -> None:
    unpacked[0] = (data & 0xFFFF0000) >> 16
    unpacked[1] = (data & 0x0000FF00) >> 8
    unpacked[2] = (data & 0xFF) - 128

def unpackDateYear(data: int) -> int:
    return (data & 0xFFFF0000) >> 16

def unpackDateMonth(data: int) -> int:
    return (data & 0x0000FF00) >> 8

def unpackDateDay(data: int) -> int:
    return (data & 0xFF) - 128

def getMonthTable(month: int, year: int, weekstart: int, table: Any, today_index: Any) -> Tuple[Any, Any]:
    from pycalendar.datetime import DateTime
    today = DateTime.getToday(None)
    today_index = [-1, -1]
    table = []
    temp = DateTime(year, month, 1, 0)
    row = -1
    initial_col = temp.getDayOfWeek() - weekstart
    if initial_col < 0:
        initial_col += 7
    col = initial_col
    max_day = daysInMonth(month, year)
    for day in range(1, max_day + 1):
        if (col == 0) or (day == 1):
            table.extend([0] * 7)
            row += 1
        table[row][col] = packDate(temp.getYear(), temp.getMonth(), day)
        if (temp.getYear() == today.getYear()) and (temp.getMonth() == today.getMonth()) and (day == today.getDay()):
            today_index = [row, col]
        col += 1
        if (col > 6):
            col = 0
    temp.offsetMonth(1)
    if col != 0:
        day = 1
        while col < 7:
            table[row][col] = packDate(temp.getYear(), temp.getMonth(), -day)
            if (temp.getYear() == today.getYear()) and (temp.getMonth() == today.getMonth()) and (day == today.getDay()):
                today_index = [row, col]
            day += 1
            col += 1
    temp.offsetMonth(-2)
    if (initial_col != 0):
        day = daysInMonth(temp.getMonth(), temp.getYear())
        back_col = initial_col - 1
        while(back_col >= 0):
            table[row][back_col] = packDate(temp.getYear(), temp.getMonth(), -day)
            if (temp.getYear() == today.getYear()) and (temp.getMonth() == today.getMonth()) and (day == today.getDay()):
                today_index = [0, back_col]
            back_col -= 1
            day -= 1
    return table, today_index

def set_difference(v1: Sequence[Any], v2: Sequence[Any]) -> List[Any]:
    if len(v1) == 0 or len(v2) == 0:
        return list(v1)
    s1 = set(v1)
    s2 = set(v2)
    s3 = s1.difference(s2)
    return list(s3)