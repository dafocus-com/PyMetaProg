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
from typing import Optional, Union, TypeAlias
from metaprog.util.writer import Writer
from metaprog.util.writable import Writable
from metaprog.util.config import Config
from .cs_config import CsConfig

class CsUsing(Writable):
    '''! A single using '''
    def __init__(self, usingName:str) -> None:
        '''! Constructor
        @param usingName   Name of the file to be usingd
        '''
        self.m_usingName:str = usingName

    def write(self, writer:Writer, config:Config)->None:
        writer.writeRaw(f'using {self.m_usingName};\n')

class CsDirective(Writable):
    '''! A single hash '#something...' '''
    def __init__(self, directiveName:str) -> None:
        '''! Constructor
        @param directiveName   Name of the file to be directived
        '''
        self.m_directiveName:str = directiveName

    def write(self, writer:Writer, config:Config)->None:
        writer.writeRaw(f'{self.m_directiveName}\n')

CsUsingsAny:TypeAlias = Optional[list[Union[str,CsUsing]]]
CsDirectivesAny:TypeAlias = Optional[list[Union[str,CsDirective]]]

class CsUsings(Writable):
    '''! A set of usings '''
    def __init__(self, usings:CsUsingsAny=None, directives:CsDirectivesAny=None) -> None:
        '''! Constructor
        @param usings   A list of usings that can be specified as 'foobar.h' or '<cstring>'
        '''
        self.m_usings:list[CsUsing] = list()
        if usings is not None:
            for using in usings:
                self.add(using=using)

        self.m_directives:list[CsDirective] = list()
        if directives is not None:
            for directive in directives:
                self.addDirective(directive=directive)

    def add(self, using:str|CsUsing):
        '''! Add an using
        @param usingName   Name of the file to be added with using
        '''
        if isinstance(using, CsUsing):
            usingName:str = using.m_usingName
        else:
            usingName:str = using
        for using in self.m_usings:
            if using.m_usingName == usingName:
                return
        self.m_usings.append(CsUsing(usingName=usingName))

    def addDirective(self, directive:str|CsDirective):
        '''! Add a directive
        @param directiveName   Text of the directive "#..."
        '''
        if isinstance(directive, CsDirective):
            directiveName:str = directive.m_directiveName
        else:
            directiveName:str = directive
        for directive in self.m_directives:
            if directive.m_directiveName == directiveName:
                return
        self.m_directives.append(CsDirective(directiveName=directiveName))

    def merge(self, other:CsUsings):
        for using in other.m_usings:
            self.add(using=using.m_usingName)
        for directive in other.m_directives:
            self.addDirective(directive=directive.m_directiveName)

    def write(self, writer:Writer, config:Config)->None:
        assert(isinstance(config, CsConfig))
        for using in self.m_usings:
            using.write(writer, config)
        for directive in self.m_directives:
            directive.write(writer, config)            