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

from abc import ABC, abstractmethod
from metaprog.util.writer import Writer
from .cs_config import CsConfig
from .cs_module_config import CsModuleConfig
from .cs_includes import CsIncludes, CsIncludesAny
from typing import Optional
from metaprog.util.extensions import Extensions, ExtensionsAny


class CsGenerable(ABC):
    '''! Base class for the objects that can be generated in C# '''
    def __init__(
            self, 
            csIncludes:CsIncludesAny,
            extensions:ExtensionsAny,
        ):
        self.m_csIncludes:CsIncludes = CsIncludes(usings=csIncludes)
        self.m_extensions:Extensions = Extensions(extensions=extensions)
        self.m_moduleConfig:Optional[CsModuleConfig] = None
        self.m_parent:Optional[CsGenerable] = None

    def getCsModuleConfig(self) -> Optional[CsModuleConfig]:
        if self.m_moduleConfig is not None:
            return self.m_moduleConfig
        if self.m_parent is not None:
            return self.m_parent.getCsModuleConfig()
        return None

    def setupModuleConfig(self, moduleConfig:CsModuleConfig) -> None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        moduleConfig.m_csIncludes.merge(self.m_csIncludes)

    @abstractmethod
    def generateCsBody(self, writer:Writer, config:CsConfig) -> None:
        '''! Generate the body part of the C# .cs file, i.e. where implementation of the methods go '''
        ...