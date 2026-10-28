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

'''! 
Generates the `hash()` code ontop of an existing class 

HASH CALCULATION RULES
^^^^^^^^^^^^^^^^^^^^^^

OBJECTS:
  hash.add("@OBJ_BEG@");
  foreach field:
    hash.add("$<fieldname>$");
    field.calc_hash(hash);
  hash.add("@OBJ_END@");

POINTERS:
  if null:
    hash.add("@NULL@");

  if polymorphic and not null:
    hash.add("%<typename>%");
  
  if not null:
    field->calc_hash(hash);

INTEGERS:
  big-endinan bytes composing the integer value (MSB first)

STRINGS
  UTF-8 encoded strings:

  hash.add("@STR_BEG@");
  foreach ch:
    ch.calc_hash(hash)
  hash.add("@STR_END@");

BINARY DATA
  Raw binary data:

  hash.add("@BIN_BEG@");
  foreach ch:
    ch.calc_hash(hash)
  hash.add("@BIN_END@");

ARRAYS:
  hash.add("@ARRAY_BEG@");
  foreach item:
    item.calc_hash(hash)
  hash.add("@ARRAY_END@");

MAPS:
  hash.add("@MAP_BEG@");
  foreach item:
    item.key.calc_hash(hash)
    hash.add("@MAP_SEP@");
    item.value.calc_hash(hash)
  hash.add("@MAP_END@");

ENUMS:
  converted to U32 values and calculated
    
'''
from .cpp_generator_base import CppGeneratorBase
from metaprog.cpp.cpp_class import CppClass
from metaprog.cpp.cpp_enum_base import CppEnumBase
from metaprog.cpp.cpp_field import CppField
from metaprog.cpp.cpp_labels import CppVisibility, CppClassVirtuality, CppInline, CppStaticity, CppVirtuality
from metaprog.cpp.cpp_method import CppMethod
from metaprog.cpp.cpp_param import CppParam
from metaprog.cpp.cpp_type import CppType, CppTypeMap, CppTypeVector, CppTypeBinary, CppTypeString, CppTypeSharedPtr, CppTypeClass
from metaprog.util.config import env
from metaprog.util.log import logError
from metaprog.util.writable_set import assertIsWritableSetAny, WritableSet

CPP_HASH_CLASS_NAME:str  = "cpp_hash_name"  # -> Alternate name used by this class to calculate the string used for hashing

CPP_HASH_CODE:str = "cpp_hash_code"
'''
HOW TO USE `CPP_HASH_CODE`:

    CppField(
        # ...
        extensions={
            CPP_HASH_CODE:WritableSet(f'{CPP_HASH_OBJ}.add({CPP_HASH_FIELD});'),
        },
        # ...
    ))

Note: it can be placed in the `CppField` or the `CppType` object.
It can be placed in the `CppClass` object as well: in that case {CPP_HASH_FIELD} is not used.
    
'''

CPP_HASH_FIELD_DISABLE:str ="cpp_hash_field_disable" # Add to disable hash of the CppField
CPP_HASH_GENERATED:str     = "cpp_hash_generated" # -> bool, created and written by this module to mark that has been processed


_CPP_HASH_OBJ="CPP_HASH_OBJ"
_CPP_HASH_FIELD="CPP_HASH_FIELD"

CPP_HASH_OBJ=env(_CPP_HASH_OBJ)
CPP_HASH_FIELD=env(_CPP_HASH_FIELD)

_CPP_HASH_OBJ_BEG   :str = "@OBJ_BEG@"
_CPP_HASH_OBJ_END   :str = "@OBJ_END@"
_CPP_HASH_NULL      :str = "@NULL@"
_CPP_HASH_STR_BEG   :str = "@STR_BEG@"
_CPP_HASH_STR_END   :str = "@STR_END@"
_CPP_HASH_BIN_BEG   :str = "@BIN_BEG@"
_CPP_HASH_BIN_END   :str = "@BIN_END@"
_CPP_HASH_ARRAY_BEG :str = "@ARRAY_BEG@"
_CPP_HASH_ARRAY_END :str = "@ARRAY_END@"
_CPP_HASH_MAP_BEG   :str = "@MAP_BEG@"
_CPP_HASH_MAP_SEP   :str = "@MAP_SEP@"
_CPP_HASH_MAP_END   :str = "@MAP_END@"


