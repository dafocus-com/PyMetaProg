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

from .py_generator_base import PyGeneratorBase
from enum import Enum
from metaprog.py.py_class import PyClass
from metaprog.py.py_enum import PyEnum
from metaprog.py.py_field import PyField
from metaprog.py.py_includes import PyIncludes
from metaprog.py.py_labels import PyVisibility, PyStaticity
from metaprog.py.py_method import PyMethod
from metaprog.py.py_param import PyParam
from metaprog.py.py_type import PyType, PyTypeClass, PyTypeSimple, PyTypeString, PyTypeBinary, PyTypeNone, PyTypeVector, PyTypeMap, PyTypeOptional
from metaprog.util.comment_entry import CommentEntry, COMMENT_BRIEF, COMMENT_RETURN, COMMENT_THROWS
from metaprog.util.log import logError
from metaprog.util.writable_set import WritableSet
from typing import Optional

# Key to be used in the PyField "extension" dictionary to enable or disable the generation of the attribute
PY_MARSHAL_FIELD_ENABLE = "py_marshal_enable"   # -> True or False
PY_MARSHAL_FIELD_NAME   = "py_marshal_name"     # -> Optional string for a different attribute name

# Key to be used in the PyClass "extension" dictionary to enable or disable the generation of the attribute
PY_MARSHAL_CLASS_GENERATED = "py_marshal_generated" # -> bool, created and written by this module to mark that has been processed
PY_MARSHAL_CLASS_NAME      = "py_marshal_name"      # -> Alternate name used by this class to calculate the name used when streaming

_PY_MARSHAL_ENCODE_COUNTER = "py_marshal_encode_counter"

_PY_TYPE_PARAMETER_BRIEF:str = 'Name of the field used to encode the type name in case of polymorphic encoding; the content of this field is used during the decoding process to create the correct instance.'

class PyMarshalGeneratorMode(Enum):
    '''
    The PyField objects, in their `extension` dictionary, may have a `PY_MARSHAL_FIELD_ENABLE`
    entry that can be missing, `True` or `False`. For example:

        cppAttrib.m_extensions[PY_MARSHAL_FIELD_ENABLE] = True

    The values below indicate whether the attribute is serialized or not:
    - if `PY_MARSHAL_FIELD_ENABLE` is specified, that indication is taken
    - if `AUTO_INCLUDE`, and  `PY_MARSHAL_FIELD_ENABLE` is not specified, the attribute will be serialized
    - if `AUTO_EXCLUDE`, and  `PY_MARSHAL_FIELD_ENABLE` is not specified, the attribute will not be serialized
    - if `EXPLICIT`, and  `PY_MARSHAL_FIELD_ENABLE` is not specified, a fatal error will occur
    '''
    AUTO_INCLUDE=0 
    AUTO_EXCLUDE=1
    EXPLICIT    =2

class PyMarshalGenerator(PyGeneratorBase):
    def __init__(
            self,
            mode:PyMarshalGeneratorMode=PyMarshalGeneratorMode.AUTO_INCLUDE,
            methodEncode:str = 'encode',  # Name of the genenerated 'encode' method
            methodDecode:str = 'decode',  # Name of the genenerated 'decode' method
            methodEncodeInternal:str = 'encodeInternal',  # Name of the genenerated 'encodeInternal' method
            methodDecodeInternal:str = 'decodeInternal',  # Name of the genenerated 'decodeInternal' method
            methodFactory:str = 'factory', # Name of the factory method
            typeParameter:str = 'typeFieldName', # Name of the parameter that tells the decoder the name of the type field
            typeParameterDefault:str = '$type', # Default value of the parameter that tells the decoder the name of the type field
            dataObjectName:str = 'dataObject',
            polymorphicEncodeParamName:str = 'polymorphicEncode',
            factoryTypeNameParamName:str = 'typeName',
        ) -> None:
        super().__init__()
        self.m_mode:PyMarshalGeneratorMode = mode
        self.m_methodEncode:str = methodEncode
        self.m_methodDecode:str = methodDecode
        self.m_methodEncodeInternal:str = methodEncodeInternal
        self.m_methodDecodeInternal:str = methodDecodeInternal
        self.m_methodFactory:str = methodFactory
        self.m_typeParameter:str = typeParameter
        self.m_typeParameterDefault:str = typeParameterDefault
        self.m_dataObjectName:str = dataObjectName
        self.m_polymorphicEncodeParamName:str = polymorphicEncodeParamName
        self.m_factoryTypeNameParamName:str = factoryTypeNameParamName

    
    #=============================================================================================
    def decorateClasses(self) -> None:
        for pyClass in self.m_pyClasses:
            if pyClass.m_extensions.getValueOrNone(PY_MARSHAL_CLASS_GENERATED) is not None:
                print(f"[ERROR] PyMarshalGenerator fatal error: class `{pyClass.getPyQualifiedName()}` generated more than once")
                exit(1)
            pyClass.m_extensions[PY_MARSHAL_CLASS_GENERATED] = True
            pyClass.m_extensions[_PY_MARSHAL_ENCODE_COUNTER] = 0

            pyClass.m_pyIncludes.importFrom(moduleName='__future__', name='annotations')

        errors:int = 0
        for pyClass in self.m_pyClasses:
            errors += self._checkBaseClasses(pyClass=pyClass)
        
        if errors: exit(1)

        for pyClass in self.m_pyClasses:
            self._addFactory(pyClass=pyClass)

            encodeInternalMethod:PyMethod = self._addEncodeInternal(pyClass=pyClass)
            self._addEncode(pyClass=pyClass, encodeInternalMethod=encodeInternalMethod)

            decodeInternalMethod:PyMethod = self._addDecodeInternal(pyClass=pyClass)
            self._addDecode(pyClass=pyClass, decodeInternalMethod=decodeInternalMethod)
