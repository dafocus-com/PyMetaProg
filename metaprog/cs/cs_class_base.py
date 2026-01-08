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

from __future__ import annotations
from .cs_namescope import CsNameScope
from .cs_usings import CsUsingsAny
from metaprog.util.extensions import ExtensionsAny

class CsClassBase(CsNameScope):
    '''! Objects that have a name scope like namespaces and classes '''
    def __init__(
            self, 
            nameScope:str,
            baseClass:str|CsClassBase|None=None, 
            csUsings:CsUsingsAny=None,
            extensions:ExtensionsAny=None,
        ) -> None:
        super().__init__(nameScope=nameScope, csUsings=csUsings, extensions=extensions)
        self.m_baseClass:str|CsClassBase|None = baseClass
