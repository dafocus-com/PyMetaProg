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

from metaprog.util.writer import Writer
from metaprog.util.config import Config
from textwrap import wrap
from metaprog.util.comment_entry import *
from metaprog.util.comment_format import CommentFormat


class CsCommentFormat(CommentFormat):
    '''! Controls how comments are generated '''
    def __init__(
            self,
            width:int = 78,
            blockIndent:int = 12,
            startWithEmtpyLine:bool=True,
            mapCommands:dict[str,str] = dict(),
        ) -> None:
        '''! Constructor

        @param width               Maximum width of the comment line
        @param startWithEmtpyLine  If set, the comment is preceeded by an empty line
        
        '''
        self.m_width:int = width
        self.m_startWithEmtpyLine:bool = startWithEmtpyLine
        self.m_mapCommands:dict[str,str] = dict()
        
        self.m_mapCommands[COMMENT_BRIEF] = COMMENT_SUMMARY
        for mapCommand in mapCommands.keys():
            self.m_mapCommands[mapCommand] = mapCommands[mapCommand]

    @staticmethod
    def xml_escape(s: str) -> str:
        return (s.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))

    #=======================================================================================
    def writeElement(self, entry:CommentEntry, writer:Writer, config:Config):
        '''! Write a comment entry using the indicated format '''
        lineStart = "/// "
        
        if entry.m_command in self.m_mapCommands:
            command:str = self.m_mapCommands[entry.m_command]
        else:
            command:str = entry.m_command

        multiLine:bool = False
        if command == COMMENT_SUMMARY:
            multiLine = True

        #print(f"[DEBUG] PRINTING CS COMMENT {entry.m_description}")

        lines:list[str] = wrap(entry.m_description, width=self.m_width)
        if len(lines) > 1:
            multiLine = True

        writer.writeRaw(f'{lineStart}<{command}')
        if entry.m_parameter:
            writer.writeRaw(f' name="{CsCommentFormat.xml_escape(entry.m_parameter)}"')
        writer.writeRaw('>')
        if multiLine: writer.writeRaw('\n')

        for line in lines:
            if multiLine: writer.writeRaw(lineStart)
            writer.write(CsCommentFormat.xml_escape(line), dedent=False)
            if multiLine: writer.writeRaw('\n')
        
        if multiLine: writer.writeRaw(lineStart)
        writer.writeNL(f'</{command}>')
            

    #=======================================================================================
    def writeComment(self, entries:list[CommentEntry], writer:Writer, config:Config):
        '''! Write a comment using the indicated format '''
        if not entries: return

        if self.m_startWithEmtpyLine:
            writer.writeRaw("\n")
        for entry in entries:
            self.writeElement(entry=entry, writer=writer, config=config)
