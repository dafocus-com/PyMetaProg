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
from metaprog.adt.adt_class import AdtClass
from metaprog.adt.adt_constant import AdtConstant
from metaprog.adt.adt_field import AdtField
from metaprog.adt.adt_enum import AdtEnum
from metaprog.adt.adt_type import AdtType
from metaprog.adt.adt_type_misc import AdtTypeInteger, AdtTypeString, AdtTypeBinary, AdtTypeClass, AdtTypeVector, AdtTypeBool, AdtTypeEnum, AdtTypeMap, AdtTypeFloat
from metaprog.adt.adt_class_set import AdtClassSet
from metaprog.py.py_class import PyClass
from metaprog.py.py_labels import PyVisibility
from metaprog.py.py_enum import PyEnum, PyEnumEntry
from metaprog.py.py_namescope_with_children import PyNameScopeWithChildren
from metaprog.py.py_type import PyType, PyTypeString, PyTypeBinary, PyTypeSimple, PyTypeClass, PyTypeMap, PyTypeVector, PyTypeOptional
from metaprog.py.py_field import PyField
from metaprog.py.py_rvalue import PyRValueAny
#from metaprog.py.py_constant import PyConstant
from metaprog.py_gen.py_marshal_generator import PY_MARSHAL_FIELD_NAME, PY_MARSHAL_CLASS_NAME, PY_MARSHAL_FIELD_ENABLE
from metaprog.util.log import logError


'''! This extension value can be added to the extensions of the `AdtClass`; must be a `PyNameScopeWithChildren` or deriveds  '''
PY_NAMESCOPE:str = "py_adt_namescope"

'''! Used in `AdtClass` and `AdtField` to indicate the name that the C++ implementation should use '''
PY_NAME:str = "py_adt_name"

PY_TYPEMAP:dict[str,str] = {
    "u8" : "int",
    "i8" : "int",
    "u16": "int",
    "i16": "int",
    "u32": "int",
    "i32": "int",
    "u64": "int",
    "i64": "int",
}

'''! 
Used in `AdtClass` to execute extra actions on the created `PyClass`, like adding methods and so on. 
It expects an instance of `PyAdtClassCustom` or a `list[PyAdtClassCustom]`. 
It will call their methods 'customAction' after having created the C# class.
'''
PY_CUSTOM_PROCESSING:str = "py_custom_processing"

'''! Used in `AdtField` with value type `string`; it is used as default value '''
PY_FIELD_DEFAULT:str = "py_field_default"

'''! Used in `AdtType` to mark a type `T` as `Optional[T]` '''
PY_OPTIONAL:str = "py_optional"


class PyAdtClassCustom:
    def customAction(self, adtClass:AdtClass, pyClass:PyClass) -> None:
        pass

class PyAdtTypeCustom:
    def customAction(self, adtType:AdtType, pyType:PyType) -> None:
        pass

