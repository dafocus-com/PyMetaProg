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
from .py_enum_base import PyEnumBase, PyEnumEntry
from .py_includes import PyIncludesAny
from .py_config import PyConfig
from metaprog.util.writer import Writer
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.comment import CommentAny

class PyEnum(PyEnumBase):
    def __init__(
            self, 
            enumClassName:str,
            enumEntries:list[PyEnumEntry] = list(),
            pyIncludesAny:PyIncludesAny=None,
            extensions:ExtensionsAny=None,
            brief:CommentAny=None,
        ):
        super().__init__(enumClassName=enumClassName, pyIncludesAny=pyIncludesAny, extensions=extensions, enumEntries=enumEntries, brief=brief)
        self.m_pyIncludes.importFrom(moduleName='enum', name='Enum')

    def generatePyBody(self, writer:Writer, config:PyConfig) -> None:
        self.m_comment.write(writer, config)
        writer.writeNL(f"class {self.getPyUnqualifiedName()}(Enum):")
        writer.incIndent()
        for enumEntry in self.m_enumEntries:
            enumEntry.m_comment.write(writer, config)
            writer.writeNL(f'{enumEntry.m_enumEntryName} = {enumEntry.m_enumEntryValue}')
        
        writer.decIndent()
