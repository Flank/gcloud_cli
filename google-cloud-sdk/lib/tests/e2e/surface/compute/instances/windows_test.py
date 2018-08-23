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
"""Integration tests for creating/deleting Windows instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import logging

from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base

WINDOWS_IMAGE_ALIAS = 'windows-2012-r2'


class WindowsInstancesTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.instance_names_used = []

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')

  def GetInstanceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    self.instance_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-windows'))
    self.instance_names_used.append(self.instance_name)

  def testInstances(self):
    self.GetInstanceName()
    self._TestInstanceCreation()
    self._TestResetWindowsPassword()
    self._TestInstanceDeletion()

  def _TestInstanceCreation(self):
    self.Run('compute instances create {0} --zone {1} --image {2}'
             .format(self.instance_name, self.zone, WINDOWS_IMAGE_ALIAS))
    self.AssertNewOutputContains(self.instance_name)
    self.Run('compute instances list')
    self.AssertNewOutputContains(self.instance_name)
    self.Run('compute instances describe {0} --zone {1} --format json'
             .format(self.instance_name, self.zone))
    instance_json = self.GetNewOutput()
    instance_dict = json.loads(instance_json)
    self.assertEqual(instance_dict['name'], self.instance_name)
    self.ip = instance_dict['networkInterfaces'][0]['accessConfigs'][0]['natIP']

  def _TestResetWindowsPassword(self):
    user = 'test-user'
    message = 'Instance setup finished.'
    booted = self.WaitForBoot(self.instance_name, message, retries=10,
                              polling_interval=60)
    self.assertTrue(booted, msg='GCE Agent not started before timeout')

    self.Run('compute reset-windows-password {0} --zone {1} --user {2} '
             '--format json'.format(self.instance_name, self.zone, user))
    connection_info = self.GetNewOutput()
    connection_dict = json.loads(connection_info)
    self.assertEqual(connection_dict['ip_address'], self.ip)
    self.assertEqual(len(connection_dict['password']), 15)
    self.assertEqual(connection_dict['username'], user)

  def _TestInstanceDeletion(self):
    self.Run('compute instances list')
    self.AssertNewOutputContains(self.instance_name)
    self.WriteInput('y\n')
    self.Run('compute instances delete {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.ClearInput()
    self.AssertNewErrContains(
        'The following instances will be deleted', reset=False)
    self.AssertNewErrContains(self.instance_name)
    self.Run('compute instances list')
    self.AssertNewOutputNotContains(self.instance_name)

if __name__ == '__main__':
  e2e_test_base.main()
