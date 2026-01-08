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

from .cpp_class_element import CppClassElement
from .cpp_labels import *
from .cpp_config import CppConfig
from .cpp_includes import CppIncludesAny
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.writable_set import WritableSet, WritableSetAny
from metaprog.util.writer import Writer

class CppClassCustom(CppClassElement):
    '''! Custom class element

    This object implements a class element, like fields and methods, but its contents is
    completely user defined.
    It contains three writables that are expanded in their related position if not `None`.
    '''
    def __init__(self, 
            desc:str,
            visibility:CppVisibility=CppVisibility.DEFAULT, 
            hppIncludes:CppIncludesAny = None,
            cppIncludes:CppIncludesAny = None,
            extensions:ExtensionsAny = None,
            writableInClass:WritableSetAny = None,
            writableInline:WritableSetAny = None,
            writableInCpp:WritableSetAny = None,
        ):
        super().__init__(visibility=visibility, hppIncludes=hppIncludes, cppIncludes=cppIncludes, extensions=extensions)
        self.m_desc:str = desc
        self.m_writableInClass:WritableSet = WritableSet(text=writableInClass)
        self.m_writableInline:WritableSet = WritableSet(text=writableInline)
        self.m_writableInCpp:WritableSet = WritableSet(text=writableInCpp)
        
    def needsCpp(self)->bool:
        '''! Must return `True` if this class requires the C++ file`'''
        return not self.m_writableInCpp.empty()

    def needsInline(self)->bool:
        '''! Must return `True` if this class requires the inline .hpp part`'''
        return not self.m_writableInline.empty()
    
    def identify(self)->str:
        '''! Returns a string that can be used to identify this element in logs '''
        return self.m_desc

    def generateHppBody(self, writer:Writer, config:CppConfig)->None:
        '''! Generate the body part of the C++ .hpp file, i.e. where the class definitions go '''
        self.m_writableInClass.write(writer=writer, config=config)


    def generateHppInline(self, writer:Writer, config:CppConfig)->None:
        '''! Generate the inline part of the C++ .hpp file, i.e. where the `inline` methods go '''
        self.m_writableInline.write(writer=writer, config=config)

    def generateCppBody(self, writer:Writer, config:CppConfig)->None:
        '''! Generate the body part of the C++ .cpp file, i.e. where implementation of the methods go '''
        self.m_writableInCpp.write(writer=writer, config=config)
