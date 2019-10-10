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

"""Tests for the command_lib.meta.cache_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.meta import cache_util
from googlecloudsdk.core.resource import resource_printer
from tests.lib import calliope_test_base


def _GetSortKey(obj):
  return '<{}><{}><{}>'.format(
      obj.collection or '',
      obj.api_version or '',
      obj.module_path or '')


class ListAttachedCompletersTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.WalkTestCli('sdk5')
    self.cli = calliope_base.Command._cli_power_users_only

  def testListAttachedCompleters(self):
    completers = cache_util.ListAttachedCompleters(self.cli)
    resource_printer.Print(sorted(completers, key=_GetSortKey),
                           print_format='json')
    self.AssertOutputContains("""\
[
  {
    "api_version": null,
    "attachments": [
      {
        "arguments": [
          "--property"
        ],
        "command": "gcloud completers-attached"
      }
    ],
    "collection": null,
    "module_path": "googlecloudsdk.command_lib.config.completers:PropertiesCompleter",
    "type": "function"
  },
  {
    "api_version": null,
    "attachments": [
      {
        "arguments": [
          "--bogus"
        ],
        "command": "gcloud completers-attached"
      }
    ],
    "collection": "ERROR: API named [bogus] does not exist in the APIs map",
    "module_path": "googlecloudsdk.completers_attached:BogusCollectionCompleter",
    "type": "ListCommandCompleter"
  },
  {
    "api_version": null,
    "attachments": [
      {
        "arguments": [
          "instance"
        ],
        "command": "gcloud completers-attached"
      }
    ],
    "collection": "compute.instances",
    "module_path": "googlecloudsdk.completers_attached:InstancesCompleter",
    "type": "ListCommandCompleter"
  },
  {
    "api_version": "v1",
    "attachments": [
      {
        "arguments": [
          "--clone"
        ],
        "command": "gcloud completers-attached"
      }
    ],
    "collection": "compute.instances",
    "module_path": "googlecloudsdk.completers_attached:InstancesCompleterV1",
    "type": "ListCommandCompleter"
  }
]
""")
