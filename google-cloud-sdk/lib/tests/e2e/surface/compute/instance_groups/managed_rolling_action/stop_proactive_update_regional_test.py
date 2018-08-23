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

"""Managed Instance Group Updater regional stop proactive update e2e test."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import e2e_managers_updater_test_base
from tests.lib.surface.compute import e2e_test_base


@test_case.Filters.skip('Failing', 'b/112466513')
class StopProactiveUpdateRegionalTest(
    e2e_managers_updater_test_base.InstanceGroupsUpdaterTestBase):
  # Keep this class a single-test-method - Updater tests are very slow

  def testStopProactiveUpdateInstancesRegional(self):
    self.prefix = (
        'managed-instance-group-updater-8')
    self.scope = e2e_test_base.REGIONAL
    self._RunStopProactiveUpdateInstancesTest(3, 0)

if __name__ == '__main__':
  e2e_test_base.main()
