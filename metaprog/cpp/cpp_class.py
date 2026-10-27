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
from .cpp_class_base import CppClassBase
from .cpp_class_element import CppClassElement
from .cpp_labels import CppClassVirtuality, CppVisibility, CppVirtuality, CppInline
from .cpp_includes import CppIncludesAny
from .cpp_config import CppConfig
from .cpp_method import CppMethod, CppMethodType
from .cpp_field import CppField
from .cpp_module_config import CppModuleConfig
from .cpp_class_custom import CppClassCustom
from metaprog.util.writer import Writer
from metaprog.util.writable_set import WritableSet
from metaprog.util.comment import Comment, CommentAny
from typing import Optional, Callable, Union
from metaprog.util.extensions import ExtensionsAny

# List containing all the CppClass objects
CPP_CLASSES:list[CppClass] = list()

def findCppSingleClassByExt(ext:str) -> CppClass:
    ''' Finds a single class that contains in its `m_extensions` the indicated extension key.
        It can be used to tag a class with a dummy extension and retrieve it later on.
        If the class is not found or multiple instances are found, an assertion is thrown.
    '''
    foundCls:Optional[CppClass] = None
    for cls in CPP_CLASSES:
        if ext in cls.m_extensions:
            assert(foundCls is None)
            foundCls = cls
    assert(foundCls is not None)
    return foundCls

def findCppClassesByExt(ext:str) -> list[CppClass]:
    ''' Finds al classes that contain in their `m_extensions` the indicated extension key.
        It can be used to tag a class with a dummy extension and retrieve it later on.
    '''
    foundCls:list[CppClass] = list()
    for cls in CPP_CLASSES:
        if ext in cls.m_extensions:
            foundCls.append(cls)
    return foundCls


