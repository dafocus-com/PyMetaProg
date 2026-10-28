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
from .cpp_enum_base import CppEnumBase, CppEnumEntry
from .cpp_includes import CppIncludesAny
from .cpp_type import CppTypeAny, CppType, CppTypeSimple, CppTypeFactory
from .cpp_config import CppConfig
from .cpp_module_config import CppModuleConfig
from metaprog.util.writer import Writer
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.comment import Comment, CommentAny
from metaprog.util.log import logError

class CppEnum(CppEnumBase):
    def __init__(
            self, 
            enumClassName:str,
            enumEntries:list[CppEnumEntry] = list(),
            enumType:CppTypeAny=CppTypeSimple(simpleType="uint32_t", includes='cstdint'),
            hppIncludes:CppIncludesAny=None,
            cppIncludes:CppIncludesAny=None,
            extensions:ExtensionsAny=None,
            brief:CommentAny=None,
        ):
        super().__init__(enumClassName=enumClassName, hppIncludes=hppIncludes, cppIncludes=cppIncludes, extensions=extensions, enumEntries=enumEntries)
        self.m_enumType:CppType = CppTypeFactory(enumType)
        self.m_comment:Comment = Comment(commentAny=brief)
        self.m_hppIncludes.add('iostream')

    def setupModuleConfig(self, moduleConfig:CppModuleConfig) -> None:
        super().setupModuleConfig(moduleConfig=moduleConfig)
        defaultEntries:int = 0
        for enumEntry in self.m_enumEntries:
            if enumEntry.m_enumEntryDefault:
                defaultEntries += 1
        if defaultEntries==0:
            logError(f"No default entry for enum {self.getCppQualifiedName()}")
        elif defaultEntries!=1:
            logError(f"Too many default entries ({defaultEntries}) for enum {self.getCppQualifiedName()}")


    def generateHppBody(self, writer:Writer, config:CppConfig) -> None:
        self.m_comment.write(writer, config)
        writer.writeNL(f"enum class {self.getCppUnqualifiedName()}: {self.m_enumType.toString(containerClass=self)} {{")
        writer.incIndent()
        for enumEntry in self.m_enumEntries:
            enumEntry.m_comment.write(writer, config)
            writer.writeNL(f'{enumEntry.m_enumEntryName} = {enumEntry.m_enumEntryValue},')
        
        writer.decIndent()
        writer.writeNL("};")

        writer.writeNL(f'// Print function for enum {self.getCppUnqualifiedName()}')
        writer.writeNL(f'inline std::ostream& operator<<(std::ostream& o, {self.getCppUnqualifiedName()} e) {{')
        writer.incIndent()
        writer.writeNL('switch(e) {')
        writer.incIndent()

        for enumEntry in self.m_enumEntries:
            writer.writeNL(f'case {self.getCppUnqualifiedName()}::{enumEntry.m_enumEntryName}: o << "{enumEntry.m_enumEntryName}"; break;')

        writer.writeNL(f'default: o << "UNKNOWN(" << ({self.m_enumType.toString(containerClass=self)})e << ")";')
        writer.decIndent()
        writer.writeNL('}')
        writer.writeNL('return o;')
        writer.decIndent()
        writer.writeNL('}')
