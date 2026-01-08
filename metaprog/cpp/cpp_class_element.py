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

from .cpp_namescope import CppNameScope
from .cpp_labels import *
from .cpp_config import CppConfig
from .cpp_module_config import CppModuleConfig
from .cpp_includes import CppIncludes, CppIncludesAny
from metaprog.util.writer import Writer
from metaprog.util.extensions import Extensions, ExtensionsAny
from abc import ABC, abstractmethod
from typing import Optional
from .cpp_class_base import CppClassBase

# Key to be used on any CppClassElement "extension" dictionary to define a different
# visibility that overrides `CppVisibility.DEFAULT` settings
CPP_CLASSELEMENT_VISIBILITY="cpp_classelement_visibility"   # -> CppVisibility enum


class CppClassElement(ABC):
    def __init__(
            self, 
            visibility:CppVisibility,
            hppIncludes:CppIncludesAny,
            cppIncludes:CppIncludesAny,
            extensions:ExtensionsAny,
        ):
        self.m_extensions:Extensions = Extensions(extensions=extensions)
        self.m_owningScope:Optional[CppNameScope] = None
        self.m_hppIncludes:CppIncludes = CppIncludes(incls=hppIncludes)
        self.m_cppIncludes:CppIncludes = CppIncludes(incls=cppIncludes)
        self.m_visibility:CppVisibility
        self.m_order:int = 0

        if visibility == CppVisibility.DEFAULT:
            if CPP_CLASSELEMENT_VISIBILITY in self.m_extensions:
                assert(isinstance(self.m_extensions[CPP_CLASSELEMENT_VISIBILITY], CppVisibility))
                self.m_visibility = self.m_extensions[CPP_CLASSELEMENT_VISIBILITY]
            else:
                self.m_visibility = CppVisibility.PUBLIC
        else:
            self.m_visibility = visibility

    @abstractmethod
    def needsCpp(self)->bool:
        '''! Must return `True` if this class requires the C++ file`'''
        ...

    @abstractmethod
    def needsInline(self)->bool:
        '''! Must return `True` if this class requires the inline .hpp part`'''
        ...
    
    @abstractmethod
    def identify(self)->str:
        '''! Returns a string that can be used to identify this element in logs '''
        ...

    def setupModuleConfig(self, moduleConfig:CppModuleConfig)->None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        moduleConfig.m_hppIncludes.merge(self.m_hppIncludes)
        moduleConfig.m_cppIncludes.merge(self.m_cppIncludes)

    @abstractmethod
    def generateHppBody(self, writer:Writer, config:CppConfig)->None:
        '''! Generate the body part of the C++ .hpp file, i.e. where the class definitions go '''
        ...

    @abstractmethod
    def generateHppInline(self, writer:Writer, config:CppConfig)->None:
        '''! Generate the inline part of the C++ .hpp file, i.e. where the `inline` methods go '''
        ...

    def generateCppBody(self, writer:Writer, config:CppConfig)->None:
        '''! Generate the body part of the C++ .cpp file, i.e. where implementation of the methods go '''
        pass

    def __str__(self)->str:
        return self.identify()

    def getCppClass(self)->CppClassBase:
        assert(self.m_owningScope is not None)
        assert(isinstance(self.m_owningScope, CppClassBase))
        return self.m_owningScope

    # WATERFALL ADDITION
    # 
    # The "waterfall addition" is the creation of other class elements due to features
    # of the existing class elements. For example, a `CppField` can create its setter
    # and getter method with the waterfall generation.
    #
    # This generation is first reset with `waterfallAdditionReset`. Then `waterfallAdditionOperate`
    # can do its changes.
    def waterfallAdditionReset(self)->None:
        '''! Reset the waterfall addition.'''
        pass

    def waterfallAdditionOperate(self, config:CppConfig)->bool:
        '''! Operate the changes. Expect to be called multiple times. 
            Return `False` if changed nothing, `True` if something has been changed.
        '''
        return False