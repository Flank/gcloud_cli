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

"""Tests for 'node-pools list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.container import base


class ListTestGA(base.TestBaseV1,
                 base.GATestBase,
                 base.NodePoolsTestBase):
  """gcloud GA track using container v1 API."""

  def _TestListNodePools(self, location):
    pool_kwargs = {
        'diskSizeGb': 50,
        'machineType': 'n1-standard-3',
        'nodeVersion': '1.7.8'}
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectListNodePools(response=self._MakeListNodePoolsResponse([pool]),
                             zone=location)

    if location == self.REGION:
      self.Run(self.regional_node_pools_command_base.format(location) +
               ' list --cluster={0}'.format(self.CLUSTER_NAME))
    else:
      self.Run(self.node_pools_command_base.format(location) +
               ' list --cluster={0}'.format(self.CLUSTER_NAME))

    self.AssertOutputMatches(
        (r'NAME MACHINE_TYPE DISK_SIZE_GB NODE_VERSION\n'
         '{name} {machine_type} {disk_size} {version}\\n')
        .format(name=pool.name,
                machine_type=pool.config.machineType,
                disk_size=pool.config.diskSizeGb,
                version=pool.version),
        normalize_space=True)

  def testListNodePools(self):
    self._TestListNodePools(self.ZONE)

  def testListRegionalNodePools(self):
    self._TestListNodePools(self.REGION)

  def testListEmptyNodePools(self):
    self.ExpectListNodePools(response=self._MakeListNodePoolsResponse([]))

    self.Run(self.node_pools_command_base.format(self.ZONE) +
             ' list --cluster={0}'.format(self.CLUSTER_NAME))
    self.AssertOutputEquals('')

  def testListHttpError(self):
    self.ExpectListNodePools(response=None, exception=self.HttpError())

    with self.assertRaises(exceptions.HttpException):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' list --cluster={0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains(
        'ResponseError: code=400, message=your request is bad '
        'and you should feel bad.')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class ListTestBetaV1API(base.BetaTestBase, ListTestGA):
  """gcloud Beta track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class ListTestBetaV1Beta1API(base.TestBaseV1Beta1, ListTestBetaV1API):
  """gcloud Beta track using container v1beta1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class ListTestAlphaV1API(base.AlphaTestBase, ListTestBetaV1API):
  """gcloud Alpha track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class ListTestAlphaV1Alpha1API(base.TestBaseV1Alpha1, ListTestAlphaV1API,
                               ListTestBetaV1Beta1API):
  """gcloud Alpha track using container v1alpha1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)


if __name__ == '__main__':
  test_case.main()
