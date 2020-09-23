# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.api_lib.util import apis
from tests.lib import test_case

import mock


class PromoteVersionTest(test_case.TestCase):

  def SetUp(self):
    self.api_client = mock.Mock(spec=appengine_api_client.AppengineApiClient)
    self.messages = apis.GetMessagesModule('appengine', 'v1')
    type(self.api_client).messages = mock.PropertyMock(
        return_value=self.messages)

  def testVersionAlreadyServing(self):
    """Promoting a version that is already serving."""
    all_services = {}
    new_version = version_util.Version('prj1', 'svc1', 'v1')

    # New version is already deployed and serving.
    version_resource = self.messages.Version()
    version_resource.servingStatus = (
        self.messages.Version.ServingStatusValueValuesEnum.SERVING)
    self.api_client.GetVersionResource.return_value = version_resource

    version_util.PromoteVersion(all_services, new_version, self.api_client,
                                stop_previous_version=False)

    # Don't call StartVersion because it's already started.
    self.api_client.StartVersion.assert_not_called()

    self.api_client.SetDefaultVersion.assert_called_once_with('svc1', 'v1')

  def testVersionResourceNonexistent(self):
    """Promoting a version whose current status cannot be determined."""
    all_services = {}
    new_version = version_util.Version('prj1', 'svc1', 'v1')

    # Fail to lookup a Version resource, so the code doesn't know whether the
    # version is currently serving.
    self.api_client.GetVersionResource.return_value = None

    version_util.PromoteVersion(all_services, new_version, self.api_client,
                                stop_previous_version=False)

    # Don't call StartVersion because we're not sure it's necessary.
    self.api_client.StartVersion.assert_not_called()

    self.api_client.SetDefaultVersion.assert_called_once_with('svc1', 'v1')

  def testErrorFetchingVersionResource(self):
    """An error occurs fetching the Version resource."""
    all_services = {}
    new_version = version_util.Version('prj1', 'svc1', 'v1')

    # Fail to lookup a Version resource, so the code doesn't know whether the
    # version is currently serving.
    self.api_client.GetVersionResource.side_effect = (
        apitools_exceptions.CommunicationError('failed'))

    version_util.PromoteVersion(all_services, new_version, self.api_client,
                                stop_previous_version=False)

    # Don't call StartVersion because we're not sure it's necessary.
    self.api_client.StartVersion.assert_not_called()

    self.api_client.SetDefaultVersion.assert_called_once_with('svc1', 'v1')

  def testStartStoppedVersion(self):
    """Verifies that a stopped version is started before promoting it."""
    all_services = {}
    new_version = version_util.Version('prj1', 'svc1', 'v1')

    # New version is already deployed but is STOPPED.
    version_resource = self.messages.Version()
    version_resource.servingStatus = (
        self.messages.Version.ServingStatusValueValuesEnum.STOPPED)
    self.api_client.GetVersionResource.return_value = version_resource

    version_util.PromoteVersion(all_services, new_version, self.api_client,
                                stop_previous_version=False)

    # Start the new version before promoting it.
    self.api_client.StartVersion.assert_called_once_with(
        'svc1', 'v1', block=True)

    self.api_client.SetDefaultVersion.assert_called_once_with('svc1', 'v1')


if __name__ == '__main__':
  test_case.main()
