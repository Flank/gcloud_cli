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
"""Unit tests for service-management enable command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base


class DescribeTest(unit_test_base.SNUnitTestBase):
  """Unit tests for services vpc-peerings operations describe command."""
  OPERATION_NAME = 'operations/abc.0000000000'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testConnect(self):
    self.ExpectOperation(self.OPERATION_NAME, 0)

    self.Run('services vpc-peerings operations describe --name=%s' %
             self.OPERATION_NAME)
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('finished successfully')

  def testConnectPermissionDenied(self):
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectOperation(self.OPERATION_NAME, 0, server_error)

    with self.assertRaisesRegex(exceptions.OperationErrorException, r'Error.'):
      self.Run('services vpc-peerings operations describe --name=%s' %
               self.OPERATION_NAME)


class DescribeAlphaTest(DescribeTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class DescribeBetaTest(DescribeTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
