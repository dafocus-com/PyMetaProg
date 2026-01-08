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

'''! Generates the dastd marshaling code ontop of an existing class '''
from __future__ import annotations
from enum import Enum
from metaprog.cpp.cpp_class import CppClass
from metaprog.cpp.cpp_type import *
from metaprog.cpp.cpp_field import CppField
from metaprog.cpp.cpp_method import CppMethod
from metaprog.cpp.cpp_param import CppParam
from metaprog.cpp.cpp_labels import *
from metaprog.util.writable import Writable
from metaprog.util.writable_set import WritableSet
from metaprog.util.writer import Writer
from metaprog.util.config import *
from metaprog.util.log import *
from metaprog.cpp_gen.cpp_rtti_generator import RTTI_GENERATED
from .cpp_generator_base import *
from .cpp_clear_generator import *

import re

# Key to be used in the CppField "extension" dictionary to enable or disable the generation of the field
CPP_MARSHAL_FIELD_ENABLE="cpp_marshal_enable"   # -> True or False
CPP_MARSHAL_FIELD_NAME  ="cpp_marshal_name"     # -> Optional string for a different field name

# Key to be used in the CppClass "extension" dictionary to enable or disable the generation of the class
CPP_MARSHAL_CLASS_GENERATED="cpp_marshal_generated" # -> bool, created and written by this module to mark that has been processed
CPP_MARSHAL_CLASS_ANTILOOP ="cpp_marshal_antiloop"
CPP_MARSHAL_CLASS_NAME     ="cpp_marshal_name"      # -> Alternate name used by this class to calculate the unique id used when streaming

# Key to be used in the CppType "extension" dictionary
CPP_MARSHAL_TYPE_HAS_ENCODE_DECODE = "cpp_marshal_has_encodece"  # -> The type has regular encode/decode functions

# Once the generator has executed, these extensions contain the name that
# has been assigned to some methods. This allows the following generators to
# invoke them by calling them with their correct name.
CPP_MARSHAL_METHOD_ENCODE:str = "cpp_marshal_method_encode"
CPP_MARSHAL_METHOD_DECODE:str = "cpp_marshal_method_decode"


class CppMarshalGeneratorMode(Enum):
    '''
    The CppField objects, in their `extension` dictionary, may have a `CPP_MARSHAL_FIELD_ENABLE`
    entry that can be missing, `True` or `False`. For example:

        cppAttrib.m_extensions[CPP_MARSHAL_FIELD_ENABLE] = True

    The values below indicate whether the attribute is serialized or not:
    - if `CPP_MARSHAL_FIELD_ENABLE` is specified, that indication is taken
    - if `AUTO_INCLUDE`, and  `CPP_MARSHAL_FIELD_ENABLE` is not specified, the attribute will be serialized
    - if `AUTO_EXCLUDE`, and  `CPP_MARSHAL_FIELD_ENABLE` is not specified, the attribute will not be serialized
    - if `EXPLICIT`, and  `CPP_MARSHAL_FIELD_ENABLE` is not specified, a fatal error will occur
    '''
    AUTO_INCLUDE=0 
    AUTO_EXCLUDE=1
    EXPLICIT    =2

CPP_MARSHAL_DECODE_FIELDTYPE_POST_CODE:str="cpp_marshal_decode_field_post_code" # Code added after the decoding of the field is completed
'''
HOW TO USE `CPP_MARSHAL_DECODE_FIELDTYPE_POST_CODE`:

    CppType(
        # ...
        extensions={
            CPP_MARSHAL_DECODE_FIELDTYPE_POST_CODE:WritableSet(f'{CPP_MARSHAL_FIELD}.doExtraStuff();'),
        },
        # ...
    ))

Note: it must be placed in the `CppType` object of the field being decoded.
    
'''

CPP_MARSHAL_DECODE_FIELDTYPE_ON_NEW_CODE:str="cpp_marshal_decode_field_post_new_code" # Code added before decoding a child
'''
HOW TO USE `CPP_MARSHAL_DECODE_FIELDTYPE_ON_NEW_CODE`:

    CppType(
        # ...
        extensions={
            CPP_MARSHAL_DECODE_FIELDTYPE_ON_NEW_CODE:WritableSet(f'{CPP_MARSHAL_FIELD}.doExtraStuff();'),
        },
        # ...
    ))

Note: it must be placed in the `CppType` object of the field being decoded.
    
'''

_CPP_MARSHAL_FIELD="CPP_MARSHAL_FIELD"

CPP_MARSHAL_FIELD=env(_CPP_MARSHAL_FIELD)

