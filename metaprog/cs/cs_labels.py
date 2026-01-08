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

from enum import Enum

class CsStaticity(Enum):
    DYNAMIC       = 1
    STATIC        = 2

class CsVirtuality(Enum):
    NORMAL           = 1
    VIRTUAL          = 2
    PURE_VIRTUAL     = 3
    VIRTUAL_OVERRIDE = 4

# Keep in numeric order as defined (used internally to promote the class status)
class CsClassVirtuality(Enum):
    CLASS_NORMAL           = 1
    CLASS_VIRTUAL          = 2
    CLASS_ABSTRACT         = 3

class CsVisibility(Enum):
    PRIVATE   = 1
    PROTECTED = 2
    PUBLIC    = 3

    def toStr(self)->str:
        if self == CsVisibility.PRIVATE: return "private"
        if self == CsVisibility.PROTECTED: return "protected"
        if self == CsVisibility.PUBLIC: return "public"
        return "unknown"
