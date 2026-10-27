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
from .cpp_namescope_with_children import CppNameScopeWithChildren
from .cpp_namescope import CppNameScope
from .cpp_includes import CppIncludesAny
from metaprog.util.extensions import ExtensionsAny
from typing import Optional
from abc import abstractmethod
from typing import TYPE_CHECKING 
if TYPE_CHECKING: 
    from .cpp_class_element import CppClassElement

class CppClassBase(CppNameScopeWithChildren):
    '''! Objects that have a name scope like namespaces and classes '''
    def __init__(
            self, 
            nameScope:str,
            baseClass:str|CppClassBase|None, 
            hppIncludes:CppIncludesAny,
            cppIncludes:CppIncludesAny,
            extensions:ExtensionsAny,
        ) -> None:
        super().__init__(nameScope=nameScope, hppIncludes=hppIncludes, cppIncludes=cppIncludes, extensions=extensions)
        self.m_baseClass:str|CppClassBase|None = baseClass


    def getCppBaseQualifiedName(self, otherScope:Optional[CppNameScope]=None)->str:
        '''! Returns the minimally qualified name required by `otherScope` to reach 
            the base class. If `otherScope` is not specified, returns the full path
            from root.
        '''
        assert(self.m_baseClass is not None)
        if isinstance(self.m_baseClass, str):
            return self.m_baseClass
        return self.m_baseClass.getCppQualifiedName(otherScope=otherScope)
        
    @abstractmethod
    def addClassElement(self, classElement:CppClassElement)->CppClassElement:
        ...
        
