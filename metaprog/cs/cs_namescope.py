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
from .cs_includes import CsIncludesAny
from .cs_generable import CsGenerable
from .cs_module_config import CsModuleConfig
from typing import Optional
from metaprog.util.writer import Writer
from .cs_config import CsConfig
from metaprog.util.extensions import ExtensionsAny

class CsNameScope(CsGenerable):
    '''! Objects that have a name scope like namespaces and classes '''
    def __init__(
            self, 
            nameScope:str,
            csIncludes:CsIncludesAny,
            extensions:ExtensionsAny,
        ) -> None:
        super().__init__(csIncludes=csIncludes, extensions=extensions)
        self.m_nameScope:str = nameScope

    def getQualifiedScope(self)->list[str]:
        if self.m_parent: 
            assert(isinstance(self.m_parent, CsNameScope))
            fullScope:list[str] = self.m_parent.getQualifiedScope()
            fullScope.append(self.m_nameScope)
        else:
            fullScope = [self.m_nameScope]
        return fullScope

    def getShortestPath(self, otherScope:Optional[CsNameScope])->list[str]:
        '''! Returns the minimally qualified name required by `otherScope` to reach 
            this CsNameScope. If `otherScope` is not specified, returns the full path
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

    def upscanType(self, searchedType:type) -> Optional[CsNameScope]:
        if isinstance(self, searchedType): return self
        if self.m_parent is None: return None
        assert(isinstance(self.m_parent, CsNameScope))
        return self.m_parent.upscanType(searchedType=searchedType)

    def getCsQualifiedName(self, otherScope:Optional[CsNameScope]=None)->str:
        '''! Returns the minimally qualified name required by `otherScope` to reach 
            this CsNameScope. If `otherScope` is not specified, returns the full path
            from root.
        '''
        if otherScope is not None and otherScope==self:
            return self.getCsUnqualifiedName()
        return ".".join(self.getShortestPath(otherScope=otherScope))

    def getCsUnqualifiedName(self)->str:
        '''! Returns the unqualified C# name '''
        return self.m_nameScope

    def addChild(self, child:CsNameScope) -> None:
        assert(child.m_parent is None)

    def setupModuleConfig(self, moduleConfig:CsModuleConfig) -> None:
        super().setupModuleConfig(moduleConfig=moduleConfig)

    def generateCsBody(self, writer:Writer, config:CsConfig) -> None:
        pass
