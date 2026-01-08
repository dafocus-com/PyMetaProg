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

from .cs_usings import CsUsings, CsUsingsAny
from .cs_module_config import CsModuleConfig
from .cs_config import CsConfig
from .cs_type import *
from .cs_class_element import CsClassElement
from typing import Optional
from metaprog.util.comment import *

class CsParam:
    '''! CsMethod parameter '''
    def __init__(
        self, 
        paramName:str, 
        paramType:CsTypeAny,
        paramDefault:Optional[str] = None,
        paramComment:CommentAny = None,
        csUsings:CsUsingsAny = None,
        isRef:bool = False,
    ):
        self.m_paramName:str = paramName
        self.m_paramType:CsType = CsTypeFactory(paramType)
        self.m_paramDefault:Optional[str] = paramDefault
        self.m_paramComment:Comment = Comment(commentAny=paramComment, commandIfString=COMMENT_PARAM, paramIfString=paramName)
        self.m_csUsings:CsUsings = CsUsings(usings=csUsings)
        self.m_owningMehod:Optional[CsClassElement] = None
        self.m_isRef:bool = isRef

    def addToComment(self, comment:Comment)->None:
        comment.merge(other=self.m_paramComment)

    def writeDecl(self, writer:Writer, config:CsConfig) -> None:
        defaultCode:str = ""
        if self.m_paramDefault:
            defaultCode = f' = {self.m_paramDefault}'
        assert(self.m_owningMehod is not None)
        self.m_paramType.declVar(writer=writer, config=config, var=self.m_paramName, containerClass=self.m_owningMehod.getCsClass(), isRef=self.m_isRef)
        writer.writeRaw(f'{defaultCode}')

    def setupModuleConfig(self, moduleConfig:CsModuleConfig)->None:
        '''! Operate on the accessible parts of the module to add usings, header parts and so on '''
        moduleConfig.m_csUsings.merge(self.m_csUsings)
