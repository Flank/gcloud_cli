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

"""Tests for 'clusters describe' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import json

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from surface.container.clusters.upgrade import UpgradeHelpText
from tests.lib import test_case
from tests.lib.surface.container import base


class DescribeTestGA(base.TestBaseV1,
                     base.GATestBase,
                     base.ClustersTestBase,
                     test_case.WithOutputCapture):
  """gcloud GA track using container v1 API."""

  def SetUp(self):
    self.api_mismatch = False

  def _TestDescribe(self, location):
    name = 'sadpanda-reg'
    message = 'Regional cluster is experiencing an existential crisis'
    self.ExpectGetCluster(self._MakeCluster(name=name,
                                            zone=location,
                                            status=self.error,
                                            statusMessage=message,
                                            endpoint=self.ENDPOINT),
                          zone=location)
    if location == self.REGION:
      self.Run(self.regional_clusters_command_base.format(location) +
               ' describe {0}'.format(name))
    else:
      self.Run(self.clusters_command_base.format(location) +
               ' describe {0}'.format(name))
    if self.api_mismatch and location == self.REGION:
      self.AssertErrContains('You invoked')
    # output should be valid yaml
    out = yaml.load(self.GetOutput())
    self.assertIsNotNone(out)
    self.assertEqual(out['status'], str(self.error))
    self.assertEqual(out['statusMessage'], message)

  def _TestDescribeWrongLocation(self, location):
    name = 'wrongzone'
    self.ExpectGetCluster(
        self._MakeCluster(name=name),
        exception=base.NOT_FOUND_ERROR,
        zone=location)
    self.ExpectListClusters([
        self._MakeCluster(
            name=name, zone='other-zone', endpoint=self.ENDPOINT)])
    if location == self.REGION:
      with self.assertRaises(c_util.Error):
        self.Run(self.regional_clusters_command_base.format(location) +
                 ' describe {0}'.format(name))
    else:
      with self.assertRaises(c_util.Error):
        self.Run(self.clusters_command_base.format(location) +
                 ' describe {0}'.format(name))
    self.AssertErrContains(api_adapter.WRONG_ZONE_ERROR_MSG.format(
        error=exceptions.HttpException(base.NOT_FOUND_ERROR,
                                       c_util.HTTP_ERROR_FORMAT),
        name=name, wrong_zone=location, zone='other-zone'))
    if self.api_mismatch and location == self.REGION:
      self.AssertErrContains('You invoked')

  def testDescribe(self):
    self._TestDescribe(self.ZONE)

  def testDescribeWrongZone(self):
    self._TestDescribeWrongLocation(self.ZONE)

  def testDescribeJson(self):
    self.ExpectGetCluster(self._RunningCluster())
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' describe {0} --format=json'.format(self.CLUSTER_NAME))
    # output should be valid json
    out = json.loads(self.GetOutput())
    self.assertIsNotNone(out)
    self.assertEqual(out['status'], str(self.running))
    self.assertEqual(out['name'], str(self.CLUSTER_NAME))

  def testDescribeOldVersion(self):
    name = 'sadpanda'
    self.ExpectGetCluster(self._MakeCluster(currentNodeVersion='1.1.1',
                                            currentMasterVersion='1.2.2',
                                            name=name))
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' describe {0}'.format(name))
    self.AssertErrContains(UpgradeHelpText.UPGRADE_AVAILABLE)
    self.AssertErrContains(UpgradeHelpText.UPGRADE_COMMAND
                           .format(name=name))
    self.AssertErrNotContains(UpgradeHelpText.UNSUPPORTED)
    self.AssertErrNotContains(UpgradeHelpText.SUPPORT_ENDING)
    # output should be valid yaml
    out = yaml.load(self.GetOutput())
    self.assertIsNotNone(out)

  def testDescribeSupportEndingVersion(self):
    name = 'sadpanda'
    self.ExpectGetCluster(self._MakeCluster(currentNodeVersion='1.1.1',
                                            currentMasterVersion='1.3.2',
                                            name=name))
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' describe {0}'.format(name))
    self.AssertErrContains(UpgradeHelpText.SUPPORT_ENDING)
    self.AssertErrContains(UpgradeHelpText.UPGRADE_COMMAND
                           .format(name=name))
    self.AssertErrNotContains(UpgradeHelpText.UNSUPPORTED)
    self.AssertErrNotContains(UpgradeHelpText.UPGRADE_AVAILABLE)
    # output should be valid yaml
    out = yaml.load(self.GetOutput())
    self.assertIsNotNone(out)

  def testDescribeUnsupportedVersion(self):
    name = 'sadpanda'
    self.ExpectGetCluster(self._MakeCluster(currentNodeVersion='1.1.1',
                                            currentMasterVersion='1.4.2',
                                            name=name))
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' describe {0}'.format(name))
    self.AssertErrContains(UpgradeHelpText.UNSUPPORTED)
    self.AssertErrContains(UpgradeHelpText.UPGRADE_COMMAND
                           .format(name=name))
    self.AssertErrNotContains(UpgradeHelpText.SUPPORT_ENDING)
    self.AssertErrNotContains(UpgradeHelpText.UPGRADE_AVAILABLE)
    # output should be valid yaml
    out = yaml.load(self.GetOutput())
    self.assertIsNotNone(out)

  def testDescribeNonexistentCluster(self):
    name = 'notfound'
    self.ExpectGetCluster(
        self._MakeCluster(name=name),
        exception=base.NOT_FOUND_ERROR)
    self.ExpectListClusters([])
    with self.assertRaises(c_util.Error):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' describe {0}'.format(name))
    self.AssertErrContains(api_adapter.NO_SUCH_CLUSTER_ERROR_MSG.format(
        error=exceptions.HttpException(base.NOT_FOUND_ERROR,
                                       c_util.HTTP_ERROR_FORMAT),
        name=name, project=self.PROJECT_ID))

  def testDescribeMissingZone(self):
    with self.assertRaises(exceptions.MinimumArgumentException):
      self.Run(self.COMMAND_BASE +
               ' clusters describe {0}'.format(self.CLUSTER_NAME))

  def testDescribeMissingProject(self):
    properties.VALUES.core.project.Set(None)
    with self.assertRaises(properties.RequiredPropertyError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' describe {0}'.format(self.CLUSTER_NAME))

  def testDescribeRegional(self):
    self._TestDescribe(self.REGION)

  def testDescribeWrongRegion(self):
    self._TestDescribeWrongLocation(self.REGION)


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class DescribeTestBetaV1API(base.BetaTestBase, DescribeTestGA):
  """gcloud Beta track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)
    self.api_mismatch = True


# Mixin class must come in first to have the correct multi-inheritance behavior.
class DescribeTestBetaV1Beta1API(base.TestBaseV1Beta1, DescribeTestBetaV1API):
  """gcloud Beta track using container v1beta1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)
    self.api_mismatch = False


# Mixin class must come in first to have the correct multi-inheritance behavior.
class DescribeTestAlphaV1API(base.AlphaTestBase, DescribeTestBetaV1API):
  """gcloud Alpha track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)
    self.api_mismatch = True


# Mixin class must come in first to have the correct multi-inheritance behavior.
class DescribeTestAlphaV1Alpha1API(
    base.TestBaseV1Alpha1, DescribeTestAlphaV1API, DescribeTestBetaV1Beta1API):
  """gcloud Alpha track using container v1alpha1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)
    self.api_mismatch = False


if __name__ == '__main__':
  test_case.main()
