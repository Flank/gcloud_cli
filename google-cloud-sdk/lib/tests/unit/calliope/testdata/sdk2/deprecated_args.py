# -*- coding: utf-8 -*- #
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

"""actions.DeprecationAction test command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base


class DeprecatedArgs(base.Command):
  """actions.DeprecationAction test command."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--begin',
        help='Begin flag help.')
    parser.add_argument(
        '--deprecated-arg',
        action=actions.DeprecationAction('deprecated_arg',
                                         warn='This flag is messed up.'),
        help='Deprecated flag help.\n\nNote we have more to say about this. '
        'Run:\n\n  $ gcloud alpha container '
        'clusters update example-cluster --zone us-central1-a '
        '--additional-zones ""\n')
    parser.add_argument(
        '--removed-arg',
        action=actions.DeprecationAction('removed_arg', removed=True),
        help='Removed flag help. Run:\n\n  gcloud bar --removed-arg=foo')
    parser.add_argument(
        '--end',
        help='End flag help.')

  def Run(self, args):
    return None
