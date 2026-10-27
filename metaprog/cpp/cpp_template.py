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
from enum import Enum
from typing import Optional
from metaprog.util.comment import Comment, CommentAny
from metaprog.util.comment_entry import COMMENT_TEMPLATE_ARG
from metaprog.util.writer import Writer
from .cpp_config import CppConfig

class CppTemplateTarget(Enum):
    DECL_WITH_DEFAULTS=1,  # Declaration with default values if specified. Example: <class A, int B=2>
    REDECL=2,              # Declaration without defaults. Example: <class A, int B>
    INVOCATION=3,          # Invocation. Example: <A, B>

class CppTemplateArgument:
    def __init__(
            self, 
            argumentName:str, 
            argumentDefault:Optional[str]=None, 
            argumentConcept:str="typename",
            brief:CommentAny=None,
            variadic:bool = False
        ) -> None:
        self.m_argumentName:str = argumentName
        self.m_argumentDefault:Optional[str] = argumentDefault
        self.m_argumentConcept:str = argumentConcept
        self.m_comment:Comment = Comment(commentAny=brief, commandIfString=COMMENT_TEMPLATE_ARG)
        self.m_variadic:bool = variadic
    
    def getArgument(self, target:CppTemplateTarget) -> str:
        variadic:str = "..." if self.m_variadic else ""
        if target==CppTemplateTarget.DECL_WITH_DEFAULTS and self.m_argumentDefault is not None:
            return f'{self.m_argumentConcept}{variadic} {self.m_argumentName} = {self.m_argumentDefault}'
        if target==CppTemplateTarget.INVOCATION:
            return self.m_argumentName
        return f'{self.m_argumentConcept}{variadic} {self.m_argumentName}'

    def addToComment(self, comment:Comment) -> None:
        comment.merge(self.m_comment)

class CppTemplate:
    def __init__(self, templateArguments:list[CppTemplateArgument]=list()) -> None:
        self.m_templateArguments:list[CppTemplateArgument] = templateArguments
    
    # Generates template<...>
    def getTemplateDecl(self, writer:Writer, config:CppConfig, withDefaults:bool) -> None:
        if len(self.m_templateArguments) == 0:
            return
        
        args:list[str] = list()
        for arg in self.m_templateArguments:
            args.append(arg.getArgument(target=CppTemplateTarget.DECL_WITH_DEFAULTS if withDefaults else CppTemplateTarget.REDECL))
        
        writer.writeNL(f'template<{", ".join(args)}>')
        

    def addToComment(self, comment:Comment) -> None:
        for arg in self.m_templateArguments:
            arg.addToComment(comment)


CppTemplateArguments = list[CppTemplateArgument]
