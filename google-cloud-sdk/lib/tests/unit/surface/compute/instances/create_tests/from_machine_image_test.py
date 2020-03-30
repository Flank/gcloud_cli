# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateFromMachineImageBeta(
    create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testCreateFrommachineImage(self):
    m = self.messages

    self.Run('compute instances create instance-1 '
             '--zone central2-a '
             '--source-machine-image machine-image-1')

    self.CheckRequests(
        self.zone_get_request, self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  name='instance-1',
                  deletionProtection=False,
                  sourceMachineImage=(
                      'https://compute.googleapis.com/compute/{}/projects/'
                      'my-project/global/machineImages/machine-image-1'.format(
                          self.api_version))),
              project='my-project',
              zone='central2-a'))])

  def testCreateFrommachineImagewithKey(self):
    m = self.messages
    private_key_fname = self.WriteKeyFile(machine_image=True)

    self.Run(
        'compute instances create instance-1 '
        '--zone central2-a '
        '--source-machine-image machine-image-1 '
        '--source-machine-image-csek-key-file {0}'.format(private_key_fname))

    self.CheckRequests(
        self.zone_get_request, self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  name='instance-1',
                  deletionProtection=False,
                  sourceMachineImage=(
                      'https://compute.googleapis.com/compute/{}/projects/'
                      'my-project/global/machineImages/machine-image-1'.format(
                          self.api_version)),
                  sourceMachineImageEncryptionKey=m.CustomerEncryptionKey(
                      rawKey=('aFellowOfInfiniteJestOfMostExcellentFancy01='))),
              project='my-project',
              zone='central2-a'))])

  def testCreateFrommachineImagewithoutImage(self):
    private_key_fname = self.WriteKeyFile(machine_image=True)
    with self.AssertRaisesExceptionMatches(
        expected_exception=exceptions.RequiredArgumentException,
        expected_message='`--source-machine-image-csek-key-file` requires '
        '`--source-machine-image` to be specified`'):
      self.Run(
          'compute instances create instance-1 '
          '--zone central2-a '
          '--source-machine-image-csek-key-file {0}'.format(private_key_fname))


class InstancesCreateFromMachineImageAlpha(InstancesCreateFromMachineImageBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
