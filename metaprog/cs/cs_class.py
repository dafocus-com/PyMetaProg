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
from .cs_class_base import CsClassBase
from .cs_class_custom import CsClassCustom
from .cs_class_element import CsClassElement
from .cs_labels import CsVisibility, CsClassVirtuality, CsVirtuality
from .cs_includes import CsIncludesAny
from .cs_config import CsConfig
from .cs_method import CsMethod, CsMethodType
from .cs_field import CsField
from .cs_attribute import CsAttributes
from .cs_module_config import CsModuleConfig
from metaprog.util.writer import Writer
from metaprog.util.writable_set import WritableSet
from metaprog.util.comment import Comment, CommentAny
from metaprog.util.extensions import ExtensionsAny
from typing import Callable, Union, Optional

# List containing all the CsClass objects
CS_CLASSES:list[CsClass] = list()

def findCsSingleClassByExt(ext:str) -> CsClass:
    ''' Finds a single class that contains in its `m_extensions` the indicated extension key.
        It can be used to tag a class with a dummy extension and retrieve it later on.
        If the class is not found or multiple instances are found, an assertion is thrown.
    '''
    foundCls:Optional[CsClass] = None
    for cls in CS_CLASSES:
        if ext in cls.m_extensions:
            assert(foundCls is None)
            foundCls = cls
    assert(foundCls is not None)
    return foundCls

def findCsClassesByExt(ext:str) -> list[CsClass]:
    ''' Finds al classes that contain in their `m_extensions` the indicated extension key.
        It can be used to tag a class with a dummy extension and retrieve it later on.
    '''
    foundCls:list[CsClass] = list()
    for cls in CS_CLASSES:
        if ext in cls.m_extensions:
            foundCls.append(cls)
    return foundCls

