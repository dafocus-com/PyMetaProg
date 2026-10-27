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
from .py_config import PyConfig
from .py_namescope import PyNameScope
from metaprog.util.config import Config
from metaprog.util.writer import Writer
from metaprog.util.writable import Writable
from typing import Optional, Union, TypeAlias
from metaprog.util.writable_set import Writable

class PyRValue(ABC):
    '''! Base class for objects that can become an R-Value '''

    @abstractmethod
    def generateValue(self, writer:Writer, config:PyConfig, otherScope:Optional[PyNameScope]=None) -> None:
        '''! Generate the R-value text '''
        ...

PyRValueAny:TypeAlias = Union[PyRValue,str,Writable,None]    

class PyRValueContainer(Writable):
    '''! Container for values '''
    def __init__(self, pyValueAny:PyRValueAny) -> None:
        self.m_pyValueAny:PyRValueAny = pyValueAny
        while self.m_pyValueAny is not None and isinstance(self.m_pyValueAny, PyRValueContainer):
            self.m_pyValueAny = self.m_pyValueAny.m_pyValueAny

    def empty(self)->bool:
        return self.m_pyValueAny is None

    def write(self, writer:Writer, config:Config) -> None:
        '''! Generate the R-value text '''
        if self.m_pyValueAny is None: 
            return
        if isinstance(self.m_pyValueAny, Writable):
            self.m_pyValueAny.write(writer=writer, config=config)
            return
        if isinstance(self.m_pyValueAny, str):
            writer.writeRaw(self.m_pyValueAny)
            return

        # It is a PyRValue
        assert(isinstance(config, PyConfig))
        pyConfig:PyConfig = config
        self.m_pyValueAny.generateValue(writer=writer, config=config, otherScope=pyConfig.m_pyCurrentNameScope) # type: ignore
        return
    

