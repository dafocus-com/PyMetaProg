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
from .cs_module_config import CsModuleConfig
from metaprog.util.writer import Writer
from .cs_config import CsConfig
from .cs_usings import CsUsingsAny
from metaprog.util.extensions import ExtensionsAny

class CsNameScopeWithChildren(CsNameScope):
    '''! Objects that have a name scope like namespaces and classes '''
    def __init__(
            self, 
            nameScope:str,
            hppUsings:CsUsingsAny=None,
            csUsings:CsUsingsAny=None,
            extensions:ExtensionsAny=None,
        ) -> None:
        super().__init__(nameScope=nameScope, csUsings=csUsings, extensions=extensions)
        self.m_children:list[CsNameScope] = list()

    def addChild(self, child:CsNameScope)->None:
        assert(child.m_parent is None)
        child.m_parent = self
        self.m_children.append(child)

    def setupModuleConfig(self, moduleConfig:CsModuleConfig)->None:
        super().setupModuleConfig(moduleConfig=moduleConfig)
        for child in self.m_children:
            child.setupModuleConfig(moduleConfig=moduleConfig)

    def generateCsBody(self, writer:Writer, config:CsConfig)->None:
        for child in self.m_children:
            child.generateCsBody(writer=writer, config=config)
