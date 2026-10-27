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
from .py_includes import PyIncludesAny, PY_IMPORT_PRIORITY_DEFAULT
from .py_module_config import PyModuleConfig
from .py_namescope import PyNameScope
from metaprog.util.config import Config
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.sourcefile import SourceFile
from metaprog.util.writable_brige import WritableBridge
from metaprog.util.writable_set import WritableSet, WritableSetAny
from metaprog.util.writer import Writer
from pathlib import Path
from typing import Optional

class PyModule(PyModuleConfig):
    '''! Represents a single .py file with all of its contents '''
    def __init__(self, 
            moduleName:str,
            pyIncludesAny:PyIncludesAny=None,
            extensions:ExtensionsAny=None,
            # Code written at top level at the end of the module
            moduleCode:WritableSetAny=None,
        ) -> None:
        super().__init__(moduleName=moduleName, pyIncludesAny=pyIncludesAny, extensions=extensions)
        self.m_moduleCode:WritableSet = WritableSet(moduleCode)

    def __writePy(self, writer:Writer, config:Config) -> None:
        assert(isinstance(config, PyConfig))
        for generable in self.m_children:
            generable.generatePyBody(writer=writer, config=config)


    def generate(self, config:PyConfig, pyFilePath:Path) -> None:
        oldNameScope:Optional[PyNameScope] = config.m_pyCurrentNameScope
        config.m_pyCurrentNameScope = self
        modulePath:Path = pyFilePath / (self.m_nameScope+'.py')

        for generable in self.m_children:
            generable.setupModuleConfig(moduleConfig=self) # type: ignore

        pyWritable:WritableBridge = WritableBridge(self, PyModule.__writePy)
        pySourceFile:SourceFile = SourceFile(modulePath)
        self.__makeOwnPackageVisibleInSysPath()
        pySourceFile.m_writables.append(self.m_moduleComment)
        pySourceFile.m_writables.append(self.m_pyHeader)
        pySourceFile.m_writables.append(self.m_pyIncludes)
        pySourceFile.m_writables.append(pyWritable)
        pySourceFile.m_writables.append(self.m_pyFooter)
        pySourceFile.m_writables.append(self.m_moduleCode)
        pySourceFile.write(config)
        config.m_pyCurrentNameScope = oldNameScope

    def __makeOwnPackageVisibleInSysPath(self) -> None:
        parentsCount:int = 0
        curr:Optional[PyNameScope] = self.m_parent
        while curr is not None:
            parentsCount += 1
            curr = curr.m_parent

        self.m_pyIncludes.add(moduleName='sys', priority=PY_IMPORT_PRIORITY_DEFAULT-50)
        self.m_pyIncludes.add(moduleName='pathlib', imports=['Path'], priority=PY_IMPORT_PRIORITY_DEFAULT-50)
        self.m_pyIncludes.addText(moduleName='root_package', priority=PY_IMPORT_PRIORITY_DEFAULT-49, code=f'''\
            # Make sure that the root package is in the path for these scripts
            __rootPath:Path = Path(__file__){'.parent'*parentsCount}.resolve()
            if not str(__rootPath) in sys.path: sys.path.append(str(__rootPath))
        ''')