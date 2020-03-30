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
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateScopesTest(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testWithSingleScope(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --scopes compute-rw
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
                          email='default',
                          scopes=[
                              'https://www.googleapis.com/auth/compute',
                          ]),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithNoScopes(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
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
          --scopes compute-rw,https://www.googleapis.com/auth/devstorage.full_control
          --service-account=1234@project.gserviceaccount.com
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
                              'https://www.googleapis.com/auth/compute',
                              ('https://www.googleapis.com/auth/devstorage'
                               '.full_control'),
                          ]),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testExplicitDefaultScopes(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --scopes compute-rw,default
          --zone central2-a
        """)

    expected_scopes = (
        create_test_base.DEFAULT_SCOPES +
        ['https://www.googleapis.com/auth/compute'])
    expected_scopes.sort()
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
                      m.ServiceAccount(email='default', scopes=expected_scopes),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithIllegalScopeValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[default=sql=https://www.googleapis.com/auth/devstorage.'
        r'full_control\] is an illegal value for \[--scopes\]. Values must be '
        r'of the form \[SCOPE\].'):
      self.Run("""
          compute instances create instance-1
            --scopes default=sql=https://www.googleapis.com/auth/devstorage.full_control,compute-rw
            --zone central2-a
          """)

    self.CheckRequests(self.zone_get_request,)

  def testWithEmptyScopeValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Scope cannot be an empty string.'):
      self.Run("""
          compute instances create instance-1
            --scopes compute-rw,,sql
            --zone central2-a
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
