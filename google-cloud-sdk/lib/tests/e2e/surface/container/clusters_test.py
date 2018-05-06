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

"""Integration tests for container clusters."""

from __future__ import absolute_import
from __future__ import unicode_literals
import datetime
import json
import logging

from apitools.base.py import encoding
from dateutil import parser
from dateutil import tz
from googlecloudsdk.calliope.base import ReleaseTrack
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container import base


class ClustersTestGA(base.IntegrationTestBase):

  def SetUp(self):
    self.releasetrack = ReleaseTrack.GA

  # We need to write a kubeconfig entry that has the executable path to gcloud,
  # so we run this test only in bundle.
  @sdk_test_base.Filters.RunOnlyInBundle
  def testClustersCreateListDelete(self):
    self.cluster_name = next(
        e2e_utils.GetResourceNameGenerator(prefix='container-test'))
    self.DoTestClusterCreation(self.ZONE, self.releasetrack)
    self.DoTestListClusters(self.releasetrack)
    self.DoTestClusterDeletion(self.ZONE, self.releasetrack)

  # This test will cleanup the leaked clusters.
  # Delete clusters that are older than 1h.
  @sdk_test_base.Filters.RunOnlyInBundle
  def testCleanup(self):
    self.DoTestCleanup(self.ZONE, self.releasetrack)
    self.DoTestCleanup(self.REGION, self.releasetrack)

  def DoTestCleanup(self, location, track):
    # The minimum age for a leaked cluster is 3 hours.
    leaked_cluster_min_age = datetime.timedelta(hours=3)
    output = self.Run('container clusters list {0}'
                      .format(self._GetLocationFlag(location)), track=track)
    jsonoutput = encoding.MessageToJson(output)
    clusters = json.loads(jsonoutput)
    for cluster in clusters:
      createtime = cluster['createTime']
      dt1 = parser.parse(createtime)
      dt2 = dt1 + leaked_cluster_min_age
      dt3 = datetime.datetime.utcnow().replace(tzinfo=tz.tzutc())  # pylint: disable=g-tzinfo-replace
      if dt2 < dt3:
        self.Run('container clusters delete {0} {1} -q --async'
                 .format(cluster['name'], self._GetLocationFlag(location)),
                 track=track)
        logging.warning('Deleting a leaked cluster: %s', cluster['name'])

  def DoTestClusterCreation(self, location, track):
    logging.info('Creating %s in %s', self.cluster_name, location)
    # --region flag is available only in gcloud alpha/beta and triggers a prompt
    # which we need to bypass here.
    self.Run(
        'container clusters create {0} {1} -q --num-nodes=1 '
        '--timeout={2}'.format(self.cluster_name,
                               self._GetLocationFlag(location), self.TIMEOUT),
        track=track)
    self.AssertErrContains('Created')
    self.AssertOutputContains(self.cluster_name)
    self.AssertOutputContains('RUNNING')

  def DoTestClusterDeletion(self, location, track):
    self.Run(
        'container clusters delete {0} {1} -q '
        '--timeout={2}'.format(self.cluster_name,
                               self._GetLocationFlag(location), self.TIMEOUT),
        track=track)
    self.AssertErrContains('Deleted')
    self.AssertErrContains(self.cluster_name)
    self.ClearOutput()
    self.ClearErr()
    self.Run('container clusters list')
    self.AssertOutputNotContains(self.cluster_name)

  def DoTestListClusters(self, track):
    logging.info('Listing clusters')
    self.Run('container clusters list', track=track)
    self.AssertOutputContains(self.cluster_name)

  # We need to write a kubeconfig entry that has the executable path to gcloud,
  # so we run this test only in bundle.
  @sdk_test_base.Filters.RunOnlyInBundle
  def testRegionalClustersCreateListDelete(self):
    self.cluster_name = next(
        e2e_utils.GetResourceNameGenerator(prefix='container-test'))
    self.DoTestClusterCreation(self.REGION, self.releasetrack)
    self.DoTestListClusters(self.releasetrack)
    self.DoTestClusterDeletion(self.REGION, self.releasetrack)


class ClustersTestBeta(ClustersTestGA):

  def SetUp(self):
    self.releasetrack = ReleaseTrack.BETA
    # Required to call v1beta1 API.
    self.Run('config set container/use_v1_api false')
    self.ZONE = 'us-east1-d'  # pylint: disable=invalid-name
    self.REGION = 'us-east1'  # pylint: disable=invalid-name


if __name__ == '__main__':
  test_case.main()
