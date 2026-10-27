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
from .py_namescope import PyNameScope
from .py_includes import PyIncludesAny
from .py_labels import PyVisibility
from .py_namescope import PyNameScope
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.comment import Comment, CommentAny

class PyEnumEntry:
    def __init__(self, enumEntryName:str, enumEntryValue:int, enumEntryDefault:bool=False, brief:CommentAny=None):
        self.m_enumEntryName   :str  = enumEntryName
        self.m_enumEntryValue  :int  = enumEntryValue
        self.m_enumEntryDefault:bool = enumEntryDefault
        self.m_comment:Comment = Comment(commentAny=brief)

class PyEnumBase(PyNameScope):
    def __init__(
            self, 
            enumClassName:str,
            enumEntries:list[PyEnumEntry] = list(),
            pyIncludesAny:PyIncludesAny=None,
            extensions:ExtensionsAny=None,
            brief:CommentAny=None,
            visibility:PyVisibility=PyVisibility.PUBLIC,
        ):
        super().__init__(nameScope=enumClassName, pyIncludesAny=pyIncludesAny, extensions=extensions, visibility=visibility)
        self.m_enumEntries:list[PyEnumEntry] = list()
        self.m_enumEntries += enumEntries
        self.m_comment:Comment = Comment(commentAny=brief)

    def getDefaultEntry(self) -> PyEnumEntry:
        for enumEntry in self.m_enumEntries:
            if enumEntry.m_enumEntryDefault:
                return enumEntry
        assert(False)
