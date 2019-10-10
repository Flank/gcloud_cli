# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.services import unit_test_base


class CreateTest(unit_test_base.SUUnitTestBase):
  """Unit tests for services identity create command."""
  SERVICE_ACCOUNT_EMAIL = 'hello@world.com'
  UNIQUE_ID = 'hello-unique-id'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreate(self):
    self.ExpectGenerateServiceIdentityCall(self.SERVICE_ACCOUNT_EMAIL,
                                           self.UNIQUE_ID)

    self.Run('services identity create --service={0} --project={1}'.format(
        self.DEFAULT_SERVICE_NAME, self.PROJECT_NAME))
    self.AssertErrContains('Service identity created: hello@world.com')


if __name__ == '__main__':
  test_case.main()
