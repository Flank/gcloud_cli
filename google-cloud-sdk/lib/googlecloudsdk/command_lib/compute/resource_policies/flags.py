# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Flags for the compute resource-policies commands."""
from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags


def MakeResourcePolicyArg():
  return compute_flags.ResourceArgument(
      resource_name='resource policy',
      regional_collection='compute.resourcePolicies',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def AddCycleFrequencyArgs(parser, flag_suffix, start_time_help,
                          cadence_help, supports_hourly=False):
  """Add Cycle Frequency args for Resource Policies."""
  freq_group = parser.add_argument_group('Cycle Frequency Group.',
                                         required=True, mutex=True)
  freq_flags_group = freq_group.add_group('From flags')
  freq_flags_group.add_argument(
      '--start-time', required=True,
      type=arg_parsers.Datetime.Parse,
      help="""\
      {}. Valid choices are 00:00, 04:00, 08:00,12:00,
      16:00 and 20:00 UTC. See $ gcloud topic datetimes for information on
      time formats. For example, `--start-time="03:00-05"`
      (which gets converted to 08:00 UTC).
      """.format(start_time_help))
  cadence_group = freq_flags_group.add_group(mutex=True, required=True)
  cadence_group.add_argument(
      '--daily-{}'.format(flag_suffix),
      dest='daily_cycle',
      action='store_true',
      help='{} occurs daily at START_TIME.'.format(cadence_help))
  base.ChoiceArgument(
      '--weekly-{}'.format(flag_suffix),
      dest='weekly_cycle',
      choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
               'saturday', 'sunday'],
      help_str='{} occurs weekly on WEEKLY_WINDOW at START_TIME.'.format(
          cadence_help)).AddToParser(cadence_group)
  if supports_hourly:
    cadence_group.add_argument(
        '--hourly-{}'.format(flag_suffix),
        metavar='HOURS',
        dest='hourly_cycle',
        type=arg_parsers.BoundedInt(lower_bound=1),
        help='{} occurs every n hours starting at START_TIME.'.format(
            cadence_help))

  freq_file_group = freq_group.add_group('From file')
  freq_file_group.add_argument(
      '--weekly-{}-from-file'.format(flag_suffix),
      dest='weekly_cycle_from_file',
      type=arg_parsers.BufferedFileInput(),
      help="""\
      A file which defines a weekly cadence with multiple days and start times.
      The format is a JSON/YAML file containing a list of objects with the
      following fields:

      day: Day of the week with the same choices as --weekly-window.
      startTime: Start time of the snapshot schedule with the same format
          as --start-time.
      """)


def AddCommonArgs(parser):
  parser.add_argument(
      '--description',
      help='An optional, textual description for the backend.')


def AddBackupScheduleArgs(parser):
  parser.add_argument(
      '--max-retention-days',
      required=True,
      type=arg_parsers.BoundedInt(lower_bound=1),
      help='Maximum number of days snapshot can be retained.')


def AddResourcePoliciesArgs(parser, action, required=False):
  parser.add_argument(
      '--resource-policies',
      metavar='RESOURCE_POLICY',
      type=arg_parsers.ArgList(),
      required=required,
      help=('A list of resource policy names to be {} the instance. '
            'The policies must exist in the same region as the instance.'
            .format(action)))