#
        #for pyClass in self.m_pyClasses:
        #    pass # TBD

    #=============================================================================================
    def _checkBaseClasses(self, pyClass:PyClass) -> int:
        errors:int = 0
        base:Optional[PyClass] = pyClass
        while True:
            if not isinstance(base.m_baseClass, PyClass): return errors
            base = base.m_baseClass
            if pyClass.m_baseClass is None: return errors
            if base.m_extensions.getValueOrNone(PY_MARSHAL_CLASS_GENERATED) is None:
                errors += 1
                print(f"[ERROR] PyMarshalGenerator class `{base.getPyQualifiedName}`, base class of `{pyClass.getPyQualifiedName()}` is not registered in the marshal generator list!")

    #=============================================================================================
    def _getUniqueVarName(self, pyClass:PyClass) -> str:
        pyBaseClass:PyClass = pyClass
        while isinstance(pyBaseClass.m_baseClass, PyClass): pyBaseClass = pyBaseClass.m_baseClass
        varName:str = f'data_{pyBaseClass.m_extensions[_PY_MARSHAL_ENCODE_COUNTER]:03}'
        pyBaseClass.m_extensions[_PY_MARSHAL_ENCODE_COUNTER] += 1
        return varName

    #=============================================================================================
    def _addDecode(self, pyClass:PyClass, decodeInternalMethod:PyMethod) -> None:
        '''! Create the decoding method '''
        code:WritableSet = WritableSet()

        pythonObject:str = "obj"

        # Create the instance to be returned
        code.append(f'''\
            # If polymorphic decode is required, the factory will be involved
            if {self.m_polymorphicEncodeParamName}:
                if {self.m_typeParameter} not in {self.m_dataObjectName}:
                    raise ValueError(f"Can not create a polymorphic instance derived from class `{pyClass.getPyQualifiedName()}` because the decoded data do not have the `{{{self.m_dataObjectName}}}` field") 
                if not isinstance({self.m_dataObjectName}[{self.m_typeParameter}], str):
                    raise ValueError(f"Can not create a polymorphic instance derived from class `{pyClass.getPyQualifiedName()}` because `{{{self.m_dataObjectName}}}` field is not a `str`") 
                {pythonObject}:{pyClass.getPyUnqualifiedName()} = {pyClass.getPyUnqualifiedName()}.{self.m_methodFactory}({self.m_factoryTypeNameParamName}={self.m_dataObjectName}[{self.m_typeParameter}])
            else:
                # If not polymorphic, create an exact instance
                {pythonObject} = {pyClass.getPyUnqualifiedName()}()
            
            {pythonObject}.{decodeInternalMethod.getPyUnqualifiedName()}({self.m_dataObjectName}={self.m_dataObjectName}, {self.m_typeParameter}={self.m_typeParameter})
                
            return {pythonObject}
        ''')

        # Generate the method
        pyClass.addChild(PyMethod(
            methodName=self.m_methodDecode,
            returnType=PyTypeClass(pyClass=pyClass),
            brief=[
                CommentEntry(command=COMMENT_BRIEF, description='Decodes this object from a Python data structure'),
                CommentEntry(command=COMMENT_RETURN, description='Returns a decoded instance'),
                CommentEntry(command=COMMENT_THROWS, description='Throws a `ValueError` exception if the decoded data type can not be converted to the field type'),
            ],
            visibility=PyVisibility.PUBLIC,
            staticity=PyStaticity.STATIC,
            params=[
                PyParam(
                    paramName=self.m_dataObjectName,
                    paramType=PyTypeSimple(simpleType='Any', pyIncludesAny=('typing', 'Any')), 
                    paramComment='The dictionary object that needs to be decoded',
                ),
                PyParam(
                    paramName=self.m_polymorphicEncodeParamName,
                    paramType=PyTypeSimple(simpleType='bool'), 
                    paramDefault='False', 
                    paramComment='Set to `True` to encode as a polymorphic object (will add the type identification field)',
                ),
                self._getTypeIdentifierParameter(),
            ],
            code=code
        ))


    #=============================================================================================
    def _addEncode(self, pyClass:PyClass, encodeInternalMethod:PyMethod) -> None:
        '''! Create the encoding method '''
        
        code:WritableSet = WritableSet()

        # Create the structure
        code.append(f'''\
            # Create the dictionary object that will contain this object data
            {self.m_dataObjectName}:dict[str,Any] = dict()

            # If requested, add the type identification field
            if {self.m_polymorphicEncodeParamName}:
                {self.m_dataObjectName}[{self.m_typeParameter}] = '{self._getMarshalClassName(pyClass=pyClass)}'

            # Encode this fields and the fields of the base classes            
            self.{encodeInternalMethod.getPyUnqualifiedName()}({self.m_dataObjectName}={self.m_dataObjectName}, {self.m_typeParameter}={self.m_typeParameter})

            # Return the encoded object
            return {self.m_dataObjectName}
        ''')

        # Generate the method
        pyClass.addChild(PyMethod(
            methodName=self.m_methodEncode,
            returnType=PyTypeSimple(simpleType='dict[str,Any]', pyIncludesAny=('typing', 'Any')),
            brief=[
                CommentEntry(command=COMMENT_BRIEF, description='Encodes this object into a Python data structure'),
                CommentEntry(command=COMMENT_RETURN, description='Returns a Python dictionary containings the exported fields'),
            ],
            visibility=PyVisibility.PUBLIC,
            staticity=PyStaticity.DYNAMIC,
            params=[
                PyParam(
                    paramName=self.m_polymorphicEncodeParamName, 
                    paramType=PyTypeSimple(simpleType='bool'), 
                    paramDefault='False', 
                    paramComment='Set to `True` to encode as a polymorphic object (will add the type identification field)',
                ),
                self._getTypeIdentifierParameter(),
            ],
            code=code
        ))

    #=============================================================================================
    def _addEncodeInternal(self, pyClass:PyClass) -> PyMethod:
        '''! Create the internal encoding method '''

        # Generate the method
        encodeInternalMethod:PyMethod = PyMethod(
            methodName=self.m_methodEncodeInternal,
            returnType=PyTypeNone(),
            brief=[
                CommentEntry(command=COMMENT_BRIEF, description='Encodes the fields of this object into a Python data structure'),
            ],
            visibility=PyVisibility.PROTECTED,
            staticity=PyStaticity.DYNAMIC,
            params=[
                PyParam(
                    paramName=self.m_dataObjectName,
                    paramType=PyTypeSimple(simpleType='dict[str,Any]', pyIncludesAny=('typing', 'Any')), 
                    paramComment='The dictionary that needs its entries added',
                ),
                self._getTypeIdentifierParameter(),
            ],
        )

        code:WritableSet = WritableSet()

        # Call the encoding on the base class as well
        if pyClass.m_baseClass is not None and isinstance(pyClass.m_baseClass, PyClass):
            code.append(f'super().{encodeInternalMethod.getPyUnqualifiedName()}({self.m_dataObjectName}={self.m_dataObjectName}, {self.m_typeParameter}={self.m_typeParameter})')

        # Adds the fields if encoded
        for pyField in pyClass.m_children:
            if isinstance(pyField, PyField):
                doInclude:bool = False
                if pyField.m_extensions.getValueOrNone(PY_MARSHAL_FIELD_ENABLE):
                    doInclude = True
                else:
                    print(f"[DEBUG] PY CLASS MARSHALING [{pyField.getPyQualifiedName()}]")
                    if self.m_mode == PyMarshalGeneratorMode.AUTO_INCLUDE: doInclude=True
                    if self.m_mode == PyMarshalGeneratorMode.AUTO_EXCLUDE: doInclude=False
                    if self.m_mode == PyMarshalGeneratorMode.EXPLICIT:
                            logError(f'In attribute `{pyField.getPyQualifiedName()}`, extension key PY_MARSHAL_FIELD_ENABLE ("{PY_MARSHAL_FIELD_ENABLE}") must be set because the `PyMarshalGenerator` mode is set to {PyMarshalGeneratorMode.EXPLICIT}')

                if doInclude:
                    code.append(f'''
                        # Encode field `{pyField.getPyUnqualifiedName()}`
                        {self.m_dataObjectName}["{self._getMarshalFieldName(pyField=pyField)}"] = {self._genEncode(pyClass=pyClass, instance=f'self.{pyField.getPyUnqualifiedName()}', pyType=pyField.m_fieldType)}
                    ''')

        encodeInternalMethod.m_code.append(text=code)
        pyClass.addChild(child=encodeInternalMethod)
        return encodeInternalMethod

    #=============================================================================================
    def _addDecodeInternal(self, pyClass:PyClass) -> PyMethod:
        '''! Create the internal decoding method '''

        # Generate the method
        decodeInternalMethod:PyMethod = PyMethod(
            methodName=self.m_methodDecodeInternal,
            returnType=PyTypeNone(),
            brief=[
                CommentEntry(command=COMMENT_BRIEF, description='Decodes the fields of this object into a Python data structure'),
            ],
            visibility=PyVisibility.PROTECTED,
            staticity=PyStaticity.DYNAMIC,
            params=[
                PyParam(
                    paramName=self.m_dataObjectName,
                    paramType=PyTypeSimple(simpleType='dict[str,Any]', pyIncludesAny=('typing', 'Any')), 
                    paramComment='The dictionary that needs its entries added',
                ),
                self._getTypeIdentifierParameter(),
            ],
        )

        code:WritableSet = WritableSet()

        # Call the decoding on the base class as well
        if pyClass.m_baseClass is not None and isinstance(pyClass.m_baseClass, PyClass):
            code.append(f'super().{decodeInternalMethod.getPyUnqualifiedName()}({self.m_dataObjectName}={self.m_dataObjectName}, {self.m_typeParameter}={self.m_typeParameter})')

        # Adds the fields if decoded
        for pyField in pyClass.m_children:
            if isinstance(pyField, PyField):
                if pyField.m_extensions.getValueOrNone(PY_MARSHAL_FIELD_ENABLE):
                    marshalFieldName:str = self._getMarshalFieldName(pyField=pyField)
                    code.append(f'''
                        # Decode field `{pyField.getPyUnqualifiedName()}`
                        if '{marshalFieldName}' in {self.m_dataObjectName}:
                            self.{pyField.getPyUnqualifiedName()} = {self._genDecode(pyClass=pyClass, data=self.m_dataObjectName+'["'+marshalFieldName+'"]', pyType=pyField.m_fieldType)}
                    ''')

        decodeInternalMethod.m_code.append(text=code)
        pyClass.addChild(child=decodeInternalMethod)
        return decodeInternalMethod

    #=============================================================================================
    def _genEncode(self, pyClass:PyClass, instance:str, pyType:PyType) -> str:
        '''! Writes all the required code to generate the encode.
            @return Returns the expression that can be assigned to the data structure to be returned
           '''
        if isinstance(pyType, PyTypeOptional):
            return f'None if {instance} is None else {self._genEncode(pyClass=pyClass, instance=instance, pyType=pyType.m_containedType)}'

        if isinstance(pyType, PyTypeString):
            return instance

        if isinstance(pyType, PyTypeBinary):
            pyClass.m_pyIncludes.add(moduleName='base64')
            return f'base64.b64encode({instance}).decode("ascii")'

        if isinstance(pyType, PyTypeSimple):
            if pyType.m_simpleType in ['int', 'bool', 'float']:
                return instance

        if isinstance(pyType, PyTypeClass):
            if isinstance(pyType.m_pyClass, PyEnum):
                return f'{instance}.value'
            else:
                polymorphic:str = "True" if pyType.m_polymorphic else "False"
                return f'{instance}.{self.m_methodEncode}({self.m_polymorphicEncodeParamName}={polymorphic}, {self.m_typeParameter}={self.m_typeParameter})'
            
        if isinstance(pyType, PyTypeVector):
            method:PyMethod = PyMethod(
                methodName=f'{self.m_methodEncode}__{self._getUniqueVarName(pyClass=pyClass)}', 
                returnType=PyTypeSimple(simpleType='list[Any]', pyIncludesAny=('typing', 'Any')),
                visibility=PyVisibility.PRIVATE,
                staticity=PyStaticity.DYNAMIC,
                brief=f'Used to encode instance `{instance}`',
                params=[
                    PyParam(paramName='instance', paramType=pyType, paramComment='The instance to be encoded'),
                    PyParam(paramName=self.m_typeParameter, paramType=PyTypeString(), paramComment=_PY_TYPE_PARAMETER_BRIEF),
                ],
                code=f'''\
                    ret:list[Any] = list()
                    for item in instance:
                        ret.append({self._genEncode(pyClass=pyClass, instance='item', pyType=pyType.m_containedType)})
                    return ret
                ''',
            )
            pyClass.addChild(child=method)
            return f'self.{method.m_nameScope}(instance={instance}, {self.m_typeParameter}={self.m_typeParameter})'
            
        if isinstance(pyType, PyTypeMap):
            method:PyMethod = PyMethod(
                methodName=f'{self.m_methodEncode}__{self._getUniqueVarName(pyClass=pyClass)}', 
                returnType=PyTypeSimple(simpleType='dict[str,Any]', pyIncludesAny=('typing', 'Any')),
                visibility=PyVisibility.PRIVATE,
                staticity=PyStaticity.DYNAMIC,
                brief=f'Used to encode instance `{instance}`',
                params=[
                    PyParam(paramName='instance', paramType=pyType, paramComment='The instance to be encoded'),
                    PyParam(paramName=self.m_typeParameter, paramType=PyTypeString(), paramComment=_PY_TYPE_PARAMETER_BRIEF),
                ],
                code=f'''\
                    ret:dict[str,Any] = dict()
                    for key, item in instance.items():
                        ret[key] = ({self._genEncode(pyClass=pyClass, instance='item', pyType=pyType.m_containedType)})
                    return ret
                ''',
            )
            pyClass.addChild(child=method)
            return f'self.{method.m_nameScope}(instance={instance}, {self.m_typeParameter}={self.m_typeParameter})'

        if isinstance(pyType, PyTypeNone):
            return 'None'

        print(f'[ERROR] PyMarshalGenerator type `{pyType.__class__.__name__}` can not be marshaled')
        exit(1)


    #=============================================================================================
    def _genDecode(self, pyClass:PyClass, data:str, pyType:PyType) -> str:
        '''! Writes all the required code to generate the decode. 
			@return Returns the expression that can be assigned to the object field
		'''
        if isinstance(pyType, PyTypeOptional):
            return f'None if {data} is None else {self._genDecode(pyClass=pyClass, data=data, pyType=pyType.m_containedType)}'

        if isinstance(pyType, PyTypeString):
            return data

        if isinstance(pyType, PyTypeBinary):
            pyClass.m_pyIncludes.add(moduleName='base64')
            return f'bytearray(base64.b64decode({data}))'
        
        if isinstance(pyType, PyTypeSimple):
            # In case of a simple instance, just convert it
            if pyType.m_simpleType in ['int', 'bool', 'float']:
                return f'{pyType.m_simpleType}({data})'

        if isinstance(pyType, PyTypeClass):
            if isinstance(pyType.m_pyClass, PyEnum):
                return f'{pyType.m_pyClass.getPyQualifiedName(otherScope=pyClass)}(int({data}))'
            else:
                return f'{pyType.m_pyClass.getPyQualifiedName(otherScope=pyClass)}.{self.m_methodDecode}({self.m_dataObjectName}={data}, {self.m_polymorphicEncodeParamName}={pyType.m_polymorphic}, {self.m_typeParameter}={self.m_typeParameter})'
            
        if isinstance(pyType, PyTypeVector):
            method:PyMethod = PyMethod(
                methodName=f'{self.m_methodDecode}__{self._getUniqueVarName(pyClass=pyClass)}', 
                returnType=pyType,
                visibility=PyVisibility.PRIVATE,
                staticity=PyStaticity.DYNAMIC,
                brief=f'Used to decode data `{data}`',
                params=[
                    PyParam(paramName='data', paramType=PyTypeSimple(simpleType='list[Any]'), paramComment='The data to be decoded'),
                    PyParam(paramName=self.m_typeParameter, paramType=PyTypeString(), paramComment=_PY_TYPE_PARAMETER_BRIEF),
                ],
                code=f'''\
                    ret:{pyType.typeHint(containerClass=pyClass)} = list()
                    for item in data:
                        ret.append({self._genDecode(pyClass=pyClass, data='item', pyType=pyType.m_containedType)})
                    return ret
                ''',
            )
            pyClass.addChild(child=method)
            return f'self.{method.m_nameScope}(data={data}, {self.m_typeParameter}={self.m_typeParameter})'
            
        if isinstance(pyType, PyTypeMap):
            method:PyMethod = PyMethod(
                methodName=f'{self.m_methodDecode}__{self._getUniqueVarName(pyClass=pyClass)}', 
                returnType=pyType,
                visibility=PyVisibility.PRIVATE,
                staticity=PyStaticity.DYNAMIC,
                brief=f'Used to decode data `{data}`',
                params=[
                    PyParam(paramName='data', paramType=pyType, paramComment='The data to be decoded'),
                    PyParam(paramName=self.m_typeParameter, paramType=PyTypeString(), paramComment=_PY_TYPE_PARAMETER_BRIEF),
                ],
                code=f'''\
                    ret:dict[str,Any] = dict()
                    for key, item in data.items():
                        ret[key] = ({self._genDecode(pyClass=pyClass, data='item', pyType=pyType.m_containedType)})
                    return ret
                ''',
            )
            pyClass.addChild(child=method)
            return f'self.{method.m_nameScope}(data={data}, {self.m_typeParameter}={self.m_typeParameter})'

        if isinstance(pyType, PyTypeNone):
            return 'None'

        print(f'[ERROR] PyMarshalGenerator type `{pyType.__class__.__name__}` can not be marshaled')
        exit(1)

    #=============================================================================================
    def _addFactory(self, pyClass:PyClass) -> None:
        '''! Create the factory method '''
        typeName:str = self.m_factoryTypeNameParamName
        privateIncludes:PyIncludes = PyIncludes()
        code:WritableSet = WritableSet()
        derivedClasses:list[PyClass] = pyClass.findDerivedClasses()

        for cls in derivedClasses:
            if cls != pyClass:
                pyClass.importInThis(toBeImported=cls, pyIncludes=privateIncludes)
            marshalClassName:str = self._getMarshalClassName(pyClass=cls)
            code.append(f'if {typeName} == "{marshalClassName}": return {cls.getPyQualifiedName(otherScope=pyClass)}()')
        
        code.append(f'raise ValueError(f"Can not create an instance of type `{{{typeName}}}`: either unknown or not a derivative of class `{pyClass.getPyQualifiedName()}`")')

        # Generate the method
        pyClass.addChild(PyMethod(
            methodName=self.m_methodFactory,
            returnType=PyTypeClass(pyClass=pyClass),
            brief=[
                CommentEntry(command=COMMENT_BRIEF, description='Creates an instance of this or one of its derivatives according to the marshaling class identifier'),
                CommentEntry(command=COMMENT_THROWS, description='Throws a `ValueError` exception in case the type name is invalid'),
            ],
            visibility=PyVisibility.PUBLIC,
            staticity=PyStaticity.STATIC,
            params=[
                PyParam(
                    paramName=typeName, 
                    paramType=PyTypeString(), 
                    paramComment='Marshaled name of this type',
                ),
            ],
            code=code
        ))
        



    #=============================================================================================
    def _getTypeIdentifierParameter(self) -> PyParam:
        return PyParam(
            paramName=self.m_typeParameter,
            paramType=PyTypeString(),
            paramDefault=f"'{self.m_typeParameterDefault}'",
            paramComment=_PY_TYPE_PARAMETER_BRIEF,
        )

    #=============================================================================================
    def _getMarshalClassName(self, pyClass:PyClass) -> str:
        name:Optional[str] = pyClass.m_extensions.getValueOrNone(PY_MARSHAL_CLASS_NAME)
        if name: return name
        return pyClass.getPyUnqualifiedName()

    #=============================================================================================
    def _getMarshalFieldName(self, pyField:PyField) -> str:
        name:Optional[str] = pyField.m_extensions.getValueOrNone(PY_MARSHAL_FIELD_NAME)
        if name: return name
        return pyField.getPyUnqualifiedName()