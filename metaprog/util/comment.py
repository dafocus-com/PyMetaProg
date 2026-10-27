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
from .writer import Writer
from .writable import Writable
from .config import Config
from typing import Optional, Union, TypeAlias
from .comment_entry import CommentEntry, COMMENT_BRIEF

CommentAny:TypeAlias = Union[None,str,CommentEntry,list[CommentEntry],"Comment"]

class Comment(Writable):
    '''! Handles a comment with its doxygen entries '''
    def __init__(self, commentAny:CommentAny=None, commandIfString:str=COMMENT_BRIEF, paramIfString:Optional[str]=None) -> None:
        self.m_entries:list[CommentEntry] = list()
        self.register(commentAny=commentAny, commandIfString=commandIfString, paramIfString=paramIfString)
    
    def addWithParam(self, command:str, parameter:str, description:str) -> None:
        '''! Add a command to the comment
        @param command     The doxygen command, like `brief` or `param`
        @param parameter   The parameter after the command, like "foobar" in "@param foobar Description..."
        @param description The text associated to the command; add newlines only where mandatory

        @see https://www.doxygen.nl/manual/commands.html
        '''
        self.m_entries.append(CommentEntry(command=command, parameter=parameter, description=description))

    def add(self, command:str, description:str) -> None:
        '''! Add a command to the comment
        @param command     The doxygen command, like `brief` or `param`
        @param description The text associated to the command; add newlines only where mandatory

        @see https://www.doxygen.nl/manual/commands.html
        '''
        self.m_entries.append(CommentEntry(command=command, parameter=None, description=description))

    def write(self, writer:Writer, config:Config) -> None:
        '''! Write a comment using the indicated format '''
        config.m_commentFormat.writeComment(entries=self.m_entries, writer=writer, config=config) # type: ignore

    def merge(self, other:Comment) -> None:
        for entry in other.m_entries:
            self.m_entries.append(entry)

    def register(self, commentAny:CommentAny, commandIfString:str, paramIfString:Optional[str]=None) -> None:
        if commentAny is None: return
        if isinstance(commentAny, str):
            if paramIfString is not None:
                self.addWithParam(command=commandIfString, description=commentAny, parameter=paramIfString)
            else:
                self.add(command=commandIfString, description=commentAny)
            return
        if isinstance(commentAny, CommentEntry):
            self.m_entries.append(commentAny)
            return
        if isinstance(commentAny, Comment):
            self.merge(other=commentAny)
            return
        
        # It is a list
        self.m_entries += commentAny



