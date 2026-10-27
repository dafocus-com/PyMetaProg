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
from .cpp_namescope import CppNameScope
from .cpp_module_config import CppModuleConfig
from metaprog.util.writer import Writer
from .cpp_config import CppConfig
from .cpp_includes import CppIncludesAny
from metaprog.util.extensions import ExtensionsAny
from .cpp_children_container import CppChildrenContainer

class CppNameScopeWithChildren(CppNameScope, CppChildrenContainer):
    '''! Objects that have a name scope like namespaces and classes '''
    def __init__(
            self, 
            nameScope:str,
            hppIncludes:CppIncludesAny=None,
            cppIncludes:CppIncludesAny=None,
            extensions:ExtensionsAny=None,
        ) -> None:
        super().__init__(nameScope=nameScope, hppIncludes=hppIncludes, cppIncludes=cppIncludes, extensions=extensions)
        self.m_children:list[CppNameScope] = list()

    def addChild(self, child:CppNameScope) -> None:
        assert(child.m_parent is None)
        child.m_parent = self
        self.m_children.append(child)

    def needsCpp(self)->bool:
        for child in self.m_children:
            if child.needsCpp(): return True
        return False

    def needsInline(self)->bool:
        for child in self.m_children:
            if child.needsInline(): return True
        return False

    def setupModuleConfig(self, moduleConfig:CppModuleConfig) -> None:
        super().setupModuleConfig(moduleConfig=moduleConfig)
        for child in self.m_children:
            child.setupModuleConfig(moduleConfig=moduleConfig)

    def generateHppBody(self, writer:Writer, config:CppConfig) -> None:
        super().generateHppBody(writer=writer, config=config)
        for child in self.m_children:
            child.generateHppBody(writer=writer, config=config)

    def generateHppInline(self, writer:Writer, config:CppConfig) -> None:
        for child in self.m_children:
            child.generateHppInline(writer=writer, config=config)

    def generateCppBody(self, writer:Writer, config:CppConfig) -> None:
        for child in self.m_children:
            child.generateCppBody(writer=writer, config=config)
