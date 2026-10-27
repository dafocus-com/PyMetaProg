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

from .writer_string import WriterString
from .writable import Writable
from .config import Config
from pathlib import Path
from metaprog.util.tools import writeIfChanged

class SourceFile:
    '''! Implemennts a .cpp or .hpp file '''

    def __init__(self, filePath: Path) -> None:
        self.m_filePath: Path = filePath
        '''! Filepath of this file'''

        self.m_writables: list[Writable] = list()
        
    def write(self, config: Config) -> bool:
        '''! Write the file
        @return Returns `True` if written, `False` if target file did not change
        '''
        writer: WriterString = WriterString()

        # Write all the writables
        for writable in self.m_writables:
            writable.write(writer, config)

        return writeIfChanged(targetFilePath=self.m_filePath, text=writer.m_body)
