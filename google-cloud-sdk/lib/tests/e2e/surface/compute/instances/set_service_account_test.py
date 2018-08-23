# -*- coding: utf-8 -*- #
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
"""Integration tests for set-service-account command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class SetServiceAccountTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testInstanceSetServiceAccount(self):
    self.GetInstanceName()
    self.Run('compute instances create {} --zone {} '.format(
        self.instance_name, self.zone))
    self.Run('compute instances stop --zone {} {}'.format(
        self.zone, self.instance_name))
    self.Run('compute instances set-service-account --scopes "" --zone {} {}'
             .format(self.zone, self.instance_name))
    result = self.Run('compute instances describe {} --zone {} --format=disable'
                      .format(self.instance_name, self.zone))
    self.assertEqual(result.serviceAccounts[0].scopes, [],
                     result.serviceAccounts[0].scopes)

  def testRemoveServiceAccount(self):
    self.GetInstanceName()
    self.Run('compute instances create {} --zone {} '.format(
        self.instance_name, self.zone))
    self.Run('compute instances stop --zone {} {}'.format(
        self.zone, self.instance_name))
    self.Run('compute instances set-service-account '
             '--no-service-account '
             '--no-scopes '
             ' --zone {} {}'.format(self.zone, self.instance_name))
    result = self.Run('compute instances describe {} --zone {} --format=disable'
                      .format(self.instance_name, self.zone))
    self.assertEqual(result.serviceAccounts, [], result.serviceAccounts)

  def testChangeServiceAccounts(self):
    new_service_account = ('cloud-sdk-integration-testing'
                           '@appspot.gserviceaccount.com')
    self.GetInstanceName()
    self.Run('compute instances create {} --zone {} '.format(
        self.instance_name, self.zone))
    self.Run('compute instances stop --zone {} {}'.format(
        self.zone, self.instance_name))
    self.Run('compute instances set-service-account '
             '--service-account {}'
             ' --zone {} {}'.format(new_service_account, self.zone,
                                    self.instance_name))
    result = self.Run('compute instances describe {} --zone {} --format=disable'
                      .format(self.instance_name, self.zone))
    self.assertEqual(new_service_account, result.serviceAccounts[0].email)

  def testAttemptChangeServiceAccountOnRunningInstance(self):
    self.GetInstanceName()
    self.Run('compute instances create {} --zone {} '.format(
        self.instance_name, self.zone))
    with self.AssertRaisesToolExceptionRegexp(
        r'.*The instance must be stopped before the service account can be '
        r'changed\..*'):
      self.Run('compute instances set-service-account '
               '--service-account {}'
               ' --zone {} {}'.format(
                   'cloud-sdk-integration-testing@appspot.gserviceaccount.com',
                   self.zone, self.instance_name))


if __name__ == '__main__':
  e2e_test_base.main()
