# -*- coding: utf-8 -*- #
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

"""Tests for the `gcloud meta cache completers list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import calliope_test_base


class ListCommandsTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.WalkTestCli('sdk5')

  def testListCommandDefaultFormat(self):
    self.Run('meta cache completers list')
    self.AssertOutputContains("""\
+------------------------------------------------------------------+----------------------+---------------------------------------------------------+-------------+
|                           MODULE_PATH                            |         TYPE         |                        COLLECTION                       | API_VERSION |
+------------------------------------------------------------------+----------------------+---------------------------------------------------------+-------------+
| googlecloudsdk.command_lib.config.completers:PropertiesCompleter | function             |                                                         |             |
+------------------------------------------------------------------+----------------------+---------------------------------------------------------+-------------+
    +----------------------------+------------+
    |          COMMAND           | ARGUMENTS  |
    +----------------------------+------------+
    | gcloud completers-attached | --property |
    +----------------------------+------------+
+------------------------------------------------------------------+----------------------+---------------------------------------------------------+-------------+
| googlecloudsdk.completers_attached:BogusCollectionCompleter      | ListCommandCompleter | ERROR: API named [bogus] does not exist in the APIs map |             |
+------------------------------------------------------------------+----------------------+---------------------------------------------------------+-------------+
    +----------------------------+-----------+
    |          COMMAND           | ARGUMENTS |
    +----------------------------+-----------+
    | gcloud completers-attached | --bogus   |
    +----------------------------+-----------+
+------------------------------------------------------------------+----------------------+---------------------------------------------------------+-------------+
| googlecloudsdk.completers_attached:InstancesCompleter            | ListCommandCompleter | compute.instances                                       |             |
+------------------------------------------------------------------+----------------------+---------------------------------------------------------+-------------+
    +----------------------------+-----------+
    |          COMMAND           | ARGUMENTS |
    +----------------------------+-----------+
    | gcloud completers-attached | instance  |
    +----------------------------+-----------+
+------------------------------------------------------------------+----------------------+---------------------------------------------------------+-------------+
| googlecloudsdk.completers_attached:InstancesCompleterV1          | ListCommandCompleter | compute.instances                                       | v1          |
+------------------------------------------------------------------+----------------------+---------------------------------------------------------+-------------+
    +----------------------------+-----------+
    |          COMMAND           | ARGUMENTS |
    +----------------------------+-----------+
    | gcloud completers-attached | --clone   |
    +----------------------------+-----------+
""")

  def testListCommandJsonFormat(self):
    self.Run('meta cache completers list --format=json')
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


if __name__ == '__main__':
  calliope_test_base.main()