class CsClass(CsClassBase):
    def __init__(
        self, 
        className:str, 
        baseClass:Union[str,CsClass,None]=None, 
        brief:CommentAny=None, # type: ignore
        csIncludes:CsIncludesAny=None, # type: ignore
        extensions:ExtensionsAny=None, # type: ignore
        classVirtuality:CsClassVirtuality = CsClassVirtuality.CLASS_NORMAL,
        classVisibility:CsVisibility = CsVisibility.PUBLIC,
    ) -> None:
        super().__init__(nameScope=className, baseClass=baseClass, csIncludes=csIncludes, extensions=extensions) # type: ignore
        self.m_classElements:list[CsClassElement] = list()
        self.m_comment:Comment = Comment(commentAny=brief) # type: ignore
        self.m_classVirtuality:CsClassVirtuality = classVirtuality
        self.m_classVisibility:CsVisibility = classVisibility

        self.m_antiLoopFlag:bool = False
        CS_CLASSES.append(self)

        self.m_startBlock:WritableSet = WritableSet()
        ''' This block is printed right after the beginning of the class, after the first open brace '''

        self.m_endBlock:WritableSet = WritableSet()
        ''' This block is printed right before the end of the class, before the last closed brace '''

        self.m_attributesClass = CsAttributes()
        ''' Attributes [key=value] '''

    def findSingleFieldByExtAllowNone(self, ext:str) -> Optional[CsField]:
        ''' Finds a single field that contains in its `m_extensions` the indicated extension key.
            It can be used to tag a field with a dummy extension and retrieve it later on.
            If the field is not found or multiple instances are found, an assertion is thrown.
        '''
        foundField:Optional[CsField] = None
        if self.m_baseClass is not None and isinstance(self.m_baseClass, CsClass):
            foundField = self.m_baseClass.findSingleFieldByExtAllowNone(ext=ext)

        for fld in self.m_classElements:
            if isinstance(fld, CsField):
                if ext in fld.m_extensions:
                    assert(foundField is None)
                    foundField = fld
        return foundField


    def findSingleFieldByExt(self, ext:str) -> CsField:
        ''' Finds a single field that contains in its `m_extensions` the indicated extension key.
            It can be used to tag a field with a dummy extension and retrieve it later on.
            If the field is not found or multiple instances are found, an assertion is thrown.
        '''
        foundField:Optional[CsField] = self.findSingleFieldByExtAllowNone(ext=ext)
        assert(foundField is not None)
        return foundField

    def findMultipleFields(self, ext:Optional[str]) -> list[CsField]:
        ''' Finds a zero or more field that contains in its `m_extensions` the indicated extension key.
            It can be used to tag fields with a dummy extension and retrieve them later on.
            If `ext` is None, it returns all fields.
            The search is extended to the base class as well.
        '''
        if self.m_baseClass is not None and isinstance(self.m_baseClass, CsClass):
            foundFields:list[CsField] = self.m_baseClass.findMultipleFields(ext=ext)
        else:
            foundFields = list()
        
        for fld in self.m_classElements:
            if isinstance(fld, CsField):
                if ext is None or ext in fld.m_extensions:
                    foundFields.append(fld)
        return foundFields

    def derivesFrom(self, otherClass:CsClass) -> bool:
        '''! Returns `True` if this class is or derives from `otherClass` '''
        assert(not self.m_antiLoopFlag) # Looping inheritance!
        if self==otherClass:return True
        if self.m_baseClass is not None and isinstance(self.m_baseClass, CsClass):
            self.m_antiLoopFlag = True
            ret:bool = self.m_baseClass.derivesFrom(otherClass=otherClass)
            self.m_antiLoopFlag = False
            return ret
        return False
    
    def findDerivedClasses(self) -> list[CsClass]:
        '''! Finds all the classes that derive from this one '''
        listOfDerivedClasses:list[CsClass] = list()
        for csClass in CS_CLASSES:
            if csClass.derivesFrom(self):
                listOfDerivedClasses.append(csClass)
        return listOfDerivedClasses


    def addClassElement(self, classElement:CsClassElement) -> None:
        self.m_classElements.append(classElement)
        classElement.m_owningScope = self


    def generateCsBody(self, writer:Writer, config:CsConfig) -> None:
        self.m_comment.write(writer, config)
        self.m_attributesClass.write(writer, config)
        writer.write(f"{self.m_classVisibility.toStr()} class {self.getCsUnqualifiedName()}")
        if self.m_baseClass is not None:
            if self.m_baseClass is str:
                writer.write(f': {self.m_baseClass}')
            else:
                writer.write(f': {self.m_baseClass.getCsQualifiedName(otherScope=self)}') # type: ignore
        writer.writeRaw(' {\n')
        writer.incIndent()
        self.m_startBlock.write(writer, config)

        visibilitySequence:list[CsVisibility] = [
            CsVisibility.PRIVATE,
            CsVisibility.PROTECTED,
            CsVisibility.PUBLIC,
        ]

        # First generate all constants (private, protected and public)
        for visibility in visibilitySequence:
            elements:list[CsClassElement] = self.__select(lambda elem: isinstance(elem,CsField) and elem.m_fieldConst, visibility=visibility)
            self.__generateElements(writer=writer, config=config, elements=elements)

        # Then generate all properties/fields and methods grouped by private, protected and public
        for visibility in visibilitySequence:
            elements = list()
            elements += self.__select(lambda elem: isinstance(elem,CsField) and not elem.m_fieldConst, visibility=visibility)
            elements += self.__select(lambda elem: isinstance(elem,CsMethod) or isinstance(elem,CsClassCustom), visibility=visibility)
            self.__generateElements(writer=writer, config=config, elements=elements)

        self.m_endBlock.write(writer, config)
        writer.decIndent()
        writer.writeNL('}')


    def getClassVirtuality(self) -> CsClassVirtuality:
        '''! Calculates the class virtuality accorting to what has been declared ant the methods '''
        thisClassVirtuality:CsClassVirtuality = self.m_classVirtuality
        baseClassVirtuality:CsClassVirtuality = CsClassVirtuality.CLASS_NORMAL
        if self.m_baseClass is not None and isinstance(self.m_baseClass, CsClass):
            baseClassVirtuality = self.m_baseClass.getClassVirtuality()
        
        # If the base class is not `CLASS_NORMAL`, then it must be virtual; therefore, we promote this class to
        # virtual as well. If also abstract, we don't know.
        if thisClassVirtuality == CsClassVirtuality.CLASS_NORMAL and baseClassVirtuality != CsClassVirtuality.CLASS_NORMAL:
            thisClassVirtuality = CsClassVirtuality.CLASS_VIRTUAL
        
        for elem in self.m_classElements:
            if isinstance(elem, CsMethod):
                if elem.m_virtuality == CsVirtuality.PURE_VIRTUAL:
                    thisClassVirtuality = CsClassVirtuality.CLASS_ABSTRACT
                elif elem.m_virtuality != CsVirtuality.NORMAL and thisClassVirtuality == CsClassVirtuality.CLASS_NORMAL:
                    thisClassVirtuality = CsClassVirtuality.CLASS_VIRTUAL
        return thisClassVirtuality
    

    def __select(self, elemSelect:Callable[[CsClassElement], bool], visibility:CsVisibility) -> list[CsClassElement]:
        elements:list[CsClassElement] = list()
        for elem in self.m_classElements:
            if elemSelect(elem) and elem.m_visibility == visibility:
                elements.append(elem)
        return elements


    def __generateElements(self, writer:Writer, config:CsConfig, elements:list[CsClassElement]) -> None:
        if not elements: return
        for element in elements: 
            element.generateCsBody(writer=writer, config=config)

    def setupModuleConfig(self, moduleConfig:CsModuleConfig) -> None:
        '''! Operate on the accessible parts of the module to add usings, header parts and so on '''
        super().setupModuleConfig(moduleConfig=moduleConfig)
        for elem in self.m_classElements:
            elem.setupModuleConfig(moduleConfig=moduleConfig)

    def getDefaultConstructor(self, createIfMissing:bool=False) -> Optional[CsMethod]:
        for elem in self.m_classElements:
            if isinstance(elem, CsMethod):
                if elem.m_methodType==CsMethodType.CONSTRUCTOR and len(elem.m_params)==0:
                    return elem
        if createIfMissing:
            self.addClassElement(CsMethod(
                methodType=CsMethodType.CONSTRUCTOR,
                brief="Constructor",
                visibility=CsVisibility.PUBLIC,
            ))
        return None
