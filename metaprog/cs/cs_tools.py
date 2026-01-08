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



def strToCsStr(text:str)->str:
    '''! Convert a regular string into a valid escaped UTF-8 C# string '''
    utf8Bytes:bytes = text.encode('utf-8')
    csStr:str = ""
    for byte in utf8Bytes:
        if byte == ord('\\'):
            csStr += "\\\\"
        elif byte == ord('"'):
            csStr += '\\"'
        elif byte == ord('\r'):
            csStr += '\\r'
        elif byte == ord('\n'):
            csStr += '\\n'
        elif byte == ord('\t'):
            csStr += '\\t'
        elif byte >= 32 and byte < 127:
            csStr += chr(byte)
        else:
            csStr += f'\\x{byte:02x}'
    return csStr