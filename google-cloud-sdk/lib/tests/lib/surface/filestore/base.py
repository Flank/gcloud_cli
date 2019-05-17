# -*- coding: utf-8 -*- #
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
"""Base class for all Cloud Filestore tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class CloudFilestoreUnitTestBase(sdk_test_base.WithFakeAuth,
                                 cli_test_base.CliTestBase):
  """Base class for Cloud Filestore unit tests that use fake auth and mocks."""

  def SetUpTrack(self, track):
    if track == calliope_base.ReleaseTrack.ALPHA:
      self.api_version = 'v1p1alpha1'
    elif track == calliope_base.ReleaseTrack.BETA:
      self.api_version = 'v1beta1'
    else:
      self.api_version = 'v1'
    self.track = track
    self.messages = core_apis.GetMessagesModule('file', self.api_version)
    self.mock_client = mock.Client(
        core_apis.GetClientClass('file', self.api_version),
        real_client=core_apis.GetClientInstance(
            'file', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def GetTestCloudFilestoreLocationsList(self):
    """Simulates listing multiple available locations."""
    return [
        self.messages.Location(
            name='projects/{}/locations/Location1'.format(self.Project())),
        self.messages.Location(
            name='projects/{}/locations/Location2'.format(self.Project())),
    ]

  def GetTestCloudFilestoreLocation(self):
    """Simulates describing an available location."""
    return self.messages.Location(name='My Cloud Filestore Location')

  def GetTestCloudFilestoreOperationsList(self):
    return [
        self.messages.Operation(
            name='projects/{}/locations/us-central1-c/operations/Operation1'
            .format(self.Project())),
        self.messages.Operation(
            name='projects/{}/locations/us-central1-c/operations/Operation2'
            .format(self.Project())),
    ]

  def GetTestCloudFilestoreOperation(self):
    return self.messages.Operation(name='My Cloud Filestore Operation')

  def GetTestCloudFilestoreInstance(self):
    return self.messages.Instance(name='My Cloud Filestore Instance')
