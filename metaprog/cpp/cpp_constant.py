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
from .cpp_namescope import CppNameScope
from .cpp_includes import CppIncludesAny
from .cpp_type import CppTypeAny, CppType, CppTypeSimple, CppTypeFactory
from .cpp_config import CppConfig
from .cpp_module_config import CppModuleConfig
from .cpp_rvalue import CppRValue
from metaprog.util.writer import Writer
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.comment import Comment, CommentAny
from typing import Optional

class CppConstant(CppNameScope, CppRValue):
    def __init__(
            self, 
            constantName:str,
            constantType:CppTypeAny=CppTypeSimple(simpleType="uint32_t"),
            hppIncludes:CppIncludesAny=None,
            cppIncludes:CppIncludesAny=None,
            extensions:ExtensionsAny=None,
            brief:CommentAny=None,
        ):
        super().__init__(nameScope=constantName, hppIncludes=hppIncludes, cppIncludes=cppIncludes, extensions=extensions)
        self.m_constantType:CppType = CppTypeFactory(constantType)
        self.m_comment:Comment = Comment(commentAny=brief)

    def setupModuleConfig(self, moduleConfig:CppModuleConfig) -> None:
        super().setupModuleConfig(moduleConfig=moduleConfig)

    def generateHppBody(self, writer:Writer, config:CppConfig) -> None:
        self.m_comment.write(writer, config)
        writer.writeNL(f"constexpr {self.m_constantType.toString(containerClass=self)} {self.getCppUnqualifiedName()} = {self.m_constantType.getAssigneableDefaultValue(self)};")

    def generateValue(self, writer:Writer, config:CppConfig, otherScope:Optional[CppNameScope]=None) -> None:
        '''! Generate the R-value text '''
        writer.writeRaw(self.getCppQualifiedName(otherScope=otherScope))
