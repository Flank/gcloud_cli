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
"""This is a command for testing."""

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Command1(base.Command):
  """Test Boolean and StoreProperty flag combinations.

  Here are the details: there aren't any.

  ## EXAMPLES

  Don't use this example as an example for writing examples.
  """

  def Run(self, args):
    log.Print('are we cool? ' + str(args.coolstuff))
    if self.context.get('filtered', False):
      log.Print('filtered context')
    log.Print('trace_email is ' +
              str(properties.VALUES.core.trace_email.Get()))
    return properties.VALUES.core.trace_email.Get()

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--coolstuff',
        action='store_true',
        help=('is your stuff cool?'))
    parser.add_argument(
        '--trace-email',
        help=('trace_email'),
        action=actions.StoreProperty(properties.VALUES.core.trace_email))

    parser.add_argument(
        '--boolean-flag-false',
        default=False,
        help='Boolean flag default=false.',
        action='store_true')
    parser.add_argument(
        '--boolean-flag-none',
        default=None,
        help='Boolean flag default=none.',
        action='store_true')
    parser.add_argument(
        '--boolean-flag-true',
        default=True,
        help='Boolean flag default=true.',
        action='store_true')

    parser.add_argument(
        '--boolean-property-false-flag-false',
        default=False,
        help='Boolean property default=true and flag default=false.',
        action=actions.StoreBooleanProperty(
            properties.VALUES.core.log_http))
    parser.add_argument(
        '--boolean-property-false-flag-none',
        default=None,
        help='Boolean property default=true and flag default=none.',
        action=actions.StoreBooleanProperty(
            properties.VALUES.core.log_http))
    parser.add_argument(
        '--boolean-property-false-flag-true',
        default=True,
        help='Boolean property default=true and flag default=true.',
        action=actions.StoreBooleanProperty(
            properties.VALUES.core.log_http))

    parser.add_argument(
        '--boolean-property-true-flag-false',
        default=False,
        help='Boolean property default=true and flag default=false.',
        action=actions.StoreBooleanProperty(
            properties.VALUES.core.user_output_enabled))
    parser.add_argument(
        '--boolean-property-true-flag-none',
        default=None,
        help='Boolean property default=true and flag default=none.',
        action=actions.StoreBooleanProperty(
            properties.VALUES.core.user_output_enabled))
    parser.add_argument(
        '--boolean-property-true-flag-true',
        default=True,
        help='Boolean property default=true and flag default=true.',
        action=actions.StoreBooleanProperty(
            properties.VALUES.core.user_output_enabled))
