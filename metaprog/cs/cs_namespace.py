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
from .cs_namescope_with_children import CsNameScopeWithChildren
from metaprog.util.writer import Writer
from .cs_config import CsConfig
from typing import Optional

class CsNamespace(CsNameScopeWithChildren):
    def __init__(self, namespaceName:str, generateAsClass:bool=False) -> None:
        super().__init__(nameScope=namespaceName)

        self.__prevNamespace:Optional[CsNamespace] = None
        self.__generateAsClass:bool = generateAsClass

    def __enterNamespace(self, writer:Writer, config:CsConfig) -> None:
        self.__prevNamespace = config.m_csCurrentNameScope # type: ignore
        config.m_csCurrentNameScope = self
        if self.__generateAsClass:
            writer.writeNL(f'public static class {self.getCsUnqualifiedName()} {{')
        else:
            writer.writeNL(f'namespace {self.getCsUnqualifiedName()} {{')
        writer.incIndent()

    def __exitNamespace(self, writer:Writer, config:CsConfig) -> None:
        writer.decIndent()
        writer.writeNL(f'}} // namespace {self.getCsUnqualifiedName()}')
        config.m_csCurrentNameScope = self.__prevNamespace

    def generateCsBody(self, writer:Writer, config:CsConfig) -> None:
        self.__enterNamespace(writer, config)
        super().generateCsBody(writer, config)
        self.__exitNamespace(writer, config)

