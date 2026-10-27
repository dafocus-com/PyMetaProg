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
from metaprog.cs.cs_class import CsClass
from metaprog.cs.cs_field import CsField
from metaprog.cs.cs_enum import CsEnum
from metaprog.cs.cs_type import CsType, CsTypeString, CsTypeSimple, CsTypeClass, CsTypeMap, CsTypeVector 
from metaprog.cs.cs_method import CsMethod
from metaprog.cs.cs_param import CsParam
from metaprog.cs.cs_labels import CsVirtuality, CsClassVirtuality, CsVisibility
from metaprog.util.log import logError
from metaprog.util.config import env
from metaprog.util.writable_set import WritableSet, assertIsWritableSetAny
from .cs_generator_base import CsGeneratorBase

CS_PRINT_GENERATED:str = "CS_print_generated" # -> bool, created and written by this module to mark that has been processed

CS_PRINT_CODE:str = "cs_print_code"
'''
HOW TO USE `CS_PRINT_CODE`:

    CsField(
        # ...
        extensions={
            CS_PRINT_CODE:WritableSet(f' TBD ... write an exampe ---'),
        },
        # ...
    ))

Note: it can be placed in the `CsField` or the `CsType` object.
It can be placed in the `CsClass` object as well: in that case {CS_PRINT_FIELD} is not used.
    
'''

CS_PRINT_FIELD_DISABLE="cs_print_field_disable" # Add to disable print of the CsField


_CS_PRINT_OUT="CS_PRINT_OUT"
_CS_PRINT_FIELD="CS_PRINT_FIELD"

CS_PRINT_OUT=env(_CS_PRINT_OUT)
CS_PRINT_FIELD=env(_CS_PRINT_FIELD)


