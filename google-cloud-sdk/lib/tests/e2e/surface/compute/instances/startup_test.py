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
"""Integration tests for startup scripts."""

import logging
import os
import textwrap
import time

from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class StartupTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.instance_names_used = []

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')

  def GetInstanceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    prefix = 'gcloud-compute-test-instance'
    self.instance_name = e2e_utils.GetResourceNameGenerator(
        prefix=prefix).next()
    self.instance_names_used.append(self.instance_name)
    self.suffix = self.instance_name[len(prefix):]
    self.temp_dir = self.CreateTempDir(name=os.path.join('startup'))
    self.startup_script = textwrap.dedent(
        """\
        #!/bin/bash
        echo "TESTING STARTUP SCRIPT"
        echo "Suffix: {0}"
        """.format(self.suffix))
    self.startup_script_file = os.path.join(self.temp_dir, 'startup.sh')
    with open(self.startup_script_file, 'w') as f:
      f.write(self.startup_script)

  def testStartup(self):
    self.GetInstanceName()
    self._TestCreateInstanceWithStartup()
    self._TestSerialPortOutput()
    self.DeleteInstance(self.instance_name)

  def _TestCreateInstanceWithStartup(self):
    self.Run('compute instances create {0} --zone {1}'
             ' --metadata-from-file startup-script={2}'
             .format(self.instance_name, self.zone,
                     self.startup_script_file))
    self.Run('compute instances describe {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputContains('name: {0}'.format(self.instance_name),
                                 reset=False)
    self.AssertNewOutputContains('echo "Suffix: {0}"'.format(self.suffix))

  def _TestSerialPortOutput(self):
    # Check to see if instance has booted far enough for the instance to
    # check for startup scripts
    message = 'Found startup-script in metadata'
    self.assertTrue(self.WaitForBoot(self.instance_name, message, retries=20))

    time.sleep(5)  # Give time for startup script to run
    self.Run('compute instances get-serial-port-output {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputContains('startup-script: TESTING STARTUP SCRIPT',
                                 reset=False)
    self.AssertNewOutputContains('startup-script: Suffix: {0}'
                                 .format(self.suffix))


if __name__ == '__main__':
  e2e_test_base.main()
