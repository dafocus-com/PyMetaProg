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

from .py_includes import PyIncludes, PyIncludesAny
from .py_module_config import PyModuleConfig
from .py_config import PyConfig
from .py_type import PyType, PyTypeFactory, PyTypeAny
from .py_namescope import PyNameScope
from typing import Optional, TYPE_CHECKING
from metaprog.util.comment import Comment, CommentAny
from metaprog.util.comment_entry import COMMENT_PARAM
from metaprog.util.writer import Writer
if TYPE_CHECKING: 
    from .py_method import PyMethod

class PyParam:
    '''! PyMethod parameter '''
    def __init__(
        self, 
        paramName:str, 
        paramType:PyTypeAny,
        paramDefault:Optional[str] = None,
        paramComment:CommentAny = None,
        pyIncludesAny:PyIncludesAny = None,
    ):
        self.m_paramName:str = paramName
        self.m_paramType:PyType = PyTypeFactory(paramType)
        self.m_paramDefault:Optional[str] = paramDefault
        self.m_paramComment:Comment = Comment(commentAny=paramComment, commandIfString=COMMENT_PARAM, paramIfString=paramName)
        self.m_pyIncludes:PyIncludes = PyIncludes(pyIncludesAny=pyIncludesAny)
        self.m_owningMehod:Optional[PyMethod] = None

    def addToComment(self, comment:Comment) -> None:
        comment.merge(other=self.m_paramComment)

    def writeDecl(self, writer:Writer, config:PyConfig) -> None:
        defaultCode:str = ""
        if self.m_paramDefault:
            defaultCode = f' = {self.m_paramDefault}'
        assert(self.m_owningMehod is not None)

        self.m_paramType.declVar(writer=writer, config=config, var=self.m_paramName, containerClass=self.m_owningMehod.upscanType(searchedType=PyNameScope))
        writer.writeRaw(f'{defaultCode}')

    def setupModuleConfig(self, moduleConfig:PyModuleConfig) -> None:
        '''! Operate on the accessible parts of the module to add imports, header parts and so on '''
        moduleConfig.m_pyIncludes.merge(self.m_pyIncludes)
        self.m_paramType.setupModuleConfig(moduleConfig=moduleConfig)