class CsPrintGenerator(CsGeneratorBase):
    #=============================================================================================
    def __init__(
            self,
            printName:str = 'Print',
            printChildrenName:str = 'PrintChildren',
        ) -> None:
        super().__init__()
        self.m_printName:str = printName
        self.m_printChildrenName:str = printChildrenName
        self.m_uniqueCounter:int = 0
   

    #=============================================================================================
    def _baseClassHasPrint(self, csClass:CsClass) -> bool:
        ''' CAN BE REDEFINED 
            Returns `True` if the `csClass` has a base class that implements print.
            By default considers deriving from a `CsClass` object as having a streamable base class.
        '''
        return csClass.m_baseClass is not None and isinstance(csClass.m_baseClass, CsClass)


    #=============================================================================================
    def decorateClasses(self) -> None:
        '''! Executes the decoration of the classes before generating the code '''
        for csClass in self.m_csClasses:
            self.__decorateClass(csClass)

    #=============================================================================================
    def __getIndName(self) -> str: # type: ignore
        '''! Get a uniquely but repeatable name for the indent stream '''
        self.m_uniqueCounter += 1
        return f'ind_{self.m_uniqueCounter:03d}'

    #=============================================================================================
    def __decorateClass(self, csClass:CsClass) -> None:
        '''! Decorate the single class with all the required code '''
        if CS_PRINT_GENERATED in csClass.m_extensions:
            logError(f"class `{csClass.getCsQualifiedName()}` generated more than once")
            return
        csClass.m_extensions[CS_PRINT_GENERATED] = True
        #logInfo(f"Decorating class `{csClass.getCsQualifiedName()}` for print - classVirtuality={csClass.getClassVirtuality()}")
        self.__decorateClassWithToString(csClass=csClass)
        self.__decorateClassWithPrint(csClass=csClass)
        self.__decorateClassWithPrintChildren(csClass=csClass)

    #=============================================================================================
    def __decorateClassWithToString(self, csClass:CsClass) -> None:
        '''! Add the master Print method '''
        if not self._baseClassHasPrint(csClass=csClass):
            toString:CsMethod = CsMethod(
                methodName="ToString",
                returnType=CsTypeString(),
                brief='Convert this object to a string',
                visibility=CsVisibility.PUBLIC,
                params=[
                ],
                virtuality=CsVirtuality.VIRTUAL_OVERRIDE
            )
            csClass.addClassElement(toString)
            toString.m_code.append(f'''\
                MetaProg.Indenter indenter = new();
                {self.m_printName}(indenter);
                return indenter.ToString();
            ''')

    #=============================================================================================
    def __decorateClassWithPrint(self, csClass:CsClass) -> None:
        '''! Add the master Print method '''
        if not self._baseClassHasPrint(csClass=csClass) or CS_PRINT_CODE in csClass.m_extensions:
            outParam:str = "indenter"
            isVirtual:bool = (csClass.getClassVirtuality() != CsClassVirtuality.CLASS_NORMAL)
            
            if isVirtual and self._baseClassHasPrint(csClass=csClass):
                methodVirtuality:CsVirtuality = CsVirtuality.VIRTUAL_OVERRIDE
            elif isVirtual:
                methodVirtuality = CsVirtuality.VIRTUAL
            else:
                methodVirtuality = CsVirtuality.NORMAL

            print:CsMethod = CsMethod(
                methodName=self.m_printName,
                brief='Print the object',
                visibility=CsVisibility.PUBLIC,
                params=[
                    CsParam(paramName=outParam, paramType=CsTypeSimple(simpleType="MetaProg.Indenter"), isRef=False, paramComment='Output indenter'),
                ],
                virtuality=methodVirtuality
            )
            csClass.addClassElement(print)
            if CS_PRINT_CODE in csClass.m_extensions:
                #------------------------------------------------------
                # CUSTOM PRINT CODE
                #------------------------------------------------------
                assertIsWritableSetAny(csClass.m_extensions[CS_PRINT_CODE])
                print.m_code.pushEnv(env={_CS_PRINT_OUT:outParam})
                print.m_code.append(csClass.m_extensions[CS_PRINT_CODE])
                print.m_code.popEnv()
            else:
                #------------------------------------------------------
                # AUTOMATIC PRINT CODE
                #------------------------------------------------------
                print.m_code.append(f'''\
                    {outParam}.AddText("{{");
                    {outParam}.IncIndent();
                    {self.m_printChildrenName}({outParam});
                    {outParam}.DecIndent();
                    {outParam}.AddText("\\n}}");
                ''')

    #=============================================================================================
    def __decorateClassWithPrintChildren(self, csClass:CsClass) -> None:
        outParam:str = "indenter"
        isVirtual:bool = (csClass.getClassVirtuality() != CsClassVirtuality.CLASS_NORMAL)
        
        if isVirtual and self._baseClassHasPrint(csClass=csClass):
            methodVirtuality:CsVirtuality = CsVirtuality.VIRTUAL_OVERRIDE
        elif isVirtual:
            methodVirtuality = CsVirtuality.VIRTUAL
        else:
            methodVirtuality = CsVirtuality.NORMAL

        print:CsMethod = CsMethod(
            methodName=self.m_printChildrenName,
            brief='Print all attributes',
            visibility=CsVisibility.PROTECTED,
            params=[
                CsParam(paramName=outParam, paramType=CsTypeSimple(simpleType="MetaProg.Indenter"), isRef=False, paramComment='Output indenter'),
            ],
            virtuality=methodVirtuality
        )
        csClass.addClassElement(print)

        
        if CS_PRINT_CODE in csClass.m_extensions:
            #------------------------------------------------------
            # CUSTOM PRINT CODE
            #------------------------------------------------------
            assertIsWritableSetAny(csClass.m_extensions[CS_PRINT_CODE])
            print.m_code.pushEnv(env={_CS_PRINT_OUT:outParam})
            print.m_code.append(csClass.m_extensions[CS_PRINT_CODE])
            print.m_code.popEnv()
        else:
            #------------------------------------------------------
            # AUTOMATIC PRINT CODE
            #------------------------------------------------------
            self.m_uniqueCounter = 0
            if self._baseClassHasPrint(csClass=csClass):
                assert(isinstance(csClass.m_baseClass, CsClass))
                print.m_code.append(f'base.{self.m_printChildrenName}({outParam});')

            for classElement in csClass.m_classElements:
                if isinstance(classElement, CsField) and not classElement.m_fieldConst:
                    print.m_code.append(f'{outParam}.AddText("\\n");')
                    if classElement.m_extensions.getValueOrNone(CS_PRINT_FIELD_DISABLE) is not None:
                        continue
                    print.m_code.append(f'{outParam}.AddText("{classElement.m_fieldName}: ");')
                    if CS_PRINT_CODE in classElement.m_extensions:
                        assertIsWritableSetAny(classElement.m_extensions[CS_PRINT_CODE])
                        print.m_code.pushEnv(env={_CS_PRINT_OUT:outParam, _CS_PRINT_FIELD:classElement.m_fieldName})
                        print.m_code.append(classElement.m_extensions[CS_PRINT_CODE])
                        print.m_code.popEnv()
                    else:
                        self._printCode(csClass=csClass, writableSet=print.m_code, outParam=outParam, fieldType=classElement.m_fieldType, fieldExpr=classElement.m_fieldName)

    #=============================================================================================
    def _printCode(self, csClass:CsClass, writableSet:WritableSet, outParam:str, fieldType:CsType, fieldExpr:str) -> None:
        if CS_PRINT_CODE in fieldType.m_extensions:
            assertIsWritableSetAny(fieldType.m_extensions[CS_PRINT_CODE])
            writableSet.pushEnv(env={_CS_PRINT_OUT:outParam, _CS_PRINT_FIELD:fieldExpr})
            writableSet.append(fieldType.m_extensions[CS_PRINT_CODE])
            writableSet.popEnv()
        elif isinstance(fieldType, CsTypeMap):
            self._mapPrintCode(csClass=csClass, outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CsTypeVector):
            self._vectorPrintCode(outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CsTypeString):
            self._stringPrintCode(outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CsTypeClass):
            self._classPrintCode(outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        else:                    
            writableSet.append(f'{outParam}.AddText(Convert.ToString({fieldExpr}));')

    #=============================================================================================
    def _vectorPrintCode(self, writableSet:WritableSet, outParam:str, fieldType:CsTypeVector, fieldExpr:str) -> None:
        item:str = self.__getIndName()
        if isinstance(fieldType.m_containedType, CsTypeClass):
            action:str = f'{item}.{self.m_printName}({outParam});\n'
        else:
            action = f'{outParam}.AddText(Convert.ToString({item}));\n'

        writableSet.append(f'''\
            {outParam}.AddText("[");
            {outParam}.IncIndent();
            bool {item}_isFirst = true;
            foreach (var {item} in {fieldExpr}) {{
                if ({item}_isFirst) {item}_isFirst=false;
                else {outParam}.AddText(",");
                {outParam}.AddNewLine();
                {action}
            }}
            {outParam}.DecIndent();
            {outParam}.AddText("\\n]");
        ''')

    #=============================================================================================
    def _mapPrintCode(self, csClass:CsClass, writableSet:WritableSet, outParam:str, fieldType:CsTypeMap, fieldExpr:str) -> None:
        item:str = self.__getIndName()
        if isinstance(fieldType.m_containedType, CsTypeClass):
            action:str = f'{item}.Value.{self.m_printName}({outParam});\n'
        else:
            action = f'{outParam}.AddText(Convert.ToString({item}.Value));\n'

        writableSet.append(f'''\
            {outParam}.AddText("[");
            {outParam}.IncIndent();
            foreach (KeyValuePair<{fieldType.m_keyType.toString(containerClass=csClass)}, {fieldType.m_containedType.toString(containerClass=csClass)}> {item} in {fieldExpr}) {{
                {outParam}.AddNewLine();
                {outParam}.AddText(Convert.ToString({item}.Key));
                {outParam}.AddText(": ");
                {action}
            }}
            {outParam}.DecIndent();
            {outParam}.AddText("\\n]");
        ''')

    #=============================================================================================
    def _stringPrintCode(self, writableSet:WritableSet, outParam:str, fieldType:CsTypeString, fieldExpr:str) -> None:
        writableSet.append(f'{outParam}.AddText(JsonSerializer.Serialize({fieldExpr}));')

    #=============================================================================================
    def _classPrintCode(self, writableSet:WritableSet, outParam:str, fieldType:CsTypeClass, fieldExpr:str) -> None:
        if isinstance(fieldType.m_csClass, CsEnum):
            writableSet.append(f'''\
                {outParam}.AddText({fieldExpr}.ToString());
            ''')
            return

        writableSet.append(f'{fieldExpr}.{self.m_printName}({outParam});')
