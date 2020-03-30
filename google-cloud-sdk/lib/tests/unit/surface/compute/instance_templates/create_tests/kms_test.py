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
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateWithKmsTestGa(
    create_test_base.InstanceTemplatesCreateTestBase, parameterized.TestCase):
  GLOBAL_KMS_KEY = ('projects/key-project/locations/global/keyRings/my-ring/'
                    'cryptoKeys/my-key')
  GLOBAL_KMS_KEY_SAME_PROJECT = ('projects/my-project/locations/global/'
                                 'keyRings/my-ring/cryptoKeys/my-key')

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.global_kms_key = self.messages.CustomerEncryptionKey(
        kmsKeyName=self.GLOBAL_KMS_KEY)
    self.global_kms_key_in_same_project = self.messages.CustomerEncryptionKey(
        kmsKeyName=self.GLOBAL_KMS_KEY_SAME_PROJECT)

  def _verifyRequestsWithOnlyBootDisk(self, expected_key=None):
    m = self.messages

    if not expected_key:
      expected_key = self.global_kms_key

    disks = [
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            diskEncryptionKey=expected_key,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    ]

    self._verifyRequestsWithAttachedDisks(disks)

  def _verifyRequestsWithNonBootDisk(self, expected_key=None):
    m = self.messages

    if not expected_key:
      expected_key = self.global_kms_key

    disks = [
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            diskEncryptionKey=expected_key,
            initializeParams=m.AttachedDiskInitializeParams(
                diskName='disk-1',
                diskSizeGb=10,
                sourceImage=(self.compute_uri +
                             '/projects/my-project/global/images/'
                             'foo')),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    ]

    self._verifyRequestsWithAttachedDisks(disks)

  def _verifyRequestsWithAttachedDisks(self, disks):
    m = self.messages
    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=disks,
            machineType=create_test_base.DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[self._default_access_config],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default', scopes=create_test_base.DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        ))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testBootDiskWithKmsKey(self):
    self.Run("""
        compute instance-templates create template-1
          --boot-disk-kms-key projects/key-project/locations/global/keyRings/my-ring/cryptoKeys/my-key
        """)

    self._verifyRequestsWithOnlyBootDisk()

  def testBootDiskWithKmsKeyAsParts(self):
    self.Run("""
        compute instance-templates create template-1
          --boot-disk-kms-key my-key
          --boot-disk-kms-project key-project
          --boot-disk-kms-location global
          --boot-disk-kms-keyring my-ring
        """)

    self._verifyRequestsWithOnlyBootDisk()

  def testBootDiskWithKmsKeyAsPartsNoKeyRing(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'KMS cryptokey resource was not fully specified.'):
      self.Run("""
          compute instance-templates create template-1
            --boot-disk-kms-key my-key
            --boot-disk-kms-location global
          """)

  def testBootDiskWithKmsKeyAsPartsUnqualifiedKey(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'KMS cryptokey resource was not fully specified.'):
      self.Run("""
          compute instance-templates create template-1
            --boot-disk-kms-key my-key
          """)

  def testBootDiskWithKmsKeyAsPartsLocationOnly(self):
    with self.AssertRaisesArgumentError():
      self.Run("""
          compute instance-templates create template-1
            --boot-disk-kms-location global
          """)

  def testCreateNonBootDiskWithKmsKey(self):
    self.Run("""
        compute instance-templates create template-1
          --create-disk name=disk-1,image=foo,size=10GB,kms-key=projects/key-project/locations/global/keyRings/my-ring/cryptoKeys/my-key
        """)
    self._verifyRequestsWithNonBootDisk()

  def testCreateNonBootDiskWithKmsKeyAsParts(self):
    self.Run("""
        compute instance-templates create template-1
          --create-disk name=disk-1,image=foo,size=10GB,kms-key=my-key,kms-project=key-project,kms-location=global,kms-keyring=my-ring
        """)
    self._verifyRequestsWithNonBootDisk()

  def testCreateNonBootDiskWithKmsKeyAsPartsUseDefaultProject(self):
    self.Run("""
        compute instance-templates create template-1
          --create-disk name=disk-1,image=foo,size=10GB,kms-key=my-key,kms-location=global,kms-keyring=my-ring
         """)
    self._verifyRequestsWithNonBootDisk(
        expected_key=self.global_kms_key_in_same_project)

  def testCreateNonBootDiskWithKmsKeyAsPartsLocationOnly(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'KMS cryptokey resource was not fully specified.'):
      self.Run("""
          compute instance-templates create template-1
            --create-disk name=disk-1,image=foo,size=10GB,kms-location=global
          """)

  def testWithNoImageAndBootDiskKmsKeyOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-kms-key\] can only be used when creating a new boot '
        r'disk.'):
      self.Run("""
          compute instance-templates create template-1
            --disk boot=yes,name=my-disk
            --boot-disk-kms-key projects/key-project/locations/global/keyRings/my-ring/cryptoKeys/my-key
          """)

    self.CheckRequests()


class InstanceTemplatesCreateWithKmsTestBeta(
    InstanceTemplatesCreateWithKmsTestGa):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstanceTemplatesCreateWithKmsTestAlpha(
    InstanceTemplatesCreateWithKmsTestGa):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
