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

from enum import Enum
from metaprog.util.writer import Writer
from metaprog.util.config import Config
from textwrap import wrap
from metaprog.util.comment_entry import CommentEntry
from metaprog.util.comment_format import CommentFormat

class CppCommentFormatType(Enum):
    SLASHSLASH      = 1  # Creates a // comment
    SLASHSLASHSLASH = 2  # Creates a /// comment
    SLASHSTAR       = 3  # Creates a /* ... */ comment 

class CppCommentFormat(CommentFormat):
    '''! Controls how comments are generated '''
    def __init__(
            self,
            commentFormatType:CppCommentFormatType = CppCommentFormatType.SLASHSLASH,
            width:int = 78,
            blockIndent:int = 12,
            startWithEmtpyLine:bool=True,
            mapCommands:dict[str,str] = dict(),
        ) -> None:
        '''! Constructor

        @param commentFormaType    Comment format style
        @param width               Maximum width of the comment line
        @param blockIndent         Indent of the description text
        @param startWithEmtpyLine  If set, the comment is preceeded by an empty line
        
        '''
        self.m_commentFormatType:CppCommentFormatType = commentFormatType
        self.m_width:int = width
        self.m_blockIndent:int = blockIndent
        self.m_startWithEmtpyLine:bool = startWithEmtpyLine
        self.m_mapCommands:dict[str,str] = dict()
        for mapCommand in mapCommands.keys():
            self.m_mapCommands[mapCommand] = mapCommands[mapCommand]

    #=======================================================================================
    def _writeElement(self, entry:CommentEntry, writer:Writer, config:Config) -> None:
        '''! Write a comment entry using the indicated format '''
        assert(self.m_width - self.m_blockIndent > 8)
        lineStart:str = ""
        if self.m_commentFormatType == CppCommentFormatType.SLASHSLASH:
            lineStart = "// "
        elif self.m_commentFormatType == CppCommentFormatType.SLASHSLASHSLASH: 
            lineStart = "/// "
        elif self.m_commentFormatType == CppCommentFormatType.SLASHSTAR:
            lineStart = "  "
        
        if entry.m_command in self.m_mapCommands:
            actualCommandString:str = self.m_mapCommands[entry.m_command]
        else:
            actualCommandString = entry.m_command

        command:str = "@"+actualCommandString+" "
        if entry.m_parameter is not None:
            command += entry.m_parameter + " "

        description:str = ""
        if len(command) > self.m_blockIndent:
            description += command[self.m_blockIndent:]
            command = command[:self.m_blockIndent]
        else:
            command += ' ' * (self.m_blockIndent- len(command))
        description += entry.m_description

        lines:list[str] = wrap(description, self.m_width-self.m_blockIndent)

        for line in lines:
            writer.writeNL(lineStart+command+line, dedent=False)
            command = " " * self.m_blockIndent

    #=======================================================================================
    def writeComment(self, entries:list[CommentEntry], writer:Writer, config:Config) -> None:
        '''! Write a comment using the indicated format '''
        if not entries: return

        firstLine:str = ''
        lastLine:str = ''
        if self.m_commentFormatType == CppCommentFormatType.SLASHSLASH:
            pass
        elif self.m_commentFormatType == CppCommentFormatType.SLASHSLASHSLASH: 
            pass
        elif self.m_commentFormatType == CppCommentFormatType.SLASHSTAR:
            firstLine = '/*\n'
            lastLine = '*/\n'

        if self.m_startWithEmtpyLine:
            writer.writeRaw("\n")
        writer.writeRaw(firstLine)
        for entry in entries:
            self._writeElement(entry=entry, writer=writer, config=config)
        writer.writeRaw(lastLine)
