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

from .cpp_includes import CppIncludes, CppIncludesAny
from .cpp_module_config import CppModuleConfig
from .cpp_config import CppConfig
from .cpp_type import CppType, CppTypeFactory, CppTypeAny
from .cpp_class_element import CppClassElement
from typing import Optional
from metaprog.util.comment import Comment, CommentAny
from metaprog.util.comment_entry import COMMENT_PARAM
from metaprog.util.writer import Writer

class CppParam:
    '''! CppMethod parameter '''
    def __init__(
        self, 
        paramName:str, 
        paramType:CppTypeAny,
        paramDefault:Optional[str] = None,
        paramComment:CommentAny = None,
        hppIncludes:CppIncludesAny = None,
        cppIncludes:CppIncludesAny = None,
        mayBeUnused:bool = False,
        variadic:bool = False,
    ):
        self.m_paramName:str = paramName
        self.m_paramType:CppType = CppTypeFactory(paramType)
        self.m_paramDefault:Optional[str] = paramDefault
        self.m_paramComment:Comment = Comment(commentAny=paramComment, commandIfString=COMMENT_PARAM, paramIfString=paramName)
        self.m_hppIncludes:CppIncludes = CppIncludes(incls=hppIncludes)
        self.m_cppIncludes:CppIncludes = CppIncludes(incls=cppIncludes)
        self.m_mayBeUnused:bool = mayBeUnused
        self.m_owningMehod:Optional[CppClassElement] = None

    def addToComment(self, comment:Comment) -> None:
        comment.merge(other=self.m_paramComment)

    def writeDecl(self, writer:Writer, config:CppConfig, withDefault:bool) -> None:
        mayBeUnused:str = ""
        if not withDefault and self.m_mayBeUnused:
            mayBeUnused = "[[maybe_unused]] "
        defaultCode:str = ""
        if withDefault and self.m_paramDefault:
            defaultCode = f' = {self.m_paramDefault}'
        writer.writeRaw(f'{mayBeUnused}')
        assert(self.m_owningMehod is not None)
        self.m_paramType.declVar(writer=writer, config=config, var=self.m_paramName, containerClass=self.m_owningMehod.getCppClass())
        writer.writeRaw(f'{defaultCode}')

    def setupModuleConfig(self, moduleConfig:CppModuleConfig) -> None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        moduleConfig.m_hppIncludes.merge(self.m_hppIncludes)
        moduleConfig.m_cppIncludes.merge(self.m_cppIncludes)
        moduleConfig.m_hppIncludes.merge(self.m_paramType.m_includes)