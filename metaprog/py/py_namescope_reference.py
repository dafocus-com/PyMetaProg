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
from .py_includes import PyIncludes

class PyNameScopeReferences:
    def __init__(self, modulePath:str, namePath:str):
        self.m_modulePath:str = modulePath
        self.m_namePath:str = namePath

    def importThisIntoOther(self, other:PyNameScopeReferences, otherImports:PyIncludes) -> None:
        if self.m_modulePath == other.m_modulePath: return
        if self.m_modulePath == '': return
        otherImports.add(moduleName=self.m_modulePath)
    
    def __str__(self) -> str:
        return f'<{self.m_modulePath}>-<{self.m_namePath}>'