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

from __future__ import annotations
from typing import Any, Union, Optional, TypeAlias

class ExtensionsBase:
    pass

ExtensionsAny:TypeAlias = Union[ExtensionsBase,dict[str,Any],None]

class Extensions(ExtensionsBase):
    def __init__(self, extensions:ExtensionsAny=None):
        self.m_keyValues:dict[str,Any] = dict()
        self.merge(extensions=extensions)
    
    def merge(self, extensions:ExtensionsAny)->None:
        if extensions is None: return
        elif isinstance(extensions, dict):
            for key in extensions.keys():
                self.m_keyValues[key] = extensions[key]
        elif isinstance(extensions, Extensions):
            for key in extensions.m_keyValues.keys():
                self.m_keyValues[key] = extensions.m_keyValues[key]
        else:
            assert(False)
    
    def newMerged(self, extensions:ExtensionsAny)->Extensions:
        ''' Returns a new Extension object made of this merged with `extensions` '''
        newExt:Extensions = Extensions(extensions=self)
        newExt.merge(extensions=extensions)
        return newExt

    def getValueOrNone(self, key:str) -> Optional[Any]:
        '''! Returns the value if the key exists; otherwise, it returns `None` '''
        if key in self.m_keyValues:
            return self.m_keyValues[key]
        return None
    
    def __str__(self)->str:
        ret:list[str] = list()
        for key in self.m_keyValues.keys():
            ret.append(f'{key}={self.m_keyValues[key]}')
        return ",".join(ret)

    def __getitem__(self, key:str)->Any:
        return self.m_keyValues[key]
    
    def __setitem__(self, key:str, value:Any)->None:
        self.m_keyValues[key] = value

    def __contains__(self, key:str)->bool:
        return key in self.m_keyValues

    def __len__(self, key:str)->int:
        return len(self.m_keyValues)
    
    def __delitem__(self, key:str)->None:
        del self.m_keyValues[key]
