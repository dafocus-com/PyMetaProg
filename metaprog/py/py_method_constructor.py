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
from .py_config import PyConfig
from .py_method import PyMethod
from .py_param import PyParam
from .py_includes import PyIncludesAny
from .py_labels import PyVisibility, PyStaticity
from metaprog.util.comment import CommentAny
from metaprog.util.extensions import ExtensionsAny
from metaprog.util.writable_set import WritableSet, WritableSetAny
from metaprog.util.writer import Writer
from .py_type import PyTypeNone
from .py_field import PyField
from typing import Optional

class PyMethodConstructor(PyMethod):
    '''! Implementastion of the __init__ class constructor '''
    def __init__(self, 
            brief:CommentAny=None,
            code:WritableSetAny=None,
            preCode:WritableSetAny=None,
            params:list[PyParam]=list(),
            baseClassInitializers:list[str]=list(), # Base class constructor initializers
            pyIncludesAny:PyIncludesAny = None,
            extensions:ExtensionsAny = None,
        ):
        super().__init__(
            methodName = '__init__',
            returnType = PyTypeNone(),
            visibility = PyVisibility.PUBLIC, 
            brief = brief,
            staticity = PyStaticity.DYNAMIC,
            code = code,
            params = params,
            pyIncludesAny = pyIncludesAny,
            extensions = extensions,
        )
        self.m_baseClassInitializers:list[str] = baseClassInitializers
        self.m_preCode:WritableSet = WritableSet(preCode)

    def _writeImpl(self, writer:Writer, config:PyConfig) -> None:
        from .py_class import PyClass
        addPass:bool = True
        writer.incIndent()

        cls:Optional[PyClass] = self.getParentClass()
        assert(cls is not None)

        if len(self.m_baseClassInitializers):
            if cls.m_baseClass is None:
                print(f'[ERROR] In constructor, class `{cls.getPyQualifiedName()}` is not derived, thus can not have initializers')
                exit(1)

        # Add the pre-code
        if not self.m_preCode.empty(): 
            addPass = False
            self.m_preCode.write(writer=writer, config=config)

        # Add the fields initializers
        for field in cls.m_children:
            if isinstance(field, PyField):
                addPass = False
                field.addConstructorCode(writer=writer, config=config)

        if not self.m_code.empty(): 
            addPass = False
            self.m_code.write(writer=writer, config=config)

        # If no code has been provided, write `pass`
        if addPass:
            writer.writeNL('pass')
        writer.decIndent()
