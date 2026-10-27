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

from .comment_format import CommentFormat
from .log import logError
import re
from typing import Union

ENV_VAR_OPEN:str = '\x01'
ENV_VAR_CLOSE:str = '\x02'
def env(txt:str)->str:
     return f'{ENV_VAR_OPEN}{txt}{ENV_VAR_CLOSE}'

class Config:
    '''! Generation configuration '''
    def __init__(self, commentFormat:CommentFormat) -> None:
        self.m_commentFormat:CommentFormat = commentFormat
        
        self.m_env:dict[str,Union[str,object]] = dict()
        '''! 
            This map is available to the callers to pass informatio to the writers 
            It can be pushed and popped using `pushEnv()` or `popEnv()`
        '''

        self.m_envStack:list[dict[str,Union[str,object]]] = list()
        '''! Environment stack '''
    
    def pushEnv(self) -> None:
        self.m_envStack.append(self.m_env)
        self.m_env = self.m_env.copy()

    def popEnv(self) -> None:
        assert(len(self.m_env) > 0)
        self.m_env = self.m_envStack[-1]
        del self.m_envStack[-1]

    def setEnv(self, key:str, value:Union[str,object,None]) -> None:
        if value is None:
            if key in self.m_env:
                del self.m_env[key]
        else:
            self.m_env[key] = value

    def addEnv(self, addition:dict[str,Union[str,object]]) -> None:
         for key in addition.keys():
              self.m_env[key] = addition[key]

    def resolveEnvVars(self, text:str)->str:
        '''! 
            Given the string `text`, replaces all the `<ENV_VAR_OPEN>xxx<ENV_VAR_CLOSE>` entries with the contents of the
            `self.m_env` dictionary.
        '''
        # Replace all the environment vars
        text = re.sub(f"{ENV_VAR_OPEN}([A-Za-z0-9_-]+){ENV_VAR_CLOSE}", lambda m: self.__replaceEnvVar(m), text)
        return text

    def __replaceEnvVar(self, m:re.Match[str]) -> str:
            word:str = m.group(1)
            if word not in self.m_env:
                 logError(f"Failed replacing unknown word $({word})")
            else:
                value: Union[str,object] = self.m_env[word]
                if isinstance(value, str):
                    word = self.resolveEnvVars(value)
                else:
                    logError(f"Failed replacing word $({word}): it is an object of type {value.__class__.__name__}, not a string")
            return word
