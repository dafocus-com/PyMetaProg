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

import textwrap
import re
from abc import ABC, abstractmethod

class Writer(ABC):
    '''! Writes the source code mainaining a given indent level 
    
    This class is abstract. Derive your own to write on the desired stream.

    EXAMPLE:

            from metaprog.util.writer import Writer

            class MyWriter(Writer):
                def __init__(self, fileName:str):
                    super().__init__()
                    self.m_file:io.TextIOBase = open(fileName, "w")

                def write(self, text:str):
                    print(text, end=None)    

    '''
    #==============================================================================================
    def __init__(self):
        ## The string used to create one indent level
        self.m_indentString: str = "\t"
        
        ## The current indent level; 0=no indent
        self.m_indentLevel: int = 0

        ## If `True` it will start by adding the required indent.
        #  If `False` it will add the text without adding the indent strings
        #  to continue on the same line.
        self.m_lastLineWasTerminated: bool = True

        ## This is the indent used by the Python editor being used. It will
        #  be used to replace that indent with the indicated `indentString`
        #  when `armonizeIndent` is specified.
        self.m_editorIndentText:str = "    "

    #==============================================================================================
    @abstractmethod
    def _internalWrite(self, text:str):
        '''! REDEFINE THIS METHOD TO PRINT ON THE ACTUAL STREAM 

        Writes without adding a newline at the end of the string
        '''
        ...

    #==============================================================================================
    def incIndent(self, indentSteps:int=1):
        '''! Increase the indent level '''
        self.m_indentLevel += indentSteps
        assert(self.m_indentLevel >= 0)

    #==============================================================================================
    def decIndent(self, indentSteps:int=1):
        '''! Derease the indent level '''
        self.m_indentLevel -= indentSteps
        assert(self.m_indentLevel >= 0)

    #==============================================================================================
    def armonizeIndentOnLine(self, line:str)->str:
        '''! Given one line, replaces all the leading `editorIndentText` sequences with `indentString` '''
        srchLen:int = len(self.m_editorIndentText)
        indents:int = 0
        while len(line) >= srchLen and line[:srchLen] == self.m_editorIndentText:
            indents += 1
            line = line[srchLen:]
        return (self.m_indentString * indents) + line

    #==============================================================================================
    def write(self, text:str, dedent:bool=True, armonizeIndent:bool=True, autoReturnAtEnd:bool=False):
        '''! Print the text using the current indent level 
        @param text            The text to be printed
        @param dedent          Automatically dedent text like `textwrap.dedent` does.
        @param armonizeIndent  Convert the Python editor indent into the specified `indentString`
        @param autoReturnAtEnd Add a return at the end if not already present
        '''
        # Remove the trailing spaces and newline on the last line
        if dedent and autoReturnAtEnd:
            text = re.sub(r'\s+$', '', text)
            #print(f'TEXT=[{text}]')

        if len(text) == 0: return


        endsWithNewLine:bool = (text[-1] == '\n')
        if not endsWithNewLine and autoReturnAtEnd:
            text += '\n'
            endsWithNewLine = True

        if dedent:
            text = textwrap.dedent(text)
        
        lines:list[str] = text.splitlines()
        currLineNo:int = 0
        lastLineNo:int = len(lines)

        for line in lines:
            currLineNo += 1
            if armonizeIndent:
                line = self.armonizeIndentOnLine(line)
            if self.m_lastLineWasTerminated:
                self._internalWrite(self.m_indentString * self.m_indentLevel)
            self._internalWrite(line)
            if currLineNo==lastLineNo and not endsWithNewLine:
                self.m_lastLineWasTerminated = False
            else:
                self.m_lastLineWasTerminated = True
                self._internalWrite("\n")
                
    #==============================================================================================
    def writeNL(self, text:str, dedent:bool=True, armonizeIndent:bool=True):
        '''! Print the text using the current indent level; adds a '\n' at the end if not already present 
        @param text            The text to be printed
        @param dedent          Automatically dedent text like `textwrap.dedent` does.
        @param armonizeIndent  Convert the Python editor indent into the specified `indentString`
        '''
        self.write(text=text, dedent=dedent, armonizeIndent=armonizeIndent, autoReturnAtEnd=True)

    #==============================================================================================
    def writeRaw(self, text:str):
        '''! Write without any manipulation of the text '''
        self.write(text=text, dedent=False, armonizeIndent=False)
