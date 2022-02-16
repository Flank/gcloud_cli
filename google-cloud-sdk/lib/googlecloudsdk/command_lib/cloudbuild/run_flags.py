# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Set up flags for creating a PipelineRun/TaskRun."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def AddCreateFlags(parser):
  parser.add_argument(
      '--file',
      required=True,
      help='The YAML file to use as the PipelineRun/TaskRun configuration file.'
  )
  parser.add_argument(
      '--region',
      required=True,
      help='Cloud region where the PipelineRun/TaskRun is.')


def AddRunFlags(parser):
  """Add flags related to a run to parser."""
  parser.add_argument('RUN_ID', help='The ID of the PipelineRun/TaskRun/Build.')
  parser.add_argument(
      '--type',
      required=True,
      choices=[
          'pipelinerun',
          'taskrun',
          'build',
      ],
      default='none',
      help='Type of Run.')
  parser.add_argument(
      '--region',
      required=True,
      help='Cloud region where the PipelineRun/TaskRun/Build is.')
