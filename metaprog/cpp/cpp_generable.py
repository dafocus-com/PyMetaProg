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
from .cpp_config import CppConfig
from .cpp_module_config import CppModuleConfig
from .cpp_includes import CppIncludes, CppIncludesAny
from metaprog.util.extensions import Extensions, ExtensionsAny
from typing import Optional


class CppGenerable(ABC):
    '''! Base class for the objects that can be generated in C++ '''
    def __init__(
            self, 
            hppIncludes:CppIncludesAny,
            cppIncludes:CppIncludesAny,
            extensions:ExtensionsAny,
        ):
        self.m_hppIncludes:CppIncludes = CppIncludes(incls=hppIncludes)
        self.m_cppIncludes:CppIncludes = CppIncludes(incls=cppIncludes)
        self.m_extensions:Extensions = Extensions(extensions=extensions)
        self.m_moduleConfig:Optional[CppModuleConfig] = None
        self.m_parent:Optional[CppGenerable] = None
    
    @abstractmethod
    def needsCpp(self)->bool:
        '''! Must return `True` if this class requires the C++ file`'''
        ...

    @abstractmethod
    def needsInline(self)->bool:
        '''! Must return `True` if this class requires the inline .hpp part`'''
        ...

    def getCppModuleConfig(self) -> Optional[CppModuleConfig]:
        if self.m_moduleConfig is not None:
            return self.m_moduleConfig
        if self.m_parent is not None:
            return self.m_parent.getCppModuleConfig()
        return None

    def setupModuleConfig(self, moduleConfig:CppModuleConfig) -> None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        moduleConfig.m_hppIncludes.merge(self.m_hppIncludes)
        moduleConfig.m_cppIncludes.merge(self.m_cppIncludes)

    def generateHppBody(self, writer:Writer, config:CppConfig) -> None:
        '''! Generate the body part of the C++ .hpp file, i.e. where the class definitions go '''
        pass


    def generateHppInline(self, writer:Writer, config:CppConfig) -> None:
        '''! Generate the inline part of the C++ .hpp file, i.e. where the `inline` methods go '''
        pass

    def generateCppBody(self, writer:Writer, config:CppConfig) -> None:
        '''! Generate the body part of the C++ .cpp file, i.e. where implementation of the methods go '''
        pass