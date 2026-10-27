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
from .py_namescope_with_children import PyNameScopeWithChildren
from metaprog.util.writer import Writer
from pathlib import Path

class PyNamespace(PyNameScopeWithChildren):
    def __init__(self, namespaceName:str) -> None:
        super().__init__(nameScope=namespaceName)

    def generatePyBody(self, writer:Writer, config:PyConfig) -> None:
        super().generatePyBody(writer, config)

    def generate(self, config:PyConfig, pyFilePath:Path) -> None:
        namespacePath:Path = pyFilePath / self.m_nameScope
        for child in self.m_children:
            child.generate(config=config, pyFilePath=namespacePath)

    def isModule(self) -> bool: return True
        