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

"""Tests for 'node-pools get' command."""

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.container import base


class GetTestGA(base.TestBaseV1,
                base.GATestBase,
                base.NodePoolsTestBase):
  """gcloud GA track using container v1 API."""

  def _TestGetNodePool(self, location):
    pool_kwargs = {'nodeVersion': '1.6.8'}
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool, zone=location)

    if location == self.REGION:
      self.Run(self.regional_node_pools_command_base.format(location) +
               ' describe {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                    self.CLUSTER_NAME))
    else:
      self.Run(self.node_pools_command_base.format(location) +
               ' describe {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                                    self.CLUSTER_NAME))
    scopes = ''.join(['- %s\n' % s for s in self._DEFAULT_SCOPES])
    self.AssertOutputMatches(
        (r'config:\n'
         'oauthScopes:\n'
         '{scopes}'
         'initialNodeCount: {initialNodeCount}\n'
         'name: {name}\n'
         'version: {version}\\n').format(
             initialNodeCount=self.NUM_NODES,
             name=pool.name,
             version=pool.version,
             scopes=scopes),
        normalize_space=True)

  def testGetNodePool(self):
    self._TestGetNodePool(self.ZONE)

  def testGetHttpError(self):
    self.ExpectGetNodePool(self.NODE_POOL_NAME, exception=self.HttpError())

    with self.assertRaises(exceptions.HttpException):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' describe {0} --cluster={1}'.format(
                   self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains(
        'ResponseError: code=400, message=your request is bad '
        'and you should feel bad.')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetTestBetaV1API(base.BetaTestBase, GetTestGA):
  """gcloud Beta track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetTestBetaV1Beta1API(base.TestBaseV1Beta1, GetTestBetaV1API):
  """gcloud Beta track using container v1beta1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetTestAlphaV1API(base.AlphaTestBase, GetTestBetaV1API):
  """gcloud Alpha track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetTestAlphaV1Alpha1API(base.TestBaseV1Alpha1, GetTestAlphaV1API,
                              GetTestBetaV1Beta1API):
  """gcloud Alpha track using container v1alpha1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)

  def testGetRegionalNodePool(self):
    self._TestGetNodePool(self.REGION)


if __name__ == '__main__':
  test_case.main()
