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
from .py_config import PyConfig
from .py_includes import PyIncludesAny
from .py_labels import PyVisibility
from .py_namescope import PyNameScope
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.writer import Writer
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .py_module_config import PyModuleConfig

class PyNameScopeWithChildren(PyNameScope):
    '''! Objects that have a name scope like namespaces and classes '''
    def __init__(
            self, 
            nameScope:str,
            pyIncludesAny:PyIncludesAny=None,
            extensions:ExtensionsAny=None,
            visibility:PyVisibility = PyVisibility.PUBLIC,
        ) -> None:
        super().__init__(nameScope=nameScope, pyIncludesAny=pyIncludesAny, extensions=extensions, visibility=visibility)
        self.m_children:list[PyNameScope] = list()

    def addChild(self, child:PyNameScope) -> None:
        assert(child.m_parent is None)
        child.m_parent = self
        self.m_children.append(child)

    def setupModuleConfig(self, moduleConfig:PyModuleConfig) -> None:
        super().setupModuleConfig(moduleConfig=moduleConfig)
        for child in self.m_children:
            child.setupModuleConfig(moduleConfig=moduleConfig)

    def generatePyBody(self, writer:Writer, config:PyConfig) -> None:
        for child in self.m_children:
            child.generatePyBody(writer=writer, config=config)
