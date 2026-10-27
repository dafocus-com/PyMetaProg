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

from metaprog.util.config import Config
from metaprog.util.comment_format import CommentFormat
from typing import Optional
from .py_comment_format import PyCommentFormat

class PyConfig(Config):
    '''! Generation configuration '''
    def __init__(self, commentFormat:CommentFormat = PyCommentFormat()) -> None:
        from .py_namescope import PyNameScope
        super().__init__(commentFormat=commentFormat)

        self.m_pyCurrentNameScope:Optional[PyNameScope] = None # type: ignore
        ''' During generation, indicates that we are inside a given python module ` '''
        
        