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

from pathlib import Path
from typing import Optional
import re

def autoNewline(text: str) -> str:
    '''! If the string is not empty and not terminated by newline, it terminates it with newline '''
    if len(text) == 0:
        return ''
    if text[-1] == '\n':
        return text
    return text+'\n'


def firstLetterLowerCase(s: str) -> str:
    return s[:1].lower() + s[1:] if s else ''


def firstLetterUpperCase(s: str) -> str:
    return s[:1].upper() + s[1:] if s else ''

def customRelativeTo(path: Path, base: Path) -> Path:
    path = Path(path).resolve()
    base = Path(base).resolve()

    try:
        return path.relative_to(base)
    except ValueError:
        # Manual fallback if relative_to fails
        path_parts = path.parts
        base_parts = base.parts

        # Find common prefix
        common = 0
        for p1, p2 in zip(path_parts, base_parts):
            if p1 != p2:
                break
            common += 1

        # Build relative path
        up = ['..'] * (len(base_parts) - common)
        down = list(path_parts[common:])
        return Path(*up, *down)


def libPath() -> Path:
    '''! Returns the path of the `lib` directory where fixed source files can be found '''
    return Path(__file__).parent.parent.parent / 'lib'


def writeIfChanged(targetFilePath:Path, text:str) -> bool:
    doWrite:bool = True
    readableFileName:str = str(targetFilePath.resolve())

    # Check if the target file is to be rewritten because changed
    if targetFilePath.is_file():
        with open(targetFilePath, "r", encoding="utf-8") as file:
            oldText:str = file.read()
        if oldText == text:
            doWrite = False
    
    if doWrite:
        dir: Path = targetFilePath.parent
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)
            print(f'Creating directory "{dir}"')

        with open(targetFilePath, "w", encoding="utf-8") as outFile:
            outFile.write(text)
        
        print(f'Written "{readableFileName}"')
    else:
        print(f'Skipped "{readableFileName}" (not changed)')
    return doWrite

def copyIfChanged(targetFilePath:Path, sourceFilePath:Path) -> bool:
    text:str = sourceFilePath.read_text(encoding="utf-8")
    return writeIfChanged(targetFilePath=targetFilePath, text=text)

def isValidIdentifier(candidate_ident:str) -> bool:
    '''! Makes sure a string is a valid C-like identifier '''
    matchResult:Optional[re.Match[str]] = re.search(r'^[A-Za-z_][A-Za-z0-9_]*$', candidate_ident)
    return (not matchResult is None)