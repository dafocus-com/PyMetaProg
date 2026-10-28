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

from metaprog.adt.adt_class_set import AdtClassSet
from metaprog.adt.adt_class import AdtClass
from metaprog.adt.adt_constant import AdtConstant
from metaprog.adt.adt_field import AdtField
from metaprog.adt.adt_enum import AdtEnum
from metaprog.adt.adt_type_misc import AdtType, AdtTypeInteger, AdtTypeString, AdtTypeClass, AdtTypeVector, AdtTypeBinary, AdtTypeBool, AdtTypeEnum, AdtTypeMap, AdtTypeFloat
from metaprog.cpp_gen.cpp_hash_generator import CPP_HASH_CLASS_NAME
from metaprog.cpp_gen.cpp_marshal_generator import CPP_MARSHAL_CLASS_NAME, CPP_MARSHAL_FIELD_ENABLE, CPP_MARSHAL_FIELD_NAME
from metaprog.cpp.cpp_children_container import CppChildrenContainer
from metaprog.cpp.cpp_class import CppClass
from metaprog.cpp.cpp_constant import CppConstant
from metaprog.cpp.cpp_enum import CppEnumEntry, CppEnum
from metaprog.cpp.cpp_field import CppField
from metaprog.cpp.cpp_labels import CppClassVirtuality
from metaprog.cpp.cpp_includes import CppIncludes
from metaprog.cpp.cpp_type import CppType, CppTypeSharedPtr, CppTypeClass, CppTypeSimple, CppTypeString, CppTypeBinary, CppTypeVector, CppTypeMap
from metaprog.cpp.cpp_rvalue import CppRValueAny
from metaprog.util.log import logError
from metaprog.util.extensions import Extensions
from typing import Optional, Any, Callable

'''! 
This extension value can be added to the extensions of the `AdtClass`
If used, it must contain a `CppNameScopeWithChildren` that will be used as a container
for the generated classes. Otherwise, it will use the `defaultNameScope`
'''
CPP_NAMESCOPE:str = "cpp_adt_namescope"

'''! Used in `AdtClass` and `AdtField` to indicate the name that the C++ implementation should use '''
CPP_NAME:str = "cpp_adt_name"

'''! 
Used in `AdtClass` to execute extra actions on the created `CppClass`, like adding methods and so on. 
It expects an instance of `CppAdtClassCustom` or a `list[CppAdtClassCustom]`. 
It will call their methods 'customAction' after having created the C++ class.
'''
CPP_CUSTOM_PROCESSING:str = "cpp_custom_processing"

'''! Used in `AdtType` with value type `CppType` of the type that the C++ implementation should use '''
CPP_TYPE:str = "cpp_adt_type"

'''! Used in `AdtField` with value type `string`; it is used as default value '''
CPP_FIELD_DEFAULT:str = "cpp_field_default"

'''! Used in `AdtClass` and `AdtField` with value `CppIncludesAny`; contains the includes to be added in C++ in the .hpp file '''
CPP_INCLUDES:str = "cpp_includes"

class CppAdtClassCustom:
    def customAction(self, adtClass:AdtClass, cppClass:CppClass) -> None:
        pass

class CppAdtTypeCustom:
    def customAction(self, adtType:AdtType, cppType:CppType) -> None:
        pass

