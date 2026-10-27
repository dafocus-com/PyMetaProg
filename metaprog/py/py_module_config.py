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
from .py_namescope_with_children import PyNameScopeWithChildren
from .py_includes import PyIncludesAny
from .py_labels import PyVisibility
from metaprog.util.comment import Comment
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.freetext import FreeText

class PyModuleConfig(PyNameScopeWithChildren):
    '''! Configuration data for a .py file '''
    def __init__(
            self,
            moduleName:str,
            pyIncludesAny:PyIncludesAny=None,
            extensions:ExtensionsAny=None,
        ) -> None:
        super().__init__(nameScope=moduleName, pyIncludesAny=pyIncludesAny, extensions=extensions, visibility=PyVisibility.PUBLIC)
        self.m_moduleComment:Comment = Comment()
        self.m_pyHeader:FreeText = FreeText()
        self.m_pyFooter:FreeText = FreeText()

    def isModule(self) -> bool: return True
