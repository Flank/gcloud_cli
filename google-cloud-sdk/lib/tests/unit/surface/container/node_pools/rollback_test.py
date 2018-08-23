# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for 'node-pools rollback' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.container import base


class RollbackTestGA(base.GATestBase, base.NodePoolsTestBase):
  """gcloud GA track using container v1 API."""

  def _TestRollbackNodePool(self, location):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')

    pool = self._MakeNodePool(version=self.VERSION)
    self.ExpectGetNodePool(pool.name, response=pool, zone=location)
    kwargs = {'zone': location}
    self.ExpectRollbackOperation(
        pool.name,
        response=self._MakeNodePoolOperation(
            operationType=self.op_upgrade_nodes, **kwargs),
        zone=location)

    self.ExpectGetOperation(
        self._MakeNodePoolOperation(operationType=self.op_upgrade_nodes,
                                    **kwargs))
    # Second get operation returns done
    self.ExpectGetOperation(self._MakeNodePoolOperation(
        operationType=self.op_upgrade_nodes,
        status=self.op_done,
        **kwargs))

    self.ClearOutput()
    self.ClearErr()
    if location == self.REGION:
      self.Run(self.regional_node_pools_command_base.format(location) +
               ' rollback {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                    self.CLUSTER_NAME))
    else:
      self.Run(self.node_pools_command_base.format(location) +
               ' rollback {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                    self.CLUSTER_NAME))
    self.AssertErrContains('will be rolled back to previous configuration')

  def testRollbackNodePool(self):
    self._TestRollbackNodePool(self.ZONE)

  def testRollbackNodePoolRegional(self):
    self._TestRollbackNodePool(self.REGION)

  def testRollbackError(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')

    pool = self._MakeNodePool(version=self.VERSION)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectRollbackOperation(
        pool.name,
        exception=self.HttpError())

    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(exceptions.HttpException):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' rollback {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                    self.CLUSTER_NAME))
    self.AssertErrContains('ResponseError: code=400')

  def testGetOperationFail(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')

    pool = self._MakeNodePool(version=self.VERSION)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectRollbackOperation(
        pool.name,
        response=self._MakeNodePoolOperation(
            operationType=self.op_upgrade_nodes))

    self.ExpectGetOperation(
        self._MakeNodePoolOperation(operationType=self.op_upgrade_nodes))

    self.ClearOutput()
    self.ClearErr()

    tv = [0]

    def fake_clock():
      tv[0] += 75  # make sure only 1 loop happens
      return tv[0]

    self.clock_mock = self.StartObjectPatch(time, 'time')
    self.clock_mock.side_effect = fake_clock

    with self.assertRaises(util.Error):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' rollback {0} --cluster={1} --timeout={2}'.format(
                   self.NODE_POOL_NAME,
                   self.CLUSTER_NAME,
                   '100'))
    self.AssertErrContains('still running')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class RollbackTestBeta(base.BetaTestBase, RollbackTestGA):
  """gcloud Beta track using container v1beta1 API."""


# Mixin class must come in first to have the correct multi-inheritance behavior.
class RollbackTestAlpha(base.AlphaTestBase, RollbackTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""


if __name__ == '__main__':
  test_case.main()
