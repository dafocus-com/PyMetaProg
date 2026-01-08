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
Generates two methods that allow encoding and decoding from/to a std::string in JSON.
Requires the `cpp_marshal_generator` to be executed as well.
'''
from .cpp_generator_base import *
from .cpp_marshal_generator import *
from metaprog.cpp.cpp_method import *
from metaprog.cpp.cpp_param import *
from metaprog.util.log import *

# Key to be used in the CppClass "extension" dictionary to enable or disable the generation of the class
CPP_MARSHAL_FAST_JSON_CLASS_GENERATED="cpp_marshal_fast_json_generated" # -> bool, created and written by this module to mark that has been processed


class CppMarshalFastJsonGenerator(CppGeneratorBase):
    #=============================================================================================
    def __init__(
            self, 
            jsonEncodeName:str = "json_encode",
            jsonDecodeName:str = "json_decode",
        ) -> None:
        super().__init__()
        self.m_jsonEncodeName:str = jsonEncodeName
        self.m_jsonDecodeName:str = jsonDecodeName

    #=============================================================================================
    def decorateClasses(self) -> None:
        '''! Executes the decoration of the classes before generating the code '''
        for cppClass in self.m_cppClasses:
            self.__decorateClass(cppClass)


    #=============================================================================================
    def __decorateClass(self, cppClass:CppClass) -> None:
        '''! Decorate the single class with all the required code '''
        if CPP_MARSHAL_FAST_JSON_CLASS_GENERATED in cppClass.m_extensions:
            logError(f"class `{cppClass.getCppQualifiedName()}` generated more than once")
            return
        if not CPP_MARSHAL_CLASS_GENERATED in cppClass.m_extensions:
            logError(f"class `{cppClass.getCppQualifiedName()}` must first be processed by the `cpp_marshal_generator` module")
            return 
        cppClass.m_extensions[CPP_MARSHAL_FAST_JSON_CLASS_GENERATED] = True
        self.__addEncode(cppClass=cppClass)
        self.__addDecode(cppClass=cppClass)


    #=============================================================================================
    def __addEncode(self, cppClass:CppClass) -> None:
        cppClass.m_hppIncludes.add('dastd/marshal_enc_json.hpp')
        cppClass.m_hppIncludes.add('sstream')
        cppClass.addClassElement(CppMethod(
            methodName=self.m_jsonEncodeName,
            returnType=CppTypeString(),
            visibility=CppVisibility.PUBLIC,
            brief='Encode this object as a JSON string',
            inline=CppInline.INLINE_OUTSIDE,
            virtuality=CppVirtuality.NORMAL,
            staticity=CppStaticity.DYNAMIC_CONST,
            params=[
                CppParam(
                    paramName='polymorphic_encoding',
                    paramType='dastd::marshal_json_polymorphic_encoding',
                    paramComment='See @ref dastd::marshal_json_polymorphic_encoding',
                    paramDefault='dastd::marshal_json_polymorphic_encoding::TYPEID_AS_FIELD_NAME',
                ),
                CppParam(
                    paramName='typed_field',
                    paramType=CppTypeString(isRef=True, isConst=True),
                    paramComment='Name of the field in case of `TYPEID_AS_STRUCT_FIELD`; see @ref dastd::marshal_json_polymorphic_encoding',
                    paramDefault='"$type"',
                ),
            ],
            code=f'''\
                std::ostringstream str;
                dastd::marshal_enc_json enc(str, polymorphic_encoding, typed_field);
                {cppClass.m_extensions[CPP_MARSHAL_METHOD_ENCODE]}(enc);
                return str.str();
            '''
        ))

    #=============================================================================================
    def __addDecode(self, cppClass:CppClass) -> None:
        cppClass.m_hppIncludes.add('dastd/marshal_dec_json.hpp')
        cppClass.m_hppIncludes.add('dastd/source_membuf.hpp')

        cppClass.addClassElement(CppMethod(
            methodName=self.m_jsonDecodeName,
            returnType='void',
            visibility=CppVisibility.PUBLIC,
            brief=[
                CommentEntry(command='brief', description='Decode this object from a JSON string'),
                CommentEntry(command='throw', description='Throws a `std::exception` in case of error decoding'),
            ],
            inline=CppInline.INLINE_OUTSIDE,
            virtuality=CppVirtuality.NORMAL,
            staticity=CppStaticity.DYNAMIC,
            params=[
                CppParam(
                    paramName='json_string',
                    paramType=CppTypeString(isRef=True, isConst=True, isConstexpr=True),
                    paramComment='See @ref dastd::marshal_json_polymorphic_encoding',
                ),
                CppParam(
                    paramName='polymorphic_encoding',
                    paramType='dastd::marshal_json_polymorphic_encoding',
                    paramComment='See @ref dastd::marshal_json_polymorphic_encoding',
                    paramDefault='dastd::marshal_json_polymorphic_encoding::TYPEID_AS_FIELD_NAME',
                ),
                CppParam(
                    paramName='typed_field',
                    paramType=CppTypeString(isRef=True, isConst=True),
                    paramComment='Name of the field in case of `TYPEID_AS_STRUCT_FIELD`; see @ref dastd::marshal_json_polymorphic_encoding',
                    paramDefault='"$type"',
                ),
            ],
            code=f'''\
                dastd::source_membuf<char> source(json_string);
                dastd::marshal_dec_json dec(source, polymorphic_encoding, typed_field);
                {cppClass.m_extensions[CPP_MARSHAL_METHOD_DECODE]}(dec);
            '''
        ))
