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

from .adt_class import AdtClass
from .adt_enum import AdtEnum
from .adt_type import AdtType
from metaprog.util.extensions import ExtensionsAny

class AdtTypeInteger(AdtType):
    ''' Type descriptor for signed and unsigned integers '''
    def __init__(self, bits:int, signed:bool, extensions:ExtensionsAny=None):
        super().__init__(extensions=extensions)
        self.m_bits:int = bits
        self.m_signed:bool = signed

def ADT_U8 (extensions:ExtensionsAny=None)->AdtTypeInteger: return AdtTypeInteger(extensions=extensions, bits= 8, signed=False)
def ADT_U16(extensions:ExtensionsAny=None)->AdtTypeInteger: return AdtTypeInteger(extensions=extensions, bits=16, signed=False)
def ADT_U32(extensions:ExtensionsAny=None)->AdtTypeInteger: return AdtTypeInteger(extensions=extensions, bits=32, signed=False)
def ADT_U64(extensions:ExtensionsAny=None)->AdtTypeInteger: return AdtTypeInteger(extensions=extensions, bits=64, signed=False)
def ADT_I8 (extensions:ExtensionsAny=None)->AdtTypeInteger: return AdtTypeInteger(extensions=extensions, bits= 8, signed=True)
def ADT_I16(extensions:ExtensionsAny=None)->AdtTypeInteger: return AdtTypeInteger(extensions=extensions, bits=16, signed=True)
def ADT_I32(extensions:ExtensionsAny=None)->AdtTypeInteger: return AdtTypeInteger(extensions=extensions, bits=32, signed=True)
def ADT_I64(extensions:ExtensionsAny=None)->AdtTypeInteger: return AdtTypeInteger(extensions=extensions, bits=64, signed=True)


class AdtTypeString(AdtType):
    ''' Type descriptor for strings '''
    def __init__(self, extensions:ExtensionsAny=None):
        super().__init__(extensions=extensions)

class AdtTypeBool(AdtType):
    ''' Type descriptor for booleans '''
    def __init__(self, extensions:ExtensionsAny=None):
        super().__init__(extensions=extensions)

class AdtTypeFloat(AdtType):
    ''' Type descriptor for floating point values '''
    def __init__(self, extensions:ExtensionsAny=None):
        super().__init__(extensions=extensions)

class AdtTypeBinary(AdtType):
    ''' Type descriptor for binary data '''
    def __init__(self, extensions:ExtensionsAny=None):
        super().__init__(extensions=extensions)

class AdtTypeClass(AdtType):
    ''' Type descriptor for ADT defined classes '''
    def __init__(self, adtClass:AdtClass, polymorphic:bool, extensions:ExtensionsAny=None):
        super().__init__(extensions=extensions)
        self.m_adtClass:AdtClass = adtClass
        self.m_polymorphic:bool = polymorphic

class AdtTypeEnum(AdtType):
    ''' Type descriptor for ADT defined enum '''
    def __init__(self, adtEnum:AdtEnum, extensions:ExtensionsAny=None):
        super().__init__(extensions=extensions)
        self.m_adtEnum:AdtEnum = adtEnum

class AdtTypeVector(AdtType):
    ''' Type descriptor for lists '''
    def __init__(self, containedType:AdtType, extensions:ExtensionsAny=None):
        super().__init__(extensions=extensions)
        self.m_containedType:AdtType = containedType

class AdtTypeMap(AdtType):
    ''' Type descriptor for key-value maps '''
    def __init__(self, keyType:AdtType, containedType:AdtType, extensions:ExtensionsAny=None):
        super().__init__(extensions=extensions)
        self.m_keyType:AdtType = keyType
        self.m_containedType:AdtType = containedType
