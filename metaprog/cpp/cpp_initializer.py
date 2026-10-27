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

from typing import Union, TypeAlias
from abc import ABC, abstractmethod

class CppInitializer(ABC):
    @abstractmethod
    def getText(self) -> str:
        ...

    def getOrder(self) -> int:
        return 0

CppInitializerAny:TypeAlias = Union[CppInitializer,str]


class CppInitializerCustom(CppInitializer):
    '''! Does a custom initialization '''
    def __init__(self, initText:str) -> None:
        self.m_initText:str = initText

    def getText(self) -> str:
        return self.m_initText



class CppInitializerSet:
    def __init__(self, initializers:list[CppInitializerAny] = list()) -> None:
        self.m_initializers:list[CppInitializer] = list()
        for initializer in initializers:
            self.append(initializer=initializer)    
    
    def append(self, initializer:CppInitializerAny) -> None:
        if isinstance(initializer, str):
            self.m_initializers.append(CppInitializerCustom(initText=initializer))
        else:
            self.m_initializers.append(initializer)

    def appendToList(self, strings:list[str]) -> list[str]:
        self.m_initializers.sort(key=lambda initializer: initializer.getOrder())
        for initializer in self.m_initializers:
            strings.append(initializer.getText())
        return strings

    def empty(self) -> bool:
        return len(self.m_initializers) == 0