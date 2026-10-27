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

'''! Generates the dastd rtti code ontop of an existing class '''
from metaprog.cpp.cpp_class import CppClass
from metaprog.util.log import logError
from .cpp_generator_base import CppGeneratorBase

CPP_RTTI_GENERATED:str = "cpp_rtti_generated" # -> bool, created and written by this module to mark that has been processed

class CppRttiGenerator(CppGeneratorBase):
    #=============================================================================================
    def __init__(
            self, 
        ) -> None:
        super().__init__()

    #=============================================================================================
    def _baseClassHasRtti(self, cppClass:CppClass)->bool:
        ''' CAN BE REDEFINED 
            Returns `True` if the `cppClass` has a base class that implements RTTI.
            By default considers deriving from a `CppClass` object as having a streamable base class.
        '''
        return cppClass.m_baseClass is not None and isinstance(cppClass.m_baseClass, CppClass)


    #=============================================================================================
    def decorateClasses(self) -> None:
        '''! Executes the decoration of the classes before generating the code '''
        for cppClass in self.m_cppClasses:
            self.__decorateClass(cppClass)

    #=============================================================================================
    def __decorateClass(self, cppClass:CppClass) -> None:
        '''! Decorate the single class with all the required code '''
        if CPP_RTTI_GENERATED in cppClass.m_extensions:
            logError(f"CppRttiGenerator class `{cppClass.getCppQualifiedName()}` generated more than once")
            return
        cppClass.m_extensions[CPP_RTTI_GENERATED] = True
        #logInfo(f"CppRttiGenerator decorating class `{cppClass.getCppQualifiedName()}`")

        cppClass.m_hppIncludes.add("dastd/rtti.hpp")

        if self._baseClassHasRtti(cppClass=cppClass):
            assert(isinstance(cppClass.m_baseClass, CppClass))
            cppClass.m_startBlock.append(f"DASTD_RTTI_DERIVED({cppClass.m_nameScope},{cppClass.m_baseClass.getCppQualifiedName(cppClass)})\n")
        else:
            cppClass.m_startBlock.append(f"DASTD_RTTI_BASE({cppClass.m_nameScope})\n")
