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
"""Integration tests for stopping and starting instances."""

from __future__ import absolute_import
from __future__ import unicode_literals
import logging

from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class StopStartTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.instance_names_used = []

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')

  def GetInstanceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    self.instance_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='compute-stopstart'))
    self.instance_names_used.append(self.instance_name)

  def testInstanceStopStart(self):
    self.GetInstanceName()
    self.CreateInstance(self.instance_name)
    self._TestStopInstance()
    self._TestStartInstance()
    self.DeleteInstance(self.instance_name)

  def _TestStopInstance(self):
    self.Run('compute instances stop {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputContains('status: TERMINATED')

  def _TestStartInstance(self):
    self.Run('compute instances start {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputContains('status: RUNNING')

if __name__ == '__main__':
  e2e_test_base.main()
