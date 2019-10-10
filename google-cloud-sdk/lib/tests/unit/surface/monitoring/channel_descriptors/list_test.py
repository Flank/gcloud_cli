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
"""Tests for `gcloud monitoring channel-descriptors list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.monitoring import base
from six.moves import range


class ChannelDescriptorsListTest(base.MonitoringTestBase):

  def _MakeDescriptors(self, project=None, n=10):
    project = project or self.Project()
    descriptors = []
    for i in range(n):
      type_name = 'type{}'.format(i)
      descriptor_name = ('projects/{0}/notificationChannelDescriptors/'
                         '{1}').format(project, type_name)
      descriptor = self.messages.NotificationChannelDescriptor(
          name=descriptor_name,
          type=type_name,
      )
      descriptors.append(descriptor)
    return descriptors

  def _ExpectList(self, descriptors, project=None, page_size=None,
                  page_token=None, next_page_token=None):
    project = project or self.Project()
    messages = self.messages  # Shortcut to respect line length limit.
    self.client.projects_notificationChannelDescriptors.List.Expect(
        messages.MonitoringProjectsNotificationChannelDescriptorsListRequest(
            name='projects/{}'.format(project),
            pageToken=page_token,
            pageSize=page_size,
        ),
        messages.ListNotificationChannelDescriptorsResponse(
            channelDescriptors=descriptors,
            nextPageToken=next_page_token))

  def testList(self):
    descriptors = self._MakeDescriptors()
    self._ExpectList(descriptors)

    results = self.Run('monitoring channel-descriptors list')

    self.assertEqual(descriptors, results)

  def testList_Uri(self):
    jobs = self._MakeDescriptors(n=3)
    self._ExpectList(jobs)
    properties.VALUES.core.user_output_enabled.Set(True)

    self.Run('monitoring channel-descriptors list --uri')

    self.AssertOutputEquals(
        """\
https://monitoring.googleapis.com/v3/projects/{project}/notificationChannelDescriptors/type0
https://monitoring.googleapis.com/v3/projects/{project}/notificationChannelDescriptors/type1
https://monitoring.googleapis.com/v3/projects/{project}/notificationChannelDescriptors/type2
        """.format(project=self.Project()), normalize_space=True)

  def testList_DifferentProject(self):
    project = 'other-project'
    descriptors = self._MakeDescriptors(project=project)
    self._ExpectList(descriptors, project=project)

    results = self.Run('monitoring channel-descriptors list '
                       '--project ' + project)

    self.assertEqual(descriptors, results)

  def testList_MultiplePages(self):
    descriptors = self._MakeDescriptors(n=10)
    self._ExpectList(descriptors[:5], page_size=5, next_page_token='token')
    self._ExpectList(descriptors[5:], page_size=5, page_token='token')

    results = self.Run('monitoring channel-descriptors list --page-size 5')

    self.assertEqual(descriptors, results)

if __name__ == '__main__':
  test_case.main()
