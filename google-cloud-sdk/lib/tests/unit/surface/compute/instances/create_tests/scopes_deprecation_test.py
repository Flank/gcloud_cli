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
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateScopesDeprecationTestsGa(
    create_test_base.InstancesCreateTestBase, parameterized.TestCase):
  # Set of tests of deprecation of old --scopes flag syntax, new --scopes flag
  # syntax and --service-account flag.

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testScopesLegacyFormatDeprecationNotice(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--scopes]: Flag format --scopes [ACCOUNT=]SCOPE,'
        '[[ACCOUNT=]SCOPE, ...] is removed. Use --scopes [SCOPE,...] '
        '--service-account ACCOUNT instead.'):
      self.Run('compute instances create asdf '
               '--scopes=acc1=scope1,acc1=scope2 '
               '--zone zone-1')

  def testScopesNewFormatNoDeprecationNotice(self):
    self.Run('compute instances create asdf '
             '--scopes=scope1,scope2 --service-account acc1@example.com '
             '--zone zone-1')
    self.AssertErrEquals('')

  def testNoServiceAccount(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instances create asdf '
               '--no-service-account '
               '--zone zone-1')

  def testScopesWithNoServiceAccount(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instances create asdf '
               '--scopes=acc1=scope1 --no-service-account '
               '--zone zone-1')

  def testWithManyScopes(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --scopes compute-rw,https://www.googleapis.com/auth/devstorage.full_control,bigquery,https://www.googleapis.com/auth/userinfo.email,sql,https://www.googleapis.com/auth/taskqueue,cloud-platform,https://www.googleapis.com/auth/source.read_only
          --service-account 1234@project.gserviceaccount.com
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='1234@project.gserviceaccount.com',
                          scopes=[
                              'https://www.googleapis.com/auth/bigquery',
                              'https://www.googleapis.com/auth/cloud-platform',
                              'https://www.googleapis.com/auth/compute',
                              ('https://www.googleapis.com/auth/devstorage'
                               '.full_control'),
                              ('https://www.googleapis.com/auth'
                               '/source.read_only'),
                              'https://www.googleapis.com/auth/sqlservice',
                              'https://www.googleapis.com/auth/taskqueue',
                              'https://www.googleapis.com/auth/userinfo.email',
                          ]),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testNoServiceAccountNoScopes(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --no-service-account
          --no-scopes
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateScopesDeprecationTestsBeta(
    InstancesCreateScopesDeprecationTestsGa):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstancesCreateScopesDeprecationTestsAlpha(
    InstancesCreateScopesDeprecationTestsBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
