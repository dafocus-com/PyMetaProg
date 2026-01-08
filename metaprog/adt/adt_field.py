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

from .adt_type import AdtType
from metaprog.util.extensions import Extensions, ExtensionsAny
from metaprog.util.comment import *
from .adt_constant import AdtConstant
from typing import Optional

class AdtField:
    def __init__(
            self, 
            fieldName:str, 
            fieldType:AdtType,
            fieldDefault:Optional[AdtConstant]=None,
            extensions:ExtensionsAny=None, 
            brief:CommentAny=None
        ):
        self.m_fieldName:str = fieldName
        self.m_fieldType:AdtType = fieldType
        self.m_fieldDefault:Optional[AdtConstant] = fieldDefault
        self.m_extensions:Extensions = Extensions(extensions=extensions)
        self.m_brief:CommentAny = brief