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
from abc import ABC, abstractmethod
from .cpp_config import CppConfig
from .cpp_namescope import CppNameScope
from metaprog.util.config import Config
from metaprog.util.writer import Writer
from metaprog.util.writable import Writable
from typing import Optional, Union, TypeAlias
from metaprog.util.writable_set import Writable

class CppRValue(ABC):
    '''! Base class for objects that can become an R-Value '''

    @abstractmethod
    def generateValue(self, writer:Writer, config:CppConfig, otherScope:Optional[CppNameScope]=None)->None:
        '''! Generate the R-value text '''
        ...

CppRValueAny:TypeAlias = Union[CppRValue,str,Writable,None]    

class CppRValueContainer(Writable):
    '''! Container for values '''
    def __init__(self, cppValueAny:CppRValueAny):
        self.m_cppValueAny:CppRValueAny = cppValueAny

    def empty(self)->bool:
        return self.m_cppValueAny is None

    def write(self, writer:Writer, config:Config):
        '''! Generate the R-value text '''
        if self.m_cppValueAny is None: return
        if isinstance(self.m_cppValueAny, Writable):
            self.m_cppValueAny.write(writer=writer, config=config)
            return
        if isinstance(self.m_cppValueAny, str):
            writer.writeRaw(self.m_cppValueAny)
            return

        # It is a CppRValue
        assert(isinstance(config, CppConfig))
        cppConfig:CppConfig = config
        self.m_cppValueAny.generateValue(writer=writer, config=config, otherScope=cppConfig.m_cppCurrentNameScope) # type: ignore
        return
    

