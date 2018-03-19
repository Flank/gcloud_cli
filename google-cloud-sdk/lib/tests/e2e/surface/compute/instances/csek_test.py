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
"""Tests for customer supplied encryption keys."""

import logging
import os.path

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


CSEK_FILE_TEMPLATE = """
        [ {{ "uri": "https://www.googleapis.com/compute/{api}/\
projects/{project}/zones/{zone}/disks/{disk}",
             "key": "abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=",
             "key-type": "raw"}} ]
        """


class CsekTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.instance_names_used = []

  def GetInstanceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    self.instance_name = e2e_utils.GetResourceNameGenerator(
        prefix='compute-csekstart').next()
    self.instance_names_used.append(self.instance_name)
    self.csek_fname = os.path.join(self.CreateTempDir(), 'csek.json')

    with open(self.csek_fname, 'w') as f:
      f.write(CSEK_FILE_TEMPLATE.format(
          api='v1', project=self.Project(),
          zone=self.zone, disk=self.instance_name))

  def testInstanceCreateCsek(self):
    self.GetInstanceName()
    self.Run('compute instances create {0} --zone {1} --csek-key-file {2}'.
             format(self.instance_name, self.zone, self.csek_fname))
    self.AssertNewOutputContains(self.instance_name)

    self.Run('compute instances delete {0} --zone {1}'.format(
        self.instance_name, self.zone))

  def TearDown(self):
    logging.info('Starting TearDown (will delete instance if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')

if __name__ == '__main__':
  e2e_test_base.main()
