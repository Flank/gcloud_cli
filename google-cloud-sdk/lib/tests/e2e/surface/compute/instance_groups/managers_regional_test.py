# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for regional instance group managers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib.surface.compute import e2e_managers_test_base
from tests.lib.surface.compute import e2e_test_base


class ManagedRegionalTest(e2e_managers_test_base.ManagedTestBase):

  def SetUp(self):
    self.prefix = 'managed-instance-group-regional'
    self.scope = e2e_test_base.REGIONAL

  def testInstanceGroupManagerCreationRegional(self):
    self.RunInstanceGroupManagerCreationTest()

  def testResizeRegional(self):
    self.RunResizeTest()

  def testSetInstanceTemplateAndRecreateRegional(self):
    self.RunSetInstanceTemplateAndRecreateTest()

  def testDeleteInstancesRegional(self):
    self.RunDeleteInstancesTest()

  def testAbandonInstancesRegional(self):
    self.RunAbandonInstancesTest()

  def testNamedPortsRegional(self):
    self.RunNamedPortsTest()

  def testInstanceGroupManagerCreationRegionalWithZoneSelection(self):
    self.RunInstanceGroupManagerCreationTest(scope_flag='--zones ' + self.zone)

if __name__ == '__main__':
  e2e_test_base.main()
