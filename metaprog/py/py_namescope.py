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
from .py_config import PyConfig
from .py_includes import PyIncludes, PyIncludesAny
from .py_labels import PyVisibility
from .py_tools import pyNameFromVisibility
from .py_namescope_reference import PyNameScopeReferences
from metaprog.util.extensions import Extensions, ExtensionsAny
from metaprog.util.writer import Writer
from typing import Optional, TYPE_CHECKING
from pathlib import Path
if TYPE_CHECKING:
    from .py_module_config import PyModuleConfig


class PyNameScope:
    '''! Objects that have a name scope like namespaces and classes '''
    def __init__(
            self, 
            nameScope:str,
            pyIncludesAny:PyIncludesAny,
            extensions:ExtensionsAny,
            visibility:PyVisibility,
        ) -> None:
        self.m_pyIncludes:PyIncludes = PyIncludes(pyIncludesAny=pyIncludesAny)
        self.m_extensions:Extensions = Extensions(extensions=extensions)
        self.m_moduleConfig:Optional[PyModuleConfig] = None
        self.m_parent:Optional[PyNameScope] = None
        self.m_visibility:PyVisibility = visibility

        # In Python we save the name as a private member because the real name
        # might have one or two leading underscores according to its visibility.
        self.__nameScope:str = nameScope
    
    @property
    def m_nameScope(self)->str:
        return pyNameFromVisibility(name=self.__nameScope, visibility=self.m_visibility)

    def getFullPath(self) -> list[str]:
        myPath:list[str] = list()
        if self.m_parent: myPath += self.m_parent.getFullPath()
        myPath.append(self.m_nameScope)
        return myPath

    def getQualifiedScope(self)->list[str]:
        if self.m_parent: 
            assert(isinstance(self.m_parent, PyNameScope))
            fullScope:list[str] = self.m_parent.getQualifiedScope()
            fullScope.append(self.m_nameScope)
        else:
            fullScope = [self.m_nameScope]
        return fullScope

    def getPyQualifiedName(self, otherScope:Optional[PyNameScope]=None)->str:
        '''! Returns the minimally qualified name required by `otherScope` to reach 
            this PyNameScope. If `otherScope` is not specified, returns the full path
            from root.
        '''
        if otherScope is not None:
            if otherScope==self:
                return self.getPyUnqualifiedName()
            else:
                selfScopeRef:PyNameScopeReferences = self.getNameScopeReferences()
                othrScopeRef:PyNameScopeReferences = otherScope.getNameScopeReferences()
                if selfScopeRef.m_modulePath == othrScopeRef.m_modulePath:
                    return self.getPyUnqualifiedName()
        return '.'.join(self.getFullPath())

    def getPyUnqualifiedName(self)->str:
        '''! Returns the unqualified python name '''
        return self.m_nameScope

    def addChild(self, child:PyNameScope) -> None:
        assert(child.m_parent is None)

    def setupModuleConfig(self, moduleConfig:PyModuleConfig) -> None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        moduleConfig.m_pyIncludes.merge(self.m_pyIncludes)

    def generatePyBody(self, writer:Writer, config:PyConfig) -> None:
        '''! Generate the body part of the Python .py file, i.e. where implementation of the methods go '''
        pass

    def generate(self, config:PyConfig, pyFilePath:Path) -> None:
        '''! Generate this file in the indicated path; used to create the actual .py files in the correct directory tree '''
        pass

    def upscanType(self, searchedType:type) -> Optional[PyNameScope]:
        if isinstance(self, searchedType): return self
        if self.m_parent is None: return None
        return self.m_parent.upscanType(searchedType=searchedType)

    def isModule(self) -> bool: return False

    def getNameScopeReferences(self) -> PyNameScopeReferences:
        '''! Returns the module path from root and the class path
        '''
        modulePath:list[str] = list()
        namePath:list[str] = list()

        curr:Optional[PyNameScope] = self
        isInModule:bool = False
        while curr is not None:
            if curr.isModule(): isInModule=True
            if isInModule:
                # Once we enter modules, we must stay in modules
                if not curr.isModule():
                    print(f"[ERROR] NOT A MODULE: {curr.__class__.__name__}")
                    exit(1)
                modulePath.insert(0, curr.m_nameScope)
            else:
                namePath.insert(0, curr.m_nameScope)

            curr = curr.m_parent

        # Once we enter modules, we must stay in modules
        if not isInModule:
            print(f"[ERROR] PyNameScope.getNameScopeReferences(), namescope=[{self.getPyQualifiedName()}] couldn't find an owning module")
            exit(1)

        return PyNameScopeReferences(modulePath='.'.join(modulePath), namePath='.'.join(namePath))

    def importInThis(self, toBeImported:PyNameScope, pyIncludes:Optional[PyIncludes]=None)->None:
        '''! Import in this namescope the `toBeImported` namescope. 
            Import is done in the internal `self.m_pyInclude` unnless a differente `pyIncludes` is specified.
        '''
        targetIncludes:PyIncludes = self.m_pyIncludes if pyIncludes is None else pyIncludes
        containerRef:PyNameScopeReferences = self.getNameScopeReferences()
        containedRef:PyNameScopeReferences = toBeImported.getNameScopeReferences()
        containedRef.importThisIntoOther(other=containerRef, otherImports=targetIncludes)
