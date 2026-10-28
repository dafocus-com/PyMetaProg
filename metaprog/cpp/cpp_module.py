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
from .cpp_config import CppConfig
from .cpp_namescope import CppNameScope
from metaprog.util.sourcefile import SourceFile
from metaprog.util.writable_brige import WritableBridge
from metaprog.util.writable_set import WritableSet
from metaprog.util.config import Config
from metaprog.util.comment import CommentAny

from .cpp_generable import CppGenerable
from .cpp_module_config import CppModuleConfig
from .cpp_children_container import CppChildrenContainer
from typing import TYPE_CHECKING 
if TYPE_CHECKING: 
    from .cpp_namescope import CppNameScope

class CppModule(CppModuleConfig, CppChildrenContainer):
    '''! Represents a .hpp and an optional .cpp file '''
    def __init__(self, hppFilePath:Path, cppFilePath:Path, config:CppConfig, brief:CommentAny=None) -> None:
        super().__init__(hppFilePath=hppFilePath, cppFilePath=cppFilePath, config=config, brief=brief)
        self.m_generables:list[CppGenerable] = list()

    def __writeCpp(self, writer:Writer, config:Config) -> None:
        assert(isinstance(config, CppConfig))
        for generable in self.m_generables:
            generable.generateCppBody(writer=writer, config=self.m_config)

    def __writeHpp(self, writer:Writer, config:Config) -> None:
        assert(isinstance(config, CppConfig))
        needsInline:bool = False
        for generable in self.m_generables:
            if generable.needsInline(): needsInline=True

        for generable in self.m_generables:
            generable.generateHppBody(writer, config)
        if needsInline:
            writer.write(r'''
                /**************************************
                |    ___       _ _                    |
                |   |_ _|_ __ | (_)_ __   ___  ___    |
                |    | || '_ \| | | '_ \ / _ \/ __|   |
                |    | || | | | | | | | |  __/\__ \   |
                |   |___|_| |_|_|_|_| |_|\___||___/   |
                |                                     |
                ***************************************/
            
            ''')
            for generable in self.m_generables:
                generable.generateHppInline(writer=writer, config=config)


    def addGenerableChild(self, generable:CppGenerable) -> None:
        assert(generable.m_moduleConfig is None)
        self.m_generables.append(generable)
        generable.m_moduleConfig = self

    def addChild(self, child:CppNameScope) -> None:
        self.addGenerableChild(generable=child)

    def generate(self) -> None:
        for generable in self.m_generables:
            generable.setupModuleConfig(self)

        needsCpp:bool = False
        for generable in self.m_generables:
            if generable.needsCpp(): needsCpp=True

        hppWritable:WritableBridge = WritableBridge(self, CppModule.__writeHpp)
        hppSourceFile:SourceFile = SourceFile(self.m_hppFilePath)

        hppSourceFile.m_writables.append(self.m_moduleComment)
        hppSourceFile.m_writables.append(WritableSet(text="#pragma once", autoReturnAtEnd=True))
        hppSourceFile.m_writables.append(self.m_hppPreIncludesHeader)
        hppSourceFile.m_writables.append(self.m_hppIncludes)
        hppSourceFile.m_writables.append(self.m_hppPostIncludesHeader)
        hppSourceFile.m_writables.append(hppWritable)
        hppSourceFile.m_writables.append(self.m_hppFooter)

        hppSourceFile.write(self.m_config)

        if needsCpp:
            self.m_cppIncludes.addRelativeToOtherFile(includedFile=self.m_hppFilePath, includingFile=self.m_cppFilePath)

            cppWritable:WritableBridge = WritableBridge(self, CppModule.__writeCpp)
            cppSourceFile:SourceFile = SourceFile(self.m_cppFilePath)

            cppSourceFile.m_writables.append(self.m_moduleComment)
            cppSourceFile.m_writables.append(self.m_cppPreIncludesHeader)
            cppSourceFile.m_writables.append(self.m_cppIncludes)
            cppSourceFile.m_writables.append(self.m_cppPostIncludesHeader)
            cppSourceFile.m_writables.append(cppWritable)
            cppSourceFile.m_writables.append(self.m_cppFooter)
            cppSourceFile.write(self.m_config)
        else:
            #print(f'.cpp file {self.m_cppFilePath} not required')
            pass