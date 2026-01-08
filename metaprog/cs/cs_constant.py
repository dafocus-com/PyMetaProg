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
from .cs_namescope import CsNameScope
from .cs_usings import CsUsingsAny
from .cs_type import CsTypeAny, CsType, CsTypeSimple, CsTypeFactory
from .cs_config import CsConfig
from .cs_module_config import CsModuleConfig
from .cs_rvalue import CsRValue
from .cs_namespace import *
from metaprog.util.writer import Writer
from metaprog.util.extensions import *
from metaprog.util.comment import *
from metaprog.util.log import *

class CsConstant(CsNameScope, CsRValue):
    def __init__(
            self, 
            constantName:str,
            constantType:CsTypeAny=CsTypeSimple(simpleType="uint32_t"),
            csUsings:CsUsingsAny=None,
            extensions:ExtensionsAny=None,
            brief:CommentAny=None,
            valueName:str="Value"
        ):
        super().__init__(nameScope=constantName, csUsings=csUsings, extensions=extensions)
        self.m_constantType:CsType = CsTypeFactory(constantType)
        self.m_comment:Comment = Comment(commentAny=brief)
        self.m_valueName:str = valueName

    def setupModuleConfig(self, moduleConfig:CsModuleConfig)->None:
        super().setupModuleConfig(moduleConfig=moduleConfig)

    def generateCsBody(self, writer:Writer, config:CsConfig)->None:
        self.m_comment.write(writer, config)
        
        if isinstance(self.m_parent, CsNamespace):
            writer.writeNL(f"public static class {self.getCsUnqualifiedName()} {{")
            writer.incIndent()
            writer.writeNL(f"public const {self.m_constantType.toString(containerClass=self)} {self.m_valueName} = {self.m_constantType.getAssigneableDefaultValue(self)};")
            writer.decIndent()
            writer.writeNL('}')
        else:
            writer.writeNL(f"public const {self.m_constantType.toString(containerClass=self)} {self.getCsUnqualifiedName()} = {self.m_constantType.getAssigneableDefaultValue(self)};")

    def generateValue(self, writer:Writer, config:CsConfig, otherScope:Optional[CsNameScope]=None)->None:
        '''! Generate the R-value text '''
        if isinstance(self.m_parent, CsNamespace):
            writer.writeRaw(f'{self.getCsQualifiedName(otherScope=otherScope)}.{self.m_valueName}')
        else:
            writer.writeRaw(self.getCsQualifiedName(otherScope=otherScope))
