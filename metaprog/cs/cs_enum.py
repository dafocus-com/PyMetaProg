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
from .cs_enum_base import CsEnumBase, CsEnumEntry
from .cs_usings import CsUsingsAny
from .cs_type import CsTypeAny, CsType, CsTypeSimple, CsTypeFactory
from .cs_config import CsConfig
from metaprog.util.writer import Writer
from metaprog.util.extensions import *
from metaprog.util.comment import *

class CsEnum(CsEnumBase):
    def __init__(
            self, 
            enumClassName:str,
            enumEntries:list[CsEnumEntry] = list(),
            enumType:CsTypeAny=CsTypeSimple(simpleType="uint"),
            csUsings:CsUsingsAny=None,
            extensions:ExtensionsAny=None,
            brief:CommentAny=None,
        ):
        super().__init__(enumClassName=enumClassName, csUsings=csUsings, extensions=extensions, enumEntries=enumEntries, brief=brief)
        self.m_enumType:CsType = CsTypeFactory(enumType)

    def generateCsBody(self, writer:Writer, config:CsConfig)->None:
        self.m_comment.write(writer, config)
        writer.writeNL(f"{self.m_visibility.toStr()} enum {self.getCsUnqualifiedName()}: {self.m_enumType.toString(containerClass=self)} {{")
        writer.incIndent()
        for enumEntry in self.m_enumEntries:
            enumEntry.m_comment.write(writer, config)
            writer.writeNL(f'{enumEntry.m_enumEntryName} = {enumEntry.m_enumEntryValue},')
        
        writer.decIndent()
        writer.writeNL("}")
