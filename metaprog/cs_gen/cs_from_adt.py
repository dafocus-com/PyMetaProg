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

from typing import Optional
from metaprog.adt.adt_class import *
from metaprog.adt.adt_type import *
from metaprog.adt.adt_type_misc import *
from metaprog.adt.adt_class_set import *
from metaprog.cs.cs_class import *
from metaprog.cs.cs_enum import *
from metaprog.cs.cs_namescope_with_children import CsNameScopeWithChildren
from metaprog.cs.cs_type import *
from metaprog.cs.cs_field import *
from metaprog.cs.cs_config import *
from metaprog.cs.cs_constant import *
from metaprog.cs_gen.cs_marshal_generator import *
from metaprog.util.log import *


'''! This extension value can be added to the extensions of the `AdtClass`; must be a `CsNameScopeWithChildren` or deriveds  '''
CS_NAMESCOPE:str = "cs_adt_namescope"

'''! Used in `AdtClass` and `AdtField` to indicate the name that the C++ implementation should use '''
CS_NAME:str = "cs_adt_name"

CS_TYPEMAP:dict[str,str] = {
    "u8" : "byte",
    "i8" : "sbyte",
    "u16": "ushort",
    "i16": "short",
    "u32": "uint",
    "i32": "int",
    "u64": "ulong",
    "i64": "long",
}

'''! 
Used in `AdtClass` to execute extra actions on the created `CsClass`, like adding methods and so on. 
It expects an instance of `CsAdtClassCustom` or a `list[CsAdtClassCustom]`. 
It will call their methods 'customAction' after having created the C# class.
'''
CS_CUSTOM_CODE:str = "cs_custom_code"

'''! Used in `AdtField` with value type `string`; it is used as default value '''
CS_FIELD_DEFAULT:str = "cs_field_default"

class CsAdtClassCustom:
    def customAction(self, adtClass:AdtClass, csClass:CsClass)->None:
        pass

class CsAdtTypeCustom:
    def customAction(self, adtType:AdtType, csType:CsType)->None:
        pass

