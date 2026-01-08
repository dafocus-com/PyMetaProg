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
from .cpp_includes import CppIncludesAny
from .cpp_generable import CppGenerable
from .cpp_module_config import CppModuleConfig
from typing import Optional
from metaprog.util.writer import Writer
from .cpp_config import CppConfig
from metaprog.util.extensions import ExtensionsAny

class CppNameScope(CppGenerable):
    '''! Objects that have a name scope like namespaces and classes '''
    def __init__(
            self, 
            nameScope:str,
            hppIncludes:CppIncludesAny,
            cppIncludes:CppIncludesAny,
            extensions:ExtensionsAny,
        ) -> None:
        super().__init__(hppIncludes=hppIncludes, cppIncludes=cppIncludes, extensions=extensions)
        self.m_nameScope:str = nameScope
        self.__prevNamescope:Optional[CppNameScope] = None

    def _enterNameScope(self, config:CppConfig)->None:
        self.__prevNamescope = config.m_cppCurrentNameScope # type: ignore
        config.m_cppCurrentNameScope = self

    def _exitNameScope(self, config:CppConfig)->None:
        config.m_cppCurrentNameScope = self.__prevNamescope
        self.__prevNamescope = None

    def getQualifiedScope(self)->list[str]:
        if self.m_parent: 
            assert(isinstance(self.m_parent, CppNameScope))
            fullScope:list[str] = self.m_parent.getQualifiedScope()
            fullScope.append(self.m_nameScope)
        else:
            fullScope = [self.m_nameScope]
        return fullScope

    def getShortestPath(self, otherScope:Optional[CppNameScope])->list[str]:
        '''! Returns the minimally qualified name required by `otherScope` to reach 
            this CppNameScope. If `otherScope` is not specified, returns the full path
            from root.
        '''
        local:list[str] = self.getQualifiedScope()
        if not otherScope: return local
        other:list[str] = otherScope.getQualifiedScope()
        count:int = 0
        while True:
            if count >= len(other) or count >= len(local) or other[count]!=local[count]:
                return local[count:]
            else:
                count += 1

    def upscanType(self, searchedType:type) -> Optional[CppNameScope]:
        if isinstance(self, searchedType): return self
        if self.m_parent is None: return None
        assert(isinstance(self.m_parent, CppNameScope))
        return self.m_parent.upscanType(searchedType=searchedType)

    def getCppQualifiedName(self, otherScope:Optional[CppNameScope]=None)->str:
        '''! Returns the minimally qualified name required by `otherScope` to reach 
            this CppNameScope. If `otherScope` is not specified, returns the full path
            from root.
        '''
        if otherScope is not None and otherScope==self:
            return self.getCppUnqualifiedName()
        return "::".join(self.getShortestPath(otherScope=otherScope))

    def getCppUnqualifiedName(self)->str:
        '''! Returns the unqualified C++ name '''
        return self.m_nameScope

    def addChild(self, child:CppNameScope)->None:
        assert(child.m_parent is None)

    def needsCpp(self)->bool:
        return False

    def needsInline(self)->bool:
        return False

    def setupModuleConfig(self, moduleConfig:CppModuleConfig)->None:
        super().setupModuleConfig(moduleConfig=moduleConfig)

    def generateHppBody(self, writer:Writer, config:CppConfig)->None:
        pass

    def generateHppInline(self, writer:Writer, config:CppConfig)->None:
        pass

    def generateCppBody(self, writer:Writer, config:CppConfig)->None:
        pass
