# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud monitoring channel-descriptors describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.monitoring import base


class ChannelDescriptorsDescribeTest(base.MonitoringTestBase):

  def _MakeDescriptor(self):
    descriptor_name = ('projects/{}/notificationChannelDescriptors/'
                       'email').format(self.Project())
    return self.messages.NotificationChannelDescriptor(
        name=descriptor_name,
        type='email',
    )

  def _ExpectDescribe(self, descriptor):
    messages = self.messages  # Shortcut to respect line length limit.
    self.client.projects_notificationChannelDescriptors.Get.Expect(
        messages.MonitoringProjectsNotificationChannelDescriptorsGetRequest(
            name=descriptor.name,
        ),
        descriptor)

  def testDescribe(self):
    descriptor = self._MakeDescriptor()
    self._ExpectDescribe(descriptor)

    output = self.Run('monitoring channel-descriptors describe email')
    self.assertEqual(descriptor, output)

  def testDescribe_Uri(self):
    descriptor = self._MakeDescriptor()
    self._ExpectDescribe(descriptor)
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')

    url = ('http://monitoring.googleapis.com/v3/projects/{}'
           '/notificationChannelDescriptors/email').format(self.Project())
    self.Run('monitoring channel-descriptors describe ' + url)

  def testDescribe_RelativeNameOverridesProjectProperty(self):
    descriptor = self._MakeDescriptor()
    self._ExpectDescribe(descriptor)
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')

    relative_name = ('projects/{}/notificationChannelDescriptors/'
                     'email').format(self.Project())
    self.Run('monitoring channel-descriptors describe ' + relative_name)


if __name__ == '__main__':
  test_case.main()
