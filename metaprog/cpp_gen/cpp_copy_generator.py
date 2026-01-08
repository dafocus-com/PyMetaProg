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
    Generates the copy constructor, `clone()` and the "operator=" methods.
'''
from metaprog.cpp.cpp_class import CppClass
from metaprog.cpp.cpp_field import CppField
from metaprog.cpp.cpp_method import *
from metaprog.cpp.cpp_labels import *
from metaprog.util.log import *
from metaprog.util.config import *
from metaprog.util.writable_set import WritableSet
from .cpp_generator_base import *

COPY_GENERATED:str="copy_generated" # -> bool, created and written by this module to mark that has been processed

CPP_COPY_FIELD_DISABLE:str="cpp_copy_field_disable" # Add to disable copy of the CppField


CPP_COPY_FIELD_POST_CODE:str="cpp_copy_field_post_code" # Code added after the copy/cloning of the field is completed
'''
HOW TO USE `CPP_COPY_FIELD_POST_CODE`:

    CppField(
        # ...
        extensions={
            CPP_COPY_FIELD_POST_CODE:WritableSet(f'{COPY_FIELD_DST}.doExtraStuff();'),
        },
        # ...
    ))

Note: it can be placed in the `CppField` or the `CppType` object.
    
'''

_COPY_FIELD_DST="COPY_FIELD_DST"
_COPY_FIELD_SRC="COPY_FIELD_SRC"

COPY_FIELD_DST=env(_COPY_FIELD_DST)
COPY_FIELD_SRC=env(_COPY_FIELD_SRC)

class CppCopyGenerator(CppGeneratorBase):
    #=============================================================================================
    def __init__(
            self,
            cloneName:str = "clone",
        ) -> None:
        super().__init__()
        self.m_cloneName:str = cloneName
   

    #=============================================================================================
    def _baseClassHasCopy(self, cppClass:CppClass)->bool:
        ''' CAN BE REDEFINED 
            Returns `True` if the `cppClass` has a base class that implements copy.
            By default considers deriving from a `CppClass` object as having a streamable base class.
        '''
        return cppClass.m_baseClass is not None and isinstance(cppClass.m_baseClass, CppClass)


    #=============================================================================================
    def decorateClasses(self) -> None:
        '''! Executes the decoration of the classes before generating the code '''
        for cppClass in self.m_cppClasses:
            self.__decorateClass(cppClass)

    #=============================================================================================
    def __decorateClass(self, cppClass:CppClass) -> None:
        '''! Decorate the single class with all the required code '''
        if COPY_GENERATED in cppClass.m_extensions:
            logError(f"class `{cppClass.getCppQualifiedName()}` generated more than once")
            return
        cppClass.m_extensions[COPY_GENERATED] = True
        #logInfo(f"Decorating class `{cppClass.getCppQualifiedName()}` for copy - classVirtuality={cppClass.getClassVirtuality()}")

        self.__generateCopyConstructor(cppClass=cppClass)
        self.__generateClone(cppClass=cppClass)
        self.__generateAssignOperator(cppClass=cppClass)


    #=============================================================================================
    # Generate the `clone` method
    #=============================================================================================
    def __generateClone(self, cppClass:CppClass) -> None:
        code:WritableSet = WritableSet()

        code.append(f'''\
            return std::make_shared<{cppClass.getCppUnqualifiedName()}>(*this);
        ''')

        isVirtual:bool = (cppClass.getClassVirtuality() != CppClassVirtuality.CLASS_NORMAL)
        
        hasBaseClass:bool = self._baseClassHasCopy(cppClass=cppClass)
        cppBaseClass:CppClass = cppClass.getTopmostBaseClass()

        if isVirtual and hasBaseClass:
            methodVirtuality:CppVirtuality = CppVirtuality.VIRTUAL_OVERRIDE
        elif isVirtual:
            methodVirtuality:CppVirtuality = CppVirtuality.VIRTUAL
        else:
            methodVirtuality:CppVirtuality = CppVirtuality.NORMAL

        cppClass.addClassElement(
            CppMethod(
                methodName=self.m_cloneName,
                staticity=CppStaticity.DYNAMIC_CONST,
                returnType=CppTypeSharedPtr(containedType=CppTypeClass(cppClass=cppBaseClass)),
                brief='Clone this object',
                inline=CppInline.INLINE_OUTSIDE,
                virtuality=methodVirtuality,
                code=code,
            )
        )



    #=============================================================================================
    # Generate the copy constructor
    #=============================================================================================
    def __generateCopyConstructor(self, cppClass:CppClass) -> None:
        sourceObj:str = "srcObj"

        code:WritableSet = WritableSet()

        baseClassInitializers:list[str]=list()
        if cppClass.m_baseClass is not None:
            baseClassInitializers.append(sourceObj)

        for cppField in cppClass.m_classElements:
            if isinstance(cppField, CppField) and not cppField.m_fieldConst and cppField.m_extensions.getValueOrNone(CPP_COPY_FIELD_DISABLE) is None:
                fieldExprSrc:str = f'{sourceObj}.{cppField.m_fieldName}'
                fieldExprDst:str = cppField.m_fieldName
                self.__generateAssignOperatorForField(cppType=cppField.m_fieldType, target=fieldExprDst, source=fieldExprSrc, code=code)
                self.__printCustomPostCode(writableSet=code, cppField=cppField, fieldExprDst=fieldExprDst, fieldExprSrc=fieldExprSrc)


        cppClass.addClassElement(
            CppMethod(
                methodType = CppMethodType.CONSTRUCTOR,
                brief='Copy constructor',
                inline=CppInline.INLINE_OUTSIDE,
                baseClassInitializers=baseClassInitializers,
                params=[
                    CppParam(
                        paramName=sourceObj,
                        paramType=CppTypeClass(cppClass=cppClass, reference=True, const=True),
                        mayBeUnused=True,
                    ),
                ],
                code=code,
            )
        )

        cppClass.getDefaultConstructor(createIfMissing=True)

    #=============================================================================================
    # Generate the `operator=` method
    #=============================================================================================
    def __generateAssignOperator(self, cppClass:CppClass) -> None:
        sourceObj:str = "srcObj"

        code:WritableSet = WritableSet()
        code.append(f'if ((&{sourceObj}) == this) return *this;')

        if self._baseClassHasCopy(cppClass=cppClass):
            code.append(f'{cppClass.getCppBaseQualifiedName()}::operator=({sourceObj});')

        for cppField in cppClass.m_classElements:
            if isinstance(cppField, CppField) and not cppField.m_fieldConst and cppField.m_extensions.getValueOrNone(CPP_COPY_FIELD_DISABLE) is None:
                fieldExprSrc:str = f'{sourceObj}.{cppField.m_fieldName}'
                fieldExprDst:str = cppField.m_fieldName
                self.__generateAssignOperatorForField(cppType=cppField.m_fieldType, target=fieldExprDst, source=fieldExprSrc, code=code)
                self.__printCustomPostCode(writableSet=code, cppField=cppField, fieldExprDst=fieldExprDst, fieldExprSrc=fieldExprSrc)

        code.append('return *this;')

        cppClass.addClassElement(
            CppMethod(
                methodName='operator=',
                returnType=CppTypeClass(cppClass=cppClass, reference=True, const=False),
                brief='Assignment operator',
                inline=CppInline.INLINE_OUTSIDE,
                params=[
                    CppParam(
                        paramName=sourceObj,
                        paramType=CppTypeClass(cppClass=cppClass, reference=True, const=True),
                        mayBeUnused=True,
                   ),
                ],
                code=code
            )
        )

    #=============================================================================================
    # Generate the `operator=` method
    #=============================================================================================
    def __generateAssignOperatorForField(self, cppType:CppType, target:str, source:str, code:WritableSet) -> None:
        if isinstance(cppType, CppTypeSimple):
            code.append(f"{target} = {source};")
            return

        if isinstance(cppType, CppTypeClass):
            assert(not cppType.m_const)
            assert(not cppType.m_reference)
            code.append(f"{target} = {source};")
            return

        if isinstance(cppType, CppTypeString):
            code.append(f"{target} = {source};")
            return

        if isinstance(cppType, CppTypeBinary):
            code.append(f"{target} = {source};")
            return

        if isinstance(cppType, CppTypeSharedPtr):
            code.append(f"""\
                {target}.reset();
                if ({source}) {target} = {source}->{self.m_cloneName}();
            """)
            return

        if isinstance(cppType, CppTypeVector):
            code.append(f"""\
                {target}.clear();
                {target}.reserve({source}.size());
                for(auto const& __item__: {source}) {{
            """)
            code.incIndent()
            code.append(f'auto& __elem__ = {target}.emplace_back();')
            self.__generateAssignOperatorForField(cppType=cppType.m_containedType, target='__elem__', source='__item__', code=code)
            code.decIndent()
            code.append(f"""\
                }}
            """)
            return

        if isinstance(cppType, CppTypeMap):
            code.append(f"""\
                {target}.clear();
                for(auto const& __item__: {source}) {{
            """)
            code.incIndent()
            code.append(f'auto __elem__ = {target}.emplace(std::piecewise_construct, std::forward_as_tuple(__item__.first), std::forward_as_tuple());\n')
            self.__generateAssignOperatorForField(cppType=cppType.m_containedType, target='__elem__.first->second', source='__item__.second', code=code)
            code.decIndent()
            code.append(f"""\
                }}
            """)
            return

        logError(f'Invalid type {cppType.__class__.__name__}')
        
    #=============================================================================================
    def __printCustomPostCode(self, writableSet:WritableSet, cppField:CppField, fieldExprDst:str, fieldExprSrc:str) -> None:
        writableSet.pushEnv(env={_COPY_FIELD_SRC:fieldExprSrc, _COPY_FIELD_DST:fieldExprDst})

        if CPP_COPY_FIELD_POST_CODE in cppField.m_extensions:
            assert(isinstance(cppField.m_extensions[CPP_COPY_FIELD_POST_CODE],WritableSet))
            writableSet.append(cppField.m_extensions[CPP_COPY_FIELD_POST_CODE])

        if CPP_COPY_FIELD_POST_CODE in cppField.m_fieldType.m_extensions:
            assert(isinstance(cppField.m_fieldType.m_extensions[CPP_COPY_FIELD_POST_CODE],WritableSet))
            writableSet.append(cppField.m_fieldType.m_extensions[CPP_COPY_FIELD_POST_CODE])

        writableSet.popEnv()
