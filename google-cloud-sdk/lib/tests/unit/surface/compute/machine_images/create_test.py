# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for the machine-images create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class MachineImagesCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testDefaultOptionsWithSingleMachineImage(self):
    self.make_requests.side_effect = [[
        self.messages.MachineImage(
            name='machine-image-1',
            status=self.messages.MachineImage.StatusValueValuesEnum.READY)
    ]]

    self.Run('compute machine-images create machine-image-1 '
             '--source-instance '
             '{compute_uri}/projects/my-project/zones/us-central3-a/'
             'instances/instance-2'.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.machineImages, 'Insert',
          self.messages.ComputeMachineImagesInsertRequest(
              machineImage=self.messages.MachineImage(
                  name='machine-image-1',
                  sourceInstance='{compute_uri}/projects/my-project/zones/'
                  'us-central3-a/instances/instance-2'.format(
                      compute_uri=self.compute_uri)),
              project='my-project'))],)

    # Check default output formatting
    self.AssertOutputEquals(
        """\
    NAME             STATUS
    machine-image-1  READY
    """,
        normalize_space=True)

  def testUriSupport(self):
    self.Run('compute machine-images create {compute_uri}/projects/my-project'
             '/global/machineImages/machine-image-1 '
             '--source-instance '
             '{compute_uri}/projects/my-project/zones/us-central3-a/'
             'instances/instance-2'.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.machineImages, 'Insert',
          self.messages.ComputeMachineImagesInsertRequest(
              machineImage=self.messages.MachineImage(
                  name='machine-image-1',
                  sourceInstance='{compute_uri}/projects/my-project/zones/'
                  'us-central3-a/instances/instance-2'.format(
                      compute_uri=self.compute_uri)),
              project='my-project'))],)

  def testDescription(self):
    self.Run('compute machine-images create machine-image-1 '
             '--description \'Tom B.\' '
             '--source-instance '
             '{compute_uri}/projects/my-project/zones/us-central3-a/'
             'instances/instance-2'.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.machineImages, 'Insert',
          self.messages.ComputeMachineImagesInsertRequest(
              machineImage=self.messages.MachineImage(
                  name='machine-image-1',
                  description='Tom B.',
                  sourceInstance='{compute_uri}/projects/my-project/zones/'
                  'us-central3-a/instances/instance-2'.format(
                      compute_uri=self.compute_uri)),
              project='my-project'))],)

  def testStorageLocation(self):

    self.Run('compute machine-images create machine-image-1 '
             '--storage-location us-central1 '
             '--source-instance '
             '{compute_uri}/projects/my-project/zones/us-central3-a/'
             'instances/instance-2'.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.machineImages, 'Insert',
          self.messages.ComputeMachineImagesInsertRequest(
              machineImage=self.messages.MachineImage(
                  name='machine-image-1',
                  storageLocations=['us-central1'],
                  sourceInstance='{compute_uri}/projects/my-project/zones/'
                                 'us-central3-a/instances/instance-2'.format(
                                     compute_uri=self.compute_uri)),
              project='my-project'
          ))],)

  def testGuestFlush(self):

    self.Run('compute machine-images create machine-image-1 '
             '--guest-flush '
             '--source-instance '
             '{compute_uri}/projects/my-project/zones/us-central3-a/'
             'instances/instance-2'.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.machineImages, 'Insert',
          self.messages.ComputeMachineImagesInsertRequest(
              machineImage=self.messages.MachineImage(
                  name='machine-image-1',
                  guestFlush=True,
                  sourceInstance='{compute_uri}/projects/my-project/zones/'
                                 'us-central3-a/instances/instance-2'.format(
                                     compute_uri=self.compute_uri)),
              project='my-project'
          ))],)

  def testCsekKey(self):
    private_key_fname = self.WriteKeyFile(machine_image=True)

    self.Run('compute machine-images create machine-image-1 '
             '--csek-key-file={key} '
             '--source-instance '
             '{compute_uri}/projects/my-project/zones/us-central3-a/'
             'instances/instance-2'.format(key=private_key_fname,
                                           compute_uri=self.compute_uri))
    self.CheckRequests(
        [(self.compute.machineImages, 'Insert',
          self.messages.ComputeMachineImagesInsertRequest(
              machineImage=self.messages.MachineImage(
                  name='machine-image-1',
                  machineImageEncryptionKey=self.messages.CustomerEncryptionKey(
                      rawKey='aFellowOfInfiniteJestOfMostExcellentFancy01='),
                  sourceInstance='{compute_uri}/projects/my-project/zones/'
                                 'us-central3-a/instances/instance-2'.format(
                                     compute_uri=self.compute_uri)),
              project='my-project'
          ))],)

  def testKmsKey(self):
    self.Run('compute machine-images create machine-image-1 '
             '--kms-key=disk-key --kms-location=global'
             ' --kms-project=key-project'
             ' --kms-keyring=disk-ring  --require-csek-key-create '
             '--source-instance '
             '{compute_uri}/projects/my-project/zones/us-central3-a/'
             'instances/instance-2'.format(compute_uri=self.compute_uri))
    self.CheckRequests(
        [(self.compute.machineImages, 'Insert',
          self.messages.ComputeMachineImagesInsertRequest(
              machineImage=self.messages.MachineImage(
                  name='machine-image-1',
                  machineImageEncryptionKey=self.messages.CustomerEncryptionKey(
                      kmsKeyName='projects/key-project/locations/global/'
                                 'keyRings/disk-ring/cryptoKeys/disk-key'),
                  sourceInstance='{compute_uri}/projects/my-project/zones/'
                                 'us-central3-a/instances/instance-2'.format(
                                     compute_uri=self.compute_uri)),
              project='my-project'
          ))],)

  def testCsekSourceDiskKey(self):
    private_key_fname = self.WriteKeyFile(machine_image=True)

    self.Run('compute machine-images create machine-image-1 '
             '--source-disk-csek-key csek-key-file={key},disk=https:'
             '//compute.googleapis.com/compute/alpha/projects/my-project/'
             'zones/central2-a/disks/hamlet '
             '--source-instance '
             '{compute_uri}/projects/my-project/zones/us-central3-a/'
             'instances/instance-2'.format(key=private_key_fname,
                                           compute_uri=self.compute_uri))
    self.CheckRequests(
        [(self.compute.machineImages, 'Insert',
          self.messages.ComputeMachineImagesInsertRequest(
              machineImage=self.messages.MachineImage(
                  name='machine-image-1',
                  sourceDiskEncryptionKeys=
                  [self.messages.SourceDiskEncryptionKey(
                      diskEncryptionKey=self.messages.CustomerEncryptionKey(
                          rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA='),
                      sourceDisk='https://compute.googleapis.com/compute/'
                                 'alpha/projects/my-project/'
                                 'zones/central2-a/disks/hamlet')],
                  sourceInstance='{compute_uri}/projects/my-project/zones/'
                                 'us-central3-a/instances/instance-2'.format(
                                     compute_uri=self.compute_uri)),
              project='my-project'
          ))],)

if __name__ == '__main__':
  test_case.main()
