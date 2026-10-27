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

from .py_attribute import PyAttributes
from .py_class_element import PyClassElement
from .py_labels import PyVisibility, PyStaticity
from .py_type import PyType, PyTypeFactory, PyTypeAny
from .py_config import PyConfig
from .py_rvalue import PyRValue, PyRValueAny, PyRValueContainer
from .py_includes import PyIncludesAny
from .py_module_config import PyModuleConfig
from .py_namescope import PyNameScope
from metaprog.util.writer import Writer
from metaprog.util.writable_set import WritableSet, WritableSetAny, WritableSetValid
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.comment import CommentAny
from metaprog.util.config import env
from typing import Optional

# Key to be used in the PyType "extension" dictionary of a PyField or in its PyType
# to execute custom code to write the field part.
#
# Prototype: Callable[[PyField, Writer, PyConfig], None]
#
# Example:
#
#     myField.m_extensions[PY_FIELD_CODE] = f'''\
#         public List<int> {PY_FIELD_NAME}{{get; set;}} = new();
#     '''
#
PY_FIELD_CODE:str="py_field_code"

_PY_FIELD_NAME:str = "PY_FIELD_NAME"
_PY_FIELD_OBJ:str = "PY_FIELD_OBJ"

PY_FIELD_NAME:str = env(_PY_FIELD_NAME)
PY_FIELD_OBJ:str = env(_PY_FIELD_OBJ)


class PyField(PyClassElement, PyRValue):
    ''' Implements fields and properties '''
    def __init__(self, 
            fieldName:str, 
            fieldType:PyTypeAny, 
            fieldDefault:PyRValueAny=None,
            visibility:PyVisibility=PyVisibility.PUBLIC, 
            staticity:PyStaticity=PyStaticity.DYNAMIC,
            brief:CommentAny=None,
            pyIncludesAny:PyIncludesAny = None,
            extensions:ExtensionsAny = None,
        ) -> None:
        super().__init__(nameScope=fieldName, visibility=visibility, pyIncludesAny=pyIncludesAny, extensions=extensions, brief=brief)
        self.m_fieldType:PyType = PyTypeFactory(fieldType)
        self.m_fieldDefault:PyRValueContainer = PyRValueContainer(pyValueAny=fieldDefault)
        self.m_attributesField = PyAttributes()
        self.m_staticity:PyStaticity = staticity

    def setupModuleConfig(self, moduleConfig:PyModuleConfig) -> None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        super().setupModuleConfig(moduleConfig=moduleConfig)
        self.m_fieldType.setupModuleConfig(moduleConfig=moduleConfig)

    def generatePyBody(self, writer:Writer, config:PyConfig) -> None:
        if self.isStatic():
            self._declareField(writer=writer, config=config, prefix='')

    def identify(self)->str:
        return self.getPyQualifiedName()
    
    def isStatic(self)->bool:
        from .py_class import PyClass
        return not isinstance(self.m_parent, PyClass) or self.m_staticity == PyStaticity.STATIC

    def generateValue(self, writer:Writer, config:PyConfig, otherScope:Optional[PyNameScope]=None) -> None:
        '''! Generate the R-value text '''
        writer.writeRaw(text=self.getPyQualifiedName(otherScope=otherScope))

    #=============================================================================================
    def _printCustomCode(self, writer:Writer, config:PyConfig, code:WritableSetValid) -> None:
        writableSet:WritableSet = WritableSet()
        writableSet.pushEnv(env={_PY_FIELD_NAME:self.m_nameScope, _PY_FIELD_OBJ:self})
        writableSet.append(code)
        writableSet.popEnv()
        writableSet.write(writer=writer, config=config)

    def _declareField(self, writer:Writer, config:PyConfig, prefix:str='self.') -> None:
        self.m_comment.write(writer, config)
        self.m_attributesField.write(writer, config)

        customCode:WritableSetAny = self.m_extensions.getValueOrNone(key=PY_FIELD_CODE)
        if customCode is None:
            customCode = self.m_fieldType.m_extensions.getValueOrNone(key=PY_FIELD_CODE)
        
        if customCode is not None:
            #customCode(self, writer, config)
            self._printCustomCode(writer=writer, config=config, code=customCode)
            return

        self.m_fieldType.declVar(writer=writer, config=config, var=prefix+self.m_nameScope, containerClass=self, userDefinedDefault=self.m_fieldDefault, provideWithDefaultIfNotSpecified=True)
        writer.writeRaw('\n')

    def addConstructorCode(self, writer:Writer, config:PyConfig, prefix:str='self.') -> None:
        if not self.isStatic():
            self._declareField(writer=writer, config=config, prefix=prefix)

    def getDefault(self, containerClass:PyNameScope) -> PyRValueContainer:
        return self.m_fieldType.getDefaultValue(containerClass=containerClass, userDefinedDefault=self.m_fieldDefault)
