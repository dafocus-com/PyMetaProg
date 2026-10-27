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
from metaprog.cpp.cpp_class import CppClass
from metaprog.cpp.cpp_field import CppField
from metaprog.cpp.cpp_enum_base import CppEnumBase
from metaprog.cpp.cpp_labels import CppClassVirtuality, CppVirtuality, CppInline, CppStaticity, CppVisibility
from metaprog.cpp.cpp_method import CppMethod
from metaprog.cpp.cpp_param import CppParam
from metaprog.cpp.cpp_type import CppType, CppTypeSharedPtr, CppTypeClass, CppTypeString, CppTypeBinary, CppTypeVector, CppTypeMap
from metaprog.util.log import logError
from metaprog.util.config import env
from metaprog.util.writable_set import assertIsWritableSetAny, WritableSet
from .cpp_generator_base import CppGeneratorBase

CPP_PRINT_GENERATED:str = "cpp_print_generated" # -> bool, created and written by this module to mark that has been processed

CPP_PRINT_CODE:str = "cpp_print_code"
'''
HOW TO USE `CPP_PRINT_CODE`:

    CppField(
        # ...
        extensions={
            CPP_PRINT_CODE:WritableSet(f'{CPP_PRINT_OUT} << "[" << {CPP_PRINT_FIELD} << "]";'),
        },
        # ...
    ))

Note: it can be placed in the `CppField` or the `CppType` object.
It can be placed in the `CppClass` object as well: in that case {CPP_PRINT_FIELD} is not used.
    
'''

CPP_PRINT_FIELD_DISABLE:str = "cpp_print_field_disable" # Add to disable print of the CppField


_CPP_PRINT_OUT:str = "CPP_PRINT_OUT"
_CPP_PRINT_FIELD:str = "CPP_PRINT_FIELD"

CPP_PRINT_OUT:str = env(_CPP_PRINT_OUT)
CPP_PRINT_FIELD:str = env(_CPP_PRINT_FIELD)


