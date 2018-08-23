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

"""Tests for 'node-pools delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.container import base


class DeleteTestGA(base.GATestBase,
                   base.NodePoolsTestBase):
  """gcloud GA track using container v1 API."""

  def _TestDeleteNodePool(self, location):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    pool = self._MakeNodePool(version=self.VERSION)
    self.ExpectGetNodePool(pool.name, response=pool, zone=location)
    self.ExpectDeleteNodePool(
        self.NODE_POOL_NAME,
        response=self._MakeNodePoolOperation(operationType=self.op_delete),
        zone=location)
    kwargs = {'zone': location}
    self.ExpectGetOperation(
        self._MakeNodePoolOperation(operationType=self.op_delete, **kwargs))
    # Second get operation returns done
    self.ExpectGetOperation(self._MakeNodePoolOperation(
        operationType=self.op_delete,
        status=self.op_done,
        **kwargs))

    self.ClearOutput()
    self.ClearErr()
    if location == self.REGION:
      self.Run(self.regional_node_pools_command_base.format(location) +
               ' delete {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                  self.CLUSTER_NAME))
    else:
      self.Run(self.node_pools_command_base.format(location) +
               ' delete {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                  self.CLUSTER_NAME))

  def testDeleteNodePool(self):
    self._TestDeleteNodePool(self.ZONE)

  def testDeleteRegionalNodePool(self):
    self._TestDeleteNodePool(self.REGION)

  def testDeleteNodePoolAsync(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    pool = self._MakeNodePool(version=self.VERSION)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectDeleteNodePool(
        self.NODE_POOL_NAME,
        response=self._MakeNodePoolOperation(operationType=self.op_delete))
    self.ClearOutput()
    self.ClearErr()
    self.Run(self.node_pools_command_base.format(self.ZONE) +
             ' delete {0} --cluster={1} --async'.format(self.NODE_POOL_NAME,
                                                        self.CLUSTER_NAME))

  def testDeleteHttpError(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    pool = self._MakeNodePool(version=self.VERSION)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectDeleteNodePool(
        self.NODE_POOL_NAME,
        exception=self.HttpError())

    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(exceptions.HttpException):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' delete {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                  self.CLUSTER_NAME))
    self.AssertErrContains(
        'ResponseError: code=400, message=your request is bad '
        'and you should feel bad.')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class DeleteTestBeta(base.BetaTestBase, DeleteTestGA):
  """gcloud Beta track using container v1beta1 API."""


# Mixin class must come in first to have the correct multi-inheritance behavior.
class DeleteTestAlpha(base.AlphaTestBase, DeleteTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""


if __name__ == '__main__':
  test_case.main()
