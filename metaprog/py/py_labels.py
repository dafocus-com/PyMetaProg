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

class PyStaticity(Enum):
    DYNAMIC       = 1
    STATIC        = 2

class PyClassVirtuality(Enum):
    CLASS_NORMAL           = 1
    CLASS_ABSTRACT         = 2

class PyVisibility(Enum):
    PRIVATE   = 1
    PROTECTED = 2
    PUBLIC    = 3

PY_METAPROGLIB:str = "metaproglib"