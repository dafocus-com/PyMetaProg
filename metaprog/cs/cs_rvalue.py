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
from .cs_config import CsConfig
from .cs_namescope import CsNameScope
from metaprog.util.config import Config
from metaprog.util.writer import Writer
from metaprog.util.writable import Writable
from typing import Optional, Union, TypeAlias
from metaprog.util.writable_set import Writable

class CsRValue(ABC):
    '''! Base class for objects that can become an R-Value '''

    @abstractmethod
    def generateValue(self, writer:Writer, config:CsConfig, otherScope:Optional[CsNameScope]=None)->None:
        '''! Generate the R-value text '''
        ...

CsRValueAny:TypeAlias = Union[CsRValue,str,Writable,None]    

class CsRValueContainer(Writable):
    '''! Container for values '''
    def __init__(self, csValueAny:CsRValueAny):
        self.m_csValueAny:CsRValueAny = csValueAny

    def empty(self)->bool:
        return self.m_csValueAny is None

    def write(self, writer:Writer, config:Config):
        '''! Generate the R-value text '''
        if self.m_csValueAny is None: return
        if isinstance(self.m_csValueAny, Writable):
            self.m_csValueAny.write(writer=writer, config=config)
            return
        if isinstance(self.m_csValueAny, str):
            writer.writeRaw(self.m_csValueAny)
            return

        # It is a CsRValue
        assert(isinstance(config, CsConfig))
        csConfig:CsConfig = config
        self.m_csValueAny.generateValue(writer=writer, config=config, otherScope=csConfig.m_csCurrentNameScope) # type: ignore
        return
    

