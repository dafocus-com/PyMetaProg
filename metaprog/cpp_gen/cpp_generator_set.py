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

from .cpp_generator_base import CppGeneratorBase
from metaprog.cpp.cpp_class import CppClass
from metaprog.cpp.cpp_enum import CppEnum
from typing import Type, TypeVar, Optional

T = TypeVar("T", bound=CppGeneratorBase)

class CppGeneratorSet:
    #=============================================================================================
    def __init__(
            self, 
        ) -> None:
        self.m_generators:list[CppGeneratorBase] = list()

    #=============================================================================================
    def find_generator_by_type(self, cls: Type[T]) -> Optional[T]:
        for generator in self.m_generators:
            if isinstance(generator, cls):
                return generator
        return None

    #=============================================================================================
    def addGenerator(self, cppGenerator:CppGeneratorBase) -> None:
        self.m_generators.append(cppGenerator)

    #=============================================================================================
    def addClass(self, cppClass:CppClass) -> None:
        '''! Add classes for future decoration '''
        for generator in self.m_generators:
            generator.addClass(cppClass)

    #=============================================================================================
    def addEnum(self, cppEnum:CppEnum) -> None:
        '''! Add classes for future decoration '''
        for generator in self.m_generators:
            generator.addEnum(cppEnum)

    #=============================================================================================
    def addClasses(self, cppClasses:list[CppClass]) -> None:
        '''! Add classes for future decoration '''
        for cppClass in cppClasses:
            self.addClass(cppClass=cppClass)

    #=============================================================================================
    def decorateClasses(self) -> None:
        for generator in self.m_generators:
            generator.decorateClasses()
