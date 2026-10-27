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
from .config import Config
from .writable import Writable
from typing import Union, TypeAlias, Any

WritableSetValid:TypeAlias = Union[str,Writable]
WritableSetValidOrInvalid:TypeAlias = Union[WritableSetValid,None]

class WritableSet(Writable):
    '''! Implements a mixed list of `str` and `Writable`.
        The strings are written with the `Write` method. '''

    class Block:
        def __init__(
                self, 
                text:WritableSetValid,      # The text to be printed
                dedent:bool=True,           # Automatically dedent text
                armonizeIndent:bool=True,   # Replace the editor indent with the generated code indent characters
                autoReturnAtEnd:bool=True,  # Always terminate the string with newline
            ) -> None:
            self.m_text:WritableSetValid = text
            self.m_dedent:bool = dedent
            self.m_armonizeIndent:bool = armonizeIndent
            self.m_autoReturnAtEnd:bool = autoReturnAtEnd
    
    class Indent:
        def __init__(self, indentSteps:int) -> None:
            self.m_indentSteps:int = indentSteps

    class PushEnv:
        def __init__(self, env:dict[str,Union[str,object]]) -> None:
            self.m_env:dict[str,Union[str,object]] = env

    class PopEnv:
        pass


    #==============================================================================================
    def __init__(self, text:WritableSetValidOrInvalid|WritableSet=None, dedent:bool=True, armonizeIndent:bool=True, autoReturnAtEnd:bool=True) -> None:
        self.m_blocks:list[WritableSet.Block|WritableSet.Indent|WritableSet.PushEnv|WritableSet.PopEnv] = list()
        if text is not None:
            self.append(text=text, dedent=dedent, armonizeIndent=armonizeIndent, autoReturnAtEnd=autoReturnAtEnd)

    #==============================================================================================
    def empty(self) -> bool:
        return len(self.m_blocks)==0

    #==============================================================================================
    def append(self, text:WritableSetValidOrInvalid|WritableSet, dedent:bool=True, armonizeIndent:bool=True, autoReturnAtEnd:bool=True) -> None:
        if text is None: return
        if isinstance(text, WritableSet):
            for block in text.m_blocks:
                self.m_blocks.append(block)
        else:
            self.m_blocks.append(WritableSet.Block(
                text=text, dedent=dedent, armonizeIndent=armonizeIndent, autoReturnAtEnd=autoReturnAtEnd
            ))

    #==============================================================================================
    def pushEnv(self, env:dict[str,Union[str,object]]) -> None:
        '''! Add some environment variables '''
        self.m_blocks.append(WritableSet.PushEnv(env=env))

    #==============================================================================================
    def popEnv(self) -> None:
        '''! Go back to previous environment '''
        self.m_blocks.append(WritableSet.PopEnv())

    #==============================================================================================
    def incIndent(self, indentSteps:int=1) -> None:
        '''! Increase the indent level '''
        self.m_blocks.append(WritableSet.Indent(indentSteps=indentSteps))

    #==============================================================================================
    def decIndent(self, indentSteps:int=1) -> None:
        '''! Derease the indent level '''
        self.incIndent(indentSteps=-indentSteps)

    #==============================================================================================
    def write(self, writer:Writer, config:Config) -> None:
        for block in self.m_blocks:
            if isinstance(block, WritableSet.Block):
                if isinstance(block.m_text, Writable):
                    block.m_text.write(writer=writer, config=config)
                else:
                    text:str = config.resolveEnvVars(block.m_text)
                    writer.write(text=text, dedent=block.m_dedent, armonizeIndent=block.m_armonizeIndent, autoReturnAtEnd=block.m_autoReturnAtEnd)

            elif isinstance(block, WritableSet.PushEnv):
                   config.pushEnv()
                   config.addEnv(block.m_env)
            elif isinstance(block, WritableSet.PopEnv):
                   config.popEnv()
            else:
                writer.incIndent(indentSteps=block.m_indentSteps)


WritableSetAny:TypeAlias = Union[WritableSetValidOrInvalid,WritableSet]

def assertIsWritableSetAny(obj:Any) -> None:
    assert(obj is None or isinstance(obj,(WritableSet|Writable|str)))
