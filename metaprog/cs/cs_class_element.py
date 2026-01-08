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

from .cs_namescope import CsNameScope
from .cs_labels import *
from .cs_config import CsConfig
from .cs_module_config import CsModuleConfig
from .cs_usings import CsUsings, CsUsingsAny
from metaprog.util.writer import Writer
from abc import ABC, abstractmethod
from metaprog.util.extensions import Extensions, ExtensionsAny
from typing import Optional
from .cs_class_base import CsClassBase
from metaprog.util.comment import *

class CsClassElement(ABC):
    def __init__(
            self, 
            visibility:CsVisibility,
            csUsings:CsUsingsAny,
            extensions:ExtensionsAny,
            brief:CommentAny=None,
        ):
        self.m_visibility = visibility
        self.m_owningScope:Optional[CsNameScope] = None
        self.m_csUsings:CsUsings = CsUsings(usings=csUsings)
        self.m_extensions:Extensions = Extensions(extensions=extensions)
        self.m_comment:Comment = Comment(commentAny=brief)

    @abstractmethod
    def identify(self)->str:
        ...

    def setupModuleConfig(self, moduleConfig:CsModuleConfig)->None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        moduleConfig.m_csUsings.merge(self.m_csUsings)

    @abstractmethod
    def generateCsBody(self, writer:Writer, config:CsConfig)->None:
        '''! Generate the body part of the C++ .cs file, i.e. where implementation of the methods go '''
        ...

    def __str__(self)->str:
        return self.identify()

    def getCsClass(self)->CsClassBase:
        assert(self.m_owningScope is not None)
        assert(isinstance(self.m_owningScope, CsClassBase))
        return self.m_owningScope

