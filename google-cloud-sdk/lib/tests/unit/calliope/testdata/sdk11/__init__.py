# Copyright 2017 Google Inc. All Rights Reserved.
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
"""gcloud sdk tests super-group."""

import argparse

from googlecloudsdk.calliope import base


class Sdk(base.Group):
  """gcloud sdk tests super-group."""

  @staticmethod
  def Args(parser):
    # This hack makes -h hidden for the cli_tree tests. cli_tree does not
    # contain single char flags.
    for flag in parser.flag_args:
      if '-h' in flag.option_strings:
        flag.hidden = True
