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
from typing import Optional, Union, TypeAlias
from metaprog.util.writer import Writer
from metaprog.util.writable import Writable
from metaprog.util.writer_string import WriterString
from metaprog.util.writable_set import WritableSet, WritableSetAny
from metaprog.util.config import Config
from .py_config import PyConfig

PY_IMPORT_PRIORITY_DEFAULT:int = 0
PY_IMPORT_PRIORITY_FUTURE:int = -1000

class PyIncludeBase(Writable):
    '''! A single imp '''
    def __init__(self, moduleName:str, priority:int) -> None:
        # Set the priority
        self.m_priority:int = priority

        # Contains the name of the module to be imported
        self.m_moduleName:str = moduleName



class PyInclude(PyIncludeBase):
    '''! A single imp '''
    def __init__(self, moduleName:str, importAs:Optional[Union[str,list[str]]]=None, imports:Optional[list[Union[str,tuple[str,str]]]]=None, priority:int=PY_IMPORT_PRIORITY_DEFAULT) -> None:
        '''! Constructor
        @param moduleName   Name of the module in `import <moduleName>` or `from <moduleName> import ...`
        @param importAs     If not None, generates `import <moduleName> as <importAs>`
        @param imports      If set, it implements a `from <moduleName> import ...`
        @param priority     Priority in the ordering; the lowest goes first

        Example: `(moduleName=`MyModule`, imports=['FooBar', ('MyLongName', 'MLN')])`
        Generates: `from MyModule import FooBar, MyLongName as MLN`

        '''
        
        # Unless otherwise specified, set the priority of __future__ so it comes firsts
        if moduleName == '__future__' and priority == PY_IMPORT_PRIORITY_DEFAULT:
            priority = PY_IMPORT_PRIORITY_FUTURE
        
        super().__init__(priority=priority, moduleName=moduleName)

        # Contains a series of akas to import the module.
        #
        # For example:
        #
        # import foobar as foo, bar
        #
        self.m_importAs:set[str] = set()

        # Contains the names imported from the module.
        #
        # For example:
        #
        # from foobar import Foo, Bar as BB, Bar as CC
        #
        # The dictionary key is `<name>|<alias>`
        self.m_fromModuleImport:dict[str,tuple[str,Optional[str]]] = dict()

        # Set to true if the `import <module>` part is required.
        # This apply when the `from <module> import <names>...` is used. If set
        # to `True`, it will generate also the simple `import <module>` import.
        self.m_importModule:bool = (imports is None) or (importAs is not None)

        if importAs is not None:
            if isinstance(importAs, str):
                self.m_importAs.add(importAs)
            else:
                for imp in importAs:
                    self.m_importAs.add(imp)

        if imports is not None:
            self.addImports(imports=imports)

    def write(self, writer:Writer, config:Config) -> None:
        writer.writeNL(self.getAsString())

    def getAsString(self, endOfLine:str='\n') -> str:
        ret:str = ""
        symbols:list[str] = list()
        if len(self.m_fromModuleImport) > 0:
            for impPair in self.m_fromModuleImport.values():
                symbol:str = impPair[0]
                importAs:Optional[str] = impPair[1]
                if importAs is not None:
                    symbol += " as "+importAs
                symbols.append(symbol)
            ret += f'from {self.m_moduleName} import {", ".join(symbols)}'
        
        if self.m_importModule:
            if ret: ret += endOfLine
            asAddition:str = ''
            if self.m_importAs:
                asAddition += ' as '+', '.join(self.m_importAs)
            ret += f'import {self.m_moduleName}{asAddition}'
        return ret

    def addImports(self, imports:list[Union[str,tuple[str,str]]]) -> None:
        for imp in imports:
            if isinstance(imp, str):
                self._addImport(symbol=imp)
            else:
                self._addImport(symbol=imp[0], importAs=imp[1])

    def _addImport(self, symbol:str, importAs:Optional[str] = None) -> None:
        # Calculate the unique key
        uniqueKey:str = symbol
        if importAs is not None: uniqueKey += '|'+importAs

        if not uniqueKey in self.m_fromModuleImport:
            self.m_fromModuleImport[uniqueKey] = (symbol, importAs)

    def addImportAs(self, importAs:str) -> None:
        self.m_importModule = True
        self.m_importAs.add(importAs)

    def merge(self, other:PyInclude) -> None:
        assert(self.m_moduleName == other.m_moduleName)
        if other.m_importModule:
            self.m_importModule = True
        for symbolPair in other.m_fromModuleImport.values():
            self._addImport(symbol=symbolPair[0], importAs=symbolPair[1])
        for importAs in other.m_importAs:
            self.addImportAs(importAs=importAs)
        
    def __str__(self)->str:
        return self.getAsString(endOfLine='; ')


class PyIncludeText(PyIncludeBase):
    '''! Custom text inserted in between the imports. Use priority to place it correctly '''
    def __init__(self, moduleName:str, priority:int, code:WritableSetAny=None) -> None:
        super().__init__(moduleName=moduleName, priority=priority)
        self.m_code:WritableSet = WritableSet(code)

    def getAsString(self, config:PyConfig) -> str:
        writerString:WriterString = WriterString()
        self.write(writer=writerString, config=config)
        return str(writerString)

    def write(self, writer:Writer, config:Config) -> None:
        self.m_code.write(writer=writer, config=config)

