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
from typing import Optional
from metaprog.util.comment_format import CommentFormat
#from metaprog.util.comment import COMMENT_BRIEF
from .cs_comment_format import CsCommentFormat

class CsConfig(Config):
    '''! Generation configuration '''
    def __init__(self, commentFormat:CommentFormat = CsCommentFormat()) -> None:
        super().__init__(commentFormat=commentFormat)
        
        self.m_csCurrentNameScope:Optional["CsNameScope"] = None # type: ignore
        ''' During generation, indicates that we are inside C# `namespace XYZ {...here...}` '''

        #self.m_commentFormat.m_mapCommands[COMMENT_BRIEF] = "summary"