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
from .py_labels import PyVisibility
from .py_namescope import PyNameScope
from .py_namescope_external import PyNameScopeExternal
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.sourcefile import SourceFile
from metaprog.util.freetext import FreeText
from pathlib import Path
from typing import Optional

class PyModuleExternal(PyNameScope):
    '''! Represents an external module.

    This object is used to represent a module defined elsewhere, like a library module.
    Inside this object, there will bel some `PyNameScopeExternal` that represent the names
    that can be taken.

    This object is not supposed to generate any file. The only thing it does is to copy
    the contents of an existing module in the file that this would generate.


    '''
    def __init__(
            self,
            moduleName:str,
            extensions:ExtensionsAny=None,

            ## If specified, copies this file as a source for the module body            
            moduleSource:Optional[Path] = None,
        ) -> None:
        super().__init__(nameScope=moduleName, extensions=extensions, pyIncludesAny=None, visibility=PyVisibility.PUBLIC)
        self.m_moduleSource:Optional[Path] = moduleSource
        self.m_names:dict[str, PyNameScopeExternal] = dict()

    def isModule(self) -> bool: return True

    def generate(self, config:PyConfig, pyFilePath:Path) -> None:

        # If no source specified, do not generate anything
        if self.m_moduleSource is None: return

        # Copy the file only if it is a different one
        config.m_pyCurrentNameScope = self
        modulePath:Path = pyFilePath / (self.m_nameScope+'.py')
        #if self.m_moduleSource.samefile(modulePath): return

        pySourceFile:SourceFile = SourceFile(modulePath)
        with open(self.m_moduleSource, "r", encoding="utf-8") as f:
            sourceModuleText:FreeText = FreeText()
            sourceModuleText.m_text = f.read()
            pySourceFile.m_writables.append(sourceModuleText)

        pySourceFile.write(config)

    def __registerChild(self, pyNameScopeExternal:PyNameScopeExternal):
        nameScope:str = pyNameScopeExternal.getPyQualifiedName()
        assert(nameScope not in self.m_names)
        assert(pyNameScopeExternal.m_parent is None)
        pyNameScopeExternal.m_parent = self
        self.m_names[nameScope] = pyNameScopeExternal

    def getNameScope(self, nameScope:str) -> PyNameScopeExternal:
        if nameScope in self.m_names: return self.m_names[nameScope]
        newName:PyNameScopeExternal = PyNameScopeExternal(nameScope=nameScope)
        self.__registerChild(pyNameScopeExternal=newName)
        return newName

    def merge(self, other:PyModuleExternal):
        for name,pyNameScopeExternal in other.m_names.items():
            if name not in self.m_names:
                self.__registerChild(pyNameScopeExternal=pyNameScopeExternal.clone())
            else:
                self.m_names[name].merge(toBeImported=pyNameScopeExternal)