class CppClass(CppClassBase):
    def __init__(
        self, 
        className:str, 
        baseClass:Union[str,CppClass,None]=None, 
        brief:CommentAny=None,
        hppIncludes:CppIncludesAny=None,
        cppIncludes:CppIncludesAny=None,
        extensions:ExtensionsAny=None,
        classVirtuality:CppClassVirtuality = CppClassVirtuality.CLASS_NORMAL,
    ) -> None:
        super().__init__(nameScope=className, baseClass=baseClass, hppIncludes=hppIncludes, cppIncludes=cppIncludes, extensions=extensions)
        self.m_classElements:list[CppClassElement] = list()
        self.m_comment:Comment = Comment(commentAny=brief)
        self.m_classVirtuality:CppClassVirtuality = classVirtuality

        self.m_antiLoopFlag:bool = False
        CPP_CLASSES.append(self)

        self.m_startBlock:WritableSet = WritableSet()
        ''' This block is printed right after the beginning of the class, after the first open brace '''

        self.m_endBlock:WritableSet = WritableSet()
        ''' This block is printed right before the end of the class, before the last closed brace '''

        self.m_postEndBlock:WritableSet = WritableSet()
        ''' This block is printed right after the end of the class, after the last closed brace '''

        self.m_inlineBlock:WritableSet = WritableSet()
        ''' This block is printed in the inline part '''

    def findSingleFieldByExtAllowNone(self, ext:str) -> Optional[CppField]:
        ''' Finds a single field that contains in its `m_extensions` the indicated extension key.
            It can be used to tag a field with a dummy extension and retrieve it later on.
            If the field is not found or multiple instances are found, an assertion is thrown.
            The search is extended to the base class as well.
        '''
        foundField:Optional[CppField] = None
        if self.m_baseClass is not None and isinstance(self.m_baseClass, CppClass):
            foundField = self.m_baseClass.findSingleFieldByExtAllowNone(ext=ext)

        for fld in self.m_classElements:
            if isinstance(fld, CppField):
                if ext in fld.m_extensions:
                    assert(foundField is None)
                    foundField = fld
        return foundField


    def findSingleFieldByExt(self, ext:str) -> CppField:
        ''' Finds a single field that contains in its `m_extensions` the indicated extension key.
            It can be used to tag a field with a dummy extension and retrieve it later on.
            If the field is not found or multiple instances are found, an assertion is thrown.
            The search is extended to the base class as well.
        '''
        foundField:Optional[CppField] = self.findSingleFieldByExtAllowNone(ext=ext)
        assert(foundField is not None)
        return foundField

    def findMultipleFields(self, ext:Optional[str]) -> list[CppField]:
        ''' Finds a zero or more field that contains in its `m_extensions` the indicated extension key.
            It can be used to tag fields with a dummy extension and retrieve them later on.
            If `ext` is None, it returns all fields.
            The search is extended to the base class as well.
        '''
        if self.m_baseClass is not None and isinstance(self.m_baseClass, CppClass):
            foundFields:list[CppField] = self.m_baseClass.findMultipleFields(ext=ext)
        else:
            foundFields = list()
        
        for fld in self.m_classElements:
            if isinstance(fld, CppField):
                if ext is None or ext in fld.m_extensions:
                    foundFields.append(fld)
        return foundFields

    def derivesFrom(self, otherClass:CppClass) -> bool:
        '''! Returns `True` if this class is or derives from `otherClass` '''
        assert(not self.m_antiLoopFlag) # Looping inheritance!
        if self==otherClass:return True
        if self.m_baseClass is not None and isinstance(self.m_baseClass, CppClass):
            self.m_antiLoopFlag = True
            ret:bool = self.m_baseClass.derivesFrom(otherClass=otherClass)
            self.m_antiLoopFlag = False
            return ret
        return False
    
    def getTopmostBaseClass(self) -> CppClass:
        if self.m_baseClass is not None and isinstance(self.m_baseClass, CppClass):
            return self.m_baseClass.getTopmostBaseClass()
        return self

    def findDerivedClasses(self) -> list[CppClass]:
        '''! Finds all the classes that derive from this one '''
        listOfDerivedClasses:list[CppClass] = list()
        for cppClass in CPP_CLASSES:
            if cppClass.derivesFrom(self):
                listOfDerivedClasses.append(cppClass)
        return listOfDerivedClasses


    def addClassElement(self, classElement:CppClassElement) -> CppClassElement:
        self.m_classElements.append(classElement)
        classElement.m_owningScope = self
        return classElement
        # print(f"[DEBUG] Class {self} add element {classElement}")

    def generateHppBody(self, writer:Writer, config:CppConfig) -> None:
        self._enterNameScope(config=config)
        self.m_comment.write(writer, config)
        writer.write(f"class {self.getCppUnqualifiedName()}")
        if self.m_baseClass is not None:
            if isinstance(self.m_baseClass, str):
                writer.write(f': public {self.m_baseClass}')
            else:
                writer.write(f': public {self.m_baseClass.getCppQualifiedName(otherScope=self)}') # type: ignore
        writer.writeRaw(' {\n')
        writer.incIndent()
        self.m_startBlock.write(writer, config)

        visibilitySequence:list[CppVisibility] = [
            CppVisibility.PRIVATE,
            CppVisibility.PROTECTED,
            CppVisibility.PUBLIC,
        ]

        if self.m_children:
            for child in self.m_children:
                writer.writeNL(child.m_visibilityWhenInClass.toStr()+":")
                writer.incIndent()
                child.generateHppBody(writer=writer, config=config)
                writer.decIndent()

        # First generate all constants (private, protected and public)
        for visibility in visibilitySequence:
            elements:list[CppClassElement] = self.__select(lambda elem: isinstance(elem,CppField) and elem.m_fieldConst, visibility=visibility)
            self.__generateElements(writer=writer, config=config, elements=elements)

        # Then generate all fields and methods grouped by private, protected and public
        for visibility in visibilitySequence:
            elements = list()
            elements += self.__select(lambda elem: isinstance(elem,CppField) and not elem.m_fieldConst, visibility=visibility)
            elements += self.__select(lambda elem: isinstance(elem,CppMethod), visibility=visibility)
            self.__generateElements(writer=writer, config=config, elements=elements)

        # First generate all custom code (private, protected and public)
        for visibility in visibilitySequence:
            elements = self.__select(lambda elem: isinstance(elem,CppClassCustom), visibility=visibility)
            self.__generateElements(writer=writer, config=config, elements=elements)

        self.m_endBlock.write(writer, config)
        writer.decIndent()
        writer.writeNL('};')
        self.m_postEndBlock.write(writer, config)
        self._exitNameScope(config=config)

    def generateHppInline(self, writer:Writer, config:CppConfig) -> None:
        super().generateHppInline(writer=writer, config=config)
        self.m_inlineBlock.write(writer=writer, config=config)
        for elem in self.m_classElements:
            elem.generateHppInline(writer=writer, config=config)

    def generateCppBody(self, writer:Writer, config:CppConfig) -> None:
        super().generateCppBody(writer, config)
        for elem in self.m_classElements:
            elem.generateCppBody(writer=writer, config=config)


    def getClassVirtuality(self)->CppClassVirtuality:
        '''! Calculates the class virtuality according to what has been declared and the methods '''
        thisClassVirtuality:CppClassVirtuality = self.m_classVirtuality
        baseClassVirtuality:CppClassVirtuality = CppClassVirtuality.CLASS_NORMAL
        if self.m_baseClass is not None and isinstance(self.m_baseClass, CppClass):
            baseClassVirtuality = self.m_baseClass.getClassVirtuality()
        
        # If the base class is not `CLASS_NORMAL`, then it must be virtual; therefore, we promote this class to
        # virtual as well. If also abstract, we don't know.
        if thisClassVirtuality == CppClassVirtuality.CLASS_NORMAL and baseClassVirtuality != CppClassVirtuality.CLASS_NORMAL:
            thisClassVirtuality = CppClassVirtuality.CLASS_VIRTUAL
        
        for elem in self.m_classElements:
            if isinstance(elem, CppMethod):
                if elem.m_virtuality == CppVirtuality.PURE_VIRTUAL:
                    thisClassVirtuality = CppClassVirtuality.CLASS_ABSTRACT
                elif elem.m_virtuality != CppVirtuality.NORMAL and thisClassVirtuality == CppClassVirtuality.CLASS_NORMAL:
                    thisClassVirtuality = CppClassVirtuality.CLASS_VIRTUAL
        return thisClassVirtuality
    
    def __calcChildrenOrder(self) -> None:
        order:int = 0
        for elem in self.m_classElements:
            order += 1
            elem.m_order = order

    def __select(self, elemSelect:Callable[[CppClassElement], bool], visibility:CppVisibility) -> list[CppClassElement]:
        elements:list[CppClassElement] = list()
        for elem in self.m_classElements:
            if elemSelect(elem) and elem.m_visibility == visibility:
                elements.append(elem)
        return elements


    def __generateElements(self, writer:Writer, config:CppConfig, elements:list[CppClassElement]) -> None:
        if not elements: return
        currVisibility:Optional[CppVisibility] = None

        for element in elements: 
            if currVisibility is None or currVisibility != element.m_visibility:
                if currVisibility is not None:
                    writer.decIndent()
                currVisibility = element.m_visibility
                writer.writeNL(f'\n{currVisibility.toStr()}:')
                writer.incIndent()
            element.generateHppBody(writer=writer, config=config)
        writer.decIndent()

    def needsCpp(self) -> bool:
        if super().needsCpp(): return True
        for elem in self.m_classElements:
            if elem.needsCpp(): return True
        return False

    def needsInline(self) -> bool:
        if super().needsInline(): return True
        for elem in self.m_classElements:
            if elem.needsInline(): return True
        return False

    def setupModuleConfig(self, moduleConfig:CppModuleConfig) -> None:
        '''! Operate on the accessible parts of the module to add includes, header parts and so on '''
        self.__addVirtualDestructorIfMissing()
        super().setupModuleConfig(moduleConfig=moduleConfig)
        for elem in self.m_classElements:
            elem.setupModuleConfig(moduleConfig=moduleConfig)
        
        for elem in self.m_classElements:
            elem.waterfallAdditionReset()
        
        repeat:bool = True
        while repeat:
            repeat = False
            for elem in self.m_classElements:
                if elem.waterfallAdditionOperate(moduleConfig.m_config):
                    repeat = True
        
        self.__calcChildrenOrder()

    def getDefaultConstructor(self, createIfMissing:bool=False) -> Optional[CppMethod]:
        for elem in self.m_classElements:
            if isinstance(elem, CppMethod):
                if elem.m_methodType==CppMethodType.CONSTRUCTOR and len(elem.m_params)==0:
                    return elem
        if createIfMissing:
            cppMethod:CppMethod = CppMethod(
                methodType=CppMethodType.CONSTRUCTOR,
                brief="Constructor",
                visibility=CppVisibility.PUBLIC,
            )
            self.addClassElement(cppMethod)
            return cppMethod
        return None

    def getDestructor(self, createIfMissing:bool=False) -> Optional[CppMethod]:
        for elem in self.m_classElements:
            if isinstance(elem, CppMethod):
                if elem.m_methodType==CppMethodType.DESTRUCTOR:
                    return elem
        if createIfMissing:
            cppMethod:CppMethod = CppMethod(
                methodType=CppMethodType.DESTRUCTOR,
                brief="Destructor",
                visibility=CppVisibility.PUBLIC,
            )
            self.addClassElement(cppMethod)
            return cppMethod
        return None

    def genDeletedCopyConstructor(self) -> None:
        '''! Creates a `= delete` copy constructor '''
        from metaprog.cpp.cpp_param import CppParam
        from metaprog.cpp.cpp_type import CppTypeClass

        self.addClassElement(
            CppMethod(
                methodType = CppMethodType.CONSTRUCTOR,
                brief='Copy constructor',
                inline=CppInline.NOT_IMPLEMENTED,
                visibility=CppVisibility.PROTECTED,
                code=None,
                virtuality=CppVirtuality.DELETED,
                params=[
                    CppParam(
                        paramName='other',
                        paramType=CppTypeClass(cppClass=self, reference=True, const=True),
                        mayBeUnused=True,
                    ),
                ],
            )
        )

    def genDeletedCopyAssignmentOperator(self) -> None:
        '''! Creates a `= delete` operator=  '''
        from metaprog.cpp.cpp_param import CppParam
        from metaprog.cpp.cpp_type import CppTypeClass

        self.addClassElement(
            CppMethod(
                methodType = CppMethodType.NORMAL,
                methodName = "operator=",
                brief='Copy assignment operator',
                inline=CppInline.NOT_IMPLEMENTED,
                visibility=CppVisibility.PROTECTED,
                code=None,
                virtuality=CppVirtuality.DELETED,
                returnType=CppTypeClass(cppClass=self, reference=True, const=False),
                params=[
                    CppParam(
                        paramName='other',
                        paramType=CppTypeClass(cppClass=self, reference=True, const=True),
                        mayBeUnused=True,
                    ),
                ],
            )
        )


    def __addVirtualDestructorIfMissing(self) -> None:
        '''! Verifies if the conditions for adding a virtual destructor are met '''
        cppClassVirtuality:CppClassVirtuality = self.getClassVirtuality()

        # Class is by no mean virtual, 
        if cppClassVirtuality == CppClassVirtuality.CLASS_NORMAL:
            return

        destructor:Optional[CppMethod] = self.getDestructor(createIfMissing=True)
        assert(destructor is not None)
        if destructor.m_virtuality != CppVirtuality.VIRTUAL:
            destructor.m_virtuality = CppVirtuality.VIRTUAL
            print(f"Making destructor virtual on C++ class {self.getCppQualifiedName()}")