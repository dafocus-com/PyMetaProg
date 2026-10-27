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
    Generates the `print()` code ontop of an existing class 
'''
from .py_generator_base import PyGeneratorBase
from metaprog.py.py_class import PyClass
from metaprog.py.py_enum import PyEnum
from metaprog.py.py_field import PyField
from metaprog.py.py_labels import PyVisibility, PyStaticity, PY_METAPROGLIB
from metaprog.py.py_method import PyMethod
from metaprog.py.py_namescope import PyNameScope
from metaprog.py.py_package import PyPackage
from metaprog.py.py_param import PyParam
from metaprog.py.py_type import PyType, PyTypeString, PyTypeClass, PyTypeMap, PyTypeVector, PyTypeOptional
from metaprog.util.config import env
from metaprog.util.log import logError
from metaprog.util.tools import libPath
from metaprog.util.writable_set import WritableSet, assertIsWritableSetAny, WritableSetValid
from typing import Optional, cast

PY_PRINT_GENERATED:str = "py_print_generated" # -> bool, created and written by this module to mark that has been processed

PY_PRINT_CODE:str = "py_print_code"
'''
HOW TO USE `PY_PRINT_CODE`:

    PyField(
        # ...
        extensions={
            PY_PRINT_CODE:WritableSet(f' TBD ... write an exampe ---'),
        },
        # ...
    ))

Note: it can be placed in the `PyField` or the `PyType` object.
It can be placed in the `PyClass` object as well: in that case {PY_PRINT_FIELD} is not used.
    
