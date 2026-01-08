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

from .writable import Writable
from .config import Config
from .writer import Writer
from .tools import autoNewline

class FreeText(Writable):
    '''! Writable that contains freetext that is not processed '''
    def __init__(self) -> None:
        super().__init__()
        self.m_text:str = ""

    def addAutoNewline(self, text:str)->None:
        '''! If the string is not empty and not terminated by newline, it terminates it with newline '''
        self.m_text += autoNewline(text)
    
    def write(self, writer:Writer, config:Config):
        writer.writeRaw(self.m_text)
