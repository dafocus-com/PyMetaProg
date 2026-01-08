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
from metaprog.util.extensions import Extensions, ExtensionsAny
from metaprog.util.comment import CommentAny

class AdtEnumEntry:
    def __init__(self, enumEntryName:str, enumEntryValue:int, enumEntryDefault:bool=False, brief:CommentAny=None):
        self.m_enumEntryName   :str  = enumEntryName
        self.m_enumEntryValue  :int  = enumEntryValue
        self.m_enumEntryDefault:bool = enumEntryDefault
        self.m_brief:CommentAny = brief

class AdtEnum:
    def __init__(
            self, 
            enumName:str, 
            enumEntries:list[AdtEnumEntry] = list(),
            extensions:ExtensionsAny=None, 
            brief:CommentAny=None,
        ):
        self.m_enumName:str = enumName
        self.m_extensions:Extensions = Extensions(extensions=extensions)
        self.m_brief:CommentAny = brief
        self.m_enumEntries:list[AdtEnumEntry] = list()
        self.m_enumEntries += enumEntries
