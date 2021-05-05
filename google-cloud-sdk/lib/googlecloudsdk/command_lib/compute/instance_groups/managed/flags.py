# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Flags for the compute instance groups managed commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      location():label=LOCATION,
      location_scope():label=SCOPE,
      baseInstanceName,
      size,
      targetSize,
      instanceTemplate.basename(),
      autoscaled
    )
"""


def AddTypeArg(parser):
  parser.add_argument(
      '--type',
      choices={
          'opportunistic': 'Do not proactively replace instances. Create new '
                           'instances and delete old on resizes of the group.',
          'proactive': 'Replace instances proactively.',
      },
      default='proactive',
      category=base.COMMONLY_USED_FLAGS,
      help='Desired update type.')


def AddMaxSurgeArg(parser):
  parser.add_argument(
      '--max-surge',
      type=str,
      help=('Maximum additional number of instances that '
            'can be created during the update process. '
            'This can be a fixed number (e.g. 5) or '
            'a percentage of size to the managed instance '
            'group (e.g. 10%). Defaults to 0 if the managed '
            'instance group has stateful configuration, or to '
            'the number of zones in which it operates otherwise.'))


def AddMaxUnavailableArg(parser):
  parser.add_argument(
      '--max-unavailable',
      type=str,
      help=('Maximum number of instances that can be '
            'unavailable during the update process. '
            'This can be a fixed number (e.g. 5) or '
            'a percentage of size to the managed instance '
            'group (e.g. 10%). Defaults to the number of zones '
            'in which the managed instance group operates.'))


def AddMinReadyArg(parser):
  parser.add_argument(
      '--min-ready',
      type=arg_parsers.Duration(lower_bound='0s'),
      help=('Minimum time for which a newly created instance '
            'should be ready to be considered available. For example `10s` '
            'for 10 seconds. See $ gcloud topic datetimes for information '
            'on duration formats.'))


def AddReplacementMethodFlag(parser):
  parser.add_argument(
      '--replacement-method',
      choices={
          'substitute':
              'Delete old instances and create instances with new names.',
          'recreate':
              'Recreate instances and preserve the instance names. '
              'The instance IDs and creation timestamps might change.',
      },
      help="Type of replacement method. Specifies what action will be taken "
           "to update instances. Defaults to ``recreate'' if the managed "
           "instance group has stateful configuration, or to ``substitute'' "
           "otherwise.")


def AddForceArg(parser):
  parser.add_argument(
      '--force',
      action='store_true',
      help=('If set, accepts any original or new version '
            'configurations without validation.'))


INSTANCE_ACTION_CHOICES_WITHOUT_NONE = collections.OrderedDict([
    ('refresh', "Apply the new configuration without stopping instances, "
                "if possible. For example, use ``refresh'' to apply changes "
                "that only affect metadata or additional disks."),
    ('restart', 'Apply the new configuration without replacing instances, '
                'if possible. For example, stopping instances and starting '
                'them again is sufficient to apply changes to machine type.'),
    ('replace', "Replace old instances according to the "
                "``--replacement-method'' flag.")
])


def _CombineOrderedChoices(choices1, choices2):
  merged = collections.OrderedDict([])
  merged.update(choices1.items())
  merged.update(choices2.items())
  return merged


INSTANCE_ACTION_CHOICES_WITH_NONE = _CombineOrderedChoices(
    {'none': 'No action'}, INSTANCE_ACTION_CHOICES_WITHOUT_NONE)


def AddMinimalActionArg(parser, choices_with_none=True, default=None):
  choices = (INSTANCE_ACTION_CHOICES_WITH_NONE if choices_with_none
             else INSTANCE_ACTION_CHOICES_WITHOUT_NONE)
  parser.add_argument(
      '--minimal-action',
      choices=choices,
      default=default,
      help='Perform at least this action on each instance while updating. '
           'If the update requires a more disruptive action, then the more '
           'disruptive action is performed.')


def AddMostDisruptiveActionArg(parser, choices_with_none=True, default=None):
  choices = (INSTANCE_ACTION_CHOICES_WITH_NONE if choices_with_none
             else INSTANCE_ACTION_CHOICES_WITHOUT_NONE)
  parser.add_argument(
      '--most-disruptive-allowed-action',
      choices=choices,
      default=default,
      help='Perform at most this action on each instance while updating. '
           'If the update requires a more disruptive action than the one '
           'specified here, then the update fails and no changes are made.')


def AddUpdateInstancesArgs(parser):
  """Add args for the update-instances command."""
  parser.add_argument(
      '--instances',
      type=arg_parsers.ArgList(min_length=1),
      metavar='INSTANCE',
      required=True,
      help='Names of instances to update.')
  AddMinimalActionArg(parser, True, 'none')
  AddMostDisruptiveActionArg(parser, True, 'replace')
