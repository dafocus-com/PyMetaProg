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
from pathlib import Path
from metaprog.util.tools import customRelativeTo
from metaprog.util.writer import Writer
from metaprog.util.writable import Writable
from metaprog.util.config import Config
from .cpp_config import CppConfig
import re
import sys

class CppInclude:
    '''! A single include '''

    def __init__(self, includeName: str, systemInclude: bool) -> None:
        '''! Constructor
        @param includeName   Name of the file to be included
        @param systemInclude `True` if to be included with <...>; `False` for "..."
        '''
        self.m_includeName: str = includeName
        self.m_systemInclude: bool = systemInclude

    def __str__(self) -> str:
        if self.m_systemInclude:
            return f'#include <{self.m_includeName}>'
        else:
            return f'#include "{self.m_includeName}"'


CppIncludesAny: TypeAlias = Optional[list[Union[str, CppInclude]]]


class CppIncludes(Writable):
    '''! A set of includes '''

    def __init__(self, incls: CppIncludesAny = None) -> None:
        '''! Constructor
        @param incls   A list of includes that can be specified as 'foobar.h' or '<cstring>'
        '''
        self.m_includes: list[CppInclude] = list()
        if incls is not None:
            for incl in incls:
                if isinstance(incl, str):
                    self.add(includeName=incl, systemInclude=None)
                else:
                    self.add(includeName=incl.m_includeName, systemInclude=incl.m_systemInclude)

    def add(self, includeName: str, systemInclude: Optional[bool] = None):
        '''! Add an include
        @param includeName   Name of the file to be included
        @param systemInclude `True` if to be included with <...>; `False` for "..."
        '''
        if systemInclude is None:
            # If the include string is wrapped in <...>, activate "systemInclude"
            matchResult: Optional[re.Match[str]] = re.search(r'^\<(.+)\>$', includeName)
            if matchResult is not None:
                includeName = matchResult[1]
                systemInclude = True

            # Includes without an extension, like 'string' or 'cstdint' are automatically
            # converted to `systemInclude`
            elif not re.search(r'\.', includeName) or re.search(r'^dastd/', includeName):
                systemInclude = True
            else:
                systemInclude = False
        for include in self.m_includes:
            if include.m_includeName == includeName:
                if systemInclude and not include.m_systemInclude:
                    include.m_systemInclude = True
                return
        self.m_includes.append(CppInclude(includeName=includeName, systemInclude=systemInclude))

    def addRelativeToOtherFile(self, includedFile: Path, includingFile: Path,
                               systemInclude: Optional[bool] = False):
        '''! Add an include calculating the path relative to another file
        @param includedFile  File being included
        @param includingFile File that is including
        @param systemInclude `True` if to be included with <...>; `False` for "..."
        '''
        relative: Path = Path()
        versionTooOld: bool = False
        includedFile = includedFile.resolve()
        includingFile = includingFile.resolve()

        try:
            if sys.version_info[0] > 3 or sys.version_info[1] >= 12:
                # , walk_up=True - not available in python 3.9
                relative = includedFile.relative_to(includingFile.parent, walk_up=True)
            else:
                # , walk_up=True - not available in python 3.9
                relative = customRelativeTo(includedFile, includingFile.parent)
                versionTooOld = True
            
        except Exception as e:
            print(
                f"[ERROR] Error calculating the relative path while including `{includedFile}` into `{includingFile}`: {e}\n")
            if versionTooOld:
                print(
                    f"        This might be due that Python version {sys.version_info[0]}.{sys.version_info[1]} does not support parameter `walk_up`\n")
                print(f"        in function `PurePath.relative_to()`; this parameter is supported starting from 3.12, consider upgrading.\n")

            print(f"        Using the full path")
            relative = includedFile

        self.add(relative.as_posix(), systemInclude=systemInclude)

    def merge(self, other: CppIncludes):
        for incl in other.m_includes:
            self.add(includeName=incl.m_includeName, systemInclude=incl.m_systemInclude)

    def write(self, writer: Writer, config: Config) -> None:
        assert (isinstance(config, CppConfig))
        includes: list[str] = list()
        for include in self.m_includes:
            includes.append(str(include))
        includes.sort()
        for includeText in includes:
            writer.writeRaw(f'{includeText}\n')
