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

from .cs_generator_base import CsGeneratorBase
from metaprog.cs.cs_class import CsClass
from metaprog.cs.cs_class_element import CsClassElement
from metaprog.cs.cs_attribute import CsAttribute
from metaprog.cs.cs_field import CsField
from metaprog.util.log import *
from metaprog.cs.cs_attribute import *

# Key to be used in the CsField "extension" dictionary to enable or disable the generation of the attribute
CS_MARSHAL_FIELD_ENABLE = "cs_marshal_enable"   # -> True or False
CS_MARSHAL_FIELD_NAME   = "cs_marshal_name"     # -> Optional string for a different attribute name

# Key to be used in the CsClass "extension" dictionary to enable or disable the generation of the attribute
CS_MARSHAL_CLASS_GENERATED = "cs_marshal_generated" # -> bool, created and written by this module to mark that has been processed
CS_MARSHAL_CLASS_NAME      = "cs_marshal_name"      # -> Alternate name used by this class to calculate the unique id used when streaming

CS_MARSHAL_CLASS_FIELDS_COUNT = "cs_marshal_fields_count"

class CsMarshalGenerator(CsGeneratorBase):
    def __init__(self):
        super().__init__()
    
    #=============================================================================================
    def decorateClasses(self) -> None:
        for csClass in self.m_csClasses:
            self.__calculateClass(csClass=csClass)

        for csClass in self.m_csClasses:
            self.__setupClass(csClass=csClass)
            self.__setupPolymorphicClass(csClass=csClass)

    #=============================================================================================
    def __calculateClass(self, csClass:CsClass) -> None:
        count:int = 0
        for csClassElement in csClass.m_classElements:
            if self.__isJsonProperty(csClassElement=csClassElement) is not None:
                count += 1
        csClass.m_extensions[CS_MARSHAL_CLASS_FIELDS_COUNT] = count

    #=============================================================================================
    def __setupClassUsings(self, csClass:CsClass) -> None:
        csClass.m_csUsings.add('System')
        csClass.m_csUsings.add('System.Text.Json')
        csClass.m_csUsings.add('System.Text.Json.Serialization')
        csClass.m_csUsings.add('System.Collections.Generic')
        csClass.m_csUsings.addDirective('#nullable enable')

    #=============================================================================================
    def __setupPolymorphicClass(self, csClass:CsClass) -> None:
        '''! Decorate the single class with all the required code '''
        # Detect classes that do not derive from anything or that derive from
        # an external type that is not involved in the polymorphic tree.
        if csClass.m_baseClass is None or not isinstance(csClass.m_baseClass, CsClass):
            derivedClasses:list[CsClass] = csClass.findDerivedClasses()
            if len(derivedClasses) > 1:
                # Generate the derivation attributes
                for derivedClass in derivedClasses:
                    self.__setupClassUsings(derivedClass)
                    if CS_MARSHAL_CLASS_NAME in derivedClass.m_extensions:
                        assert(isinstance(derivedClass.m_extensions[CS_MARSHAL_CLASS_NAME], str))
                        marshalClassName:str = derivedClass.m_extensions[CS_MARSHAL_CLASS_NAME]
                    else:
                        marshalClassName:str = derivedClass.getCsQualifiedName(csClass)
                    csClass.m_attributesClass.append(csAttribute=CsAttribute(attribKey=f'JsonDerivedType(typeof({derivedClass.getCsQualifiedName(csClass)}), typeDiscriminator:"{marshalClassName}")'))


    #=============================================================================================
    def __setupClass(self, csClass:CsClass) -> None:
        if CS_MARSHAL_CLASS_GENERATED in csClass.m_extensions:
            logError(f"Class `{csClass.getCsQualifiedName()}` generated more than once")
            return
        self.__setupClassUsings(csClass)
        csClass.m_extensions[CS_MARSHAL_CLASS_GENERATED] = True

        order:int = self.__getInitialFieldOrder(csClass=csClass)
        for csClassElement in csClass.m_classElements:
            csField:Optional[CsField] = self.__isJsonProperty(csClassElement=csClassElement)
            if csField is not None:
                if CS_MARSHAL_FIELD_NAME in csClassElement.m_extensions:
                    csField.m_attributesField.append(CsAttribute(attribKey=f'JsonPropertyName("{csClassElement.m_extensions[CS_MARSHAL_FIELD_NAME]}")'))
                csField.m_attributesField.append(CsAttribute(attribKey=f'JsonPropertyOrder({order})'))
                order += 1
            elif isinstance(csClassElement, CsField):
                csClassElement.m_attributesField.append(CsAttribute(attribKey='JsonIgnore'))


    #=============================================================================================
    def __isJsonProperty(self, csClassElement:CsClassElement) -> Optional[CsField]:
        if isinstance(csClassElement, CsField):
            if csClassElement.isProperty():
                if CS_MARSHAL_FIELD_ENABLE in csClassElement.m_extensions and csClassElement.m_extensions[CS_MARSHAL_FIELD_ENABLE]==True:
                    return csClassElement
        return None

    #=============================================================================================
    def __countJsonFields(self, csClass:CsClass) -> int:
        assert(isinstance(csClass.m_extensions[CS_MARSHAL_CLASS_FIELDS_COUNT], int))
        count:int = csClass.m_extensions[CS_MARSHAL_CLASS_FIELDS_COUNT]
        if csClass.m_baseClass is not None and isinstance(csClass.m_baseClass, CsClass):
            count += self.__countJsonFields(csClass.m_baseClass)
        return count

    #=============================================================================================
    def __getInitialFieldOrder(self, csClass:CsClass) -> int:
        assert(isinstance(csClass.m_extensions[CS_MARSHAL_CLASS_FIELDS_COUNT], int))
        if csClass.m_baseClass is not None and isinstance(csClass.m_baseClass, CsClass):
            return self.__countJsonFields(csClass.m_baseClass)
        return 0
