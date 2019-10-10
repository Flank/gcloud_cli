# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests of the services_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from tests.lib.surface.services import unit_test_base


class WaitOperationTest(unit_test_base.SUUnitTestBase):
  """Unit tests for WaitOperation."""

  def testWaitOperation(self):
    """Test WaitOperation returns operation when successful."""
    op_name = 'operations/abc.0000000000'
    want = self.services_messages.Operation(name=op_name, done=True)
    self.ExpectOperation(op_name, 3)

    got = services_util.WaitOperation(op_name, serviceusage.GetOperation)

    self.assertEqual(got, want)
