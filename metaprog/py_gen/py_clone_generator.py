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
from metaprog.py.py_class import PyClass
from metaprog.py.py_enum import PyEnum
from metaprog.py.py_field import PyField
from metaprog.py.py_labels import PyVisibility, PyStaticity
from metaprog.py.py_method import PyMethod
from metaprog.py.py_param import PyParam
from metaprog.py.py_type import PyType, PyTypeClass, PyTypeSimple, PyTypeString, PyTypeBinary, PyTypeNone, PyTypeVector, PyTypeMap, PyTypeOptional
from metaprog.util.comment_entry import CommentEntry, COMMENT_BRIEF, COMMENT_RETURN
from metaprog.util.writable_set import WritableSet
from typing import Optional

# Key to be used in the PyField "extension" dictionary to enable or disable the generation of the attribute
PY_CLONE_FIELD_ENABLE:str = "py_clone_enable"   # -> True or False; defaults to `True`

# Key to be used in the PyClass "extension" dictionary to enable or disable the generation of the attribute
PY_CLONE_CLASS_GENERATED = "py_clone_generated" # -> bool, created and written by this module to mark that has been processed

_PY_CLONE_ENCODE_COUNTER = "py_marshal_encode_counter"

class PyCloneGenerator(PyGeneratorBase):
    def __init__(
            self,
            methodClone:str = 'clone',  # Name of the genenerated 'clone' method
            methodCloneInternal:str = 'cloneInternal',  # Name of the genenerated 'encodeInternal' method
            dataObjectName:str = 'dataObject',
        ) -> None:
        super().__init__()
        self.m_methodClone:str = methodClone
        self.m_methodCloneInternal:str = methodCloneInternal
        self.m_dataObjectName:str = dataObjectName

    
    #=============================================================================================
    def decorateClasses(self) -> None:
        for pyClass in self.m_pyClasses:
            if pyClass.m_extensions.getValueOrNone(PY_CLONE_CLASS_GENERATED) is not None:
                print(f"[ERROR] PyCloneGenerator fatal error: class `{pyClass.getPyQualifiedName()}` generated more than once")
                exit(1)
            pyClass.m_extensions[PY_CLONE_CLASS_GENERATED] = True
            pyClass.m_pyIncludes.importFrom(moduleName='__future__', name='annotations')

        errors:int = 0
        for pyClass in self.m_pyClasses:
            errors += self._checkBaseClasses(pyClass=pyClass)
        
        if errors: exit(1)

        for pyClass in self.m_pyClasses:
            cloneInternalMethod:PyMethod = self._addCloneInternal(pyClass=pyClass)
            self._addClone(pyClass=pyClass, cloneInternalMethod=cloneInternalMethod)
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
            if base.m_extensions.getValueOrNone(PY_CLONE_CLASS_GENERATED) is None:
                errors += 1
                print(f"[ERROR] PyCloneGenerator class `{base.getPyQualifiedName}`, base class of `{pyClass.getPyQualifiedName()}` is not registered in the clone generator list!")

    #=============================================================================================
    def _getUniqueVarName(self, pyClass:PyClass) -> str:
        pyBaseClass:PyClass = pyClass
        while isinstance(pyBaseClass.m_baseClass, PyClass): pyBaseClass = pyBaseClass.m_baseClass
        varName:str = f'data_{pyBaseClass.m_extensions[_PY_CLONE_ENCODE_COUNTER]:03}'
        pyBaseClass.m_extensions[_PY_CLONE_ENCODE_COUNTER] += 1
        return varName



    #=============================================================================================
    def _addClone(self, pyClass:PyClass, cloneInternalMethod:PyMethod) -> None:
        '''! Create the encoding method '''
        
        code:WritableSet = WritableSet()

        # Create the structure
        code.append(f'''\
            # Create the dictionary object that will contain this object data
            {self.m_dataObjectName}:{pyClass.getPyQualifiedName(otherScope=pyClass)} = {pyClass.getPyQualifiedName(otherScope=pyClass)}()

            # Clone this fields and the fields of the base classes            
            self.{cloneInternalMethod.getPyUnqualifiedName()}({self.m_dataObjectName}={self.m_dataObjectName})

            # Return the encoded object
            return {self.m_dataObjectName}
        ''')

        # Generate the method
        pyClass.addChild(PyMethod(
            methodName=self.m_methodClone,
            returnType=PyTypeClass(pyClass=pyClass),
            brief=[
                CommentEntry(command=COMMENT_BRIEF, description='Clones this object'),
                CommentEntry(command=COMMENT_RETURN, description='Returns new instance that is a clone of this instance'),
            ],
            visibility=PyVisibility.PUBLIC,
            staticity=PyStaticity.DYNAMIC,
            params=[
            ],
            code=code
        ))

    #=============================================================================================
    def _addCloneInternal(self, pyClass:PyClass) -> PyMethod:
        '''! Create the internal encoding method '''

        # Generate the method
        cloneInternalMethod:PyMethod = PyMethod(
            methodName=self.m_methodCloneInternal,
            returnType=PyTypeNone(),
            brief=[
                CommentEntry(command=COMMENT_BRIEF, description='Clones the fields of this object into a new instance'),
            ],
            visibility=PyVisibility.PROTECTED,
            staticity=PyStaticity.DYNAMIC,
            params=[
                PyParam(
                    paramName=self.m_dataObjectName,
                    paramType=PyTypeClass(pyClass=pyClass), 
                    paramComment='The dictionary that needs its entries added',
                ),
            ],
        )

        code:WritableSet = WritableSet()

        # Call the encoding on the base class as well
        if pyClass.m_baseClass is not None and isinstance(pyClass.m_baseClass, PyClass):
            code.append(f'super().{cloneInternalMethod.getPyUnqualifiedName()}({self.m_dataObjectName}={self.m_dataObjectName})')

        # Adds the fields if encoded
        for pyField in pyClass.m_children:
            if isinstance(pyField, PyField):
                doInclude:Optional[bool] = pyField.m_extensions.getValueOrNone(PY_CLONE_FIELD_ENABLE)
                if doInclude is None:
                    doInclude = True

                if doInclude:
                    code.append(f'''
                        # Clone field `{pyField.getPyUnqualifiedName()}`
                        {self.m_dataObjectName}.{pyField.getPyUnqualifiedName()} = {self._genClone(pyClass=pyClass, instance=f'self.{pyField.getPyUnqualifiedName()}', pyType=pyField.m_fieldType)}
                    ''')

        cloneInternalMethod.m_code.append(text=code)
        pyClass.addChild(child=cloneInternalMethod)
        return cloneInternalMethod

    #=============================================================================================
    def _genClone(self, pyClass:PyClass, instance:str, pyType:PyType) -> str:
        '''! Writes all the required code to generate the encode.
            @return Returns the expression that can be assigned to the data structure to be returned
           '''
        if isinstance(pyType, PyTypeOptional):
            return f'None if {instance} is None else {self._genClone(pyClass=pyClass, instance=instance, pyType=pyType.m_containedType)}'

        if isinstance(pyType, PyTypeString):
            return instance

        if isinstance(pyType, PyTypeBinary):
            return instance

        if isinstance(pyType, PyTypeSimple):
            if pyType.m_simpleType in ['int', 'bool', 'float']:
                return instance

        if isinstance(pyType, PyTypeClass):
            if isinstance(pyType.m_pyClass, PyEnum):
                return f'{instance}'
            else:
                return f'{instance}.{self.m_methodClone}()'
            
        if isinstance(pyType, PyTypeVector):
            method:PyMethod = PyMethod(
                methodName=f'{self.m_methodClone}__{self._getUniqueVarName(pyClass=pyClass)}', 
                returnType=pyType,
                visibility=PyVisibility.PRIVATE,
                staticity=PyStaticity.DYNAMIC,
                brief=f'Used to encode instance `{instance}`',
                params=[
                    PyParam(paramName='instance', paramType=pyType, paramComment='The instance to be encoded'),
                ],
                code=f'''\
                    ret:{pyType.typeHint(containerClass=pyClass)} = list()
                    for item in instance:
                        ret.append({self._genClone(pyClass=pyClass, instance='item', pyType=pyType.m_containedType)})
                    return ret
                ''',
            )
            pyClass.addChild(child=method)
            return f'self.{method.m_nameScope}(instance={instance})'
            
        if isinstance(pyType, PyTypeMap):
            method:PyMethod = PyMethod(
                methodName=f'{self.m_methodClone}__{self._getUniqueVarName(pyClass=pyClass)}', 
                returnType=pyType,
                visibility=PyVisibility.PRIVATE,
                staticity=PyStaticity.DYNAMIC,
                brief=f'Used to encode instance `{instance}`',
                params=[
                    PyParam(paramName='instance', paramType=pyType, paramComment='The instance to be encoded'),
                ],
                code=f'''\
                    ret:{pyType.typeHint(containerClass=pyClass)}= dict()
                    for key, item in instance.items():
                        ret[key] = ({self._genClone(pyClass=pyClass, instance='item', pyType=pyType.m_containedType)})
                    return ret
                ''',
            )
            pyClass.addChild(child=method)
            return f'self.{method.m_nameScope}(instance={instance})'

        if isinstance(pyType, PyTypeNone):
            return 'None'

        print(f'[ERROR] PyCloneGenerator type `{pyType.__class__.__name__}` can not be cloneed')
        exit(1)

