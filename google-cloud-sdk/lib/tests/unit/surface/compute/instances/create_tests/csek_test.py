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

import re

from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateCsekTest(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testFoundInstNameKeyFile(self):
    private_key_fname = self.WriteKeyFile()
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --csek-key-file {0}
          --zone central2-a
        """.format(private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      msg.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          deviceName='hamlet',
                          initializeParams=msg.AttachedDiskInitializeParams(
                              sourceImage=create_test_base.DefaultImageOf(
                                  self.api_version)),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          diskEncryptionKey=msg.CustomerEncryptionKey(
                              rawKey=('abcdefghijklmnopqrstuv'
                                      'wxyz1234567890AAAAAAA=')),
                      )
                  ],
                  machineType=create_test_base.DefaultMachineTypeOf(
                      self.api_version),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version))
                  ],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=msg.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testFoundInstNameKeyFromStdin(self):
    self.WriteInput(self.GetKeyFileContent())
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --csek-key-file -
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      msg.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          deviceName='hamlet',
                          initializeParams=msg.AttachedDiskInitializeParams(
                              sourceImage=create_test_base.DefaultImageOf(
                                  self.api_version)),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          diskEncryptionKey=msg.CustomerEncryptionKey(
                              rawKey=('abcdefghijklmnopqrstuv'
                                      'wxyz1234567890AAAAAAA=')),
                      )
                  ],
                  machineType=create_test_base.DefaultMachineTypeOf(
                      self.api_version),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version))
                  ],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=msg.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testFoundInstNameKeyFileRsaWrappedKey(self):
    private_key_fname = self.WriteKeyFile(include_rsa_encrypted=True)

    with self.assertRaisesRegex(
        csek_utils.BadKeyTypeException,
        re.escape(
            'Invalid key type [rsa-encrypted]: this feature is only allowed in the '
            'alpha and beta versions of this command.')):
      self.Run("""
          compute instances create hamlet
            --csek-key-file {0}
            --zone central2-a
          """.format(private_key_fname))

  def testNotFoundInstNameKeyFileFail(self):
    private_key_fname = self.WriteKeyFile()

    with self.AssertRaisesExceptionMatches(csek_utils.MissingCsekException,
                                           'Key required for resource'):
      self.Run("""
          compute instances create instance-1
            --csek-key-file {0}
            --zone central2-a
          """.format(private_key_fname))

  def testNotFoundInstNameKeyFileOk(self):
    private_key_fname = self.WriteKeyFile()
    msg = self.messages

    self.Run("""
        compute instances create instance-1
          --csek-key-file {0}
          --zone central2-a
          --no-require-csek-key-create
        """.format(private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      msg.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          deviceName='instance-1',
                          initializeParams=msg.AttachedDiskInitializeParams(
                              sourceImage=create_test_base.DefaultImageOf(
                                  self.api_version)),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=create_test_base.DefaultMachineTypeOf(
                      self.api_version),
                  metadata=msg.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version))
                  ],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=msg.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testFoundInstNameImageNameKeyFile(self):
    private_key_fname = self.WriteKeyFile()
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --csek-key-file {0}
          --zone central2-a
          --image yorik
        """.format(private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      msg.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          deviceName='hamlet',
                          initializeParams=msg.AttachedDiskInitializeParams(
                              sourceImage=(self.compute_uri +
                                           '/projects/my-project/global/images/'
                                           'yorik'),
                              sourceImageEncryptionKey=msg
                              .CustomerEncryptionKey(
                                  rawKey=('aFellowOfInfiniteJestOf'
                                          'MostExcellentFancy00='))),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          diskEncryptionKey=msg.CustomerEncryptionKey(
                              rawKey=('abcdefghijklmnopqrstuv'
                                      'wxyz1234567890AAAAAAA=')))
                  ],
                  machineType=create_test_base.DefaultMachineTypeOf(
                      self.api_version),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version))
                  ],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=msg.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testTwoDisksFoundKeyFile(self):
    private_key_fname = self.WriteKeyFile()
    msg = self.messages

    self.Run("""
        compute instances create instance-1
          --disk name=hamlet,boot=yes
          --disk name=ophelia
          --csek-key-file {0}
          --zone central2-a
        """.format(private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      msg.AttachedDisk(
                          autoDelete=False,
                          boot=True,
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'hamlet'.format(api=self.api)),
                          diskEncryptionKey=msg.CustomerEncryptionKey(
                              rawKey=('abcdefghijklmnopqrstuv'
                                      'wxyz1234567890AAAAAAA='))),
                      msg.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'ophelia'.format(api=self.api)),
                          diskEncryptionKey=msg.CustomerEncryptionKey(
                              rawKey=('OpheliaOphelia00000000'
                                      '00000000000000000000X=')))
                  ],
                  machineType=create_test_base.DefaultMachineTypeOf(
                      self.api_version),
                  metadata=msg.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version))
                  ],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=msg.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateCsekTestBeta(InstancesCreateCsekTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testFoundInstanceNameKeyFileWrappedRsaKey(self):
    private_key_fname = self.WriteKeyFile(include_rsa_encrypted=True)
    msg = self.messages

    self.Run("""
        compute instances create wrappedkeydisk
          --csek-key-file {0}
          --zone central2-a
        """.format(private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      msg.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          deviceName='wrappedkeydisk',
                          initializeParams=msg.AttachedDiskInitializeParams(
                              sourceImage=create_test_base.DefaultImageOf(
                                  self.api_version)),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          diskEncryptionKey=msg.CustomerEncryptionKey(
                              rsaEncryptedKey=test_base.SAMPLE_WRAPPED_CSEK_KEY)
                      )
                  ],
                  machineType=create_test_base.DefaultMachineTypeOf(
                      self.api_version),
                  metadata=msg.Metadata(),
                  name='wrappedkeydisk',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version))
                  ],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=msg.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testFoundInstNameKeyFileRsaWrappedKey(self):
    pass

if __name__ == '__main__':
  test_case.main()
