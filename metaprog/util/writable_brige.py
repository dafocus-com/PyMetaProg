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

from .writer import Writer
from .writable import Writable
from .config import Config
from typing import Any, Callable

class WritableBridge(Writable):
    '''! Bridge that call a method on a generic object '''
    def __init__(self, obj:Any, method: Callable[[Any, Writer, Config], None]) -> None:
        super().__init__()
        self.m_obj:Any = obj
        self.m_method:Callable[[Any, Writer, Config], None] = method


    def write(self, writer:Writer, config:Config) -> None:
        (self.m_method)(self.m_obj, writer, config)

class WritableBridgeOnFunction(Writable):
    '''! Bridge that calls a functiton '''
    def __init__(self, method: Callable[[Writer, Config], None]) -> None:
        super().__init__()
        self.m_method:Callable[[Writer, Config], None] = method

    def write(self, writer:Writer, config:Config) -> None:
        (self.m_method)(writer, config)
        