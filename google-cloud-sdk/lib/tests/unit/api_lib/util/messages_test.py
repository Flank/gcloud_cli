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
"""Tests for googlecloudsdk.api_lib.util.messages."""
from __future__ import absolute_import
from __future__ import division

from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import messages as messages_util
from tests.lib import subtests
from tests.lib import test_case


class UpdateMessageTest(subtests.Base):
  """Tests messages.UpdateMessage."""

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('sql', 'v1beta4')
    self.update_message = messages_util.UpdateMessage

  def testUpdateWithBasicDiff(self):
    instance = self.messages.DatabaseInstance(
        name='test-instance',
        region='us-central',
        settings=self.messages.Settings(
            userLabels=None, availabilityType='ZONAL'))
    diff = {
        'name': 'different-test',
        'settings': {
            'availabilityType': 'REGIONAL'
        }
    }
    instance = self.update_message(instance, diff)

    # Ensure that the values in the diff have changed
    self.assertEqual(instance.name, 'different-test')
    self.assertEqual(instance.settings.availabilityType, 'REGIONAL')

    # Ensure that values outside the diff have not changed
    self.assertEqual(instance.region, 'us-central')

  def testUpdateWithBadProp(self):
    instance = self.messages.DatabaseInstance(
        name='test-instance',
        settings=self.messages.Settings(
            userLabels=None, availabilityType='ZONAL'))
    diff = {'settings': {'ohno': 234, 'availabilityType': 'REGIONAL'}}
    instance = self.update_message(instance, diff)

    # Test that the bad property didn't somehow get added
    self.assertFalse(hasattr(instance, 'ohno'))

    # Test that valid property got added
    self.assertEqual(instance.settings.availabilityType, 'REGIONAL')


if __name__ == '__main__':
  test_case.main()