PyIncludesAnyOne:TypeAlias = Union[str,PyIncludeBase,tuple[str,str]]

# PyIncludesAny is an array of a single item:
#
#  - a `PyIncludeBase` instance
#  - a string, that will become `import <text>`
#  - a tuple `(<a>, <b>)` that will become `from <a> import <b>`
#
PyIncludesAny:TypeAlias = Union[None, list[PyIncludesAnyOne], PyIncludesAnyOne]

class PyIncludes(Writable):
    '''! A set of imports '''
    def __init__(self, pyIncludesAny:PyIncludesAny=None) -> None:
        '''! Constructor
        @param imports   A list of imports that can be specified as 'foobar.h' or '<pytring>'
        '''
        self.m_imports:dict[str,PyIncludeBase] = dict()
        self.addAny(pyIncludesAny=pyIncludesAny)


    def add(self, moduleName:str, importAs:Optional[Union[str,list[str]]]=None, imports:Optional[list[Union[str,tuple[str,str]]]]=None, priority:int = PY_IMPORT_PRIORITY_DEFAULT) -> None:
        '''! Add an imp
        @param moduleName   Name of the module to be imported
        @param importAs     Set if the module is to be imported `as <something>`
        @param imports      List of names to be imported `from` the module
        '''
        self.addPyInclude(PyInclude(moduleName=moduleName, importAs=importAs, imports=imports, priority=priority))

    def addText(self, moduleName:str, priority:int=PY_IMPORT_PRIORITY_DEFAULT, code:WritableSetAny=None):
        self.addPyInclude(pyInclude=PyIncludeText(moduleName=moduleName, priority=priority, code=code))

    ## @brief Execute a `from <moduleName> import <name> [as <nameAs>]`
    def importFrom(self, moduleName:str, name:str, nameAs:Optional[str]=None) -> None:
        self.add(moduleName=moduleName, imports=[name if nameAs is None else (name, nameAs)])

    def addAnyOne(self, pyIncludesAnyOne:PyIncludesAnyOne) -> None:
        if isinstance(pyIncludesAnyOne, PyIncludeBase):
            self.addPyInclude(pyInclude=pyIncludesAnyOne)
        elif isinstance(pyIncludesAnyOne, tuple):
            self.importFrom(moduleName=pyIncludesAnyOne[0], name=pyIncludesAnyOne[1])
        else:
            self.add(moduleName=pyIncludesAnyOne)

    def addAny(self, pyIncludesAny:PyIncludesAny) -> None:
        if pyIncludesAny is None: return
        if isinstance(pyIncludesAny, list):
            for imp in pyIncludesAny:
                self.addAnyOne(pyIncludesAnyOne=imp)
        else:
            self.addAnyOne(pyIncludesAnyOne=pyIncludesAny)

    def addPyInclude(self, pyInclude:PyIncludeBase) -> None:
        if pyInclude.m_moduleName in self.m_imports:
            mergeTarget:PyIncludeBase = self.m_imports[pyInclude.m_moduleName]
            if isinstance(mergeTarget, PyInclude) and isinstance(pyInclude, PyInclude):
                # If two PyInclude have the same module name, merge them
                mergeTarget.merge(other=pyInclude)
            elif isinstance(mergeTarget, PyIncludeText) and isinstance(pyInclude, PyIncludeText):
                # If two texts have the same module name, drop one if identical or
                # issue an error in case they are different
                config:PyConfig = PyConfig()
                wrt1:WriterString = WriterString()
                wrt2:WriterString = WriterString()
                mergeTarget.m_code.write(writer=wrt1, config=config)
                mergeTarget.m_code.write(writer=wrt2, config=config)
                if wrt1.m_body != wrt2.m_body:
                    raise(ValueError(f'[ERROR] PyIncludes, adding twice the same `PyIncludeText` with same id `{pyInclude.m_moduleName}` but different contents'))
            else:
                raise(ValueError(f'[ERROR] PyIncludes, adding two incompatible entries with same id `{pyInclude.m_moduleName}`'))
        else:
            self.m_imports[pyInclude.m_moduleName] = pyInclude

    def merge(self, other:PyIncludes) -> None:
        for imp in other.m_imports.values():
            self.addPyInclude(pyInclude=imp)

    def write(self, writer:Writer, config:Config) -> None:
        assert(isinstance(config, PyConfig))
        for imp in self.getSortedPyIncludes():
            imp.write(writer, config)

    def getSortedPyIncludes(self) -> list[PyIncludeBase]:
        return sorted(self.m_imports.values(), key=lambda x: (x.m_priority, x.m_moduleName))

    def __str__(self)->str:
        if len(self.m_imports) == 0: return '<empty>'
        text:str = ""
        for imp in self.getSortedPyIncludes():
            text += '\n'+str(imp)
        return text
