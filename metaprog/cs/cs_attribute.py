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

from typing import Optional
from metaprog.util.writable import *
from metaprog.util.writable_set import *
from .cs_config import CsConfig

class CsAttribute:
    '''! 
        Implementation of the CSharp 'attributes', i.e. declaration in the form
        of `[KeyValue]` or `[KeyValue = value]` that can preceed classes, properties,
        fields and methods.
    '''
    def __init__(self, attribKey:str, attribValue:WritableSetAny=None):
        self.m_attribKey:str = attribKey
        self.m_attribValue:Optional[WritableSet] = None
        if attribValue is not None: self.m_attribValue = WritableSet(text=attribValue)

    def write(self, writer:Writer, config:CsConfig):
        writer.writeRaw(f"[{self.m_attribKey}")
        if self.m_attribValue is not None:
            writer.writeRaw(" = ")
            self.m_attribValue.write(writer=writer, config=config)
        writer.writeNL("]")


class CsAttributes:
    def __init__(self, attributesList:list[CsAttribute]=list()):
        self.m_attributesList:list[CsAttribute] = list()
        self.m_attributesList += attributesList

    def write(self, writer:Writer, config:CsConfig):
        for csAttribute in self.m_attributesList:
            csAttribute.write(writer=writer, config=config)
    
    def append(self, csAttribute:CsAttribute):
        self.m_attributesList.append(csAttribute)