class CppPrintGenerator(CppGeneratorBase):
    #=============================================================================================
    def __init__(
            self,
            printName:str = 'print',
            printChildrenName:str = 'printChildren',
        ) -> None:
        super().__init__()
        self.m_printName:str = printName
        self.m_printChildrenName:str = printChildrenName
        self.m_fmtParam:str = "fmt"
        self.m_uniqueCounter:int = 0
   

    #=============================================================================================
    def _baseClassHasPrint(self, cppClass:CppClass)->bool:
        ''' CAN BE REDEFINED 
            Returns `True` if the `cppClass` has a base class that implements print.
            By default considers deriving from a `CppClass` object as having a streamable base class.
        '''
        return cppClass.m_baseClass is not None and isinstance(cppClass.m_baseClass, CppClass)


    #=============================================================================================
    def decorateClasses(self) -> None:
        '''! Executes the decoration of the classes before generating the code '''
        for cppClass in self.m_cppClasses:
            self.__decorateClass(cppClass)

    #=============================================================================================
    def __getIndName(self) -> str:
        '''! Get a uniquely but repeatable name for the indent stream '''
        self.m_uniqueCounter += 1
        return f'ind_{self.m_uniqueCounter:03d}'

    #=============================================================================================
    def __decorateClass(self, cppClass:CppClass) -> None:
        '''! Decorate the single class with all the required code '''
        if CPP_PRINT_GENERATED in cppClass.m_extensions:
            logError(f"class `{cppClass.getCppQualifiedName()}` generated more than once")
            return
        cppClass.m_extensions[CPP_PRINT_GENERATED] = True
        #logInfo(f"Decorating class `{cppClass.getCppQualifiedName()}` for print - classVirtuality={cppClass.getClassVirtuality()}")
        self.__decorateClassWithPrint(cppClass=cppClass)
        self.__decorateClassWithPrintChildren(cppClass=cppClass)

    #=============================================================================================
    def __decorateClassWithPrint(self, cppClass:CppClass) -> None:
        '''! Add the master Print method '''
        if not self._baseClassHasPrint(cppClass=cppClass) or CPP_PRINT_CODE in cppClass.m_extensions:
            outParam:str = "out"
            isVirtual:bool = (cppClass.getClassVirtuality() != CppClassVirtuality.CLASS_NORMAL)
            
            if isVirtual and self._baseClassHasPrint(cppClass=cppClass):
                methodVirtuality:CppVirtuality = CppVirtuality.VIRTUAL_OVERRIDE
            elif isVirtual:
                methodVirtuality = CppVirtuality.VIRTUAL
            else:
                methodVirtuality = CppVirtuality.NORMAL

            print:CppMethod = CppMethod(
                methodName=self.m_printName,
                brief='Print the object',
                inline=CppInline.INLINE_OUTSIDE,
                staticity=CppStaticity.DYNAMIC_CONST,
                visibility=CppVisibility.PUBLIC,
                params=[
                    CppParam(paramName=outParam, paramType="std::ostream&", hppIncludes=["iostream"], paramComment='Output stream', mayBeUnused=True),
                    CppParam(paramName=self.m_fmtParam, paramType="const dastd::fmt_print_t&", hppIncludes=["dastd/fmt_print.hpp"], paramComment='Preferred formatting', mayBeUnused=True, paramDefault='dastd::fmt_print_f::PRINT_PACKED'),
                ],
                virtuality=methodVirtuality
            )
            cppClass.addClassElement(print)
            if CPP_PRINT_CODE in cppClass.m_extensions:
                #------------------------------------------------------
                # CUSTOM PRINT CODE
                #------------------------------------------------------
                assertIsWritableSetAny(cppClass.m_extensions[CPP_PRINT_CODE])
                print.m_code.pushEnv(env={_CPP_PRINT_OUT:outParam})
                print.m_code.append(cppClass.m_extensions[CPP_PRINT_CODE])
                print.m_code.popEnv()
            else:
                #------------------------------------------------------
                # AUTOMATIC PRINT CODE
                #------------------------------------------------------
                cppClass.m_hppIncludes.add('dastd/ostream_indent.hpp')
                ind:str = self.__getIndName()
                print.m_code.append(f'''\
                    if ({self.m_fmtParam} == dastd::fmt_print_f::PRINT_INDENTED) {{
                        {outParam} << "{{";
                        dastd::ostream_indent {ind}({outParam});
                        {self.m_fmtParam}.configure({ind});
                        {self.m_printChildrenName}({ind}, {self.m_fmtParam});
                        {outParam} << std::endl << "}}";
                    }}
                    else {{
                        {self.m_printChildrenName}({outParam}, {self.m_fmtParam});
                    }}
                ''')

        if not self._baseClassHasPrint(cppClass=cppClass):
            cppClass.m_inlineBlock.append(f'inline std::ostream& operator<<(std::ostream& o, const {cppClass.getCppUnqualifiedName()}& c) {{c.print(o); return o;}}')

    #=============================================================================================
    def __decorateClassWithPrintChildren(self, cppClass:CppClass) -> None:
        outParam:str = "out"
        isVirtual:bool = (cppClass.getClassVirtuality() != CppClassVirtuality.CLASS_NORMAL)
        
        if isVirtual and self._baseClassHasPrint(cppClass=cppClass):
            methodVirtuality:CppVirtuality = CppVirtuality.VIRTUAL_OVERRIDE
        elif isVirtual:
            methodVirtuality = CppVirtuality.VIRTUAL
        else:
            methodVirtuality = CppVirtuality.NORMAL

        print:CppMethod = CppMethod(
            methodName=self.m_printChildrenName,
            brief='Print all attributes',
            inline=CppInline.INLINE_OUTSIDE,
            staticity=CppStaticity.DYNAMIC_CONST,
            visibility=CppVisibility.PROTECTED,
            params=[
                CppParam(paramName=outParam, paramType="std::ostream&", hppIncludes=["iostream"], paramComment='Output stream', mayBeUnused=True),
                CppParam(paramName=self.m_fmtParam, paramType="const dastd::fmt_print_t&", hppIncludes=["dastd/fmt_print.hpp"], paramComment='Preferred formatting', mayBeUnused=True, paramDefault='dastd::fmt_print_f::PRINT_PACKED'),
            ],
            virtuality=methodVirtuality
        )
        cppClass.addClassElement(print)

        
        if CPP_PRINT_CODE in cppClass.m_extensions:
            #------------------------------------------------------
            # CUSTOM PRINT CODE
            #------------------------------------------------------
            assertIsWritableSetAny(cppClass.m_extensions[CPP_PRINT_CODE])
            print.m_code.pushEnv(env={_CPP_PRINT_OUT:outParam})
            print.m_code.append(cppClass.m_extensions[CPP_PRINT_CODE])
            print.m_code.popEnv()
        else:
            #------------------------------------------------------
            # AUTOMATIC PRINT CODE
            #------------------------------------------------------
            self.m_uniqueCounter = 0
            if self._baseClassHasPrint(cppClass=cppClass):
                assert(isinstance(cppClass.m_baseClass, CppClass))
                print.m_code.append(f'{cppClass.m_baseClass.getCppQualifiedName(cppClass)}::{self.m_printChildrenName}({outParam}, {self.m_fmtParam});')
                require_space:bool = True
            else:
                require_space = False
            
            for classElement in cppClass.m_classElements:
                if isinstance(classElement, CppField) and not classElement.m_fieldConst:
                    if classElement.m_extensions.getValueOrNone(CPP_PRINT_FIELD_DISABLE) is not None:
                        continue

                    if require_space:
                        print.m_code.append(f'if ({self.m_fmtParam} == dastd::fmt_print_f::PRINT_INDENTED) {outParam} << std::endl; else {outParam} << " ";')
                    else:
                        require_space = True
                        print.m_code.append(f'if ({self.m_fmtParam} == dastd::fmt_print_f::PRINT_INDENTED) {outParam} << std::endl;')

                    printCodeBegin:str = f'{outParam} << "{classElement.m_fieldName}="'
                    print.m_code.append(f'{printCodeBegin};')
                    if CPP_PRINT_CODE in classElement.m_extensions:
                        assert(isinstance(classElement.m_extensions[CPP_PRINT_CODE],WritableSet))
                        print.m_code.pushEnv(env={_CPP_PRINT_OUT:outParam, _CPP_PRINT_FIELD:classElement.m_fieldName})
                        print.m_code.append(classElement.m_extensions[CPP_PRINT_CODE])
                        print.m_code.popEnv()
                    else:
                        self._printCode(writableSet=print.m_code, outParam=outParam, fieldType=classElement.m_fieldType, fieldExpr=classElement.m_fieldName)

    #=============================================================================================
    def _printCode(self, writableSet:WritableSet, outParam:str, fieldType:CppType, fieldExpr:str) -> None:
        if CPP_PRINT_CODE in fieldType.m_extensions:
            assertIsWritableSetAny(fieldType.m_extensions[CPP_PRINT_CODE])
            writableSet.pushEnv(env={_CPP_PRINT_OUT:outParam, _CPP_PRINT_FIELD:fieldExpr})
            writableSet.append(fieldType.m_extensions[CPP_PRINT_CODE])
            writableSet.popEnv()
        elif isinstance(fieldType, CppTypeMap):
            self._mapPrintCode(outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CppTypeVector):
            self._vectorPrintCode(outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CppTypeString):
            self._stringPrintCode(outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CppTypeBinary):
            self._binaryPrintCode(outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CppTypeSharedPtr):
            self._sharedPtrPrintCode(outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        elif isinstance(fieldType, CppTypeClass):
            self._classPrintCode(outParam=outParam, writableSet=writableSet, fieldType=fieldType, fieldExpr=fieldExpr)
        else:                    
            writableSet.append(f'{outParam} << {fieldExpr};')

    #=============================================================================================
    def _vectorPrintCode(self, writableSet:WritableSet, outParam:str, fieldType:CppTypeVector, fieldExpr:str) -> None:
        fieldType.m_includes.add('dastd/ostream_indent.hpp')
        iterator:str = '__iterator'
        ind:str = self.__getIndName()

        writableSet.append(f'''\
            dastd::ostream_indent {ind}({outParam}, ({self.m_fmtParam} == dastd::fmt_print_f::PRINT_INDENTED ? 1 : 0));
            {self.m_fmtParam}.configure({ind});
            {outParam} << "[";
        ''')
        writableSet.append(f'for(auto {iterator}={fieldExpr}.begin(); {iterator}!={fieldExpr}.end(); ++{iterator}) {{')
        writableSet.incIndent()

        writableSet.append(f'''\
            if ({self.m_fmtParam} == dastd::fmt_print_f::PRINT_INDENTED) {ind} << std::endl;
            else if ({iterator} != {fieldExpr}.begin()) {ind} << ",";
        ''')
        self._printCode(writableSet=writableSet, outParam=ind, fieldType=fieldType.m_containedType, fieldExpr=f'(*{iterator})')
        writableSet.decIndent()
        writableSet.append(f'''\
            }}
            if (({self.m_fmtParam} == dastd::fmt_print_f::PRINT_INDENTED) && (!{fieldExpr}.empty())) {outParam} << std::endl;
            {outParam} << "]";
        ''')

    #=============================================================================================
    def _mapPrintCode(self, writableSet:WritableSet, outParam:str, fieldType:CppTypeMap, fieldExpr:str) -> None:
        fieldType.m_includes.add('dastd/fmt_string.hpp')
        fieldType.m_includes.add('dastd/ostream_indent.hpp')
        iterator:str = '__iterator'
        ind:str = self.__getIndName()

        writableSet.append(f'''\
            dastd::ostream_indent {ind}({outParam}, ({self.m_fmtParam} == dastd::fmt_print_f::PRINT_INDENTED ? 1 : 0));
            {self.m_fmtParam}.configure({ind});
            {outParam} << "[";
        ''')
        writableSet.append(f'for(auto {iterator}={fieldExpr}.begin(); {iterator}!={fieldExpr}.end(); ++{iterator}) {{')
        writableSet.incIndent()
        writableSet.append(f'''\
            if ({self.m_fmtParam} == dastd::fmt_print_f::PRINT_INDENTED) {ind} << std::endl;
            else if ({iterator} != {fieldExpr}.begin()) {ind} << ",";
        ''')
        writableSet.append(f'{ind} << dastd::fmt_cq({iterator}->first) << "=";')
        self._printCode(writableSet=writableSet, outParam=ind, fieldType=fieldType.m_containedType, fieldExpr=f'({iterator}->second)')
        writableSet.decIndent()
        writableSet.append(f'''\
            }}
            if ({self.m_fmtParam} == dastd::fmt_print_f::PRINT_INDENTED) {outParam} << std::endl;
            {outParam} << "]";
        ''')

    #=============================================================================================
    def _stringPrintCode(self, writableSet:WritableSet, outParam:str, fieldType:CppTypeString, fieldExpr:str) -> None:
        fieldType.m_includes.add('dastd/fmt_string.hpp')
        writableSet.append(f'{outParam} << dastd::fmt_cq({fieldExpr});')

    #=============================================================================================
    def _binaryPrintCode(self, writableSet:WritableSet, outParam:str, fieldType:CppTypeBinary, fieldExpr:str) -> None:
        fieldType.m_includes.add('dastd/fmt_bin.hpp')
        writableSet.append(f'{outParam} << dastd::fmt_bin({fieldExpr}, dastd::fmt_bin_format::TWO_HEX_DIGITS_LC);')

    #=============================================================================================
    def _sharedPtrPrintCode(self, writableSet:WritableSet, outParam:str, fieldType:CppTypeSharedPtr, fieldExpr:str) -> None:
        
        writableSet.append(f'if (!{fieldExpr}) {outParam} << "null";')
        writableSet.append('else {')
        writableSet.incIndent()

        if fieldType.m_polymorphic:
            writableSet.append(f'{outParam} << "<" << {fieldExpr}->class_name() << "> ";')

        writableSet.append(f'{fieldExpr}->print({outParam}, {self.m_fmtParam});')
        writableSet.decIndent()
        writableSet.append('}')


    #=============================================================================================
    def _classPrintCode(self, writableSet:WritableSet, outParam:str, fieldType:CppTypeClass, fieldExpr:str) -> None:
        if isinstance(fieldType.m_cppClass, CppEnumBase):
            writableSet.append(f'''
                {outParam} << {fieldExpr};
            ''')
            return

        fieldType.m_includes.add('dastd/ostream_indent.hpp')
        writableSet.append(f'''
            {{
                if ({self.m_fmtParam} == dastd::fmt_print_f::PRINT_PACKED) {outParam} << "{{";
                {fieldExpr}.print({outParam}, {self.m_fmtParam});
                if ({self.m_fmtParam} == dastd::fmt_print_f::PRINT_PACKED) {outParam} << "}}";
            }}
        ''')