'''

PY_PRINT_FIELD_DISABLE="py_print_field_disable" # Add to disable print of the PyField


_PY_PRINT_OUT="PY_PRINT_OUT"
_PY_PRINT_FIELD="PY_PRINT_FIELD"

PY_PRINT_OUT=env(_PY_PRINT_OUT)
PY_PRINT_FIELD=env(_PY_PRINT_FIELD)


class PyPrintGenerator(PyGeneratorBase):
    #=============================================================================================
    def __init__(
            self,
            printName:str = 'print',
            printChildrenName:str = 'printChildren',
            metaProgTextModule:str = PY_METAPROGLIB,
        ) -> None:
        super().__init__()
        self.m_printName:str = printName
        self.m_printChildrenName:str = printChildrenName
        self.m_uniqueCounter:int = 0
        self.m_metaProgTextModule:str = metaProgTextModule

        self.m_metaProgText:dict[str, PyNameScope] = dict()
        self.m_metaProgTextStr:dict[str, PyNameScope] = dict()
   

    #=============================================================================================
    def _getMetaProgTextType(self, hostingPyNameScope:PyNameScope) -> PyType:
        package:Optional[PyPackage] = cast(PyPackage, hostingPyNameScope.upscanType(PyPackage))
        assert(package is not None)
        packageName:str = package.getPyQualifiedName()
        assert(packageName in self.m_metaProgText)
        #print(f"[DEBUG] PyPrintGenerator._getMetaProgTextType [{self.m_metaProgText[packageName].m_nameScope}]")
        return PyTypeClass(pyClass=self.m_metaProgText[packageName])

    #=============================================================================================
    def _getMetaProgTextStrClass(self, hostingPyNameScope:PyNameScope) -> PyType:
        package:Optional[PyPackage] = cast(PyPackage, hostingPyNameScope.upscanType(PyPackage))
        assert(package is not None)
        packageName:str = package.getPyQualifiedName()
        assert(packageName in self.m_metaProgTextStr)
        return PyTypeClass(pyClass=self.m_metaProgTextStr[packageName])

    #=============================================================================================
    def _baseClassHasPrint(self, pyClass:PyClass) -> bool:
        ''' CAN BE REDEFINED 
            Returns `True` if the `pyClass` has a base class that implements print.
            By default considers deriving from a `PyClass` object as having a streamable base class.
        '''
        return pyClass.m_baseClass is not None and isinstance(pyClass.m_baseClass, PyClass)


    #=============================================================================================
    def decorateClasses(self) -> None:
        '''! Executes the decoration of the classes before generating the code '''
        for pyClass in self.m_pyClasses:
            package:Optional[PyPackage] = cast(PyPackage, pyClass.upscanType(PyPackage))
            if not package:
                print(f'[ERROR] Can not execute `PyPrintGenerator` on class `{pyClass.getPyQualifiedName()} because it is not inside a package')
            packageName:str = package.getPyQualifiedName()
            if packageName not in self.m_metaProgText:
                self.m_metaProgText[packageName] = package.importExternal(moduleName=self.m_metaProgTextModule, importedName='MetaProgText', moduleSource=libPath() / 'py/MetaProgText.py')
                self.m_metaProgTextStr[packageName] = package.importExternal(moduleName=self.m_metaProgTextModule, importedName='MetaProgTextStr', moduleSource=libPath() / 'py/MetaProgText.py')

        for pyClass in self.m_pyClasses:
            self.__decorateClass(pyClass)

    #=============================================================================================
    def __getIndName(self) -> str: # type: ignore
        '''! Get a uniquely but repeatable name for the indent stream '''
        self.m_uniqueCounter += 1
        return f'ind_{self.m_uniqueCounter:03d}'

    #=============================================================================================
    def __decorateClass(self, pyClass:PyClass) -> None:
        '''! Decorate the single class with all the required code '''
        if PY_PRINT_GENERATED in pyClass.m_extensions:
            logError(f"class `{pyClass.getPyQualifiedName()}` generated more than once")
            return
        pyClass.m_extensions[PY_PRINT_GENERATED] = True
        #logInfo(f"Decorating class `{pyClass.getPyQualifiedName()}` for print - classVirtuality={pyClass.getClassVirtuality()}")
        printChildrenMethod:PyMethod = self.__decorateClassWithPrintChildren(pyClass=pyClass)
        self.__decorateClassWithToString(pyClass=pyClass)
        self.__decorateClassWithPrint(pyClass=pyClass, printChildrenMethod=printChildrenMethod)

    #=============================================================================================
    def __decorateClassWithToString(self, pyClass:PyClass) -> None:
        '''! Add the master Print method '''
        if not self._baseClassHasPrint(pyClass=pyClass):
            toString:PyMethod = PyMethod(
                methodName="__str__",
                returnType=PyTypeString(),
                brief='Convert this object to a string',
                visibility=PyVisibility.PUBLIC,
                params=[
                ],
            )
            
            metaProgTextStrClass:PyType = self._getMetaProgTextStrClass(hostingPyNameScope=pyClass)

            pyClass.addChild(toString)
            toString.m_code.append(f'''\
                indenter:{metaProgTextStrClass.typeHint(containerClass=pyClass)} = {metaProgTextStrClass.typeHint(containerClass=pyClass)}()
                self.{self.m_printName}(indenter=indenter)
                return str(indenter)
            ''')

    #=============================================================================================
    def __decorateClassWithPrint(self, pyClass:PyClass, printChildrenMethod:PyMethod) -> None:
        '''! Add the master Print method '''
        if not self._baseClassHasPrint(pyClass=pyClass) or PY_PRINT_CODE in pyClass.m_extensions:
            outParam:str = "indenter"

            print:PyMethod = PyMethod(
                methodName=self.m_printName,
                brief='Print the object',
                visibility=PyVisibility.PUBLIC,
                params=[
                    PyParam(paramName=outParam, paramType=self._getMetaProgTextType(hostingPyNameScope=pyClass), paramComment='Output indenter'),
                ],
            )
            pyClass.addChild(print)
            if PY_PRINT_CODE in pyClass.m_extensions:
                #------------------------------------------------------
                # CUSTOM PRINT CODE
                #------------------------------------------------------
                assertIsWritableSetAny(pyClass.m_extensions[PY_PRINT_CODE])
                print.m_code.pushEnv(env={_PY_PRINT_OUT:outParam})
                print.m_code.append(pyClass.m_extensions[PY_PRINT_CODE])
                print.m_code.popEnv()
            else:
                #------------------------------------------------------
                # AUTOMATIC PRINT CODE
                #------------------------------------------------------
                print.m_code.append(f'''\
                    {outParam}.addText("{{")
                    {outParam}.incIndent()
                    self.{printChildrenMethod.getPyUnqualifiedName()}(indenter={outParam})
                    {outParam}.decIndent()
                    {outParam}.addNewLine()
                    {outParam}.addText("}}")
                ''')

    #=============================================================================================
    def __decorateClassWithPrintChildren(self, pyClass:PyClass) -> PyMethod:
        outParam:str = "indenter"

        print:PyMethod = PyMethod(
            methodName=self.m_printChildrenName,
            brief='Print all attributes',
            visibility=PyVisibility.PROTECTED,
            params=[
                PyParam(paramName=outParam, paramType=self._getMetaProgTextType(hostingPyNameScope=pyClass), paramComment='Output indenter'),
            ],
        )
        pyClass.addChild(print)

        
        if PY_PRINT_CODE in pyClass.m_extensions:
            #------------------------------------------------------
            # CUSTOM PRINT CODE
            #------------------------------------------------------
            assertIsWritableSetAny(pyClass.m_extensions[PY_PRINT_CODE])
            print.m_code.pushEnv(env={_PY_PRINT_OUT:outParam})
            print.m_code.append(pyClass.m_extensions[PY_PRINT_CODE])
            print.m_code.popEnv()
        else:
            #------------------------------------------------------
            # AUTOMATIC PRINT CODE
            #------------------------------------------------------
            self.m_uniqueCounter = 0
            if self._baseClassHasPrint(pyClass=pyClass):
                assert(isinstance(pyClass.m_baseClass, PyClass))
                print.m_code.append(f'super().{print.getPyUnqualifiedName()}({outParam})')

            for classElement in pyClass.m_children:
                if isinstance(classElement, PyField) and classElement.m_staticity == PyStaticity.DYNAMIC:
                    if classElement.m_extensions.getValueOrNone(PY_PRINT_FIELD_DISABLE) is not None:
                        continue
                    print.m_code.append(f'{outParam}.addNewLine()')
                    print.m_code.append(f'{outParam}.addText("{classElement.getPyUnqualifiedName()}: ")')

                    # Detect custom print code for this field
                    customPrintCode:Optional[WritableSetValid] = None

                    if customPrintCode is None and PY_PRINT_CODE in classElement.m_extensions:
                        customPrintCode = classElement.m_extensions[PY_PRINT_CODE]

                    if customPrintCode is None and PY_PRINT_CODE in classElement.m_fieldType.m_extensions:
                        customPrintCode = classElement.m_extensions[PY_PRINT_CODE]

                    if customPrintCode is not None:
                        assertIsWritableSetAny(customPrintCode)
                        print.m_code.pushEnv(env={_PY_PRINT_OUT:outParam, _PY_PRINT_FIELD:classElement.getPyUnqualifiedName()})
                        print.m_code.append(customPrintCode)
                        print.m_code.popEnv()
                    else:
                        self._printCode(pyClass=pyClass, writableSet=print.m_code, outParam=outParam, fieldType=classElement.m_fieldType, fieldExpr=f'self.{classElement.getPyUnqualifiedName()}')
        return print

    #=============================================================================================
    def _printCode(self, pyClass:PyClass, writableSet:WritableSet, outParam:str, fieldType:PyType, fieldExpr:str) -> None:
        if isinstance(fieldType, PyTypeMap):
            self._mapPrintCode(pyClass=pyClass, outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, PyTypeVector):
            self._vectorPrintCode(outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, PyTypeString):
            self._stringPrintCode(pyClass=pyClass, outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, PyTypeClass):
            self._classPrintCode(outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, PyTypeOptional):
            self._optionalPrintCode(pyClass=pyClass, outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        else:                    
            writableSet.append(f'{outParam}.addText(str({fieldExpr}))')

    #=============================================================================================
    def _vectorPrintCode(self, writableSet:WritableSet, outParam:str, fieldType:PyTypeVector, fieldExpr:str) -> None:
        item:str = self.__getIndName()
        if isinstance(fieldType.m_containedType, PyTypeClass):
            action:str = f'{item}.{self.m_printName}({outParam})\n'
        else:
            action = f'{outParam}.addText(str({item}))\n'

        writableSet.append(f'''\
            # Printing a `list`
            if {fieldExpr}:
                {outParam}.addText("[")
                {outParam}.incIndent()
                {item}_isFirst:bool = True
                for {item} in {fieldExpr}:
                    if ({item}_isFirst): {item}_isFirst=False
                    else: {outParam}.addText(",")
                    {outParam}.addNewLine()
                    {action}
                {outParam}.decIndent()
                {outParam}.addNewLine()
                {outParam}.addText("]")
            else:
                {outParam}.addText("[]")
        ''')

    #=============================================================================================
    def _mapPrintCode(self, pyClass:PyClass, writableSet:WritableSet, outParam:str, fieldType:PyTypeMap, fieldExpr:str) -> None:
        item:str = self.__getIndName()
        keyName:str = f'{item}_key'
        valName:str = f'{item}_val'

        if isinstance(fieldType.m_containedType, PyTypeClass):
            action:str = f'{valName}.{self.m_printName}({outParam})\n'
        else:
            action = f'{outParam}.addText(str({valName}))\n'

        writableSet.append(f'''\
            # Printing a `map`
            if {fieldExpr}:
                {outParam}.addText("{{")
                {outParam}.incIndent()
                for {keyName}, {valName} in {fieldExpr}.items():
                    {outParam}.addNewLine()
                    {outParam}.addText(str({item}_key))
                    {outParam}.addText(": ")
                    {action}
                {outParam}.decIndent()
                {outParam}.addNewLine()
                {outParam}.addText("}}")
            else:
                {outParam}.addText("{{}}")
        ''')

    #=============================================================================================
    def _stringPrintCode(self, pyClass:PyClass, writableSet:WritableSet, outParam:str, fieldType:PyTypeString, fieldExpr:str) -> None:
        pyClass.m_pyIncludes.add(moduleName='json')
        writableSet.append(f'{outParam}.addText(json.dumps({fieldExpr}))')
        

    #=============================================================================================
    def _classPrintCode(self, writableSet:WritableSet, outParam:str, fieldType:PyTypeClass, fieldExpr:str) -> None:
        if isinstance(fieldType.m_pyClass, PyEnum):
            writableSet.append(f'''\
                # Printing a `enum`
                {outParam}.addText(str({fieldExpr}))
            ''')
            return

        writableSet.append(f'{fieldExpr}.{self.m_printName}({outParam})')

    #=============================================================================================
    def _optionalPrintCode(self, pyClass:PyClass, writableSet:WritableSet, outParam:str, fieldType:PyTypeOptional, fieldExpr:str) -> None:
        writableSet.append(f'''\
            if {fieldExpr} is None:
                {outParam}.addText('None')
            else:
        ''')
        writableSet.incIndent()
        self._printCode(pyClass=pyClass, writableSet=writableSet, outParam=outParam, fieldType=fieldType.m_containedType, fieldExpr=fieldExpr)
        writableSet.decIndent()
