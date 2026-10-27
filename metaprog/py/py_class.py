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

from __future__ import annotations
from .py_config import PyConfig
from .py_includes import PyIncludesAny
from .py_labels import PyVisibility
from .py_method_constructor import PyMethodConstructor
from .py_module_config import PyModuleConfig
from .py_namescope import PyNameScope
from .py_namescope_reference import PyNameScopeReferences
from .py_namescope_with_children import PyNameScopeWithChildren
from .py_param import PyParam
from metaprog.util.comment import Comment, CommentAny
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.writer import Writer
from metaprog.util.writable_set import WritableSetAny
from typing import Optional
    

# List containing all the PyClass objects
PY_CLASSES:list[PyClass] = list()

def findPySingleClassByExt(ext:str) -> PyClass:
    ''' Finds a single class that contains in its `m_extensions` the indicated extension key.
        It can be used to tag a class with a dummy extension and retrieve it later on.
        If the class is not found or multiple instances are found, an assertion is thrown.
    '''
    foundCls:Optional[PyClass] = None
    for cls in PY_CLASSES:
        if ext in cls.m_extensions:
            assert(foundCls is None)
            foundCls = cls
    assert(foundCls is not None)
    return foundCls

def findPyClassesByExt(ext:str) -> list[PyClass]:
    ''' Finds al classes that contain in their `m_extensions` the indicated extension key.
        It can be used to tag a class with a dummy extension and retrieve it later on.
    '''
    foundCls:list[PyClass] = list()
    for cls in PY_CLASSES:
        if ext in cls.m_extensions:
            foundCls.append(cls)
    return foundCls

class PyClass(PyNameScopeWithChildren):
    '''! Objects that have a name scope like namespaces and classes '''
    def __init__(
            self, 
            className:str,
            baseClass:str|PyClass|None=None, 
            pyIncludesAny:PyIncludesAny=None,
            visibility:PyVisibility=PyVisibility.PUBLIC,
            brief:CommentAny=None,
            constructorParams:list[PyParam]=list(),
            constructorPreCode:WritableSetAny=None,
            extensions:ExtensionsAny=None,
            children:Optional[list[PyNameScope]]=None,
        ) -> None:
        super().__init__(nameScope=className, pyIncludesAny=pyIncludesAny, extensions=extensions, visibility=visibility)
        self.m_baseClass:str|PyClass|None = baseClass
        self.m_constructor:PyMethodConstructor = PyMethodConstructor(params=constructorParams, preCode=constructorPreCode, brief=f'Constructor of class `{className}`')
        self.addChild(child=self.m_constructor)
        if children is not None:
            for child in children:
                self.addChild(child=child)
        self.m_comment:Comment = Comment(commentAny=brief)
        self._params:list[PyParam] = list()
        self.m_antiLoopFlag:bool = False
        PY_CLASSES.append(self)

    def setupModuleConfig(self, moduleConfig:PyModuleConfig) -> None:
        super().setupModuleConfig(moduleConfig=moduleConfig)
        if self.m_baseClass is not None and isinstance(self.m_baseClass, PyClass):
            containerModuleRef:PyNameScopeReferences = moduleConfig.getNameScopeReferences()
            containedClassRef:PyNameScopeReferences = self.m_baseClass.getNameScopeReferences()
            containedClassRef.importThisIntoOther(other=containerModuleRef, otherImports=moduleConfig.m_pyIncludes)

    def generatePyBody(self, writer:Writer, config:PyConfig) -> None:
        self.m_comment.write(writer=writer, config=config)
        writer.writeRaw(f'class {self.m_nameScope}')
        if self.m_baseClass is not None:
            if isinstance(self.m_baseClass, PyClass):
                writer.writeRaw(f'({self.m_baseClass.getPyQualifiedName(otherScope=self)})')
            else:
                writer.writeRaw(f'({self.m_baseClass})')
        writer.writeNL(f':')
        writer.incIndent()

        for child in self.m_children:
            child.generatePyBody(writer=writer, config=config)

        writer.decIndent()

    def derivesFrom(self, otherClass:PyClass) -> bool:
        '''! Returns `True` if this class is or derives from `otherClass` '''
        assert(not self.m_antiLoopFlag) # Looping inheritance!
        if self==otherClass:return True
        if self.m_baseClass is not None and isinstance(self.m_baseClass, PyClass):
            self.m_antiLoopFlag = True
            ret:bool = self.m_baseClass.derivesFrom(otherClass=otherClass)
            self.m_antiLoopFlag = False
            return ret
        return False
    
    def findDerivedClasses(self) -> list[PyClass]:
        '''! Finds all the classes that derive from this one, including this one '''
        listOfDerivedClasses:list[PyClass] = list()
        for pyClass in PY_CLASSES:
            if pyClass.derivesFrom(self):
                listOfDerivedClasses.append(pyClass)
        return listOfDerivedClasses

