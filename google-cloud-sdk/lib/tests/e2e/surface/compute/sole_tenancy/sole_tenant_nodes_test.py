# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Integration tests for using node based sole tenancy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.core.util import retry
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class NodeSoleTenantTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.retryer = retry.Retryer(max_wait_ms=60000)

    # We have the most CPU quota in us-central1
    self.region = 'us-central1'
    self.zone = 'us-central1-c'
    self.node_type = 'n1-node-96-624'

  def _GetResourceName(self):
    return next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-sole-tenant-test'))

  @contextlib.contextmanager
  def _CreateInstance(self, node_group_name):
    instance_name = self._GetResourceName()
    try:
      self.Run(('compute instances create {0} --zone {1} --node-group {2} '
                '--machine-type n1-standard-2').format(instance_name, self.zone,
                                                       node_group_name))
      yield instance_name
    finally:
      self.Run('compute instances delete {0} --zone {1} --quiet'.format(
          instance_name, self.zone))

  @contextlib.contextmanager
  def _CreateNodeTemplate(self, node_template_name):
    try:
      self.Run(
          'compute sole-tenancy node-templates create {0} --region {1} '
          '--node-type {2}'.format(
              node_template_name, self.region, self.node_type))
      self.Run('compute sole-tenancy node-templates list')
      self.AssertNewOutputContains(node_template_name)
      yield node_template_name
    finally:
      self.Run('compute sole-tenancy node-templates delete {0} --region {1} '
               '--quiet'.format(node_template_name, self.region))

  def _CheckGetNodeGroup(self, node_group_name, node_template_name):
    self.Run('compute sole-tenancy node-groups describe {0} --zone {1}'
             .format(node_group_name, self.zone))
    self.AssertNewOutputContainsAll([node_group_name, node_template_name])

  @contextlib.contextmanager
  def _CreateNodeGroup(self, node_group_name, node_template_name):
    try:
      self.Run('compute sole-tenancy node-groups create {0} --zone {1} '
               '--node-template {2} --target-size 1'
               .format(node_group_name, self.zone, node_template_name))
      # There is sometimes a delay between creation and get returning
      # successfully.
      self.retryer.RetryOnException(self._CheckGetNodeGroup,
                                    [node_group_name, node_template_name])
      yield node_group_name
    finally:
      self.Run('compute sole-tenancy node-groups delete {0} --zone {1} '
               '--quiet'.format(node_group_name, self.zone))

  @test_case.Filters.skip('Failing', 'b/112334537')
  def testNodeBasedSoleTenancy(self):
    node_template_name = self._GetResourceName()
    node_group_name = self._GetResourceName()
    with self._CreateNodeTemplate(node_template_name), \
         self._CreateNodeGroup(node_group_name, node_template_name), \
         self._CreateInstance(node_group_name) as instance_name:
      self.Run('compute sole-tenancy node-groups list-nodes {0} --zone {1}'
               .format(node_group_name, self.zone))
      self.AssertNewOutputContains(instance_name)


if __name__ == '__main__':
  e2e_test_base.main()
