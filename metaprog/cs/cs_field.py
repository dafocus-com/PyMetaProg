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

from .cs_attribute import CsAttributes
from .cs_class_element import CsClassElement
from .cs_class_base import CsClassBase
from .cs_labels import CsVisibility
from .cs_type import CsType, CsTypeFactory, CsTypeAny
from .cs_config import CsConfig
from .cs_rvalue import CsRValueAny, CsRValueContainer
from .cs_includes import CsIncludesAny
from .cs_module_config import CsModuleConfig
from metaprog.util.writer import Writer
from metaprog.util.writable_set import WritableSet, WritableSetAny, WritableSetValid
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.comment import CommentAny
from metaprog.util.config import env
from typing import Union

# Key to be used in the CsType "extension" dictionary of a CsField or in its CsType
# to execute custom code to write the field part.
#
# Prototype: Callable[[CsField, Writer, CsConfig], None]
#
# Example:
#
#     myField.m_extensions[CS_FIELD_CODE] = f'''\
#         public List<int> {CS_FIELD_NAME}{{get; set;}} = new();
#     '''
#
CS_FIELD_CODE:str="cs_field_code"

_CS_FIELD_NAME:str = "CS_FIELD_NAME"
_CS_FIELD_OBJ:str = "CS_FIELD_OBJ"

CS_FIELD_NAME:str = env(_CS_FIELD_NAME)
CS_FIELD_OBJ:str = env(_CS_FIELD_OBJ)


class CsField(CsClassElement):
    ''' Implements fields and properties '''
    def __init__(self, 
            fieldName:str, 
            fieldType:CsTypeAny, 
            fieldDefault:CsRValueAny=None,
            fieldConst:bool=False,    # If set, generates a constexpr
            visibility:CsVisibility=CsVisibility.PUBLIC, 
            brief:CommentAny=None,
            csIncludes:CsIncludesAny = None,
            extensions:ExtensionsAny = None,
            propertySet:Union[bool,WritableSetAny] = None, # Specify `True` for `get;` or a writable for `get{...}`
            propertyGet:Union[bool,WritableSetAny] = None, # Specify `True` for `set;` or a writable for `set{...}`
        ) -> None:
        super().__init__(visibility=visibility, csIncludes=csIncludes, extensions=extensions, brief=brief)
        self.m_fieldName:str = fieldName
        self.m_fieldType:CsType = CsTypeFactory(fieldType)
        self.m_fieldConst:bool = fieldConst
        self.m_fieldDefault:CsRValueContainer = CsRValueContainer(csValueAny=fieldDefault)
        self.m_propertySet:Union[bool,WritableSetAny] = propertySet
        self.m_propertyGet:Union[bool,WritableSetAny] = propertyGet
        self.m_attributesField = CsAttributes()

    def setupModuleConfig(self, moduleConfig:CsModuleConfig) -> None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        super().setupModuleConfig(moduleConfig=moduleConfig)
        self.m_fieldType.setupModuleConfig(moduleConfig=moduleConfig)

    def isProperty(self)->bool:
        '''! Returns true if the item is a property (i.e. with get or set)
            or `False` if a field
        '''
        return self.m_propertySet is not None or self.m_propertyGet is not None

    def generateCsBody(self, writer:Writer, config:CsConfig) -> None:
        self.m_comment.write(writer, config)
        self.m_attributesField.write(writer, config)

        customCode:WritableSetAny = self.m_extensions.getValueOrNone(key=CS_FIELD_CODE)
        if customCode is None:
            customCode = self.m_fieldType.m_extensions.getValueOrNone(key=CS_FIELD_CODE)
        
        if customCode is not None:
            #customCode(self, writer, config)
            self._printCustomCode(writer=writer, config=config, code=customCode)
            return

        writer.writeRaw(self.m_visibility.toStr()+" ")
        if self.m_fieldConst:
            writer.writeRaw('const ')
            assert(self.m_fieldDefault is not None)

        assert(isinstance(self.m_owningScope, CsClassBase))
        self.m_fieldType.declVar(writer=writer, config=config, var=self.m_fieldName, containerClass=self.m_owningScope, isRef=False)

        if self.m_propertySet is not None or self.m_propertyGet is not None:
            self._generateGetSet(writer=writer, config=config)
            hasCustomGetSet:bool = not isinstance(self.m_propertySet, bool) or not isinstance(self.m_propertyGet, bool)
            hasGetSet:bool = True
        else:
            hasGetSet = False
            hasCustomGetSet = False

        if not self.m_fieldDefault.empty():
            writer.writeRaw(' = ')
            self.m_fieldDefault.write(writer, config)
            writer.writeRaw(";")
        elif not hasCustomGetSet and self.m_fieldType.getAssigneableDefaultValue(containerClass=self.getCsClass()) is not None:
            writer.writeRaw(f' = {self.m_fieldType.getAssigneableDefaultValue(containerClass=self.getCsClass())};')
        elif not hasGetSet:
            writer.writeRaw(";")
        writer.writeRaw('\n')

    def identify(self)->str:
        qualifiedName:str = ""
        if self.m_owningScope is not None:
            qualifiedName = self.m_owningScope.getCsQualifiedName() + "."
        qualifiedName += self.m_fieldName
        return qualifiedName

    def _generateGetSet(self, writer:Writer, config:CsConfig)->bool:
        multiLine:bool = (isinstance(self.m_propertyGet, WritableSet) or isinstance(self.m_propertySet, WritableSet))
        
        if multiLine:
            writer.writeNL(" {")
            writer.incIndent()
            self._WriteGetSet(writer=writer, config=config, text="get", data=self.m_propertyGet)
            writer.writeNL("")
            self._WriteGetSet(writer=writer, config=config, text="set", data=self.m_propertySet)
            writer.writeNL("")
            writer.decIndent()
            writer.write("}")
        else:
            writer.writeRaw("{")
            self._WriteGetSet(writer=writer, config=config, text="get", data=self.m_propertyGet)
            if self.m_propertyGet is not None and self.m_propertySet is not None: writer.writeRaw(" ")
            self._WriteGetSet(writer=writer, config=config, text="set", data=self.m_propertySet)
            writer.writeRaw("}")
        return multiLine

    def _WriteGetSet(self, writer:Writer, config:CsConfig, text:str, data:Union[bool,WritableSetAny]) -> None:
        if isinstance(data, bool) and data == True:
            writer.write(f'{text};')
        elif data is not None and isinstance(data, WritableSet):
            writer.writeNL(f'{text} {{')
            writer.incIndent()
            data.write(writer=writer, config=config)
            writer.decIndent()
            writer.writeNL('}')

    #=============================================================================================
    def _printCustomCode(self, writer:Writer, config:CsConfig, code:WritableSetValid) -> None:
        writableSet:WritableSet = WritableSet()
        writableSet.pushEnv(env={_CS_FIELD_NAME:self.m_fieldName, _CS_FIELD_OBJ:self})
        writableSet.append(code)
        writableSet.popEnv()
        writableSet.write(writer=writer, config=config)
