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

"""Tests for 'node-pools get' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.container import base


class GetTestGA(base.GATestBase,
                base.NodePoolsTestBase):
  """gcloud GA track using container v1 API."""

  def _TestGetNodePool(self, location):
    pool_kwargs = {
        'nodeVersion': '1.6.8',
        'management': self.messages.NodeManagement(
            autoRepair=True, autoUpgrade=True)
    }
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
         'management:\n'
         'autoRepair: true\n'
         'autoUpgrade: true\n'
         'name: {name}\n'
         'version: {version}\\n').format(
             initialNodeCount=self.NUM_NODES,
             name=pool.name,
             version=pool.version,
             scopes=scopes),
        normalize_space=True)

  def testGetNodePool(self):
    self._TestGetNodePool(self.ZONE)

  def testGetRegionalNodePool(self):
    self._TestGetNodePool(self.REGION)

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
class GetTestBeta(base.BetaTestBase, GetTestGA):
  """gcloud Beta track using container v1beta1 API."""


# Mixin class must come in first to have the correct multi-inheritance behavior.
class GetTestAlpha(base.AlphaTestBase, GetTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""


if __name__ == '__main__':
  test_case.main()
