# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.config import completers as config_completers
from googlecloudsdk.command_lib.util import completers


class BogusCollectionCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(BogusCollectionCompleter, self).__init__(
        collection='bogus.collection',
        list_command='completers-attached list --uri',
        timeout=123,
        **kwargs)


class InstancesCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InstancesCompleter, self).__init__(
        collection='compute.instances',
        list_command='completers-attached list --uri',
        timeout=123,
        **kwargs)


class InstancesCompleterV1(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InstancesCompleterV1, self).__init__(
        collection='compute.instances',
        api_version='v1',
        list_command='completers-attached list --uri',
        timeout=123,
        **kwargs)


class CompletersAttached(calliope_base.SilentCommand):
  """Attached completer test command."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'instance', help='Auxilio aliis.', completer=InstancesCompleter)
    parser.add_argument(
        '--clone', help='Auxilio aliis.', completer=InstancesCompleterV1)
    parser.add_argument(
        '--bogus', help='Auxilio aliis.', completer=BogusCollectionCompleter)
    parser.add_argument(
        '--property', help='Auxilio aliis.',
        completer=config_completers.PropertiesCompleter)

  def Run(self, args):
    return None
