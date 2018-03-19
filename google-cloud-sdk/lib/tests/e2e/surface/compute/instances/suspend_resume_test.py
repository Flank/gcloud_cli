# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Integration tests for suspending and resuming instances."""

import logging

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import log
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class SuspendResumeTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.instance_names_used = []

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')

  def GetInstanceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up.
    name = e2e_utils.GetResourceNameGenerator(prefix='compute-suspend').next()
    self.instance_names_used.append(name)
    return name

  def testInstanceSuspendResume(self):
    name = self.GetInstanceName()
    self.CreateInstance(name)
    self._TestSuspendInstance(name)
    self._TestResumeInstance(name)
    # Cleanup.
    self.DeleteInstance(name)
    self.Run('compute instances list --zones {0}'.format(self.zone))
    self.AssertNewOutputNotContains(name)

  def testInstanceSuspendWithDiscardTrue(self):
    name = self.GetInstanceName()
    self.CreateInstance(name)
    self._TestSuspendInstance(name, discard_local_ssd=True)
    self._TestResumeInstance(name)
    # Cleanup.
    self.DeleteInstance(name)
    self.Run('compute instances list --zones {0}'.format(self.zone))
    self.AssertNewOutputNotContains(name)

  # Note: This test invokes the Suspend API, which is still in Alpha and is
  # controlled by a GCE CM experiment whitelist.
  def _TestSuspendInstance(self, instance_name, discard_local_ssd=None):
    # Suspend action is currently in the Alpha track.
    discard_param = ('--discard-local-ssd' if discard_local_ssd else '')
    log.info('Invoking suspend with discard param: %s', discard_param)
    self.Run('compute instances suspend {0} --zone {1} {2}'
             .format(instance_name, self.zone, discard_param))
    self.Run('compute instances describe {0} --zone {1}'
             .format(instance_name, self.zone))
    self.AssertNewOutputContains('status: SUSPENDED')

  def _TestResumeInstance(self, instance_name):
    self.Run('compute instances resume {0} --zone {1}'
             .format(instance_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'
             .format(instance_name, self.zone))
    self.AssertNewOutputContains('status: RUNNING')

if __name__ == '__main__':
  e2e_test_base.main()