class CppFromAdt:

    '''
    Starting from a set of AdtClass instances, creates the related C++ classes.
    It uses some extension values in the AdtClass to control the C++ generation
    '''
    def __init__(
            self, 
            defaultNameScope:Optional[CppChildrenContainer]=None,   # This is the namescope 
            fieldPostProcessor:Optional[Callable[[CppField], None]]=None, # Called for every Field; allows post processing
        ):
        self.m_defaultNameScope:Optional[CppChildrenContainer] = defaultNameScope
        self.m_fieldPostProcessor:Optional[Callable[[CppField], None]] = fieldPostProcessor
        
        self.m_classMap:dict[str,CppClass] = dict()
        ''' Maps the ADT class name with the related C++ class '''

        self.m_enumMap:dict[str,CppEnum] = dict()
        ''' Maps the ADT enums with the related C++ class '''

        self.m_constantMap:dict[str,CppConstant] = dict()
        ''' Maps the ADT constants '''

    #=======================================================================================================
    def generate(self, adtClassSet:AdtClassSet) -> list[CppClass]:
        '''! Generate the C++ classes related to the specified ADT classes '''
        for adtConstant in adtClassSet.m_constants:
            self.__generateConstant(adtConstant=adtConstant)

        for adtEnum in adtClassSet.m_enums:
            self.__generateEnum(adtEnum=adtEnum)

        for adtClass in adtClassSet.m_classes:
            self.__generateClass(adtClass=adtClass)

        # Resolve inheritance
        for adtClass in adtClassSet.m_classes:
            self.__resolveInheritance(adtClass=adtClass)

        cppClasses:list[CppClass] = list()
        for cppClass in self.m_classMap.values():
            cppClasses.append(cppClass)

        # Call the custom actions
        # Resolve inheritance
        for adtClass in adtClassSet.m_classes:
            self.__callCustomCodeOnClass(adtClass=adtClass)

        return cppClasses

    #=======================================================================================================
    def __generateClass(self, adtClass:AdtClass) -> None:
        if adtClass.m_className in self.m_classMap:
            logError(f"Dupe ADT class {adtClass.m_className}")
        
        if CPP_NAMESCOPE in adtClass.m_extensions:
            assert(isinstance(adtClass.m_extensions[CPP_NAMESCOPE], CppChildrenContainer))
            nameScope:CppChildrenContainer = adtClass.m_extensions[CPP_NAMESCOPE]
        elif self.m_defaultNameScope is not None:
            nameScope = self.m_defaultNameScope
        else:
            logError(f"No namescope defined for class {adtClass.m_className}")
            return
            
        if CPP_NAME in adtClass.m_extensions:
            cppClassName:str = adtClass.m_extensions[CPP_NAME]
        else:
            cppClassName = adtClass.m_className

        cppClass:CppClass = CppClass(
            className=cppClassName,
            brief=adtClass.m_brief,
            classVirtuality=CppClassVirtuality.CLASS_VIRTUAL,
            extensions={
                CPP_MARSHAL_CLASS_NAME:adtClass.m_className,
                CPP_HASH_CLASS_NAME:adtClass.m_className,
            }
        )
        self.__mergeIncludes(cppClass.m_hppIncludes, adtClass.m_extensions)
        cppClass.m_extensions.merge(adtClass.m_extensions)
        self.m_classMap[adtClass.m_className] = cppClass
        nameScope.addChild(child=cppClass)

        for adtField in adtClass.m_fields:
            self.__generateField(adtField=adtField, cppClass=cppClass)


    #=======================================================================================================
    def __generateEnum(self, adtEnum:AdtEnum) -> None:
        if adtEnum.m_enumName in self.m_enumMap:
            logError(f"Dupe ADT enum {adtEnum.m_enumName}")

        if CPP_NAMESCOPE in adtEnum.m_extensions:
            assert(isinstance(adtEnum.m_extensions[CPP_NAMESCOPE], CppChildrenContainer))
            nameScope:CppChildrenContainer = adtEnum.m_extensions[CPP_NAMESCOPE]
        elif self.m_defaultNameScope is not None:
            nameScope = self.m_defaultNameScope
        else:
            logError(f"No namescope defined for enum {adtEnum.m_enumName}")
            return
            
        if CPP_NAME in adtEnum.m_extensions:
            cppEnumName:str = adtEnum.m_extensions[CPP_NAME]
        else:
            cppEnumName = adtEnum.m_enumName

        cppEnumEntries:list[CppEnumEntry] = list()
        for adtEnumEntry in adtEnum.m_enumEntries:
            cppEnumEntries.append(CppEnumEntry(
                enumEntryName=adtEnumEntry.m_enumEntryName,
                enumEntryValue=adtEnumEntry.m_enumEntryValue,
                enumEntryDefault=adtEnumEntry.m_enumEntryDefault,
                brief=adtEnumEntry.m_brief,
            ))

        cppEnum:CppEnum = CppEnum(
            enumClassName=cppEnumName,
            brief=adtEnum.m_brief,
            enumEntries=cppEnumEntries,
            extensions=adtEnum.m_extensions.newMerged(extensions={
                CPP_MARSHAL_CLASS_NAME:adtEnum.m_enumName,
                CPP_HASH_CLASS_NAME:adtEnum.m_enumName,
            })
        )
        self.m_enumMap[adtEnum.m_enumName] = cppEnum
        nameScope.addChild(child=cppEnum)

    #=======================================================================================================
    def __generateConstant(self, adtConstant:AdtConstant) -> None:
        if adtConstant.m_constantName in self.m_constantMap:
            logError(f"Dupe ADT constant {adtConstant.m_constantName}")

        if CPP_NAMESCOPE in adtConstant.m_extensions:
            assert(isinstance(adtConstant.m_extensions[CPP_NAMESCOPE], CppChildrenContainer))
            nameScope:CppChildrenContainer = adtConstant.m_extensions[CPP_NAMESCOPE]
        elif self.m_defaultNameScope is not None:
            nameScope = self.m_defaultNameScope
        else:
            logError(f"No namescope defined for constant {adtConstant.m_constantName}")
            return
            
        if CPP_NAME in adtConstant.m_extensions:
            cppConstantName:str = adtConstant.m_extensions[CPP_NAME]
        else:
            cppConstantName = adtConstant.m_constantName

        cppConstant:CppConstant = CppConstant(
            constantName=cppConstantName,
            constantType=self.__getCppType(adtType=adtConstant.m_constantType, adtDefault=adtConstant.m_constantValue, isArrayElement=False, isConstexpr=True),
            
            brief=adtConstant.m_brief,
            extensions=adtConstant.m_extensions.newMerged(extensions={
                CPP_MARSHAL_CLASS_NAME:adtConstant.m_constantName,
                CPP_HASH_CLASS_NAME:adtConstant.m_constantName,
            })
        )
        self.m_constantMap[adtConstant.m_constantName] = cppConstant
        nameScope.addChild(child=cppConstant)


    #=======================================================================================================
    def __resolveInheritance(self, adtClass:AdtClass) -> None:
        if adtClass.m_baseClass is None: return
        if adtClass.m_baseClass.m_className not in self.m_classMap:
            logError(f"ADT class {adtClass.m_className} derives from unexisting class {adtClass.m_baseClass.m_className}")
            return
        
        thisCppClass:CppClass = self.m_classMap[adtClass.m_className]
        baseCppClass:CppClass = self.m_classMap[adtClass.m_baseClass.m_className]
        thisCppClass.m_baseClass = baseCppClass

    #=======================================================================================================
    def __callCustomCodeOnClass(self, adtClass:AdtClass) -> None:
        assert(adtClass.m_className in self.m_classMap)
        cppClass:CppClass = self.m_classMap[adtClass.m_className]
        if CPP_CUSTOM_PROCESSING in adtClass.m_extensions:
            customCode = adtClass.m_extensions[CPP_CUSTOM_PROCESSING]
            if isinstance(customCode, CppAdtClassCustom):
                customCode.customAction(adtClass=adtClass, cppClass=cppClass)
            elif isinstance(customCode, list):
                for customAction in customCode: # type: ignore
                    assert(isinstance(customAction, CppAdtClassCustom))
                    customAction.customAction(adtClass=adtClass, cppClass=cppClass)
        
    #=======================================================================================================
    def __generateField(self, adtField:AdtField, cppClass:CppClass) -> None:
        if CPP_NAME in adtField.m_extensions:
            assert(isinstance(adtField.m_extensions[CPP_NAME], str))
            cppFieldName:str = adtField.m_extensions[CPP_NAME]
        else:
            cppFieldName = adtField.m_fieldName

        # First, privilege an explicit CPP_FIELD_DEFAULT value
        extensionDefinedDefault:CppRValueAny = adtField.m_extensions.getValueOrNone(CPP_FIELD_DEFAULT)

        # If an explicit CPP_FIELD_DEFAULT is not defined, see if an ADT constant
        # has been associated to the field.
        if extensionDefinedDefault is None and adtField.m_fieldDefault is not None:
            cppConstant:CppConstant = self.m_constantMap[adtField.m_fieldDefault.m_constantName]
            extensionDefinedDefault = cppConstant

        cppField:CppField = CppField(
            fieldName=cppFieldName,
            adtFieldName=adtField.m_fieldName,
            fieldType=self.__getCppType(adtField.m_fieldType),
            extensions=adtField.m_extensions.newMerged(extensions={
                CPP_MARSHAL_FIELD_ENABLE:True,
                CPP_MARSHAL_FIELD_NAME:adtField.m_fieldName,
            }),
            brief=adtField.m_brief,
            fieldDefault=extensionDefinedDefault,
        )

        cppField.m_extensions.merge(adtField.m_extensions)
        self.__mergeIncludes(cppField.m_hppIncludes, adtField.m_extensions)
        cppClass.addClassElement(classElement=cppField)
        if self.m_fieldPostProcessor is not None:
            self.m_fieldPostProcessor(cppField)

    #=======================================================================================================
    def __getCppType2(self, adtType:AdtType, isArrayElement:bool=False, adtDefault:Optional[str]=None, isConstexpr:bool=False) -> CppType:
        if CPP_TYPE in adtType.m_extensions:
            assert(adtDefault is None)
            assert(isinstance(adtType.m_extensions[CPP_TYPE], CppType))
            return adtType.m_extensions[CPP_TYPE]

        if isinstance(adtType, AdtTypeInteger):
            cppTypeSimple:CppTypeSimple = CppTypeSimple(simpleType=f'{"" if adtType.m_signed else "u"}int{adtType.m_bits}_t')
            if adtDefault is not None:
                cppTypeSimple.m_defaultValue = adtDefault
            return cppTypeSimple

        if isinstance(adtType, AdtTypeString):
            #print(f'[DEBUG] adtDefault={adtDefault}')
            #assert(adtDefault is None)
            cppTypeString:CppTypeString = CppTypeString(defaultValue=adtDefault, isConstexpr=isConstexpr)
            return cppTypeString

        if isinstance(adtType, AdtTypeBinary):
            assert(adtDefault is None)
            cppTypeBinary:CppTypeBinary = CppTypeBinary()
            return cppTypeBinary

        if isinstance(adtType, AdtTypeBool):
            cppTypeSimple = CppTypeSimple(simpleType='bool')
            if adtDefault is not None:
                if adtDefault.lower() == 'true':
                    cppTypeSimple.m_defaultValue = 'true'
                elif adtDefault.lower() == 'false':
                    cppTypeSimple.m_defaultValue = 'false'
                else:
                    logError(f"Invalid boolean '{adtDefault}'")
            return cppTypeSimple

        if isinstance(adtType, AdtTypeFloat):
            cppTypeSimple = CppTypeSimple(simpleType='double')
            return cppTypeSimple

        elif isinstance(adtType, AdtTypeClass):
            assert(adtDefault is None)
            if adtType.m_adtClass.m_className in self.m_classMap:
                if adtType.m_polymorphic or isArrayElement:
                    return CppTypeSharedPtr(containedType=CppTypeClass(cppClass=self.m_classMap[adtType.m_adtClass.m_className]), polymorphic=adtType.m_polymorphic)
                else:
                    return CppTypeClass(cppClass=self.m_classMap[adtType.m_adtClass.m_className])
            else:
                logError(f"ADT type reference an ADT class named '{adtType.m_adtClass.m_className}' which has not been generated in C++")
                return CppTypeSimple(simpleType="void")

        elif isinstance(adtType, AdtTypeEnum):
            assert(adtDefault is None)
            return CppTypeClass(cppClass=self.m_enumMap[adtType.m_adtEnum.m_enumName])

        elif isinstance(adtType, AdtTypeVector):
            assert(adtDefault is None)
            if isinstance(adtType.m_containedType, AdtTypeClass):
                return CppTypeVector(containedType=self.__getCppType(adtType=adtType.m_containedType, isArrayElement=True))
            return CppTypeVector(containedType=self.__getCppType(adtType=adtType.m_containedType, isArrayElement=True))

        elif isinstance(adtType, AdtTypeMap):
            assert(adtDefault is None)
            if isinstance(adtType.m_containedType, AdtTypeClass):
                return CppTypeMap(keyType=CppTypeString(), containedType=self.__getCppType(adtType=adtType.m_containedType))
            return CppTypeMap(keyType=CppTypeString(), containedType=self.__getCppType(adtType=adtType.m_containedType))

        else:
            logError(f"ADT type reference invalid: {adtType}")
            return CppTypeSimple(simpleType="void")

    #=======================================================================================================
    def __getCppType(self, adtType:AdtType, isArrayElement:bool=False, adtDefault:Optional[str]=None, isConstexpr:bool=False) -> CppType:
        cppType:CppType = self.__getCppType2(adtType=adtType, isArrayElement=isArrayElement, adtDefault=adtDefault, isConstexpr=isConstexpr)
        cppType.m_extensions.merge(adtType.m_extensions)

        includes:Optional[Any] = adtType.m_extensions.getValueOrNone(CPP_INCLUDES)
        if includes is not None:
            cppType.m_includes.merge(CppIncludes(includes))
        
        if CPP_CUSTOM_PROCESSING in adtType.m_extensions:
            assert(isinstance(adtType.m_extensions[CPP_CUSTOM_PROCESSING], CppAdtTypeCustom))
            adtType.m_extensions[CPP_CUSTOM_PROCESSING].customAction(adtType=adtType, cppType=cppType)

        return cppType

    #=======================================================================================================
    def __mergeIncludes(self, targetIncludes:CppIncludes, extensions:Extensions) -> None:
        ''' 
        See if `extensions` contains the `CPP_INCLUDES` key referring to a CppIncludesAny
        If so, it will merge the includes in the `extensions` into `targetIncludes`
        '''
        if CPP_INCLUDES in extensions:
            cppIncludes:CppIncludes = CppIncludes(incls=extensions[CPP_INCLUDES])
            targetIncludes.merge(cppIncludes)
    
