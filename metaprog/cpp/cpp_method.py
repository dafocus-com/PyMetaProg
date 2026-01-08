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

from .cpp_class_element import CppClassElement
from .cpp_labels import *
from .cpp_param import CppParam
from .cpp_module_config import CppModuleConfig
from .cpp_namescope import CppNameScope
from .cpp_config import CppConfig
from .cpp_includes import CppIncludesAny
from .cpp_template import *
from .cpp_type import *
from .cpp_class_base import CppClassBase
from .cpp_initializer import CppInitializerSet, CppInitializerAny
from metaprog.util.writer import Writer
from metaprog.util.writable_set import WritableSet, WritableSetAny
from metaprog.util.comment import *
from metaprog.util.extensions import ExtensionsAny

class CppMethodType(Enum):
    NORMAL           = 1
    CONSTRUCTOR      = 2
    DESTRUCTOR       = 3


class CppMethod(CppClassElement):
    def __init__(self, 
            methodName:str="undefined", 
            returnType:CppTypeAny="void", 
            methodType:CppMethodType = CppMethodType.NORMAL,
            visibility:CppVisibility=CppVisibility.DEFAULT, 
            brief:CommentAny=None,
            inline:CppInline=CppInline.INLINE_OUTSIDE,
            virtuality:CppVirtuality=CppVirtuality.NORMAL,
            staticity:CppStaticity=CppStaticity.DYNAMIC,
            code:WritableSetAny=None,
            params:list[CppParam]=list(),
            initializers:list[CppInitializerAny]=list(), # Constructor initializers
            baseClassInitializers:list[str]=list(), # Base class constructor initializers
            hppIncludes:CppIncludesAny = None,
            cppIncludes:CppIncludesAny = None,
            extensions:ExtensionsAny = None,
            methodTemplate:CppTemplateArguments = list(), # Specify the template parameters this method must have
        ):
        super().__init__(visibility=visibility, hppIncludes=hppIncludes, cppIncludes=cppIncludes, extensions=extensions)
        self.m_methodName:str = methodName
        self.m_returnType:CppType = CppTypeFactory(returnType)
        self.m_methodType:CppMethodType = methodType
        self.m_params:list[CppParam] = params
        for param in self.m_params:
            assert(param.m_owningMehod is None)
            param.m_owningMehod = self

        self.m_outOfClassReturnType:CppType = CppTypeFactory(returnType)
        self.m_inline:CppInline = inline
        self.m_virtuality:CppVirtuality = virtuality
        self.m_staticity:CppStaticity = staticity
        self.m_code:WritableSet = WritableSet(code)
        self.m_comment:Comment = Comment(commentAny=brief)
        self.m_initializers:CppInitializerSet = CppInitializerSet(initializers=initializers)
        self.m_baseClassInitializers:list[str] = baseClassInitializers
        self.m_methodTemplate:CppTemplate = CppTemplate(templateArguments=methodTemplate)

    def needsInline(self)->bool:
        return self.m_inline == CppInline.INLINE_OUTSIDE

    def needsCpp(self)->bool:
        return self.m_inline == CppInline.OUT_OF_LINE

    def setupModuleConfig(self, moduleConfig:CppModuleConfig)->None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        super().setupModuleConfig(moduleConfig=moduleConfig)
        self.m_returnType.setupModuleConfig(moduleConfig=moduleConfig)
        self.m_outOfClassReturnType.setupModuleConfig(moduleConfig=moduleConfig)
        for param in self.m_params:
            param.setupModuleConfig(moduleConfig=moduleConfig)
            param.addToComment(self.m_comment)
        self.m_methodTemplate.addToComment(self.m_comment)
        

    def generateHppBody(self, writer:Writer, config:CppConfig)->None:
        self.m_comment.write(writer, config)
        assert(self.m_methodType != CppMethodType.CONSTRUCTOR or (self.m_virtuality==CppVirtuality.NORMAL and self.m_staticity == CppStaticity.DYNAMIC))

        self.m_methodTemplate.getTemplateDecl(writer=writer, config=config, withDefaults=True)
        if self.m_virtuality!=CppVirtuality.NORMAL:
            writer.writeRaw("virtual ")
        elif self.m_staticity == CppStaticity.STATIC:
            writer.writeRaw("static ")
        if self.m_methodType == CppMethodType.NORMAL:
            writer.writeRaw(f'{self.m_returnType.toString(self.getCppClass())} ')
        self.__proto(writer=writer, config=config, withDefault=True)
        if self.m_virtuality == CppVirtuality.VIRTUAL_OVERRIDE:
            writer.writeRaw(" override")
        elif self.m_virtuality == CppVirtuality.PURE_VIRTUAL:
            writer.writeRaw(" = 0;\n")
        if self.m_inline == CppInline.INLINE_INSIDE:
            self.__writeImpl(writer, config)
        else:
            writer.writeRaw(";\n")


    def generateHppInline(self, writer:Writer, config:CppConfig)->None:
        '''! Generate the inline part of the C++ .hpp file, i.e. where the `inline` methods go '''
        if self.m_inline != CppInline.INLINE_OUTSIDE: return
        self.__externImpl(writer=writer, config=config, inline=True)

    def generateCppBody(self, writer:Writer, config:CppConfig)->None:
        '''! Generate the body part of the C++ .cpp file, i.e. where implementation of the methods go '''
        if self.m_inline != CppInline.OUT_OF_LINE: return
        self.__externImpl(writer=writer, config=config, inline=False)

    def __getMethodName(self) -> str:
        assert(isinstance(self.m_owningScope, CppNameScope))
        if self.m_methodType == CppMethodType.NORMAL: return self.m_methodName
        if self.m_methodType == CppMethodType.CONSTRUCTOR: return self.m_owningScope.getCppUnqualifiedName()
        if self.m_methodType == CppMethodType.DESTRUCTOR: return "~"+self.m_owningScope.getCppUnqualifiedName()
        return "INVALID"

    def __proto(self, writer:Writer, config:CppConfig, withDefault:bool) -> None:
        '''! Return a basic prototype (method name, parameters, const) without the return value '''
        const:str = " const" if self.m_staticity==CppStaticity.DYNAMIC_CONST else ""
        writer.writeRaw(f'{self.__getMethodName()}(')
        self.__paramsDecl(writer=writer, config=config, withDefault=withDefault)
        writer.writeRaw(f'){const}')

    def __externProto(self, writer:Writer, config:CppConfig) -> None:
        '''! Return a complete external prototype '''
        assert(self.m_owningScope is not None)
        assert(config.m_cppCurrentNameScope is None or isinstance(config.m_cppCurrentNameScope, CppNameScope))  # type: ignore
        cls:str = self.m_owningScope.getCppQualifiedName(config.m_cppCurrentNameScope) # TBD
        #print(f'CLASS=[{self.m_owningScope.getCppQualifiedName(None)}] targetNameScope=[{targetNameScope.getCppQualifiedName(None)}]')
        if len(cls) > 0: cls += "::"
        if self.m_methodType == CppMethodType.NORMAL:
            writer.writeRaw(f'{self.m_outOfClassReturnType.toString(self.getCppClass())} ')
        writer.writeRaw(f'{cls}')
        self.__proto(writer=writer, config=config, withDefault=False)

    def __externImpl(self, writer:Writer, config:CppConfig, inline:bool) -> None:
        '''! Return a complete external implementation '''
        self.m_methodTemplate.getTemplateDecl(writer=writer, config=config, withDefaults=False)
        if inline: writer.write("inline ")
        self.__externProto(writer, config)
        self.__writeImpl(writer, config=config)

    def __paramsDecl(self, writer:Writer, config:CppConfig, withDefault:bool) -> None:
        first:bool = True
        for param in self.m_params:
            if first: first=False
            else: writer.writeRaw(", ")
            param.writeDecl(writer=writer, config=config, withDefault=withDefault)
        
    
    def __writeImpl(self, writer:Writer, config:CppConfig) -> None:
        if self.m_virtuality == CppVirtuality.PURE_VIRTUAL: 
            assert(self.m_code is None)
            return
        
        initializers:list[str] = list()
        if len(self.m_baseClassInitializers)>0:
            cls:CppClassBase = self.getCppClass()
            assert(cls.m_baseClass is not None)
            if isinstance(cls.m_baseClass,CppClassBase):
                initializers.append(f'{cls.m_baseClass.getCppQualifiedName(cls)}({",".join(self.m_baseClassInitializers)})')
            else:
                initializers.append(f'{cls.m_baseClass}({",".join(self.m_baseClassInitializers)})')
        
        self.m_initializers.appendToList(initializers)

        if len(initializers) > 0:
            assert(self.m_methodType == CppMethodType.CONSTRUCTOR)
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
            qualifiedName = self.m_owningScope.getCppQualifiedName() + "::"
        qualifiedName += self.__getMethodName() + "(...)"
        return qualifiedName
