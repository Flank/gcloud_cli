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
"""Integration tests for creating/using/deleting instances."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class InstancesCreateDiskTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testInstanceCreationWithCreateDisk(self):
    self.GetInstanceName()
    self.Run('compute instances create {0} '
             '--create-disk size=10GB,name={0}-3,mode=rw,'
             'device-name=data,auto-delete=yes,image=debian-8 '
             '--create-disk size=10GB,name={0}-4,mode=rw,'
             'device-name=data-2,auto-delete=no '
             '--zone {1}'.format(self.instance_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertNewOutputContainsAll(
        ['deviceName: data', 'mode: READ_WRITE', 'deviceName: data-2'])


if __name__ == '__main__':
  e2e_test_base.main()
