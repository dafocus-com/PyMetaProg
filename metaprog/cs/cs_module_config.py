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
from .cs_usings import CsUsings

class CsModuleConfig:
    '''! Configuration data for a .cs and an optional .cpp file '''
    def __init__(self, csFilePath:Path) -> None:
        self.m_moduleComment:Comment = Comment()

        self.m_csPreUsings:FreeText = FreeText()
        self.m_csUsings:CsUsings = CsUsings()
        self.m_csPostUsings:FreeText = FreeText()
        self.m_csFooter:FreeText = FreeText()

        self.m_csFilePath:Path = csFilePath

    def usingModuleInCs(self, otherModule:CsModuleConfig):
        '''! Add the include related to `otherModule` to this module .cpp file '''
        #self.m_cppUsings.addRelativeToOtherFile(otherModule.m_csFilePath, self.m_cppFilePath)
        pass # TBD

