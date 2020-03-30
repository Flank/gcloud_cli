# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Unit tests for `gcloud memcache instances create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.memcache import memcache_test_base


@test_case.Filters.SkipOnPy3('Flaking due to labels order', 'b/150677175')
class CreateTest(memcache_test_base.InstancesUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectCreate(self, instance, is_async=False):
    operation = self.messages.Operation(name=self.wait_operation_relative_name)
    create_req = self.messages.MemcacheProjectsLocationsInstancesCreateRequest()
    create_req.instance = instance
    create_req.parent = self.instance_ref.Parent().RelativeName()
    create_req.instanceId = self.instance_id
    self.instances_service.Create.Expect(request=create_req, response=operation)
    if is_async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_service.Get.Expect(
        request=self.messages.MemcacheProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)

    expected_created_instance = copy.deepcopy(instance)
    expected_created_instance.name = self.instance_relative_name
    self.instances_service.Get.Expect(
        request=self.messages.MemcacheProjectsLocationsInstancesGetRequest(
            name=expected_created_instance.name),
        response=expected_created_instance)

  def _MakeInstance(self):
    instance = self.MakeInstance()
    instance.authorizedNetwork = 'full_name_of_network'
    instance.displayName = 'Display Name'
    instance.labels = self.MakeLabels({'a': 'b', 'c': 'd'})
    instance.memcacheVersion = (
        self.messages.Instance.MemcacheVersionValueValuesEnum('MEMCACHE_1_5'))
    instance.nodeConfig = self.messages.NodeConfig(
        cpuCount=3, memorySizeMb=2000)
    instance.nodeCount = 5
    instance.zones = ['us-central1-a', 'us-central1-b']
    instance.parameters = self.MakeParameters({'a': 'b', 'c': 'd'})
    return instance

  def testCreate(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    instance = self._MakeInstance()
    self._ExpectCreate(instance)
    self.Run('memcache instances create {} --region {} '
             '--authorized-network {} '
             '--display-name \'{}\' '
             '--labels a=b,c=d '
             '--node-count {} '
             '--node-cpu {} '
             '--node-memory 2000mb '
             '--zones {} '
             '--memcached-version 1.5 '
             '--parameters a=b,c=d '.format(self.instance_id, self.region_id,
                                            instance.authorizedNetwork,
                                            instance.displayName,
                                            instance.nodeCount,
                                            instance.nodeConfig.cpuCount,
                                            ','.join(instance.zones)))

  def testCreate_UsingRelativeName(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    instance = self._MakeInstance()
    self._ExpectCreate(instance)
    self.Run('memcache instances create {} '
             '--authorized-network {} '
             '--display-name \'{}\' '
             '--labels a=b,c=d '
             '--node-count {} '
             '--node-cpu {} '
             '--node-memory 2000mb '
             '--zones {} '
             '--memcached-version 1.5 '
             '--parameters a=b,c=d '.format(self.instance_ref.RelativeName(),
                                            instance.authorizedNetwork,
                                            instance.displayName,
                                            instance.nodeCount,
                                            instance.nodeConfig.cpuCount,
                                            ','.join(instance.zones)))

  def testCreate_Async(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    instance = self._MakeInstance()
    self._ExpectCreate(instance, is_async=True)
    self.Run('memcache instances create {} '
             '--authorized-network {} '
             '--display-name \'{}\' '
             '--labels a=b,c=d '
             '--node-count {} '
             '--node-cpu {} '
             '--node-memory 2000mb '
             '--zones {} '
             '--memcached-version 1.5 '
             '--parameters a=b,c=d '
             '--async -q '.format(self.instance_ref.RelativeName(),
                                  instance.authorizedNetwork,
                                  instance.displayName, instance.nodeCount,
                                  instance.nodeConfig.cpuCount,
                                  ','.join(instance.zones)))
    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.wait_operation_relative_name))


if __name__ == '__main__':
  test_case.main()
