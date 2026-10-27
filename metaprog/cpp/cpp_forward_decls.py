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
from .cpp_namescope import CppNameScope
from metaprog.util.writer import Writer
from metaprog.util.writable import Writable
from metaprog.util.config import Config
from metaprog.util.writable import Writable
from .cpp_config import CppConfig
from typing import Optional

class CppForwardDecls(Writable):
    '''! A single forward declaration '''
    def __init__(self, homeNameScope:Optional[CppNameScope]) -> None:
        self.m_homeNameScope:Optional[CppNameScope] = homeNameScope
        self.m_classes:set[CppNameScope] = set()
        self.m_texts:set[str] = set()

    def addClass(self, cppNameScope:CppNameScope) -> None:
        self.m_classes.add(cppNameScope)

    def addText(self, text:str) -> None:
        self.m_texts.add(text)
    
    def write(self, writer: Writer, config: Config) -> None:
        assert (isinstance(config, CppConfig))
        for cls in self.m_classes:
            writer.writeNL(f"class {cls.getCppQualifiedName(otherScope=self.m_homeNameScope)};")
        for txt in self.m_texts:
            writer.writeNL(txt)

