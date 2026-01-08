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
from typing import Optional
from .adt_field import AdtField
from metaprog.util.extensions import Extensions, ExtensionsAny
from metaprog.util.comment import CommentAny
from typing import Any, Optional

class AdtClass:
    def __init__(self, className:str, baseClass:Optional[AdtClass]=None, fields:list[AdtField]=list(), extensions:ExtensionsAny=None, brief:CommentAny=None):
        self.m_className:str = className
        self.m_baseClass:Optional[AdtClass] = baseClass
        self.m_fields:list[AdtField]=list()
        self.m_fields += fields
        self.m_extensions:Extensions = Extensions(extensions=extensions)
        self.m_brief:CommentAny = brief

    def getExtOrNone(self, key:str) -> Optional[Any]:
        '''! Returns the value if the key exists in the extension of this class or
             one the base classes; otherwise, it returns `None` '''

        ret:Optional[Any] = self.m_extensions.getValueOrNone(key=key);
        if ret is None and self.m_baseClass:
            return self.m_baseClass.getExtOrNone(key=key)
        return ret