class CppHashGenerator(CppGeneratorBase):
    #=============================================================================================
    def __init__(
            self,
            calcHashName:str = 'calc_hash',
            getHashClassName:str = "get_hash_class_name",
        ) -> None:
        super().__init__()
        self.m_calcHashName:str = calcHashName
        self.m_hashParam:str = "hash"
        self.m_getHashClassName = getHashClassName

    #=============================================================================================
    def _baseClassHasHash(self, cppClass:CppClass)->bool:
        ''' CAN BE REDEFINED 
            Returns `True` if the `cppClass` has a base class that implements hash.
            By default considers deriving from a `CppClass` object as having a streamable base class.
        '''
        return cppClass.m_baseClass is not None and isinstance(cppClass.m_baseClass, CppClass)


    #=============================================================================================
    def decorateClasses(self) -> None:
        '''! Executes the decoration of the classes before generating the code '''
        for cppClass in self.m_cppClasses:
            self.__decorateClass(cppClass)

    #=============================================================================================
    def __decorateClass(self, cppClass:CppClass) -> None:
        '''! Decorate the single class with all the required code '''
        if CPP_HASH_GENERATED in cppClass.m_extensions:
            logError(f"class `{cppClass.getCppQualifiedName()}` generated more than once")
            return
        cppClass.m_extensions[CPP_HASH_GENERATED] = True
        #logInfo(f"Decorating class `{cppClass.getCppQualifiedName()}` for hash - classVirtuality={cppClass.getClassVirtuality()}")
        self.__decorateClassWithHashClassName(cppClass=cppClass)
        self.__decorateClassWithHash(cppClass=cppClass)

    #=============================================================================================
    def __decorateClassWithHashClassName(self, cppClass:CppClass) -> None:
        if CPP_HASH_CLASS_NAME in cppClass.m_extensions:
            assert(isinstance(cppClass.m_extensions[CPP_HASH_CLASS_NAME], str))
            className:str = cppClass.m_extensions[CPP_HASH_CLASS_NAME]
        else:
            className = cppClass.getCppQualifiedName()

        derived:bool = self._baseClassHasHash(cppClass)
        cppClass.addClassElement(
            CppMethod(
                methodName=self.m_getHashClassName,
                returnType='const char*',
                virtuality=CppVirtuality.VIRTUAL_OVERRIDE if derived else CppVirtuality.VIRTUAL,
                inline=CppInline.INLINE_OUTSIDE,
                code=f'return "%{className}%";',
                staticity=CppStaticity.DYNAMIC_CONST,
                visibility=CppVisibility.PUBLIC,
                brief='Return the name used by the marshaling system used to identify this class when streaming and unstreaming',
            )
        )

    #=============================================================================================
    def __decorateClassWithHash(self, cppClass:CppClass) -> None:
        '''! Add the master Hash method '''
        isVirtual:bool = (cppClass.getClassVirtuality() != CppClassVirtuality.CLASS_NORMAL)
        
        if isVirtual and self._baseClassHasHash(cppClass=cppClass):
            methodVirtuality:CppVirtuality = CppVirtuality.VIRTUAL_OVERRIDE
        elif isVirtual:
            methodVirtuality = CppVirtuality.VIRTUAL
        else:
            methodVirtuality = CppVirtuality.NORMAL

        hash:CppMethod = CppMethod(
            methodName=self.m_calcHashName,
            brief='Hash the object',
            inline=CppInline.INLINE_OUTSIDE,
            staticity=CppStaticity.DYNAMIC_CONST,
            visibility=CppVisibility.PUBLIC,
            params=[
                CppParam(paramName=self.m_hashParam, paramType="dastd::hash&", hppIncludes=["dastd/hash.hpp"], paramComment='Target hash object', mayBeUnused=True),
            ],
            virtuality=methodVirtuality
        )
        cppClass.addClassElement(hash)
        if CPP_HASH_CODE in cppClass.m_extensions:
            #------------------------------------------------------
            # CUSTOM HASH CODE
            #------------------------------------------------------
            assertIsWritableSetAny(cppClass.m_extensions[CPP_HASH_CODE])
            hash.m_code.pushEnv(env={_CPP_HASH_OBJ:self.m_hashParam})
            hash.m_code.append(cppClass.m_extensions[CPP_HASH_CODE])
            hash.m_code.popEnv()
        else:
            #------------------------------------------------------
            # AUTOMATIC HASH CODE
            #------------------------------------------------------
            self._hashTag(writableSet=hash.m_code, tag=_CPP_HASH_OBJ_BEG)
            for classElement in cppClass.m_classElements:
                if isinstance(classElement, CppField) and not classElement.m_fieldConst and not classElement.m_extensions.getValueOrNone(CPP_HASH_FIELD_DISABLE):
                    hash.m_code.append(f'\n// Hash calculation: FIELD `{classElement.m_fieldName}`')
                    self._hashTag(writableSet=hash.m_code, tag=f'${classElement.getAdtFieldName()}$')
                    self._hashCode(writableSet=hash.m_code, fieldType=classElement.m_fieldType, fieldExpr=classElement.m_fieldName)
            self._hashTag(writableSet=hash.m_code, tag=_CPP_HASH_OBJ_END)

    #=============================================================================================
    def _hashTag(self, writableSet:WritableSet, tag:str) -> None:
        writableSet.append(f'{self.m_hashParam}.add("{tag}");')

    #=============================================================================================
    def _hashCode(self, writableSet:WritableSet, fieldType:CppType, fieldExpr:str) -> None:
        if CPP_HASH_CODE in fieldType.m_extensions:
            assertIsWritableSetAny(fieldType.m_extensions[CPP_HASH_CODE])
            writableSet.pushEnv(env={_CPP_HASH_OBJ:self.m_hashParam, _CPP_HASH_FIELD:fieldExpr})
            writableSet.append(fieldType.m_extensions[CPP_HASH_CODE])
            writableSet.popEnv()
        elif isinstance(fieldType, CppTypeMap):
            self._mapHashCode(writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CppTypeVector):
            self._arrayHashCode(writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CppTypeString):
            self._stringHashCode(writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CppTypeBinary):
            self._binaryHashCode(writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CppTypeSharedPtr):
            self._sharedPtrHashCode(writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CppTypeClass):
            self._classHashCode(writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        else:                    
            writableSet.append(f'{self.m_hashParam}.add({fieldExpr});')

    #=============================================================================================
    def _arrayHashCode(self, writableSet:WritableSet, fieldType:CppTypeVector, fieldExpr:str) -> None:
        iterator:str = '__iterator'

        writableSet.append('// Hash calculation: ARRAY')
        self._hashTag(writableSet=writableSet, tag=_CPP_HASH_ARRAY_BEG)
        writableSet.append(f'for(auto {iterator}={fieldExpr}.begin(); {iterator}!={fieldExpr}.end(); ++{iterator}) {{')
        writableSet.incIndent()

        self._hashCode(writableSet=writableSet, fieldType=fieldType.m_containedType, fieldExpr=f'(*{iterator})')
        writableSet.decIndent()
        writableSet.append('}')
        self._hashTag(writableSet=writableSet, tag=_CPP_HASH_ARRAY_END)

    #=============================================================================================
    def _mapHashCode(self, writableSet:WritableSet, fieldType:CppTypeMap, fieldExpr:str) -> None:
        iterator:str = '__iterator'

        writableSet.append('// Hash calculation: MAP')
        self._hashTag(writableSet=writableSet, tag=_CPP_HASH_MAP_BEG)
        writableSet.append(f'for(auto {iterator}={fieldExpr}.begin(); {iterator}!={fieldExpr}.end(); ++{iterator}) {{')
        writableSet.incIndent()
        self._hashCode(writableSet=writableSet, fieldType=fieldType.m_containedType, fieldExpr=f'({iterator}->first)')
        self._hashTag(writableSet=writableSet, tag=_CPP_HASH_MAP_SEP)
        self._hashCode(writableSet=writableSet, fieldType=fieldType.m_containedType, fieldExpr=f'({iterator}->second)')
        writableSet.decIndent()
        writableSet.append('}')
        self._hashTag(writableSet=writableSet, tag=_CPP_HASH_MAP_END)

    #=============================================================================================
    def _stringHashCode(self, writableSet:WritableSet, fieldType:CppTypeString, fieldExpr:str) -> None:
        writableSet.append('// Hash calculation: STRING')
        self._hashTag(writableSet=writableSet, tag=_CPP_HASH_STR_BEG)
        writableSet.append(f'{self.m_hashParam}.add({fieldExpr});')
        self._hashTag(writableSet=writableSet, tag=_CPP_HASH_STR_END)

    #=============================================================================================
    def _binaryHashCode(self, writableSet:WritableSet, fieldType:CppTypeBinary, fieldExpr:str) -> None:
        writableSet.append('// Hash calculation: BINARY')
        self._hashTag(writableSet=writableSet, tag=_CPP_HASH_BIN_BEG)
        writableSet.append(f'{self.m_hashParam}.add({fieldExpr});')
        self._hashTag(writableSet=writableSet, tag=_CPP_HASH_BIN_END)

    #=============================================================================================
    def _sharedPtrHashCode(self, writableSet:WritableSet, fieldType:CppTypeSharedPtr, fieldExpr:str) -> None:
        
        if fieldType.m_polymorphic:
            writableSet.append('// Hash calculation: POLYMORMHIC POINTER')
        else:
            writableSet.append('// Hash calculation: NOT-POLYMORMHIC POINTER')

        writableSet.append(f'if (!{fieldExpr}) {self.m_hashParam}.add("{_CPP_HASH_NULL}");')
        writableSet.append('else {')
        writableSet.incIndent()

        if fieldType.m_polymorphic:
            writableSet.append(f'// Calculate the hash of the polymorphic type')
            writableSet.append(f'{self.m_hashParam}.add({self.m_getHashClassName}());')
        
        self._hashCode(writableSet=writableSet, fieldType=fieldType.m_containedType, fieldExpr=f'(*({fieldExpr}))')

        writableSet.decIndent()
        writableSet.append('}')


    #=============================================================================================
    def _classHashCode(self, writableSet:WritableSet, fieldType:CppTypeClass, fieldExpr:str) -> None:
        if isinstance(fieldType.m_cppClass, CppEnumBase):
            writableSet.append(f'''
                // Hash calculation: ENUM
                {self.m_hashParam}.add((uint32_t){fieldExpr});
            ''')
            return

        writableSet.append(f'''
            // Hash calculation: OBJECT
            {fieldExpr}.{self.m_calcHashName}({self.m_hashParam});
        ''')
