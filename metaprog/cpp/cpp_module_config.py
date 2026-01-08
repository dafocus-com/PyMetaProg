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
from pathlib import Path
from metaprog.util.comment import *
from metaprog.util.freetext import FreeText
from .cpp_includes import CppIncludes
from .cpp_config import CppConfig

class CppModuleConfig:
    '''! Configuration data for a .hpp and an optional .cpp file '''
    def __init__(self, hppFilePath:Path, cppFilePath:Path, config:CppConfig, brief:CommentAny=None) -> None:
        self.m_moduleComment:Comment = Comment(commentAny=brief)

        self.m_hppPreIncludesHeader:FreeText = FreeText()
        self.m_hppIncludes:CppIncludes = CppIncludes()
        self.m_hppPostIncludesHeader:FreeText = FreeText()
        self.m_hppFooter:FreeText = FreeText()

        self.m_cppPreIncludesHeader:FreeText = FreeText()
        self.m_cppIncludes:CppIncludes = CppIncludes()
        self.m_cppPostIncludesHeader:FreeText = FreeText()
        self.m_cppFooter:FreeText = FreeText()

        self.m_hppFilePath:Path = hppFilePath
        self.m_cppFilePath:Path = cppFilePath

        self.m_config:CppConfig = config

    def includeModuleInCpp(self, otherModule:CppModuleConfig):
        '''! Add the include related to `otherModule` to this module .cpp file '''
        self.m_cppIncludes.addRelativeToOtherFile(otherModule.m_hppFilePath, self.m_cppFilePath)

    def includeModuleInHpp(self, otherModule:CppModuleConfig):
        '''! Add the include related to `otherModule` to this module .hpp file '''
        self.m_hppIncludes.addRelativeToOtherFile(otherModule.m_hppFilePath, self.m_hppFilePath)