# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Test of the 'describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.bigtable import base


class DescribeCommandTestGA(base.BigtableV2TestBase,
                            sdk_test_base.WithOutputCapture):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.svc = self.client.projects_instances_clusters.Get
    self.msg = self.msgs.BigtableadminProjectsInstancesClustersGetRequest(
        name='projects/{0}/instances/theinstance/clusters/thecluster'.format(
            self.Project()))

  def _RunSuccessTest(self, cmd):
    kms_key = 'projects/p/locations/l/keyRings/r/cryptoKeys/k'
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.Cluster(
            name='projects/theprojects/instances/theinstance/clusters/thecluster',
            serveNodes=6,
            defaultStorageType=(
                self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD),
            encryptionConfig=self.msgs.EncryptionConfig(kmsKeyName=kms_key)))
    self.Run(cmd)
    self.AssertOutputContains('thecluster')
    self.AssertOutputContains('6')
    self.AssertOutputContains('SSD')
    self.AssertOutputContains(kms_key)

  def testDescribe(self):
    self._RunSuccessTest(
        'bigtable clusters describe thecluster --instance=theinstance')

  def testDescribeByUri(self):
    cmd = ('bigtable clusters describe https://bigtableadmin.googleapis.com/v2/'
           'projects/{0}/instances/theinstance/clusters/thecluster'.format(
               self.Project()))
    self._RunSuccessTest(cmd)

  def testErrorResponse(self):
    with self.AssertHttpResponseError(self.svc, self.msg):
      self.Run('bigtable clusters describe thecluster --instance=theinstance')


class DescribeCommandTestBeta(DescribeCommandTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class DescribeCommandTestAlpha(DescribeCommandTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
