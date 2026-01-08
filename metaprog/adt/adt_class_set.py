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
from .adt_class import AdtClass
from .adt_enum import AdtEnum
from .adt_constant import AdtConstant

class AdtClassSet:
    def __init__(self, classes:list[AdtClass]=list(), enums:list[AdtEnum]=list(), constants:list[AdtConstant]=list()):
        self.m_classes:list[AdtClass]=list()
        self.m_classes += classes
        self.m_enums:list[AdtEnum]=list()
        self.m_enums += enums
        self.m_constants:list[AdtConstant]=list()
        self.m_constants += constants
    
    def appendClass(self, adtClass:AdtClass)->AdtClass:
        self.m_classes.append(adtClass)
        return adtClass

    def appendEnum(self, adtEnum:AdtEnum)->AdtEnum:
        self.m_enums.append(adtEnum)
        return adtEnum

    def appendConstant(self, adtConstant:AdtConstant)->AdtConstant:
        self.m_constants.append(adtConstant)
        return adtConstant

    def merge(self, adtClassSet:AdtClassSet)->None:
        for adtClass in adtClassSet.m_classes:
            self.appendClass(adtClass=adtClass)

        for adtEnum in adtClassSet.m_enums:
            self.appendEnum(adtEnum=adtEnum)

        for adtConstant in adtClassSet.m_constants:
            self.appendConstant(adtConstant=adtConstant)
