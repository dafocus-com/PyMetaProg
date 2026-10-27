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

from metaprog.py.py_class import PyClass
from metaprog.py.py_enum import PyEnum
from abc import ABC, abstractmethod

class PyGeneratorBase(ABC):
    #=============================================================================================
    def __init__(
            self,
        ) -> None:
        self.m_pyClasses:list[PyClass] = list()
        self.m_pyEnums:list[PyEnum] = list()

    
    #=============================================================================================
    def addClass(self, pyClass:PyClass) -> None:
        '''! Add classes for future decoration '''
        self.m_pyClasses.append(pyClass)

    #=============================================================================================
    def addEnum(self, pyEnum:PyEnum) -> None:
        '''! Add classes for future decoration '''
        self.m_pyEnums.append(pyEnum)

    #=============================================================================================
    @abstractmethod
    def decorateClasses(self) -> None:
        ...
