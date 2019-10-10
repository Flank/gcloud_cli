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

"""Tests of the 'resource-descriptors' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base

v2 = core_apis.GetMessagesModule('logging', 'v2')


class ResourceDescriptorsListTest(base.LoggingTestBase):

  def SetUp(self):
    self._resource_descriptors = [
        v2.MonitoredResourceDescriptor(type='gce_instance'),
        v2.MonitoredResourceDescriptor(type='gae_app')]

  def _setExpect(self, page_size=None):
    self.mock_client_v2.monitoredResourceDescriptors.List.Expect(
        v2.LoggingMonitoredResourceDescriptorsListRequest(
            pageSize=page_size),
        v2.ListMonitoredResourceDescriptorsResponse(
            resourceDescriptors=self._resource_descriptors))

  def testListLimit(self):
    # This stops the command's Display() method from running.
    properties.VALUES.core.user_output_enabled.Set(False)

    self._setExpect(page_size=1)
    result = self.RunLogging('resource-descriptors list --limit 1')
    self.assertEqual(list(result), self._resource_descriptors[:1])

  def testList(self):
    # This stops the command's Display() method from running.
    properties.VALUES.core.user_output_enabled.Set(False)

    self._setExpect()
    result = self.RunLogging('resource-descriptors list')
    self.assertEqual(list(result), self._resource_descriptors)

  def testListNoPerms(self):
    self.mock_client_v2.monitoredResourceDescriptors.List.Expect(
        v2.LoggingMonitoredResourceDescriptorsListRequest(pageSize=None),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('resource-descriptors list')

  def testListNoProject(self):
    properties.VALUES.core.project.Set(None)
    # This command can run without a project.
    self._setExpect()
    self.RunLogging('resource-descriptors list')

  def testListNoAuth(self):
    self.RunWithoutAuth('resource-descriptors list')


if __name__ == '__main__':
  test_case.main()
