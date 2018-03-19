# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A command for testing how required/not-required arguments are handled."""

from googlecloudsdk.calliope import base


class Example(base.Command):
  """Test command for display_info and required/not-required arguments."""

  @staticmethod
  def _Flags(parser):
    parser.display_info.AddFormat('table(flags)')
    parser.display_info.AddAliases({'ALL': 'flags', 'FLAGS': 'Flags'})

  def Run(self, args):
    return []
