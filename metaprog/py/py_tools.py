# Copyright 2025-2026 Davide Achilli (DAFOCUS - https://www.dafocus.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Davide Achilli <davide.achilli@dafocus.com>

from .py_labels import PyVisibility

## @brief Calculate the name according to the visibility.
#
# In python, private and protected is obtained by using respectively two and one
# underscores as a prefix.
#
def pyNameFromVisibility(name:str, visibility:PyVisibility) -> str:
    if visibility == PyVisibility.PRIVATE: return f'__{name}'
    if visibility == PyVisibility.PROTECTED: return f'_{name}'
    return name

## @brief Convert a regular string into a valid escaped UTF-8 Python string
def strToPyStr(text:str)->str:
    utf8Bytes:bytes = text.encode('utf-8')
    pyStr:str = ""
    for byte in utf8Bytes:
        if byte == ord('\\'):
            pyStr += "\\\\"
        elif byte == ord('"'):
            pyStr += '\\"'
        elif byte == ord('\r'):
            pyStr += '\\r'
        elif byte == ord('\n'):
            pyStr += '\\n'
        elif byte == ord('\t'):
            pyStr += '\\t'
        elif byte >= 32 and byte < 127:
            pyStr += chr(byte)
        else:
            pyStr += f'\\x{byte:02x}'
    return pyStr
