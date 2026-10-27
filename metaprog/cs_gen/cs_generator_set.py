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

from .cs_generator_base import CsGeneratorBase
from metaprog.cs.cs_class import CsClass
from metaprog.cs.cs_enum import CsEnum

class CsGeneratorSet:
    #=============================================================================================
    def __init__(
            self, 
        ) -> None:
        self.m_generators:list[CsGeneratorBase] = list()
    
    #=============================================================================================
    def addGenerator(self, csGenerator:CsGeneratorBase) -> None:
        self.m_generators.append(csGenerator)

    #=============================================================================================
    def addClass(self, csClass:CsClass) -> None:
        '''! Add classes for future decoration '''
        for generator in self.m_generators:
            generator.addClass(csClass)

    #=============================================================================================
    def addEnum(self, csEnum:CsEnum) -> None:
        '''! Add classes for future decoration '''
        for generator in self.m_generators:
            generator.addEnum(csEnum)

    #=============================================================================================
    def addClasses(self, csClasses:list[CsClass]) -> None:
        '''! Add classes for future decoration '''
        for csClass in csClasses:
            self.addClass(csClass=csClass)

    #=============================================================================================
    def decorateClasses(self) -> None:
        for generator in self.m_generators:
            generator.decorateClasses()
