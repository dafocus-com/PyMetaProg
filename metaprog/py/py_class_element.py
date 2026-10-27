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

from .py_namescope import PyNameScope
from .py_labels import PyVisibility
from .py_config import PyConfig
from .py_module_config import PyModuleConfig
from .py_includes import PyIncludesAny
from metaprog.util.writer import Writer
from abc import abstractmethod
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.comment import Comment, CommentAny

class PyClassElement(PyNameScope):
    def __init__(
            self, 
            nameScope:str,
            visibility:PyVisibility,
            pyIncludesAny:PyIncludesAny,
            extensions:ExtensionsAny,
            brief:CommentAny=None,
        ):
        super().__init__(nameScope=nameScope, pyIncludesAny=pyIncludesAny, extensions=extensions, visibility=visibility)
        self.m_comment:Comment = Comment(commentAny=brief)

    @abstractmethod
    def identify(self)->str:
        ...

    def setupModuleConfig(self, moduleConfig:PyModuleConfig) -> None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        moduleConfig.m_pyIncludes.merge(self.m_pyIncludes)

    @abstractmethod
    def generatePyBody(self, writer:Writer, config:PyConfig) -> None:
        '''! Generate the body part of the .py file, i.e. where implementation of the methods go '''
        ...

    def __str__(self)->str:
        return self.identify()
