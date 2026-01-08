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

from .cs_class_element import CsClassElement
from .cs_labels import *
from .cs_config import CsConfig
from .cs_usings import CsUsingsAny
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.comment import *
from metaprog.util.writable_set import WritableSet, WritableSetAny
from metaprog.util.writer import Writer

class CsClassCustom(CsClassElement):
    '''! Custom class element

    This object implements a class element, like fields and methods, but its contents is
    completely user defined.
    It contains three writables that are expanded in their related position if not `None`.
    '''
    def __init__(self, 
            desc:str,
            visibility:CsVisibility=CsVisibility.PRIVATE, 
            brief:CommentAny=None,
            extensions:ExtensionsAny = None,
            csUsings:CsUsingsAny = None,
            writableInClass:WritableSetAny = None,
        ):
        super().__init__(visibility=visibility, csUsings=csUsings, extensions=extensions)
        self.m_desc:str = desc
        self.m_comment:Comment = Comment(commentAny=brief)
        self.m_writableInClass:WritableSet = WritableSet(text=writableInClass)
    
    def identify(self)->str:
        '''! Returns a string that can be used to identify this element in logs '''
        return self.m_desc

    def generateCsBody(self, writer:Writer, config:CsConfig)->None:
        '''! Generate the body part of the C++ .hpp file, i.e. where the class definitions go '''
        self.m_comment.write(writer, config)
        self.m_writableInClass.write(writer=writer, config=config)
