# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for DM labels utility."""

from googlecloudsdk.api_lib.deployment_manager import dm_labels
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base


class DmLabelsTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for labels command functionality."""

  def testCreateLabels(self):
    # create subtest
    create_labels = {
        'key1': 'value1',
        'key2': 'value2',
    }
    labels = dm_labels.UpdateLabels(None,
                                    self.messages.DeploymentLabelEntry,
                                    update_labels=create_labels)
    expected = """\
[<DeploymentLabelEntry
 key: 'key1'
 value: 'value1'>, <DeploymentLabelEntry
 key: 'key2'
 value: 'value2'>]"""
    self.assertEqual(expected, str(labels))

  def testUpdateLabels(self):
    labels = [self.messages.DeploymentLabelEntry(key='key1', value='value1'),
              self.messages.DeploymentLabelEntry(key='key2', value='value2')]
    update_labels = {
        'key2': 'update2',
        'key3': 'value3',
    }
    remove_labels = [
        'key1',
    ]
    updated_labels = dm_labels.UpdateLabels(labels,
                                            self.messages.DeploymentLabelEntry,
                                            update_labels=update_labels,
                                            remove_labels=remove_labels)
    expected = """\
[<DeploymentLabelEntry
 key: 'key2'
 value: 'update2'>, <DeploymentLabelEntry
 key: 'key3'
 value: 'value3'>]"""
    self.assertEqual(expected, str(updated_labels))

  def testNoOpLabels(self):
    labels = [self.messages.DeploymentLabelEntry(key='key2', value='update2'),
              self.messages.DeploymentLabelEntry(key='key3', value='value3')]
    updated_labels = dm_labels.UpdateLabels(labels,
                                            self.messages.DeploymentLabelEntry)

    expected = """\
[<DeploymentLabelEntry
 key: 'key2'
 value: 'update2'>, <DeploymentLabelEntry
 key: 'key3'
 value: 'value3'>]"""

    self.assertEqual(expected, str(updated_labels))

  def testRemoveLabels(self):
    labels = [self.messages.DeploymentLabelEntry(key='key2', value='value2'),
              self.messages.DeploymentLabelEntry(key='key3', value='value3')]
    remove_labels = [
        'key2',
        'key3',
        'key4',
    ]
    updated_labels = dm_labels.UpdateLabels(labels,
                                            self.messages.DeploymentLabelEntry,
                                            remove_labels=remove_labels)
    expected = '[]'
    self.assertEqual(expected, str(updated_labels))


if __name__ == '__main__':
  test_case.main()


