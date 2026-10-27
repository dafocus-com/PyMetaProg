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

from .py_attribute import PyAttributes
from .py_class_element import PyClassElement
from .py_namescope import PyNameScope
from .py_config import PyConfig
from .py_labels import PyVisibility, PyStaticity
from .py_module_config import PyModuleConfig
from .py_param import PyParam
from .py_type import PyType, PyTypeFactory, PyTypeAny, PyTypeNone
from .py_includes import PyIncludes, PyIncludesAny 
from metaprog.util.comment import CommentAny
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.writable_set import WritableSet, WritableSetAny
from metaprog.util.writer import Writer
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING: 
    from .py_class import PyClass


class PyMethod(PyClassElement):
    def __init__(self, 
            methodName:str="undefined", 
            returnType:PyTypeAny=PyTypeNone(), 
            visibility:PyVisibility=PyVisibility.PUBLIC, 
            brief:CommentAny=None,
            staticity:PyStaticity=PyStaticity.DYNAMIC,
            code:WritableSetAny=None,
            params:list[PyParam]=list(),
            pyIncludesAny:PyIncludesAny = None,
            pyLocalIncludesAny:PyIncludesAny = None, # Runtime imports added inside the method code
            extensions:ExtensionsAny = None,
        ):
        super().__init__(nameScope=methodName, visibility=visibility, pyIncludesAny=pyIncludesAny, extensions=extensions, brief=brief)
        self.m_returnType:PyType = PyTypeFactory(returnType)
        self._params:list[PyParam] = list()
        for param in params:
            self.addParam(param=param)

        self.m_outOfClassReturnType:PyType = PyTypeFactory(returnType)
        self.m_staticity:PyStaticity = staticity
        self.m_code:WritableSet = WritableSet(code)
        self.m_attributesMeth = PyAttributes()
        self.m_pyLocalIncludes:PyIncludes = PyIncludes(pyIncludesAny=pyLocalIncludesAny)

    def addParam(self, param:PyParam) -> None:
        assert(param.m_owningMehod is None)
        param.m_owningMehod = self
        self._params.append(param)

    def setupModuleConfig(self, moduleConfig:PyModuleConfig) -> None:
        '''! Operate on the accessible parts of the module to add imports, header parts and so on '''
        super().setupModuleConfig(moduleConfig=moduleConfig)
        self.m_returnType.setupModuleConfig(moduleConfig=moduleConfig)
        self.m_outOfClassReturnType.setupModuleConfig(moduleConfig=moduleConfig)
        for param in self._params:
            param.setupModuleConfig(moduleConfig=moduleConfig)
            param.addToComment(self.m_comment)

    def generatePyBody(self, writer:Writer, config:PyConfig) -> None:
        self.m_comment.write(writer, config)
        self.m_attributesMeth.write(writer, config)

        isNextPar:bool = False
        isInClass:bool = self.getParentClass() is not None
        isDynamic:bool = (self.m_staticity == PyStaticity.DYNAMIC) and isInClass

        if not isDynamic and isInClass:
            writer.writeNL('@classmethod')

        writer.writeRaw(f'def {self.__getMethodName()}(')
        if isDynamic:
            writer.writeRaw(f'self')
            isNextPar = True
        elif not isDynamic and isInClass:
            writer.writeRaw(f'cls')
            isNextPar = True
            

        # Generate the other parameters
        for param in self._params:
            if isNextPar: writer.writeRaw(', ')
            else: isNextPar = True
            param.writeDecl(writer=writer, config=config)
        
        writer.writeRaw(f') -> {self.m_returnType.typeHint(containerClass=self.getParentClass())}:\n')
        self._writeImpl(writer=writer, config=config)
        
    def getParentClass(self) -> Optional[PyClass]:
        from .py_class import PyClass
        if self.m_parent is None: return None
        cls:Optional[PyNameScope] = self.m_parent.upscanType(searchedType=PyClass)
        if cls is None: return None
        assert(isinstance(cls, PyClass))
        return cls

    def __getMethodName(self) -> str:
        return self.m_nameScope
        
    def _writeImpl(self, writer:Writer, config:PyConfig) -> None:
        addPass:bool = True
        writer.incIndent()

        self.m_pyLocalIncludes.write(writer=writer, config=config)

        if not self.m_code.empty(): 
            addPass = False
            self.m_code.write(writer=writer, config=config)

        # If no code has been provided, write `pass`
        if addPass:
            writer.writeNL('pass')
        writer.decIndent()

    def identify(self)->str:
        return self.getPyQualifiedName()