class PyFromAdt:

    '''
    Starting from a set of AdtClass instances, creates the related C# classes.
    It uses some extension values in the AdtClass to control the C# generation
    '''
    def __init__(
            self, 
            defaultNameScope:Optional[PyNameScopeWithChildren]=None   # This is the namescope 
        ):
        self.m_defaultNameScope:Optional[PyNameScopeWithChildren] = defaultNameScope
        
        self.m_classMap:dict[str,PyClass] = dict()
        ''' Maps the ADT class name with the related C++ class '''

        self.m_enumMap:dict[str,PyEnum] = dict()
        ''' Maps the ADT enum name with the related C++ class '''

        self.m_constantMap:dict[str,PyField] = dict()
        ''' Maps the ADT constants '''

    #=======================================================================================================
    def generate(self, adtClassSet:AdtClassSet)->list[PyClass]:
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

        pyClasses:list[PyClass] = list()
        for pyClass in self.m_classMap.values():
            pyClasses.append(pyClass)

        # Call the custom actions
        # Resolve inheritance
        for adtClass in adtClassSet.m_classes:
            self.__callCustomCode(adtClass=adtClass)

        return pyClasses

    #=======================================================================================================
    def __generateClass(self, adtClass:AdtClass) -> None:
        if adtClass.m_className in self.m_classMap:
            logError(f"Dupe ADT class {adtClass.m_className}")
        
        if PY_NAMESCOPE in adtClass.m_extensions:
            assert(isinstance(adtClass.m_extensions[PY_NAMESCOPE], PyNameScopeWithChildren))
            nameScope:PyNameScopeWithChildren = adtClass.m_extensions[PY_NAMESCOPE]
        elif self.m_defaultNameScope is not None:
            nameScope = self.m_defaultNameScope
        else:
            logError(f"No namescope defined for class {adtClass.m_className}")
            return
            
        if PY_NAME in adtClass.m_extensions:
            pyClassName:str = adtClass.m_extensions[PY_NAME]
        else:
            pyClassName = adtClass.m_className

        pyClass:PyClass = PyClass(
            className=pyClassName,
            brief=adtClass.m_brief,
            visibility=PyVisibility.PUBLIC,
            extensions={
                PY_MARSHAL_CLASS_NAME:adtClass.m_className,
            }
        )
        pyClass.m_extensions.merge(adtClass.m_extensions)
        self.m_classMap[adtClass.m_className] = pyClass
        nameScope.addChild(child=pyClass)

        for adtField in adtClass.m_fields:
            self.__generateField(adtField=adtField, pyClass=pyClass)

    #=======================================================================================================
    def __generateEnum(self, adtEnum:AdtEnum) -> None:
        if adtEnum.m_enumName in self.m_enumMap:
            logError(f"Dupe ADT enum {adtEnum.m_enumName}")

        if PY_NAMESCOPE in adtEnum.m_extensions:
            assert(isinstance(adtEnum.m_extensions[PY_NAMESCOPE], PyNameScopeWithChildren))
            nameScope:PyNameScopeWithChildren = adtEnum.m_extensions[PY_NAMESCOPE]
        elif self.m_defaultNameScope is not None:
            nameScope = self.m_defaultNameScope
        else:
            logError(f"No namescope defined for enum {adtEnum.m_enumName}")
            return
            
        if PY_NAME in adtEnum.m_extensions:
            pyEnumName:str = adtEnum.m_extensions[PY_NAME]
        else:
            pyEnumName = adtEnum.m_enumName

        pyEnumEntries:list[PyEnumEntry] = list()
        for adtEnumEntry in adtEnum.m_enumEntries:
            pyEnumEntries.append(PyEnumEntry(
                enumEntryName=adtEnumEntry.m_enumEntryName,
                enumEntryValue=adtEnumEntry.m_enumEntryValue,
                enumEntryDefault=adtEnumEntry.m_enumEntryDefault,
                brief=adtEnumEntry.m_brief,
            ))

        pyEnum:PyEnum = PyEnum(
            enumClassName=pyEnumName,
            brief=adtEnum.m_brief,
            enumEntries=pyEnumEntries,
            extensions={
                PY_MARSHAL_CLASS_NAME:adtEnum.m_enumName,
            }
        )
        self.m_enumMap[adtEnum.m_enumName] = pyEnum
        nameScope.addChild(child=pyEnum)

    #=======================================================================================================
    def __generateConstant(self, adtConstant:AdtConstant) -> None:
        if adtConstant.m_constantName in self.m_constantMap:
            logError(f"Dupe ADT constant {adtConstant.m_constantName}")

        if PY_NAMESCOPE in adtConstant.m_extensions:
            assert(isinstance(adtConstant.m_extensions[PY_NAMESCOPE], PyNameScopeWithChildren))
            nameScope:PyNameScopeWithChildren = adtConstant.m_extensions[PY_NAMESCOPE]
        elif self.m_defaultNameScope is not None:
            nameScope = self.m_defaultNameScope
        else:
            logError(f"No namescope defined for constant {adtConstant.m_constantName}")
            return
            
        if PY_NAME in adtConstant.m_extensions:
            pyConstantName:str = adtConstant.m_extensions[PY_NAME]
        else:
            pyConstantName = adtConstant.m_constantName

        pyConstant:PyField = PyField(
            fieldName=pyConstantName,
            fieldType=self.__getPyType(adtType=adtConstant.m_constantType, adtDefault=adtConstant.m_constantValue),
            fieldDefault=adtConstant.m_constantValue,
            brief=adtConstant.m_brief,
            extensions=adtConstant.m_extensions.newMerged(extensions={
                PY_MARSHAL_CLASS_NAME:adtConstant.m_constantName,
            })
        )
        self.m_constantMap[adtConstant.m_constantName] = pyConstant
        nameScope.addChild(child=pyConstant)
    
    #=======================================================================================================
    def __resolveInheritance(self, adtClass:AdtClass) -> None:
        if adtClass.m_baseClass is None: return
        if adtClass.m_baseClass.m_className not in self.m_classMap:
            logError(f"ADT class {adtClass.m_className} derives from unexisting class {adtClass.m_baseClass.m_className}")
            return
        
        thisPyClass:PyClass = self.m_classMap[adtClass.m_className]
        basePyClass:PyClass = self.m_classMap[adtClass.m_baseClass.m_className]
        thisPyClass.m_baseClass = basePyClass

    #=======================================================================================================
    def __callCustomCode(self, adtClass:AdtClass) -> None:
        assert(adtClass.m_className in self.m_classMap)
        pyClass:PyClass = self.m_classMap[adtClass.m_className]
        if PY_CUSTOM_PROCESSING in adtClass.m_extensions:
            customCode = adtClass.m_extensions[PY_CUSTOM_PROCESSING]
            if isinstance(customCode, PyAdtClassCustom):
                customCode.customAction(adtClass=adtClass, pyClass=pyClass)
            elif isinstance(customCode, list):
                for customAction in customCode: # type: ignore
                    assert(isinstance(customAction, PyAdtClassCustom))
                    customAction.customAction(adtClass=adtClass, pyClass=pyClass)

    #=======================================================================================================
    def __generateField(self, adtField:AdtField, pyClass:PyClass) -> None:
        if PY_NAME in adtField.m_extensions:
            assert(isinstance(adtField.m_extensions[PY_NAME], str))
            pyFieldName:str = adtField.m_extensions[PY_NAME]
        else:
            pyFieldName = adtField.m_fieldName

        # First, privilege an explicit PY_FIELD_DEFAULT value
        extensionDefinedDefault:PyRValueAny = adtField.m_extensions.getValueOrNone(PY_FIELD_DEFAULT)

        # If an explicit PY_FIELD_DEFAULT is not defined, see if an ADT constant
        # has been associated to the field.
        if extensionDefinedDefault is None and adtField.m_fieldDefault is not None:
            pyConstant:PyField = self.m_constantMap[adtField.m_fieldDefault.m_constantName]
            extensionDefinedDefault = pyConstant

        pyField:PyField = PyField(
            fieldName=pyFieldName,
            fieldType=self.__getPyType(adtField.m_fieldType),
            visibility=PyVisibility.PUBLIC,
            extensions={
                PY_MARSHAL_FIELD_ENABLE:True,
                PY_MARSHAL_FIELD_NAME:adtField.m_fieldName,
            },
            brief=adtField.m_brief,
            fieldDefault=extensionDefinedDefault,
        )
        pyClass.addChild(child=pyField)
        pyField.m_extensions.merge(adtField.m_extensions)

    #=======================================================================================================
    def __getPyType2(self, adtType:AdtType, adtDefault:Optional[str]=None) -> PyType:

        if isinstance(adtType, AdtTypeInteger):
            typeId:str = f'{"i" if adtType.m_signed else "u"}{adtType.m_bits}'
            if not typeId in PY_TYPEMAP:
                logError(f"ADT class invalid simple type of {adtType.m_bits} bits (typeId='{typeId}')")
                return PyTypeSimple(simpleType="void")
            pyTypeSimple:PyTypeSimple = PyTypeSimple(simpleType=PY_TYPEMAP[typeId])
            if adtDefault is not None:
                pyTypeSimple.m_defaultValue = adtDefault
            return pyTypeSimple

        if isinstance(adtType, AdtTypeString):
            return PyTypeString(defaultValue=adtDefault)

        if isinstance(adtType, AdtTypeBinary):
            return PyTypeBinary(defaultValue=adtDefault)

        if isinstance(adtType, AdtTypeBool):
            pyTypeSimple = PyTypeSimple(simpleType="bool")
            if adtDefault is not None:
                if adtDefault.lower() == 'true':
                    pyTypeSimple.m_defaultValue = 'true'
                elif adtDefault.lower() == 'false':
                    pyTypeSimple.m_defaultValue = 'false'
                else:
                    logError(f"Invalid boolean '{adtDefault}'")
            return pyTypeSimple

        if isinstance(adtType, AdtTypeFloat):
            pyTypeSimple = PyTypeSimple(simpleType="float")
            return pyTypeSimple

        if isinstance(adtType, AdtTypeEnum):
            assert(adtDefault is None)
            return PyTypeClass(pyClass=self.m_enumMap[adtType.m_adtEnum.m_enumName])

        if isinstance(adtType, AdtTypeClass):
            assert(adtDefault is None)
            if adtType.m_adtClass.m_className in self.m_classMap:
                return PyTypeClass(pyClass=self.m_classMap[adtType.m_adtClass.m_className], polymorphic=adtType.m_polymorphic)
            else:
                logError(f"ADT type reference an ADT class named '{adtType.m_adtClass.m_className}' which has not been generated in Python; valid classes are: {', '.join(self.m_classMap.keys())}")
                return PyTypeSimple(simpleType="int")

        if isinstance(adtType, AdtTypeVector):
            assert(adtDefault is None)
            return PyTypeVector(containedType=self.__getPyType(adtType=adtType.m_containedType))

        if isinstance(adtType, AdtTypeMap):
            assert(adtDefault is None)
            return PyTypeMap(keyType=PyTypeString(), containedType=self.__getPyType(adtType=adtType.m_containedType))
        
        logError(f"ADT type reference invalid: {adtType.__class__.__name__}")
        return PyTypeSimple(simpleType="int")
    

    #=======================================================================================================
    def __getPyType(self, adtType:AdtType, adtDefault:Optional[str]=None) -> PyType:
        pyType:PyType = self.__getPyType2(adtType=adtType, adtDefault=adtDefault)
        pyType.m_extensions.merge(adtType.m_extensions)
        if pyType.m_extensions.getValueOrNone(key=PY_OPTIONAL) is not None:
            pyType = PyTypeOptional(containedType=pyType, extensions=pyType.m_extensions)

        if PY_CUSTOM_PROCESSING in adtType.m_extensions:
            assert(isinstance(adtType.m_extensions[PY_CUSTOM_PROCESSING], PyAdtTypeCustom))
            adtType.m_extensions[PY_CUSTOM_PROCESSING].customAction(adtType=adtType, pyType=pyType)

        return pyType

