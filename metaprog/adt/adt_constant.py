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
from .adt_type import AdtType

class AdtConstant:
    def __init__(
            self, 
            constantName:str, 
            constantType:AdtType,
            constantValue:str,
            extensions:ExtensionsAny=None, 
            brief:CommentAny=None,
        ):
        self.m_constantName:str = constantName
        self.m_constantType:AdtType = constantType
        self.m_constantValue:str = constantValue
        self.m_extensions:Extensions = Extensions(extensions=extensions)
        self.m_brief:CommentAny = brief
