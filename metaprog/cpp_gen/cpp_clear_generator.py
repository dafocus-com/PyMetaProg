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

'''! Generates the `clear()` code ontop of an existing class '''
from metaprog.cpp.cpp_class import CppClass
from metaprog.cpp.cpp_field import CppField
from metaprog.cpp.cpp_method import CppMethod
from metaprog.cpp.cpp_labels import CppInline
from metaprog.cpp.cpp_type import CppTypeSharedPtr, CppTypeSimple,CppTypeVector, CppTypeMap
from metaprog.util.log import logError
from .cpp_generator_base import CppGeneratorBase
from typing import Union

CPP_CLEAR_GENERATED:str = "cpp_clear_generated" # -> bool, created and written by this module to mark that has been processed

# Once the generator has executed, these extensions contain the name that
# has been assigned to some methods. This allows the following generators to
# invoke them by calling them with their correct name.
CLEAR_METHOD:str = "cpp_clear_method"

CPP_CLEAR_FIELD_DISABLE="cpp_clear_field_disable" # Add to disable clear of the CppField

class CppClearGenerator(CppGeneratorBase):
    #=============================================================================================
    def __init__(
            self,
            clearName:str = 'clear',
        ) -> None:
        super().__init__()
        self.m_clearName:str = clearName
   

    #=============================================================================================
    def _baseClassHasClear(self, cppClass:CppClass)->bool:
        ''' CAN BE REDEFINED 
            Returns `True` if the `cppClass` has a base class that has the `clear()` method.
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
        if CPP_CLEAR_GENERATED in cppClass.m_extensions:
            logError(f"class `{cppClass.getCppQualifiedName()}` generated more than once")
            return
        cppClass.m_extensions[CPP_CLEAR_GENERATED] = True
        #logInfo(f"Decorating class `{cppClass.getCppQualifiedName()}`")

        cppClass.m_extensions[CLEAR_METHOD] = self.m_clearName

        clear:CppMethod = CppMethod(
            methodName=self.m_clearName,
            brief='Clear all values to their default',
            inline=CppInline.INLINE_OUTSIDE,
        )
        cppClass.addClassElement(clear)
        if self._baseClassHasClear(cppClass=cppClass):
            assert(isinstance(cppClass.m_baseClass, CppClass))
            clear.m_code.append(f'{cppClass.m_baseClass.getCppQualifiedName(cppClass)}::{self.m_clearName}();')
        
        for classElement in cppClass.m_classElements:
            if isinstance(classElement, CppField) and not classElement.m_fieldConst and not CPP_CLEAR_FIELD_DISABLE in classElement.m_extensions:
                if isinstance(classElement.m_fieldType, CppTypeSharedPtr):
                    clear.m_code.append(text=f'{classElement.m_fieldName}.reset();')
                elif isinstance(classElement.m_fieldType, CppTypeVector):
                    clear.m_code.append(text=f'{classElement.m_fieldName}.clear();')
                elif isinstance(classElement.m_fieldType, CppTypeMap):
                    clear.m_code.append(text=f'{classElement.m_fieldName}.clear();')
                elif classElement.m_fieldDefault.empty():
                    if isinstance(classElement.m_fieldType, CppTypeSimple):
                        if classElement.m_fieldType.m_defaultValue is None:
                            clear.m_code.append(text=f'{classElement.m_fieldName} = 0;')
                        elif isinstance(classElement.m_fieldType.m_defaultValue, bool):
                            clear.m_code.append(text=f'{classElement.m_fieldName}.clear();')
                        else:
                            clear.m_code.append(text=f'{classElement.m_fieldName} = {classElement.m_fieldType.m_defaultValue};')
                        
                    else:
                        assignableDefault:Union[str,None] = classElement.m_fieldType.getAssigneableDefaultValue(containerClass=cppClass)
                        if assignableDefault is None:
                            clear.m_code.append(text=f'{classElement.m_fieldName}.clear();')
                        else:
                            clear.m_code.append(text=f'{classElement.m_fieldName} = {assignableDefault};')
                else:
                    clear.m_code.append(text=f'{classElement.m_fieldName} = ', autoReturnAtEnd=False)
                    clear.m_code.append(text=classElement.m_fieldDefault)
                    clear.m_code.append(text=f';', autoReturnAtEnd=True)
