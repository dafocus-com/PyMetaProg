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
from .cpp_namescope_with_children import CppNameScopeWithChildren
from metaprog.util.writer import Writer
from .cpp_config import CppConfig

class CppNamespace(CppNameScopeWithChildren):
    def __init__(self, namespaceName:str) -> None:
        super().__init__(nameScope=namespaceName)

    def __enterNamespace(self, writer:Writer, config:CppConfig) -> None:
        self._enterNameScope(config=config)
        config.m_cppCurrentNameScope = self
        writer.writeNL(f'namespace {self.getCppUnqualifiedName()} {{')
        writer.incIndent()

    def __exitNamespace(self, writer:Writer, config:CppConfig) -> None:
        writer.decIndent()
        writer.writeNL(f'}} // namespace {self.getCppUnqualifiedName()}')
        self._exitNameScope(config=config)

    def generateHppBody(self, writer:Writer, config:CppConfig) -> None:
        self.__enterNamespace(writer, config)
        super().generateHppBody(writer, config)
        self.__exitNamespace(writer, config)

    def generateHppInline(self, writer:Writer, config:CppConfig) -> None:
        self.__enterNamespace(writer, config)
        super().generateHppInline(writer, config)
        self.__exitNamespace(writer, config)

    def generateCppBody(self, writer:Writer, config:CppConfig) -> None:
        self.__enterNamespace(writer, config)
        super().generateCppBody(writer, config)
        self.__exitNamespace(writer, config)

