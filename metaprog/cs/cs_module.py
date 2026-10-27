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

from pathlib import Path
from metaprog.util.writer import Writer
from .cs_config import CsConfig
from metaprog.util.sourcefile import SourceFile
from metaprog.util.writable_brige import WritableBridge
from metaprog.util.config import Config

from .cs_generable import CsGenerable
from .cs_module_config import CsModuleConfig

class CsModule(CsModuleConfig):
    '''! Represents a .hpp and an optional .cs file '''
    def __init__(self, csFilePath:Path) -> None:
        super().__init__(csFilePath=csFilePath)
        self.m_generables:list[CsGenerable] = list()

    def __writeCs(self, writer:Writer, config:Config) -> None:
        assert(isinstance(config, CsConfig))
        for generable in self.m_generables:
            generable.generateCsBody(writer=writer, config=config)


    def addChild(self, generable:CsGenerable) -> None:
        assert(generable.m_moduleConfig is None)
        self.m_generables.append(generable)
        generable.m_moduleConfig = self

    def generate(self, config:CsConfig) -> None:
        for generable in self.m_generables:
            generable.setupModuleConfig(self) # type: ignore

        csWritable:WritableBridge = WritableBridge(self, CsModule.__writeCs)
        csSourceFile:SourceFile = SourceFile(self.m_csFilePath)

        csSourceFile.m_writables.append(self.m_moduleComment)
        csSourceFile.m_writables.append(self.m_csPreIncludes)
        csSourceFile.m_writables.append(self.m_csIncludes)
        csSourceFile.m_writables.append(self.m_csPostIncludes)
        csSourceFile.m_writables.append(csWritable)
        csSourceFile.m_writables.append(self.m_csFooter)
        csSourceFile.write(config)
