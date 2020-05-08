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

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base
import mock


class EnableVpcServiceControlsTest(unit_test_base.SNUnitTestBase):
  """Unit tests for services vpc-peerings enable VPC service controls command."""
  OPERATION_NAME = 'operations/abc.0000000000'
  NETWORK = 'hello'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testEnableVpcServiceControls_Success(self):
    self.ExpectEnableVpcServiceControls(self.NETWORK, self.OPERATION_NAME)
    self.ExpectOperation(self.OPERATION_NAME, poll_count=3)
    self.SetProjectNumber()

    self.Run(('services vpc-peerings enable-vpc-service-controls '
              '--service={0} --network={1}').format(self.service, self.NETWORK))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('finished successfully')

  def testEnableVpcServiceControls_WithDefaultService(self):
    self.service = 'servicenetworking.googleapis.com'
    self.ExpectEnableVpcServiceControls(self.NETWORK, self.OPERATION_NAME)
    self.ExpectOperation(self.OPERATION_NAME, poll_count=3)
    self.SetProjectNumber()

    self.Run('services vpc-peerings enable-vpc-service-controls --network={0}'
             .format(self.NETWORK))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('finished successfully')

  def testEnableVpcServiceControls_Async(self):
    self.ExpectEnableVpcServiceControls(self.NETWORK, self.OPERATION_NAME)
    self.SetProjectNumber()

    self.Run(
        ('services vpc-peerings enable-vpc-service-controls '
         '--service={0} --network={1} --async').format(self.service,
                                                       self.NETWORK))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('operation is in progress')

  def testEnableVpcServiceControls_AsyncWithDefaultService(self):
    self.service = 'servicenetworking.googleapis.com'
    self.ExpectEnableVpcServiceControls(self.NETWORK, self.OPERATION_NAME)
    self.SetProjectNumber()

    self.Run(('services vpc-peerings enable-vpc-service-controls '
              '--network={0} --async').format(self.NETWORK))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('operation is in progress')

  def testEnableVpcServiceControls_PermissionDenied(self):
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectEnableVpcServiceControls(self.NETWORK, None, error=server_error)
    self.SetProjectNumber()

    with self.assertRaisesRegex(
        exceptions.EnableVpcServiceControlsPermissionDeniedException,
        r'Error.'):
      self.Run(('services vpc-peerings enable-vpc-service-controls '
                '--service={0} --network={1}'.format(self.service,
                                                     self.NETWORK)))

  def SetProjectNumber(self):
    mock_get = self.StartObjectPatch(projects_api, 'Get')
    p = mock.Mock()
    p.projectNumber = self.PROJECT_NUMBER
    mock_get.return_value = p


if __name__ == '__main__':
  test_case.main()
