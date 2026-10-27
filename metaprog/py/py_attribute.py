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

from .py_config import PyConfig
from metaprog.util.writer import Writer

class PyAttribute:
    '''! 
        Implementation of the Python 'decorators', i.e. declaration in the form
        of `@xyz` classes, fields and methods.
        It is called `PyAttribute` to maintain the standardized PyMetaProg
        naming convention.
    '''
    def __init__(self, decoratorText:str) -> None:
        self.m_decoratorText:str = decoratorText

    def write(self, writer:Writer, config:PyConfig) -> None:
        writer.writeRaw(f"@{self.m_decoratorText}")


class PyAttributes:
    def __init__(self, attributesList:list[PyAttribute]=list()) -> None:
        self.m_attributesList:list[PyAttribute] = list()
        self.m_attributesList += attributesList

    def write(self, writer:Writer, config:PyConfig) -> None:
        for pyAttribute in self.m_attributesList:
            pyAttribute.write(writer=writer, config=config)
    
    def append(self, pyAttribute:PyAttribute) -> None:
        self.m_attributesList.append(pyAttribute)