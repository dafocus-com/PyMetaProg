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

import io

WINDOWS_LINE_ENDING: str = '\r\n'
UNIX_LINE_ENDING: str = '\n'


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
        doWrite: bool = True
        writer: WriterString = WriterString()

        # Write all the writables
        for writable in self.m_writables:
            writable.write(writer, config)

        newText: str = writer.m_body.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)

        # Check if the target file is to be rewritten because changed
        if self.m_filePath.is_file():
            with open(self.m_filePath, 'r') as file:
                oldText: str = file.read()
            oldText = oldText.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)
            if oldText == newText:
                doWrite = False
        
        readableFileName: str = str(self.m_filePath.resolve())
        if doWrite:
            dir: Path = self.m_filePath.parent
            if not dir.exists():
                dir.mkdir(parents=True, exist_ok=True)
                print(f'Creating directory "{dir}"')

            outFile: io.BufferedWriter = open(self.m_filePath, 'wb')
            outFile.write(newText.encode(encoding='utf-8'))
            print(f'Written "{readableFileName}"')
        else:
            print(f'Skipped "{readableFileName}" (not changed)')
        return doWrite
