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

from metaprog.util.config import Config
from metaprog.util.comment_format import CommentFormat
from .cpp_comment_format import CppCommentFormat
from typing import Optional
import re

class CppConfig(Config):
    '''! Generation configuration '''
    def __init__(self, commentFormat:CommentFormat = CppCommentFormat()) -> None:
        super().__init__(commentFormat=commentFormat)
        
        self.m_cppCurrentNameScope:Optional["CppNameScope"] = None # type: ignore
        ''' During generation, indicates that we are inside C++ `namespace XYZ {...here...}` '''
    
    def getGetterSetterMethodName(self, fieldName:str, getter:bool)->str:
        '''! Calculates the name of the getter method for `CppField` in case `CPP_FIELD_GETSET` is active '''
        # Remove `m_` from the beginning of the method
        fieldName = re.sub(r'^m_', '', fieldName)

        # Make the first letter upper case
        fieldName = fieldName[0].upper() + fieldName[1:]

        if getter:
            return f'get{fieldName}'
        else:
            return f'set{fieldName}'
        
        