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
"""Integration tests for creating/using/deleting instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class InstancesWithContainerTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testInstanceCreationWithContainer(self):
    self.GetInstanceName()
    self.Run('compute instances create-with-container {0} '
             '--container-image=gcr.io/google-containers/busybox '
             '--zone {1}'.format(self.instance_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertOutputContains('containers')
    self.AssertOutputContains('image: gcr.io/google-containers/busybox')

  def testInstanceUpdateContainer(self):
    self.GetInstanceName()
    self.Run('compute instances create-with-container {0} '
             '--container-image=gcr.io/google-containers/busybox '
             '--zone {1}'.format(self.instance_name, self.zone))
    self.Run('compute instances update-container {0} --zone {1} '
             '--container-image=gcr.io/google-containers/addon-resizer'.format(
                 self.instance_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertOutputContains('containers')
    self.AssertOutputContains('image: gcr.io/google-containers/addon-resizer')

if __name__ == '__main__':
  e2e_test_base.main()
