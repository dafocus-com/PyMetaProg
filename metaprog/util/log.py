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

import inspect

glob_errors:int = 0


def __callerInfo__()->str:
    frameInfo:inspect.FrameInfo = inspect.stack()[2]
    cls:str = ""
    if 'self' in frameInfo.frame.f_locals:
        cls = f'{frameInfo.frame.f_locals["self"].__class__.__name__}.'
    return cls+str(frameInfo.function)
    


def logError(what:str) -> None:
    global glob_errors
    print(f'[ERROR] {__callerInfo__()} - {what}')
    glob_errors += 1

def logInfo(what:str) -> None:
    print(f'[INFO] {__callerInfo__()} - {what}')

def getErrors() -> int:
    return glob_errors