class CsFromAdt:

    '''
    Starting from a set of AdtClass instances, creates the related C# classes.
    It uses some extension values in the AdtClass to control the C# generation
    '''
    def __init__(
            self, 
            defaultNameScope:Optional[CsNameScopeWithChildren]=None   # This is the namescope 
        ):
        self.m_defaultNameScope:Optional[CsNameScopeWithChildren] = defaultNameScope
        
        self.m_classMap:dict[str,CsClass] = dict()
        ''' Maps the ADT class name with the related C++ class '''

        self.m_enumMap:dict[str,CsEnum] = dict()
        ''' Maps the ADT enum name with the related C++ class '''

        self.m_constantMap:dict[str,CsConstant] = dict()
        ''' Maps the ADT constants '''

    #=======================================================================================================
    def generate(self, adtClassSet:AdtClassSet)->list[CsClass]:
        '''! Generate the C# classes related to the specified ADT classes '''
        for adtConstant in adtClassSet.m_constants:
            self.__generateConstant(adtConstant=adtConstant)

        for adtEnum in adtClassSet.m_enums:
            self.__generateEnum(adtEnum=adtEnum)

        for adtClass in adtClassSet.m_classes:
            self.__generateClass(adtClass=adtClass)
        
        # Resolve inheritance
        for adtClass in adtClassSet.m_classes:
            self.__resolveInheritance(adtClass=adtClass)

        csClasses:list[CsClass] = list()
        for csClass in self.m_classMap.values():
            csClasses.append(csClass)

        # Call the custom actions
        # Resolve inheritance
        for adtClass in adtClassSet.m_classes:
            self.__callCustomCode(adtClass=adtClass)

        return csClasses

    #=======================================================================================================
    def __generateClass(self, adtClass:AdtClass):
        if adtClass.m_className in self.m_classMap:
            logError(f"Dupe ADT class {adtClass.m_className}")
        
        if CS_NAMESCOPE in adtClass.m_extensions:
            assert(isinstance(adtClass.m_extensions[CS_NAMESCOPE], CsNameScopeWithChildren))
            nameScope:CsNameScopeWithChildren = adtClass.m_extensions[CS_NAMESCOPE]
        elif self.m_defaultNameScope is not None:
            nameScope:CsNameScopeWithChildren = self.m_defaultNameScope
        else:
            logError(f"No namescope defined for class {adtClass.m_className}")
            return
            
        if CS_NAME in adtClass.m_extensions:
            csClassName:str = adtClass.m_extensions[CS_NAME]
        else:
            csClassName:str = adtClass.m_className

        csClass:CsClass = CsClass(
            className=csClassName,
            brief=adtClass.m_brief,
            classVirtuality=CsClassVirtuality.CLASS_VIRTUAL,
            classVisibility=CsVisibility.PUBLIC,
            extensions={
                CS_MARSHAL_CLASS_NAME:adtClass.m_className,
            }
        )
        csClass.m_extensions.merge(adtClass.m_extensions)
        self.m_classMap[adtClass.m_className] = csClass
        nameScope.addChild(child=csClass)

        for adtField in adtClass.m_fields:
            self.__generateField(adtField=adtField, csClass=csClass)

    #=======================================================================================================
    def __generateEnum(self, adtEnum:AdtEnum):
        if adtEnum.m_enumName in self.m_enumMap:
            logError(f"Dupe ADT enum {adtEnum.m_enumName}")

        if CS_NAMESCOPE in adtEnum.m_extensions:
            assert(isinstance(adtEnum.m_extensions[CS_NAMESCOPE], CsNameScopeWithChildren))
            nameScope:CsNameScopeWithChildren = adtEnum.m_extensions[CS_NAMESCOPE]
        elif self.m_defaultNameScope is not None:
            nameScope:CsNameScopeWithChildren = self.m_defaultNameScope
        else:
            logError(f"No namescope defined for enum {adtEnum.m_enumName}")
            return
            
        if CS_NAME in adtEnum.m_extensions:
            csEnumName:str = adtEnum.m_extensions[CS_NAME]
        else:
            csEnumName:str = adtEnum.m_enumName

        csEnumEntries:list[CsEnumEntry] = list()
        for adtEnumEntry in adtEnum.m_enumEntries:
            csEnumEntries.append(CsEnumEntry(
                enumEntryName=adtEnumEntry.m_enumEntryName,
                enumEntryValue=adtEnumEntry.m_enumEntryValue,
                enumEntryDefault=adtEnumEntry.m_enumEntryDefault,
                brief=adtEnumEntry.m_brief,
            ))

        csEnum:CsEnum = CsEnum(
            enumClassName=csEnumName,
            brief=adtEnum.m_brief,
            enumEntries=csEnumEntries,
            extensions={
                CS_MARSHAL_CLASS_NAME:adtEnum.m_enumName,
            }
        )
        self.m_enumMap[adtEnum.m_enumName] = csEnum
        nameScope.addChild(child=csEnum)

    #=======================================================================================================
    def __generateConstant(self, adtConstant:AdtConstant):
        if adtConstant.m_constantName in self.m_constantMap:
            logError(f"Dupe ADT constant {adtConstant.m_constantName}")

        if CS_NAMESCOPE in adtConstant.m_extensions:
            assert(isinstance(adtConstant.m_extensions[CS_NAMESCOPE], CsNameScopeWithChildren))
            nameScope:CsNameScopeWithChildren = adtConstant.m_extensions[CS_NAMESCOPE]
        elif self.m_defaultNameScope is not None:
            nameScope:CsNameScopeWithChildren = self.m_defaultNameScope
        else:
            logError(f"No namescope defined for constant {adtConstant.m_constantName}")
            return
            
        if CS_NAME in adtConstant.m_extensions:
            csConstantName:str = adtConstant.m_extensions[CS_NAME]
        else:
            csConstantName:str = adtConstant.m_constantName

        csConstant:CsConstant = CsConstant(
            constantName=csConstantName,
            constantType=self.__getCsType(adtType=adtConstant.m_constantType, adtDefault=adtConstant.m_constantValue),
            brief=adtConstant.m_brief,
            extensions=adtConstant.m_extensions.newMerged(extensions={
                CS_MARSHAL_CLASS_NAME:adtConstant.m_constantName,
            })
        )
        self.m_constantMap[adtConstant.m_constantName] = csConstant
        nameScope.addChild(child=csConstant)
    
    #=======================================================================================================
    def __resolveInheritance(self, adtClass:AdtClass):
        if adtClass.m_baseClass is None: return
        if adtClass.m_baseClass.m_className not in self.m_classMap:
            logError(f"ADT class {adtClass.m_className} derives from unexisting class {adtClass.m_baseClass.m_className}")
            return
        
        thisCsClass:CsClass = self.m_classMap[adtClass.m_className]
        baseCsClass:CsClass = self.m_classMap[adtClass.m_baseClass.m_className]
        thisCsClass.m_baseClass = baseCsClass

    #=======================================================================================================
    def __callCustomCode(self, adtClass:AdtClass):
        assert(adtClass.m_className in self.m_classMap)
        csClass:CsClass = self.m_classMap[adtClass.m_className]
        if CS_CUSTOM_CODE in adtClass.m_extensions:
            customCode = adtClass.m_extensions[CS_CUSTOM_CODE]
            if isinstance(customCode, CsAdtClassCustom):
                customCode.customAction(adtClass=adtClass, csClass=csClass)
            elif isinstance(customCode, list):
                for customAction in customCode: # type: ignore
                    assert(isinstance(customAction, CsAdtClassCustom))
                    customAction.customAction(adtClass=adtClass, csClass=csClass)

    #=======================================================================================================
    def __generateField(self, adtField:AdtField, csClass:CsClass):
        if CS_NAME in adtField.m_extensions:
            assert(isinstance(adtField.m_extensions[CS_NAME], str))
            csFieldName:str = adtField.m_extensions[CS_NAME]
        else:
            csFieldName:str = adtField.m_fieldName

        # First, privilege an explicit CS_FIELD_DEFAULT value
        extensionDefinedDefault:CsRValueAny = adtField.m_extensions.getValueOrNone(CS_FIELD_DEFAULT)

        # If an explicit CS_FIELD_DEFAULT is not defined, see if an ADT constant
        # has been associated to the field.
        if extensionDefinedDefault is None and adtField.m_fieldDefault is not None:
            csConstant:CsConstant = self.m_constantMap[adtField.m_fieldDefault.m_constantName]
            extensionDefinedDefault = csConstant

        csField:CsField = CsField(
            fieldName=csFieldName,
            fieldType=self.__getCsType(adtField.m_fieldType),
            propertyGet=True,
            propertySet=True,
            visibility=CsVisibility.PUBLIC,
            extensions={
                CS_MARSHAL_FIELD_ENABLE:True,
                CS_MARSHAL_FIELD_NAME:adtField.m_fieldName,
            },
            brief=adtField.m_brief,
            fieldDefault=extensionDefinedDefault,
        )
        csClass.addClassElement(classElement=csField)
        csField.m_extensions.merge(adtField.m_extensions)

    #=======================================================================================================
    def __getCsType2(self, adtType:AdtType, adtDefault:Optional[str]=None)->CsType:

        if isinstance(adtType, AdtTypeInteger):
            typeId:str = f'{"i" if adtType.m_signed else "u"}{adtType.m_bits}'
            if not typeId in CS_TYPEMAP:
                logError(f"ADT class invalid simple type of {adtType.m_bits} bits (typeId='{typeId}')")
                return CsTypeSimple(simpleType="void")
            csTypeSimple:CsTypeSimple = CsTypeSimple(simpleType=CS_TYPEMAP[typeId])
            if adtDefault is not None:
                csTypeSimple.m_defaultValue = adtDefault
            return csTypeSimple

        if isinstance(adtType, AdtTypeString):
            return CsTypeString(defaultValue=adtDefault)

        if isinstance(adtType, AdtTypeBool):
            csTypeSimple:CsTypeSimple = CsTypeSimple(simpleType="bool")
            if adtDefault is not None:
                if adtDefault.lower() == 'true':
                    csTypeSimple.m_defaultValue = 'true'
                elif adtDefault.lower() == 'false':
                    csTypeSimple.m_defaultValue = 'false'
                else:
                    logError(f"Invalid boolean '{adtDefault}'")
            return csTypeSimple

        if isinstance(adtType, AdtTypeEnum):
            assert(adtDefault is None)
            return CsTypeClass(csClass=self.m_enumMap[adtType.m_adtEnum.m_enumName])

        if isinstance(adtType, AdtTypeClass):
            assert(adtDefault is None)
            if adtType.m_adtClass.m_className in self.m_classMap:
                return CsTypeClass(csClass=self.m_classMap[adtType.m_adtClass.m_className])
            else:
                logError(f"ADT type reference an ADT class named '{adtType.m_adtClass.m_className}' which has not been generated in C++")
                return CsTypeSimple(simpleType="void")

        if isinstance(adtType, AdtTypeVector):
            assert(adtDefault is None)
            return CsTypeVector(containedType=self.__getCsType(adtType=adtType.m_containedType))

        if isinstance(adtType, AdtTypeMap):
            assert(adtDefault is None)
            return CsTypeMap(keyType=CsTypeString(), containedType=self.__getCsType(adtType=adtType.m_containedType))
        
        logError(f"ADT type reference invalid")
        return CsTypeSimple(simpleType="void")
    

    #=======================================================================================================
    def __getCsType(self, adtType:AdtType, adtDefault:Optional[str]=None)->CsType:
        csType:CsType = self.__getCsType2(adtType=adtType, adtDefault=adtDefault)
        csType.m_extensions.merge(adtType.m_extensions)

        if CS_CUSTOM_CODE in adtType.m_extensions:
            assert(isinstance(adtType.m_extensions[CS_CUSTOM_CODE], CsAdtTypeCustom))
            adtType.m_extensions[CS_CUSTOM_CODE].customAction(adtType=adtType, csType=csType)

        return csType

