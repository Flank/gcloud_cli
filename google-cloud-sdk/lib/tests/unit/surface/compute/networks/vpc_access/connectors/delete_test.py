# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests of 'gcloud compute networks vpc-access connectors delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.networks.vpc_access import base


class ConnectorsDeleteTestBeta(base.VpcAccessUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'v1beta1'

  def testConnectorsDelete(self):
    self._ExpectDelete()

    self.WriteInput('y')
    self.Run('compute networks vpc-access connectors delete {} --region={}'
             .format(self.connector_id, self.region_id))

    self.AssertErrContains('You are about to delete connector [{}] in [{}].'
                           .format(self.connector_id, self.region_id))
    self.AssertErrContains('Any associated data will be lost.')
    self.AssertErrContains('Delete request issued for: [{}]'
                           .format(self.connector_id))
    self.AssertErrContains('Deleted connector [{}].'.format(self.connector_id))

  def testConnectorsDelete_Async(self):
    self._ExpectDelete(is_async=True)

    self.WriteInput('y')
    self.Run(
        'compute networks vpc-access connectors delete {} '
        '--region={} --async'
        .format(self.connector_id, self.region_id))

    self.AssertErrContains('You are about to delete connector [{}] in [{}].'
                           .format(self.connector_id, self.region_id))
    self.AssertErrContains('Any associated data will be lost.')
    self.AssertErrContains('Delete request issued for: [{}]'
                           .format(self.connector_id))
    self.AssertErrContains('Check operation [{}] for status.'
                           .format(self.operation_id))

  def testConnectorsDelete_UsingRelativeConnectorName(self):
    self._ExpectDelete()

    self.WriteInput('y')
    self.Run('compute networks vpc-access connectors delete {} --region={}'
             .format(self.connector_id, self.region_id))

    self.AssertErrContains('You are about to delete connector [{}] in [{}].'
                           .format(self.connector_id, self.region_id))
    self.AssertErrContains('Any associated data will be lost.')
    self.AssertErrContains('Delete request issued for: [{}]'
                           .format(self.connector_id))
    self.AssertErrContains('Deleted connector [{}].'.format(self.connector_id))

  def _ExpectDelete(self, is_async=False):
    operation = self.messages.Operation(name=self.operation_relative_name)
    self.connectors_client.Delete.Expect(
        request=self.messages.VpcaccessProjectsLocationsConnectorsDeleteRequest(
            name=self.connector_relative_name),
        response=operation)

    if is_async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_client.Get.Expect(
        request=self.messages.VpcaccessProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)


class ConnectorsDeleteTestAlpha(ConnectorsDeleteTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'v1alpha1'


if __name__ == '__main__':
  test_case.main()
