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
from .cs_class_base import CsClassBase
from .cs_labels import *
from .cs_param import CsParam
from .cs_module_config import CsModuleConfig
from .cs_namescope import CsNameScope
from .cs_config import CsConfig
from .cs_usings import CsUsingsAny
from .cs_type import *
from .cs_attribute import CsAttributes
from metaprog.util.writer import Writer
from metaprog.util.writable_set import WritableSet, WritableSetAny
from metaprog.util.comment import *
from metaprog.util.extensions import ExtensionsAny
class CsMethodType(Enum):
    NORMAL           = 1
    CONSTRUCTOR      = 2
    DESTRUCTOR       = 3


class CsMethod(CsClassElement):
    def __init__(self, 
            methodName:str="undefined", 
            returnType:CsTypeAny="void", 
            methodType:CsMethodType = CsMethodType.NORMAL,
            visibility:CsVisibility=CsVisibility.PUBLIC, 
            brief:CommentAny=None,
            virtuality:CsVirtuality=CsVirtuality.NORMAL,
            staticity:CsStaticity=CsStaticity.DYNAMIC,
            code:WritableSetAny=None,
            params:list[CsParam]=list(),
            genericeParams:list[str]=list(), # Generic parameters, i.e. the C# templates
            initializers:list[str]=list(), # Constructor initializers
            baseClassInitializers:list[str]=list(), # Base class constructor initializers
            csUsings:CsUsingsAny = None,
            extensions:ExtensionsAny = None,
        ):
        super().__init__(visibility=visibility, csUsings=csUsings, extensions=extensions)
        self.m_methodName:str = methodName
        self.m_returnType:CsType = CsTypeFactory(returnType)
        self.m_methodType:CsMethodType = methodType
        self.m_params:list[CsParam] = params
        for param in self.m_params:
            assert(param.m_owningMehod is None)
            param.m_owningMehod = self

        self.m_genericeParams:list[str] = genericeParams
        self.m_outOfClassReturnType:CsType = CsTypeFactory(returnType)
        self.m_virtuality:CsVirtuality = virtuality
        self.m_staticity:CsStaticity = staticity
        self.m_code:WritableSet = WritableSet(code)
        self.m_comment:Comment = Comment(commentAny=brief)
        self.m_initializers:list[str] = initializers
        self.m_baseClassInitializers:list[str] = baseClassInitializers
        self.m_attributesMeth = CsAttributes()

    def setupModuleConfig(self, moduleConfig:CsModuleConfig)->None:
        '''! Operate on the accessible parts of the module to add usings, header parts and so on '''
        super().setupModuleConfig(moduleConfig=moduleConfig)
        self.m_returnType.setupModuleConfig(moduleConfig=moduleConfig)
        self.m_outOfClassReturnType.setupModuleConfig(moduleConfig=moduleConfig)
        for param in self.m_params:
            param.setupModuleConfig(moduleConfig=moduleConfig)
            param.addToComment(self.m_comment)

    def generateCsBody(self, writer:Writer, config:CsConfig)->None:
        self.m_comment.write(writer, config)
        self.m_attributesMeth.write(writer, config)
        assert(self.m_methodType != CsMethodType.CONSTRUCTOR or (self.m_virtuality==CsVirtuality.NORMAL and self.m_staticity == CsStaticity.DYNAMIC))

        writer.writeRaw(self.m_visibility.toStr()+" ")
        if self.m_virtuality == CsVirtuality.NORMAL: pass
        elif self.m_virtuality == CsVirtuality.VIRTUAL: writer.writeRaw("virtual ")
        elif self.m_virtuality == CsVirtuality.VIRTUAL_OVERRIDE: writer.writeRaw("override ")
        elif self.m_virtuality == CsVirtuality.PURE_VIRTUAL: writer.writeRaw("abstract ")

        if self.m_methodType == CsMethodType.NORMAL:
            writer.writeRaw(f'{self.m_returnType.toString(self.getCsClass())} ')
        self.__proto(writer=writer, config=config, withDefault=True)

        if self.m_virtuality != CsVirtuality.PURE_VIRTUAL:
            self.__writeImpl(writer, config)
        else:
            writer.writeRaw(";\n")

    def __getMethodName(self) -> str:
        assert(isinstance(self.m_owningScope, CsNameScope))
        if self.m_methodType == CsMethodType.NORMAL: return self.m_methodName
        if self.m_methodType == CsMethodType.CONSTRUCTOR: return self.m_owningScope.getCsUnqualifiedName()
        if self.m_methodType == CsMethodType.DESTRUCTOR: return "~"+self.m_owningScope.getCsUnqualifiedName()
        return "INVALID"

    def __proto(self, writer:Writer, config:CsConfig, withDefault:bool) -> None:
        '''! Return a basic prototype (method name, parameters, const) without the return value '''
        writer.writeRaw(self.__getMethodName())
        if self.m_genericeParams:
            writer.writeRaw(f'<{",".join(self.m_genericeParams)}>')

        writer.writeRaw(f'(')
        self.__paramsDecl(writer=writer, config=config, withDefault=withDefault)
        writer.writeRaw(f')')

    def __paramsDecl(self, writer:Writer, config:CsConfig, withDefault:bool) -> None:
        first:bool = True
        for param in self.m_params:
            if first: first=False
            else: writer.writeRaw(", ")
            param.writeDecl(writer=writer, config=config)
        
    
    def __writeImpl(self, writer:Writer, config:CsConfig) -> None:
        if self.m_virtuality == CsVirtuality.PURE_VIRTUAL: 
            assert(self.m_code is None)
            return
        
        initializers:list[str] = list()
        if len(self.m_baseClassInitializers)>0:
            cls:CsClassBase = self.getCsClass()
            assert(cls.m_baseClass is not None)
            assert(isinstance(cls.m_baseClass,CsClassBase))
            initializers.append(f'base({",".join(self.m_baseClassInitializers)})')

        initializers += self.m_initializers

        if len(initializers) > 0:
            assert(self.m_methodType == CsMethodType.CONSTRUCTOR)
            writer.writeRaw(f': {", ".join(initializers)}\n')
        else:
            writer.writeRaw(' ')

        writer.writeRaw('{\n')
        writer.incIndent()
        self.m_code.write(writer=writer, config=config)

        writer.decIndent()
        writer.writeNL('}')

    def identify(self)->str:
        qualifiedName:str = ""
        if self.m_owningScope is not None:
            qualifiedName = self.m_owningScope.getCsQualifiedName() + "."
        qualifiedName += self.__getMethodName() + "(...)"
        return qualifiedName
