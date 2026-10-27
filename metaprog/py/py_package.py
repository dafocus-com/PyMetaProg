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

from .py_config import PyConfig
from .py_namescope import PyNameScope
from .py_namescope_with_children import PyNameScopeWithChildren
from .py_includes import PyIncludesAny
from .py_labels import PyVisibility
from .py_module_external import PyModuleExternal
from metaprog.util.extensions import ExtensionsAny
from pathlib import Path
from typing import Optional

class PyPackage(PyNameScopeWithChildren):
    '''! Generates a package '''
    def __init__(
            self,
            packageName:str,
            pyIncludesAny:PyIncludesAny = None,
            extensions:ExtensionsAny = None,
        ) -> None:
        super().__init__(nameScope=packageName, pyIncludesAny=pyIncludesAny, extensions=extensions, visibility=PyVisibility.PUBLIC)

        # Map of external modules
        self._externalModules:dict[str,PyModuleExternal] = dict()

    def generate(self, config:PyConfig, pyFilePath:Path) -> None:
        '''! Generate this file in the indicated path (if meaningful) '''
        packagePath:Path = pyFilePath / self.m_nameScope
        for child in self.m_children:
            child.generate(config=config, pyFilePath=packagePath)

    def isModule(self) -> bool: return True

    def addChild(self, child:PyNameScope) -> None:
        if isinstance(child, PyModuleExternal):
            self._registerExernalModule(externalModule=child)
        else:
            super().addChild(child=child)


    def _registerExernalModule(self, externalModule:PyModuleExternal) -> PyModuleExternal:
        moduleName:str = externalModule.getPyQualifiedName()
        if moduleName not in self._externalModules:
            super().addChild(child=externalModule)
            self._externalModules[moduleName] = externalModule
            return externalModule
        
        existingExternalModule:PyModuleExternal = self._externalModules[moduleName]
        incompatibleFileNames:bool = False
        if existingExternalModule.m_moduleSource is not None and externalModule.m_moduleSource is not None:
            if not existingExternalModule.m_moduleSource.samefile(externalModule.m_moduleSource):
                incompatibleFileNames = True
        elif (existingExternalModule.m_moduleSource is not None) != (externalModule.m_moduleSource is not None):
            incompatibleFileNames = True

        if incompatibleFileNames:
            print(f'[ERROR] in PyPackage `{self.getPyQualifiedName()}` added multiple external module `{moduleName}` with incompatible file name')
            print(f'        previous...: {existingExternalModule.m_moduleSource}')
            print(f'        new........: {externalModule.m_moduleSource}')
            exit(1)
            
        # Merge the contents
        existingExternalModule.merge(other=externalModule)
        return existingExternalModule

    def importExternal(self, moduleName:str, importedName:str, moduleSource:Optional[Path]=None) -> PyNameScope:
        module:PyModuleExternal = PyModuleExternal(moduleName=moduleName, moduleSource=moduleSource)
        module = self._registerExernalModule(externalModule=module)
        return module.getNameScope(nameScope=importedName)