class CppMarshalGenerator(CppGeneratorBase):
    #=============================================================================================
    # MARSHALED ATTRIBUTE CLASS
    #=============================================================================================
    class MarshaledAttribute:
        def __init__(self, cppField:CppField, cppClass:CppClass, streamedName:str, keyConstexprName:str, absolutePosition:int, derivedFromBaseClass:bool):
            self.m_cppAttrib:CppField = cppField
            self.m_cppClass:CppClass = cppClass
            self.m_streamedName:str = streamedName
            self.m_keyConstexprName:str = keyConstexprName # Name of the constexpr that contains the name of the field
            self.m_derivedFromBaseClass:bool = derivedFromBaseClass
            self.m_absolutePosition:int = absolutePosition
            

    #=============================================================================================
    def __init__(
            self, 
            mode:CppMarshalGeneratorMode=CppMarshalGeneratorMode.AUTO_INCLUDE,
            fieldsArrayName:str = "k_struct_fields",
            fieldsCountName:str = "k_struct_fields_count",
            decodeMethodName:str = "decode",
            decodeAttrMethodName:str = "decode_attr",
            encodeMethodName:str = "encode",
            encodeAttrMethodName:str = "encode_attr",
            marshalLabelId:str = "k_marshal_label_id",
            marshalClassName:str = "k_marshal_class_name",
            getMarshalLabelId:str = "get_marshal_label_id",
            getMarshalClassName:str = "get_marshal_class_name",
            newInstance:str = "new_instance",
            polymorphicDecode:str = "polymorphic_decode",
            polymorphicEncode:str = "polymorphic_encode",
        ) -> None:
        super().__init__()
        self.m_mode:CppMarshalGeneratorMode = mode
        self.m_fieldsArrayName:str = fieldsArrayName
        self.m_fieldsCountName:str = fieldsCountName
        self.m_decodeMethodName:str = decodeMethodName
        self.m_decodeAttrMethodName:str = decodeAttrMethodName
        self.m_encodeMethodName:str = encodeMethodName
        self.m_encodeAttrMethodName:str = encodeAttrMethodName
        self.m_marshalLabelId:str = marshalLabelId
        self.m_marshalClassName:str = marshalClassName
        self.m_getMarshalLabelId:str = getMarshalLabelId
        self.m_getMarshalClassName:str = getMarshalClassName
        self.m_newInstance:str = newInstance
        self.m_polymorphicDecode:str = polymorphicDecode
        self.m_polymorphicEncode:str = polymorphicEncode


    #=============================================================================================
    def decorateClasses(self) -> None:
        '''! Executes the decoration of the classes before generating the code '''
        for cppClass in self.m_cppClasses:
            self.__decorateClass(cppClass)

    #=============================================================================================
    def _convertCppFieldNameToStreamedAttributeName(self, cppField:CppField)->str:
        ''' 
            CAN BE REDEFINED - Returns the name to be used as a streaming attribute in case it
            has not been specified with `CPP_MARSHAL_FIELD_NAME` in the extensions.
            A derived class can redefine this method to use a custom translation (for example,
            a regex to convert all attributes named `m_XYZ` to `XYZ`).
        '''
        return cppField.m_fieldName

    #=============================================================================================
    def _calcStreamedAttributeName(self, cppField:CppField)->str:
        ''' CAN BE REDEFINED '''
        if CPP_MARSHAL_FIELD_NAME not in cppField.m_extensions:
            return self._convertCppFieldNameToStreamedAttributeName(cppField=cppField)
        else:
            assert(isinstance(cppField.m_extensions[CPP_MARSHAL_FIELD_NAME], str))
            return cppField.m_extensions[CPP_MARSHAL_FIELD_NAME]

    #=============================================================================================
    def _calcFieldNameConstant(self, cppField:CppField, streamedName:str)->str:
        ''' CAN BE REDEFINED '''
        return f"k_marshal_attr_name_{streamedName}"

    #=============================================================================================
    def _baseClassHasStreaming(self, cppClass:CppClass)->bool:
        ''' CAN BE REDEFINED 
            Returns `True` if the `cppClass` has a base class that is streamable.
            By default considers deriving from a `CppClass` object as having a streamable base class.
        '''
        return cppClass.m_baseClass is not None and isinstance(cppClass.m_baseClass, CppClass)

    #=============================================================================================
    def _writeDecodeCodeInner(self, writer:Writer, config:Config, fieldType:CppType, fieldExpr:str, cppClass:CppClass, dec:str):
        ''' CAN BE REDEFINED 
            Writes the decoding according to the attribute type
        '''
        if isinstance(fieldType, CppTypeVector):
            self.__writeDecodeCodeForVector(writer=writer, config=config, fieldType=fieldType, fieldExpr=fieldExpr, cppClass=cppClass, dec=dec)
            return
        elif isinstance(fieldType, CppTypeMap):
            self.__writeDecodeCodeForMap(writer=writer, config=config, fieldType=fieldType, fieldExpr=fieldExpr, cppClass=cppClass, dec=dec)
            return
        elif isinstance(fieldType, CppTypeSharedPtr):
            self.__writeDecodeCodeForSharedPtr(writer=writer, config=config, fieldType=fieldType, fieldExpr=fieldExpr, cppClass=cppClass, dec=dec)
            return
        elif isinstance(fieldType, CppTypeClass):
            self.__writeDecodeCodeForClass(writer=writer, config=config, fieldType=fieldType, fieldExpr=fieldExpr, cppClass=cppClass, dec=dec)
            return
        elif isinstance(fieldType, CppTypeString):
            writer.writeNL(f'{dec}.decode_string_utf8({fieldExpr});')
            return
        elif isinstance(fieldType, CppTypeBinary):
            writer.writeNL(f'{dec}.decode_varsize_binary({fieldExpr});')
            return

        cppType:str = fieldType.toString(cppClass)

        if CPP_MARSHAL_TYPE_HAS_ENCODE_DECODE in fieldType.m_extensions:
            writer.writeNL(f'{fieldExpr}.decode({dec});')
            return
        
        if re.search(r'^u?int([0-9]+)_t$', cppType) or cppType=='bool':
            writer.writeNL(f'{fieldExpr} = {dec}.decode<{cppType}>();')
            return

        writer.writeNL(f'#error PyMetaProg.CppMarshalGenerator._writeDecodeCode does not support type `{cppType}` used by attribute `{fieldExpr}`')
        logError(f"attribute `{fieldExpr}` uses an unsupported type: {cppType}")

    #=============================================================================================
    def _writeDecodeCode(self, writer:Writer, config:Config, fieldType:CppType, fieldExpr:str, cppClass:CppClass, dec:str):
        self._writeDecodeCodeInner(writer=writer, config=config, fieldType=fieldType, fieldExpr=fieldExpr, cppClass=cppClass, dec=dec)
        if CPP_MARSHAL_DECODE_FIELDTYPE_POST_CODE in fieldType.m_extensions:
            assert(isinstance(fieldType.m_extensions[CPP_MARSHAL_DECODE_FIELDTYPE_POST_CODE],WritableSet))
            writableSet = WritableSet()
            writableSet.pushEnv(env={_CPP_MARSHAL_FIELD:fieldExpr})
            writableSet.append(fieldType.m_extensions[CPP_MARSHAL_DECODE_FIELDTYPE_POST_CODE])
            writableSet.popEnv()
            writableSet.write(writer=writer, config=config)

    #=============================================================================================
    def _writeDecodeCustomOnNewCode(self, writer:Writer, config:Config, fieldType:CppType, fieldExpr:str, cppClass:CppClass, dec:str):
        if CPP_MARSHAL_DECODE_FIELDTYPE_ON_NEW_CODE in fieldType.m_extensions:
            assert(isinstance(fieldType.m_extensions[CPP_MARSHAL_DECODE_FIELDTYPE_ON_NEW_CODE],WritableSet))
            writableSet = WritableSet()
            writableSet.pushEnv(env={_CPP_MARSHAL_FIELD:fieldExpr})
            writableSet.append(fieldType.m_extensions[CPP_MARSHAL_DECODE_FIELDTYPE_ON_NEW_CODE])
            writableSet.popEnv()
            writableSet.write(writer=writer, config=config)


    #=============================================================================================
    def _writeEncodeCode(self, writer:Writer, config:Config, fieldType:CppType, fieldExpr:str, cppClass:CppClass, enc:str):
        ''' CAN BE REDEFINED 
            Writes the decoding according to the attribute type
        '''
        if isinstance(fieldType, CppTypeVector):
            self.__writeEncodeCodeForVector(writer=writer, config=config, fieldType=fieldType, fieldExpr=fieldExpr, cppClass=cppClass, enc=enc)
            return
        elif isinstance(fieldType, CppTypeMap):
            self.__writeEncodeCodeForMap(writer=writer, config=config, fieldType=fieldType, fieldExpr=fieldExpr, cppClass=cppClass, enc=enc)
            return
        elif isinstance(fieldType, CppTypeSharedPtr):
            self.__writeEncodeCodeForSharedPtr(writer=writer, config=config, fieldType=fieldType, fieldExpr=fieldExpr, cppClass=cppClass, enc=enc)
            return
        elif isinstance(fieldType, CppTypeClass):
            self.__writeEncodeCodeForClass(writer=writer, config=config, fieldType=fieldType, fieldExpr=fieldExpr, cppClass=cppClass, enc=enc)
            return
        elif isinstance(fieldType, CppTypeString):
            writer.writeNL(f'{enc}.encode_string_utf8({fieldExpr});')
            return
        elif isinstance(fieldType, CppTypeBinary):
            writer.writeNL(f'{enc}.encode_varsize_binary({fieldExpr});')
            return

        cppType:str = fieldType.toString(cppClass)

        if CPP_MARSHAL_TYPE_HAS_ENCODE_DECODE in fieldType.m_extensions:
            writer.writeNL(f'{fieldExpr}.encode({enc});')
            return
        
        if re.search(r'^u?int([0-9]+)_t$', cppType) or cppType=='bool':
            writer.writeNL(f'{enc}.encode<{cppType}>({fieldExpr});')
            return

        writer.writeNL(f'#error PyMetaProg.CppMarshalGenerator._writeEncodeCode does not support type `{cppType}` used by attribute `{fieldExpr}`')
        logError(f"attribute `{fieldExpr}` uses an unsupported type: {cppType}")

    #=============================================================================================
    def __writeDecodeCodeForVector(self, writer:Writer, config:Config, fieldType:CppTypeVector, fieldExpr:str, cppClass:CppClass, dec:str):
        anticipatedSizeVar:str = '__num_of_elements'
        writer.writeNL(text=f'''\
            size_t {anticipatedSizeVar} = {dec}.decode_array_begin();
            if ({anticipatedSizeVar} != dastd::marshal_array_SIZE_UNKNOWN) {{
                {fieldExpr}.reserve({anticipatedSizeVar});
            }}
        ''')
        
        writer.writeNL(text=f'''\
            // Keep looping on array elements
            while({dec}.decode_array_element_begin()) {{
        ''')
        writer.incIndent()

        fieldExpr2:str = f'{fieldExpr}.emplace_back()'
        self._writeDecodeCode(writer=writer, config=config, fieldType=fieldType.m_containedType, fieldExpr=fieldExpr2, cppClass=cppClass, dec=dec)

        writer.writeNL('dec.decode_array_element_end();')
        writer.decIndent()
        writer.writeNL('''\
            }
            dec.decode_array_end();
        ''')


    #=============================================================================================
    def __writeEncodeCodeForVector(self, writer:Writer, config:Config, fieldType:CppTypeVector, fieldExpr:str, cppClass:CppClass, enc:str):
        iterator:str = "__item"

        writer.writeNL(text=f'''\
            {enc}.encode_array_begin({fieldExpr}.size());
            for(auto const& {iterator}: {fieldExpr}) {{
        ''')
        writer.incIndent()
        writer.writeNL(text='''\
            enc.encode_array_element_begin();
        ''')

        self._writeEncodeCode(writer=writer, config=config, fieldType=fieldType.m_containedType, fieldExpr=iterator, cppClass=cppClass, enc=enc)

        writer.writeNL(text='''\
            enc.encode_array_element_end();
        ''')
        writer.decIndent()
        writer.writeNL(text=f'''\
            }}
            {enc}.encode_array_end();
        ''')

    #=============================================================================================
    def __writeDecodeCodeForMap(self, writer:Writer, config:Config, fieldType:CppTypeMap, fieldExpr:str, cppClass:CppClass, dec:str):
        if not isinstance(fieldType.m_keyType, CppTypeString):
            logError(f"attribute `{fieldExpr}` uses CppTypeMap with key of type {fieldType.m_keyType}: only CppTypeString are supported as keys.")
            return

        key:str = "__key__"
        mapElement:str = "__map_element__";
        writer.writeNL(text="{")
        writer.incIndent()
        writer.writeNL(text=f'''\
            std::string {key};
            {dec}.decode_dictionary_begin();
        ''')
        
        writer.writeNL(text=f'''\
            // Keep looping on dictionary elements
            while({dec}.decode_dictionary_element_begin({key})) {{
        ''')
        writer.incIndent()
        writer.writeNL(text=f'''\
            // In case of dupe keys, keep the last one. There shouldn't be any dupe
            // key, but who knows...
            {fieldExpr}.erase({key});

            // Create a new map instance associated to the related key
            auto {mapElement} = {fieldExpr}.emplace(std::piecewise_construct, std::forward_as_tuple({key}), std::forward_as_tuple());
        ''')

        fieldExpr2:str = f'{mapElement}.first->second'
        self._writeDecodeCode(writer=writer, config=config, fieldType=fieldType.m_containedType, fieldExpr=fieldExpr2, cppClass=cppClass, dec=dec)
        writer.writeNL('dec.decode_dictionary_element_end();')
        writer.decIndent()
        writer.writeNL('''\
            }
            dec.decode_dictionary_end();
        ''')
        writer.decIndent()
        writer.writeNL(text="}")


    #=============================================================================================
    def __writeEncodeCodeForMap(self, writer:Writer, config:Config, fieldType:CppTypeMap, fieldExpr:str, cppClass:CppClass, enc:str):
        if not isinstance(fieldType.m_keyType, CppTypeString):
            logError(f"attribute `{fieldExpr}` uses CppTypeMap with key of type {fieldType.m_keyType}: only CppTypeString are supported as keys.")
            return
        iterator:str = "__item"

        writer.writeNL(text=f'''\
            {enc}.encode_dictionary_begin({fieldExpr}.size());
            for(auto const& {iterator}: {fieldExpr}) {{
        ''')
        writer.incIndent()
        writer.writeNL(text=f'''\
            enc.encode_dictionary_element_begin({iterator}.first);
        ''')

        self._writeEncodeCode(writer=writer, config=config, fieldType=fieldType.m_containedType, fieldExpr=f'{iterator}.second', cppClass=cppClass, enc=enc)

        writer.writeNL(text='''\
            enc.encode_dictionary_element_end();
        ''')
        writer.decIndent()
        writer.writeNL(text=f'''\
            }}
            {enc}.encode_dictionary_end();
        ''')



    #=============================================================================================
    def __writeDecodeCodeForSharedPtr(self, writer:Writer, config:Config, fieldType:CppTypeSharedPtr, fieldExpr:str, cppClass:CppClass, dec:str)->None:
        typeVar:str = "marshal_type"
        ptrVar:str = "marshal_ptr"

        assert(isinstance(fieldType.m_containedType, CppTypeClass))
        attribClass:CppNameScope = fieldType.m_containedType.m_cppClass
        attribClassName:str = attribClass.getCppQualifiedName(cppClass)

        if fieldType.m_polymorphic:
            writer.writeNL(f'''
                dastd::marshal_label_id_t {typeVar} = {dec}.decode_typed_begin(true);
                std::shared_ptr<{attribClassName}> {ptrVar} = {attribClassName}::new_instance({typeVar});
            ''')
        else:
            writer.writeNL(f'''
                std::shared_ptr<{attribClassName}> {ptrVar} = std::make_shared<{attribClassName}>();
            ''')

        writer.writeNL(f'''
            if ({ptrVar}) {{
        ''')
        writer.incIndent()
        self._writeDecodeCustomOnNewCode(writer=writer, config=config, fieldType=fieldType, fieldExpr=ptrVar, cppClass=cppClass, dec=dec)
        writer.writeNL(f'''\
            {fieldExpr} = {ptrVar};
            {ptrVar}->{self.m_decodeMethodName}({dec});
        ''')
        writer.decIndent()
        writer.writeNL(f'''\
            }}
            else {{
                DASTD_THROW(dastd::exception_marshal, "{cppClass.getCppQualifiedName()}::{self.m_decodeMethodName} invalid type for attribute '{fieldExpr}'");
            }}
        ''')

        if fieldType.m_polymorphic:
            writer.write(f'{dec}.decode_typed_end();')


    #=============================================================================================
    def __writeEncodeCodeForClass(self, writer:Writer, config:Config, fieldType:CppTypeClass, fieldExpr:str, cppClass:CppClass, enc:str)->None:
        if isinstance(fieldType.m_cppClass, CppEnumBase):
            writer.writeNL(f'{enc}.encode<{fieldType.m_cppClass.getCppQualifiedName(otherScope=cppClass)}>({fieldExpr});')
        else:    
            writer.writeNL(f'{fieldExpr}.encode({enc});')


    #=============================================================================================
    def __writeDecodeCodeForClass(self, writer:Writer, config:Config, fieldType:CppTypeClass, fieldExpr:str, cppClass:CppClass, dec:str)->None:
        if isinstance(fieldType.m_cppClass, CppEnumBase):
            writer.writeNL(f'{fieldExpr} = {dec}.decode<{fieldType.m_cppClass.getCppQualifiedName(otherScope=cppClass)}>();')
        else:    
            writer.writeNL(f'{fieldExpr}.decode({dec});')


    #=============================================================================================
    def __writeEncodeCodeForSharedPtr(self, writer:Writer, config:Config, fieldType:CppTypeSharedPtr, fieldExpr:str, cppClass:CppClass, enc:str)->None:
        writer.writeNL(f'''
            if ({fieldExpr} == nullptr) {{
                DASTD_THROW(dastd::exception_marshal, "{cppClass.getCppQualifiedName()}::{self.m_encodeMethodName} shared pointer '{fieldExpr}' is null");
            }}
        ''')

        if fieldType.m_polymorphic:
            writer.writeNL(f'''
                {enc}.encode_typed_begin(dastd::marshal_label({fieldExpr}->{self.m_getMarshalClassName}(), {fieldExpr}->{self.m_getMarshalLabelId}()), true);
            ''')

        writer.writeNL(f'''
            {fieldExpr}->encode({enc});
        ''')

        if fieldType.m_polymorphic:
            writer.writeNL(f'''
                {enc}.encode_typed_end();
            ''')



    #=============================================================================================
    def __decorateClass(self, cppClass:CppClass) -> None:
        '''! Decorate the single class with all the required code '''
        if CPP_MARSHAL_CLASS_GENERATED in cppClass.m_extensions:
            logError(f"class `{cppClass.getCppQualifiedName()}` generated more than once")
            return
        if not RTTI_GENERATED in cppClass.m_extensions:
            logError(f"class `{cppClass.getCppQualifiedName()}` must first be processed by the `cpp_rtti_generator` module")
            return 
        if not CLEAR_GENERATED in cppClass.m_extensions:
            logError(f"class `{cppClass.getCppQualifiedName()}` must first be processed by the `cpp_clear_generator` module")
            return 
        cppClass.m_extensions[CPP_MARSHAL_CLASS_GENERATED] = True
        #logInfo(f"decorating class `{cppClass.getCppQualifiedName()}`")

        self.__addIncludes(cppClass)
        # Create the list of attributes
        marshaledAttributes:list[CppMarshalGenerator.MarshaledAttribute] = list()
        self.__fillMarshaledAttributes(cppClass=cppClass, marshaledAttributes=marshaledAttributes)

        # Generate the name constants
        for marshaledAttribute in marshaledAttributes: self.__generateFieldNameConstant(cppClass=cppClass, marshaledAttribute=marshaledAttribute)
        self.__generateFieldDescriptor(cppClass=cppClass, marshaledAttributes=marshaledAttributes)
        self.__generateDecodeMethod(cppClass=cppClass, marshaledAttributes=marshaledAttributes)
        self.__generateDecodeAttrMethod(cppClass=cppClass, marshaledAttributes=marshaledAttributes)
        self.__generateEncodeMethod(cppClass=cppClass, marshaledAttributes=marshaledAttributes)
        self.__generateEncodeAttrMethod(cppClass=cppClass, marshaledAttributes=marshaledAttributes)
        self.__generateMarshalClassId(cppClass=cppClass)
        self.__generateMarshalnewInstance(cppClass=cppClass)

    #=============================================================================================
    def __fillMarshaledAttributes(self, marshaledAttributes:list[MarshaledAttribute], cppClass:CppClass, isBaseClass:bool=False):
        if self._baseClassHasStreaming(cppClass=cppClass):
            assert(isinstance(cppClass.m_baseClass, CppClass))
            baseClass:CppClass = cppClass.m_baseClass
            assert(CPP_MARSHAL_CLASS_ANTILOOP not in baseClass.m_extensions) # Detected class inheritance loop!
            baseClass.m_extensions[CPP_MARSHAL_CLASS_ANTILOOP] = True
            self.__fillMarshaledAttributes(marshaledAttributes=marshaledAttributes, cppClass=baseClass, isBaseClass=True)
            del baseClass.m_extensions[CPP_MARSHAL_CLASS_ANTILOOP]

        cppFields:list[CppField] = self.__selectAttributes(cppClass)
        for cppField in cppFields:
            streamedName:str = self._calcStreamedAttributeName(cppField=cppField)
            keyConstexprName:str = self._calcFieldNameConstant(cppField=cppField, streamedName=streamedName)
            marshaledAttributes.append(CppMarshalGenerator.MarshaledAttribute(
                cppField=cppField,
                cppClass=cppClass,
                streamedName=streamedName, 
                keyConstexprName=keyConstexprName, 
                absolutePosition=len(marshaledAttributes),
                derivedFromBaseClass=isBaseClass
            ))

    #=============================================================================================
    def __addIncludes(self, cppClass:CppClass) -> None:
        '''! Add the required includes '''
        cppClass.m_hppIncludes.add("dastd/marshal_dec.hpp")
        cppClass.m_hppIncludes.add("dastd/marshal_enc.hpp")

    #=============================================================================================
    def __selectAttributes(self, cppClass:CppClass) -> list[CppField]:
        '''! Select the `CppField` of the indicated `cppClass` that are to be serialized '''
        fields:list[CppField] = list()
        for classElement in cppClass.m_classElements:
            if isinstance(classElement, CppField) and not classElement.m_fieldConst:
                doInclude:bool = True
                if CPP_MARSHAL_FIELD_ENABLE in classElement.m_extensions:
                    if not isinstance(classElement.m_extensions[CPP_MARSHAL_FIELD_ENABLE], bool):
                        logError(f'In attribute `{classElement}`, extension key CPP_MARSHAL_FIELD_ENABLE ("{CPP_MARSHAL_FIELD_ENABLE}") must be a bool, not a {type(classElement.m_extensions[CPP_MARSHAL_FIELD_ENABLE])}')
                    doInclude=classElement.m_extensions[CPP_MARSHAL_FIELD_ENABLE]
                else:
                    if self.m_mode == CppMarshalGeneratorMode.AUTO_INCLUDE: doInclude=True
                    if self.m_mode == CppMarshalGeneratorMode.AUTO_EXCLUDE: doInclude=False
                    if self.m_mode == CppMarshalGeneratorMode.EXPLICIT:
                            logError(f'In attribute `{classElement}`, extension key CPP_MARSHAL_FIELD_ENABLE ("{CPP_MARSHAL_FIELD_ENABLE}") must be set because the `CppMarshalGenerator` mode is set to {CppMarshalGeneratorMode.EXPLICIT}')
                if doInclude:
                    fields.append(classElement)

        return fields

    #=============================================================================================
    def __generateFieldNameConstant(self, cppClass:CppClass, marshaledAttribute:MarshaledAttribute):
        if marshaledAttribute.m_derivedFromBaseClass: return
        cppClass.addClassElement(
            CppField(
                fieldName=marshaledAttribute.m_keyConstexprName,
                fieldType=CppTypeSimple(simpleType='char', arrayPostfix='[]'),
                fieldConst=True,
                fieldDefault=f'"{marshaledAttribute.m_streamedName}"',
                visibility=CppVisibility.PROTECTED,
                brief=f'Streamed field name for `{marshaledAttribute.m_cppAttrib.m_fieldName}`'
            )
        )

    #=============================================================================================
    def __generateFieldDescriptor(self, cppClass:CppClass, marshaledAttributes:list[MarshaledAttribute]):

        class FieldDescritptor(Writable):
            def __init__(self, marshaledAttributes:list[CppMarshalGenerator.MarshaledAttribute]):
                self.m_marshaledAttributes:list[CppMarshalGenerator.MarshaledAttribute] = marshaledAttributes
            
            def write(self, writer:Writer, config:Config):

                writer.writeNL("{")
                writer.incIndent()
                for marshaledAttribute in self.m_marshaledAttributes:
                    writer.writeNL(f'dastd::marshal_label_info_calc({marshaledAttribute.m_keyConstexprName}, false),')

                writer.decIndent()
                writer.write('}')

        
        if len(marshaledAttributes) > 0:
            # Generate the field descriptor
            cppClass.addClassElement(
                CppField(
                    fieldName=self.m_fieldsArrayName,
                    fieldType=CppTypeSimple(simpleType='dastd::marshal_label_info_t', arrayPostfix='[]'),
                    fieldConst=True,
                    fieldDefault=FieldDescritptor(marshaledAttributes=marshaledAttributes),
                    visibility=CppVisibility.PROTECTED,
                    brief='Table of structure field ids, required for marshal decoding'
                )
            )

        # Generate the field descriptor
        cppClass.addClassElement(
            CppField(
                fieldName=self.m_fieldsCountName,
                fieldType='size_t',
                fieldConst=True,
                fieldDefault=f'sizeof({self.m_fieldsArrayName})/sizeof({self.m_fieldsArrayName}[0])' if len(marshaledAttributes)>0 else '0',
                visibility=CppVisibility.PROTECTED,
                brief='Number of elements in table of structure field ids, required for marshal decoding'
            )
        )

    #=============================================================================================
    def __generateDecodeMethod(self, cppClass:CppClass, marshaledAttributes:list[MarshaledAttribute]):
        cppClass.m_extensions[CPP_MARSHAL_METHOD_DECODE] = self.m_decodeMethodName
        mayBeUnused:bool = (len(marshaledAttributes) == 0)
        derived:bool = self._baseClassHasStreaming(cppClass)

        
        methodName:str = f'{cppClass.getCppQualifiedName()}::{self.m_decodeMethodName}'
        code:WritableSet = WritableSet()
        if len(marshaledAttributes) > 0:
            DUPEMAP:str = "dupeMap"
            dupeMap:str = DUPEMAP
            code.append(f'''\
                bool {DUPEMAP}[{self.m_fieldsCountName}];
                memset({DUPEMAP}, 0, sizeof(dupeMap));
            ''')
            structFields:str = self.m_fieldsArrayName
            structFieldsCount:str = self.m_fieldsCountName
        else:
            dupeMap:str = "nullptr"
            structFields:str = "nullptr"
            structFieldsCount:str = "0"

        code.append(f'''\
            // Clear the object before decoding
            {cppClass.m_extensions[CLEAR_METHOD]}();

            dec.decode_struct_begin(true, {structFields}, {structFieldsCount});
            for(;;) {{
                bool field_is_present;
                
                // Request the decoding of the next field. The `field_is_present` flag
                // will be set to `false` if the field is optional and marked "missing".
                dastd::marshal_label_id_t label_id = dec.decode_struct_field_begin(&field_is_present);
                
                // If returns 'marshal_label_id_INVALID', it means there are no more fields.
                if (label_id == dastd::marshal_label_id_INVALID) {{
                    break;
                }}
                
                if (field_is_present) {{
                    bool decoded = {self.m_decodeAttrMethodName}(dec, label_id, {dupeMap});
                    if (!decoded) {{
                        dastd::char32string label_text;
                        if (dec.get_field_name(label_id, label_text)) {{
                            DASTD_THROW(dastd::exception_marshal, "{methodName} unknown attribute " << dastd::fmt32_cq(label_text));
                        }}
                        else {{
                            DASTD_THROW(dastd::exception_marshal, "{methodName} unknown attribute with label_id=" << label_id);
                        }}
                    }}
                }}
                
                dec.decode_struct_field_end();
            }}
            dec.decode_struct_end();

        ''')


        cppClass.addClassElement(
            CppMethod(
                methodName=self.m_decodeMethodName,
                returnType='void',
                virtuality=CppVirtuality.VIRTUAL_OVERRIDE if derived else CppVirtuality.VIRTUAL,
                inline=CppInline.INLINE_OUTSIDE,
                code=code,
                brief='Decode the contents',
                hppIncludes=["dastd/fmt_string.hpp"],
                params=[
                    CppParam(
                        paramName='dec',
                        paramType='dastd::marshal_dec&',
                        paramComment='Decoder object',
                        mayBeUnused=mayBeUnused,
                    ),
                ],
            )
        )

    #=============================================================================================
    def __generateDecodeAttrMethod(self, cppClass:CppClass, marshaledAttributes:list[MarshaledAttribute]):
        mayBeUnused:bool = (len(marshaledAttributes) == 0)
        derived:bool = self._baseClassHasStreaming(cppClass)

        class DecodeAttrMethodCode(Writable):
            def __init__(self, cppMarshalGenerator:CppMarshalGenerator, methodName:str, cppClass:CppClass, marshaledAttributes:list[CppMarshalGenerator.MarshaledAttribute], derived:bool):
                self.m_methodName:str = methodName
                self.m_cppMarshalGenerator:CppMarshalGenerator = cppMarshalGenerator
                self.m_marshaledAttributes:list[CppMarshalGenerator.MarshaledAttribute] = marshaledAttributes
                self.m_cppClass:CppClass = cppClass
                self.m_derived:bool = derived
            
            def write(self, writer:Writer, config:Config):
                if self.m_derived:
                    assert(isinstance(self.m_cppClass.m_baseClass, CppClass))
                    writer.writeNL(f"if ({self.m_cppClass.m_baseClass.getCppQualifiedName(self.m_cppClass)}::{self.m_methodName}(dec, label_id, dupe_map)) return true;")
                
                addedCase:bool = False
                for marshaledAttribute in self.m_marshaledAttributes:
                    if not marshaledAttribute.m_derivedFromBaseClass:
                        if not addedCase:
                            writer.writeNL('switch(label_id) {')
                            writer.incIndent()
                            addedCase = True
                        writer.writeNL(f'// DECODE FIELD: {marshaledAttribute.m_cppAttrib.m_fieldName}')
                        writer.writeNL(f'case dastd::marshal_label::const_hash({marshaledAttribute.m_keyConstexprName}): {{')
                        writer.incIndent()
                        writer.writeNL(f'if (dupe_map[{marshaledAttribute.m_absolutePosition}]) DASTD_THROW(dastd::exception_marshal, "{marshaledAttribute.m_cppClass.getCppQualifiedName()}::{self.m_methodName}() detected dupe attribute \'{marshaledAttribute.m_streamedName}\'");')
                        writer.writeNL(f'dupe_map[{marshaledAttribute.m_absolutePosition}] = true;')
                        self.m_cppMarshalGenerator._writeDecodeCode(writer=writer, config=config, fieldType=marshaledAttribute.m_cppAttrib.m_fieldType, fieldExpr=marshaledAttribute.m_cppAttrib.m_fieldName, cppClass=cppClass, dec="dec")
                        writer.writeNL('return true;')
                        writer.decIndent()
                        writer.writeNL('}')

                if addedCase:
                    writer.decIndent()
                    writer.writeNL("}")
                writer.writeNL("return false;")


        cppClass.addClassElement(
            CppMethod(
                methodName=self.m_decodeAttrMethodName,
                returnType='bool',
                virtuality=CppVirtuality.VIRTUAL_OVERRIDE if derived else CppVirtuality.VIRTUAL,
                inline=CppInline.INLINE_OUTSIDE,
                code=DecodeAttrMethodCode(cppMarshalGenerator=self, methodName=self.m_decodeAttrMethodName, cppClass=cppClass, marshaledAttributes=marshaledAttributes, derived=derived),
                brief='Decode the given attribute',
                params=[
                    CppParam(
                        paramName='dec',
                        paramType='dastd::marshal_dec&',
                        paramComment='Decoder object',
                        mayBeUnused=mayBeUnused,
                    ),
                    CppParam(
                        paramName='label_id',
                        paramType='dastd::marshal_label_id_t',
                        paramComment='Indicates the id of the attribute being decoded (i.e. the hash of the attribute name)',
                        mayBeUnused=mayBeUnused,
                    ),
                    CppParam(
                        paramName='dupe_map',
                        paramType='bool*',
                        paramComment='Array of booleans; each element is related to an attribute and tells whether the attribute has been already decoded; used to avoid dupes.',
                        mayBeUnused=mayBeUnused,
                    ),
                ],
            )
        )

    #=============================================================================================
    def __generateEncodeMethod(self, cppClass:CppClass, marshaledAttributes:list[MarshaledAttribute]):
        cppClass.m_extensions[CPP_MARSHAL_METHOD_ENCODE] = self.m_encodeMethodName
        if self._baseClassHasStreaming(cppClass): return

        cppClass.addClassElement(
            CppMethod(
                methodName=self.m_encodeMethodName,
                returnType='void',
                virtuality=CppVirtuality.VIRTUAL,
                inline=CppInline.INLINE_OUTSIDE,
                staticity=CppStaticity.DYNAMIC_CONST,
                code=f'''\
                    enc.encode_struct_begin(true);
                    {self.m_encodeAttrMethodName}(enc);
                    enc.encode_struct_end();
                ''',
                brief='Encode the object as a structure',
                params=[
                    CppParam(
                        paramName='enc',
                        paramType='dastd::marshal_enc&',
                        paramComment='Encoder object',
                    ),
                ],
            )
        )

        cppClass.addClassElement(
            CppMethod(
                methodName=self.m_polymorphicEncode,
                returnType='void',
                virtuality=CppVirtuality.VIRTUAL,
                inline=CppInline.INLINE_OUTSIDE,
                staticity=CppStaticity.DYNAMIC_CONST,
                code=f'''\
                    enc.encode_typed_begin(dastd::marshal_label({self.m_getMarshalClassName}(), {self.m_getMarshalLabelId}()), true);
                    enc.encode_struct_begin(true);
                    {self.m_encodeAttrMethodName}(enc);
                    enc.encode_struct_end();
                    enc.encode_typed_end();
                ''',
                brief='Encode the object as a polymorphic structure',
                params=[
                    CppParam(
                        paramName='enc',
                        paramType='dastd::marshal_enc&',
                        paramComment='Encoder object',
                    ),
                ],
            )
        )

        #

    #=============================================================================================
    def __generateEncodeAttrMethod(self, cppClass:CppClass, marshaledAttributes:list[MarshaledAttribute]):
        mayBeUnused:bool = (len(marshaledAttributes) == 0)
        derived:bool = self._baseClassHasStreaming(cppClass)
        
        class EncodeAttrMethodCode(Writable):
            def __init__(self, cppMarshalGenerator:CppMarshalGenerator, methodName:str, cppClass:CppClass, marshaledAttributes:list[CppMarshalGenerator.MarshaledAttribute], derived:bool):
                self.m_methodName:str = methodName
                self.m_cppMarshalGenerator:CppMarshalGenerator = cppMarshalGenerator
                self.m_marshaledAttributes:list[CppMarshalGenerator.MarshaledAttribute] = marshaledAttributes
                self.m_cppClass:CppClass = cppClass
                self.m_derived:bool = derived
            
            def write(self, writer:Writer, config:Config):
                if self.m_derived:
                    assert(isinstance(self.m_cppClass.m_baseClass, CppClass))
                    writer.writeNL(f"{self.m_cppClass.m_baseClass.getCppQualifiedName(self.m_cppClass)}::{self.m_methodName}(enc);")
                
                for marshaledAttribute in self.m_marshaledAttributes:
                    if not marshaledAttribute.m_derivedFromBaseClass:
                        writer.writeNL(f'// ENCODE FIELD: {marshaledAttribute.m_cppAttrib.m_fieldName}')
                        writer.writeNL(f'enc.encode_struct_field_begin(dastd::marshal_label({marshaledAttribute.m_keyConstexprName}));')
                        self.m_cppMarshalGenerator._writeEncodeCode(writer=writer, config=config, fieldType=marshaledAttribute.m_cppAttrib.m_fieldType, fieldExpr=marshaledAttribute.m_cppAttrib.m_fieldName, cppClass=cppClass, enc="enc")
                        writer.writeNL('enc.encode_struct_field_end();')

        cppClass.addClassElement(
            CppMethod(
                methodName=self.m_encodeAttrMethodName,
                returnType='void',
                virtuality=CppVirtuality.VIRTUAL_OVERRIDE if derived else CppVirtuality.VIRTUAL,
                inline=CppInline.INLINE_OUTSIDE,
                staticity=CppStaticity.DYNAMIC_CONST,
                code=EncodeAttrMethodCode(cppMarshalGenerator=self, methodName=self.m_encodeAttrMethodName, cppClass=cppClass, marshaledAttributes=marshaledAttributes, derived=derived),
                brief='Encode the attributes',
                params=[
                    CppParam(
                        paramName='enc',
                        paramType='dastd::marshal_enc&',
                        paramComment='Encoder object',
                        mayBeUnused=mayBeUnused,
                    ),
                ],
            )
        )

    #=============================================================================================
    def __generateMarshalClassId(self, cppClass:CppClass):
        derived:bool = self._baseClassHasStreaming(cppClass)

        if CPP_MARSHAL_CLASS_NAME in cppClass.m_extensions:
            assert(isinstance(cppClass.m_extensions[CPP_MARSHAL_CLASS_NAME], str))
            className:str = cppClass.m_extensions[CPP_MARSHAL_CLASS_NAME]
        else:
            className = cppClass.getCppQualifiedName()

        # self.m_marshalClassName

        cppClass.addClassElement(
            CppField(
                fieldName=self.m_marshalClassName,
                fieldType=CppTypeSimple(simpleType="char", arrayPostfix="[]"),
                fieldConst=True,
                visibility=CppVisibility.PUBLIC,
                brief='Name used by the marshaling system used to identify this class when streaming and unstreaming',
                fieldDefault=f'"{className}"'
            )
        )

        cppClass.addClassElement(
            CppField(
                fieldName=self.m_marshalLabelId,
                fieldType="dastd::marshal_label_id_t",
                fieldConst=True,
                visibility=CppVisibility.PUBLIC,
                brief='Type identifier',
                fieldDefault=f'dastd::marshal_label::const_hash({self.m_marshalClassName})'
            )
        )

        cppClass.addClassElement(
            CppMethod(
                methodName=self.m_getMarshalLabelId,
                returnType='dastd::marshal_label_id_t',
                virtuality=CppVirtuality.VIRTUAL_OVERRIDE if derived else CppVirtuality.VIRTUAL,
                inline=CppInline.INLINE_OUTSIDE,
                code=f'return {self.m_marshalLabelId};',
                staticity=CppStaticity.DYNAMIC_CONST,
                visibility=CppVisibility.PUBLIC,
                brief='Return the label id for this instance',
            )
        )

        cppClass.addClassElement(
            CppMethod(
                methodName=self.m_getMarshalClassName,
                returnType='const char*',
                virtuality=CppVirtuality.VIRTUAL_OVERRIDE if derived else CppVirtuality.VIRTUAL,
                inline=CppInline.INLINE_OUTSIDE,
                code=f'return {self.m_marshalClassName};',
                staticity=CppStaticity.DYNAMIC_CONST,
                visibility=CppVisibility.PUBLIC,
                brief='Return the name used by the marshaling system used to identify this class when streaming and unstreaming',
            )
        )

    #=============================================================================================
    def __generateMarshalnewInstance(self, cppClass:CppClass):
        derived:bool = self._baseClassHasStreaming(cppClass)
        if derived: return
        
        # Module that contains the base class
        baseModuleConfig:Optional[CppModuleConfig] = cppClass.getCppModuleConfig()
        assert(baseModuleConfig is not None)

        # Get all the derived classes
        derivedClasses:list[CppClass] = cppClass.findDerivedClasses()

        modules:set[CppModuleConfig] = set()

        for derivedClass in derivedClasses:
            cppModuleConfig:Optional[CppModuleConfig] = derivedClass.getCppModuleConfig()
            assert(cppModuleConfig is not None)
            modules.add(cppModuleConfig)

        # If the classes are all in the same module, we can afford making the factory method
        # inline. Otherwise, we must put it in a .cpp file and include the other includes.
        if len(modules)==1:
            for module in modules:
                assert(module == baseModuleConfig)
            cppInline:CppInline = CppInline.INLINE_OUTSIDE
        else:
            cppInline:CppInline = CppInline.OUT_OF_LINE
            for module in modules:
                baseModuleConfig.includeModuleInCpp(module)
        
        #-----------------------------------------------------------------------------
        # NEW INSTANCE - Method implementation
        #-----------------------------------------------------------------------------
        marshalLabelId:str = 'marshal_label_id'
        newInstanceCode:WritableSet = WritableSet()
        newInstanceCode.append(f'switch({marshalLabelId}) {{')
        newInstanceCode.incIndent()

        for derivedClass in derivedClasses:
            derivedClassName:str = derivedClass.getCppQualifiedName(cppClass)
            newInstanceCode.append(f'case {derivedClassName}::{self.m_marshalLabelId}: return std::make_shared<{derivedClassName}>();')

        newInstanceCode.decIndent()
        newInstanceCode.append(f'}}')
        newInstanceCode.append(f'return nullptr;')

        #-----------------------------------------------------------------------------
        # NEW INSTANCE - Method declaration
        #-----------------------------------------------------------------------------
        cppClass.addClassElement(
            CppMethod(
                methodName=self.m_newInstance,
                returnType=CppTypeSharedPtr(CppTypeClass(cppClass)),
                inline=cppInline,
                code=newInstanceCode,
                staticity=CppStaticity.STATIC,
                visibility=CppVisibility.PUBLIC,
                brief='Create an instance of this type or one of its derived',
                params=[
                    CppParam(
                        paramName=marshalLabelId,
                        paramType='dastd::marshal_label_id_t',
                        paramComment='Unique identifier of the class type'
                    )
                ]
            )
        )
        

        #-----------------------------------------------------------------------------
        # POLYMORHPIC DECODE - Method implementation
        #-----------------------------------------------------------------------------
        marshalDecoder:str = 'dec'
        typeVar:str = "marshal_type"
        ptrVar:str = "marshal_ptr"
        polymorphicDecodeCode:WritableSet = WritableSet()
        polymorphicDecodeCode.append(f'''
            dastd::marshal_label_id_t {typeVar} = {marshalDecoder}.decode_typed_begin(true);
            std::shared_ptr<{cppClass.getCppUnqualifiedName()}> {ptrVar} = {cppClass.getCppUnqualifiedName()}::new_instance({typeVar});
            if ({ptrVar}) {{
                {ptrVar}->{self.m_decodeMethodName}({marshalDecoder});
            }}
            else {{
                DASTD_THROW(dastd::exception_marshal, "{cppClass.getCppQualifiedName()}::{self.m_decodeMethodName} invalid type");
            }}
            {marshalDecoder}.decode_typed_end();
            return {ptrVar};
        ''')
        
        #-----------------------------------------------------------------------------
        # POLYMORHPIC DECODE - Method declaration
        #-----------------------------------------------------------------------------
        cppClass.addClassElement(
            CppMethod(
                methodName=self.m_polymorphicDecode,
                returnType=CppTypeSharedPtr(CppTypeClass(cppClass)),
                inline=cppInline,
                code=polymorphicDecodeCode,
                staticity=CppStaticity.STATIC,
                    visibility=CppVisibility.PUBLIC,
                    brief='Decode an unknown structure that begins with a `decode_typed_begin`',
                    params=[
                    CppParam(
                        paramName=marshalDecoder,
                        paramType='dastd::marshal_dec&',
                        paramComment='Decoder object'
                    )
                ]
            )
        )

