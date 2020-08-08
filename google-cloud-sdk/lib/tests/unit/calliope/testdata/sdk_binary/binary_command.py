# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""gcloud sdk tests command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core.util import platforms


class StreamingOperation(
    binary_operations.StreamingBinaryBackedOperation):
  """Simple Streaming implementation."""

  def _ParseArgsForCommand(self, exec_type, exec_val=None, **kwargs):
    del kwargs  # Not used here, passed through.
    cmd = ['--a', exec_type]
    if exec_val:
      cmd.extend(['--b', exec_val])
    return cmd


@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.GA)
class RequireCoverage(calliope_base.BinaryBackedCommand):
  """gcloud sdk tests command."""

  @staticmethod
  def Args(parser):
    """Adds args for this command."""

    parser.add_argument(
        'exec_mode',
        help='Execution Mode')

    parser.add_argument(
        '--exec-value',
        required=False,
        help='Execution Value')

    parser.add_argument(
        '--stream-only',
        required=False,
        action='store_true',
        help='Stream only or capture output.')

    parser.add_argument(
        '--result-handler',
        hidden=True,
        required=False,
        choices=['basic', 'structured'],
        default='basic',
        help='Result Handler'
    )

  def Run(self, args):
    exec_mode = args.exec_mode
    exec_value = args.exec_value
    platform = platforms.OperatingSystem.Current().file_name
    binary = 'basic_{}_go'.format(platform)
    capture = not args.stream_only
    operation = StreamingOperation(binary, capture_output=capture)
    return self._DefaultOperationResponseHandler(operation(exec_type=exec_mode,
                                                           exec_val=exec_value))


