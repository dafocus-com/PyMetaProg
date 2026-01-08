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
from .cpp_type import *
from .cpp_config import CppConfig
from .cpp_class_base import CppClassBase
from .cpp_method import CppMethod, CppMethodType
from .cpp_param import CppParam
from .cpp_rvalue import CppRValueContainer, CppRValueAny
from .cpp_rvalue import CppRValue
from metaprog.util.writer import Writer
from metaprog.util.comment import *
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.log import *


# Key to be used in the CppField "extension" dictionary to enable the generation of the
# get and set methods. If set, the field is tagged as protected.
CPP_FIELD_GETSET="cpp_field_getset"   # -> True or False



class CppField(CppClassElement, CppRValue):
    def __init__(self, 
            fieldName:str, 
            fieldType:CppTypeAny, 
            fieldDefault:CppRValueAny=None,
            fieldConst:bool=False,    # If set, generates a constexpr
            visibility:CppVisibility=CppVisibility.DEFAULT, 
            brief:CommentAny=None,
            hppIncludes:CppIncludesAny = None,
            cppIncludes:CppIncludesAny = None,
            extensions:ExtensionsAny = None,
            adtFieldName:Optional[str] = None,  # Contains the name coming from ADT, which could be different from the actual name of the C++ field
        ):
        super().__init__(visibility=visibility, hppIncludes=hppIncludes, cppIncludes=cppIncludes, extensions=extensions)
        self.m_fieldName:str = fieldName
        self.m_adtFieldName:Optional[str] = adtFieldName
        self.m_fieldType:CppType = CppTypeFactory(fieldType)
        self.m_fieldConst:bool = fieldConst
        self.m_fieldDefault:CppRValueContainer = CppRValueContainer(cppValueAny=fieldDefault)
        self.m_comment:Comment = Comment(commentAny=brief)
        self.m_waterfallDone:bool = False

    def getAdtFieldName(self)->str:
        if self.m_adtFieldName is not None: return self.m_adtFieldName
        return self.m_fieldName

    def setupModuleConfig(self, moduleConfig:CppModuleConfig)->None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        super().setupModuleConfig(moduleConfig=moduleConfig)
        self.m_fieldType.setupModuleConfig(moduleConfig=moduleConfig)

    def needsInline(self)->bool:
        return False

    def needsCpp(self)->bool:
        return False

    def generateHppBody(self, writer:Writer, config:CppConfig)->None:
        self.m_comment.write(writer, config)
        if self.m_fieldConst:
            writer.writeRaw('static constexpr ')
            assert(self.m_fieldDefault is not None)

        assert(isinstance(self.m_owningScope, CppClassBase))
        self.m_fieldType.declVar(writer=writer, config=config, var=self.m_fieldName, containerClass=self.m_owningScope)

        if not self.m_fieldDefault.empty():
            writer.writeRaw(' = ')
            self.m_fieldDefault.write(writer, config)
        elif self.m_fieldType.getAssigneableDefaultValue(self.getCppClass()) is not None:
            writer.writeRaw(f' = {self.m_fieldType.getAssigneableDefaultValue(self.getCppClass())}')
            
        writer.writeRaw(";\n")

    
    def getCppQualifiedName(self, otherScope:Optional[CppNameScope]=None)->str:
        '''! Returns the minimally qualified name required by `otherScope` to reach 
            this CppNameScope. If `otherScope` is not specified, returns the full path
            from root.
        '''
        if otherScope is not None and otherScope==self.getCppClass():
            return self.m_fieldName
        return self.getCppClass().getCppQualifiedName(otherScope=otherScope)+"::"+self.m_fieldName

    def generateValue(self, writer:Writer, config:CppConfig, otherScope:Optional[CppNameScope]=None)->None:
        '''! Generate the R-value text '''
        if not self.m_fieldConst:
            logError(f"Can not use non const field {self.m_fieldName} as a const R-value")
            return
        writer.writeRaw(self.getCppQualifiedName(otherScope=otherScope))

    def generateHppInline(self, writer:Writer, config:CppConfig)->None:
        pass

    def generateCppBody(self, writer:Writer, config:CppConfig)->None:
        pass

    def identify(self)->str:
        qualifiedName:str = ""
        if self.m_owningScope is not None:
            qualifiedName = self.m_owningScope.getCppQualifiedName() + "::"
        qualifiedName += self.m_fieldName
        return qualifiedName

    def waterfallAdditionReset(self)->None:
        '''! Reset the waterfall addition.'''
        self.m_waterfallDone = False

    def waterfallAdditionOperate(self, config:CppConfig)->bool:
        '''! Operate the changes. Expect to be called multiple times. 
            Return `False` if changed nothing, `True` if something has been changed.
        '''
        if self.m_waterfallDone:
            return False
        self.m_waterfallDone = True
        somethingChanged:bool = False
        if CPP_FIELD_GETSET in self.m_extensions:
            self._generateGetSet(config=config)
            somethingChanged = True
        return somethingChanged

    def _generateGetSet(self, config:CppConfig):
        assert(self.m_owningScope is not None)
        assert(isinstance(self.m_owningScope, CppClassBase))

        # GETTER METHOD
        self.m_owningScope.addClassElement( # pyright: ignore[reportUnknownMemberType]
            CppMethod(
                methodName=config.getGetterSetterMethodName(fieldName=self.m_fieldName, getter=True),
                methodType=CppMethodType.NORMAL,
                returnType=self.m_fieldType.getReadOnlyReturnType(containerClass=self.m_owningScope),
                visibility=CppVisibility.PUBLIC,
                code=f'return {self.m_fieldName};',
                brief=f'Getter method for field `{self.m_fieldName}`',
                staticity=CppStaticity.DYNAMIC_CONST,
            )
        )

        # SETTER METHOD
        self.m_owningScope.addClassElement( # pyright: ignore[reportUnknownMemberType]
            CppMethod(
                methodName=config.getGetterSetterMethodName(fieldName=self.m_fieldName, getter=False),
                methodType=CppMethodType.NORMAL,
                returnType='void',
                visibility=CppVisibility.PUBLIC,
                params=[
                    CppParam(paramName='value', paramType=self.m_fieldType.constInputParam(containerClass=self.m_owningScope),)
                ],
                code=f'{self.m_fieldName} = value;',
                brief=f'Setter method for field `{self.m_fieldName}`',
                staticity=CppStaticity.DYNAMIC,
            )
        )