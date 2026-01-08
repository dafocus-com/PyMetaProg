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

from metaprog.cpp.cpp_class import CppClass
from metaprog.cpp.cpp_enum import CppEnum
from abc import ABC, abstractmethod

class CppGeneratorBase(ABC):
    #=============================================================================================
    def __init__(
            self,
        ) -> None:
        self.m_cppClasses:list[CppClass] = list()
        self.m_cppEnums:list[CppEnum] = list()
   
    
    #=============================================================================================
    def addClass(self, cppClass:CppClass) -> None:
        '''! Add classes for future decoration '''
        self.m_cppClasses.append(cppClass)

    #=============================================================================================
    def addEnum(self, cppEnum:CppEnum) -> None:
        '''! Add classes for future decoration '''
        self.m_cppEnums.append(cppEnum)

    #=============================================================================================
    @abstractmethod
    def decorateClasses(self) -> None:
        ...
