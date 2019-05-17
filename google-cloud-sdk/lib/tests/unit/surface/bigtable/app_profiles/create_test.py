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
"""Test of the 'create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import app_profiles
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.bigtable import base


class AppProfileCreateTestsGA(base.BigtableV2TestBase,
                              cli_test_base.CliTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.clusters_list_mock = self.client.projects_instances_clusters.List
    self.app_profile_create_mock = self.StartObjectPatch(
        app_profiles,
        'Create',
        return_value=self.msgs.AppProfile(name='my-app-profile'))

  def testCreateMultiCluster(self):
    self.Run('bigtable app-profiles create my-app-profile '
             '--instance my-instance --description my-description '
             '--route-any')
    self.app_profile_create_mock.assert_called_once_with(
        util.GetAppProfileRef('my-instance', 'my-app-profile'),
        cluster=None,
        description='my-description',
        multi_cluster=True,
        transactional_writes=False,
        force=False)

  def testCreateSingleCluster(self):
    self.Run('bigtable app-profiles create my-app-profile '
             '--instance my-instance --description my-description '
             '--route-to my-cluster')
    self.app_profile_create_mock.assert_called_once_with(
        util.GetAppProfileRef('my-instance', 'my-app-profile'),
        cluster='my-cluster',
        description='my-description',
        multi_cluster=False,
        transactional_writes=False,
        force=False)

  def testCreateTransactional(self):
    self.Run('bigtable app-profiles create my-app-profile '
             '--instance my-instance --description my-description '
             '--route-to my-cluster --transactional-writes')
    self.app_profile_create_mock.assert_called_once_with(
        util.GetAppProfileRef('my-instance', 'my-app-profile'),
        cluster='my-cluster',
        description='my-description',
        multi_cluster=False,
        transactional_writes=True,
        force=False)

  def testCreateMultiClusterTransactionalInvalid(self):
    with self.AssertRaisesArgumentError():
      self.Run('bigtable app-profiles create my-app-profile '
               '--instance my-instance --description my-description '
               '--route-any --transactional-writes')
      self.app_profile_create_mock.assert_not_called()

  def testRouteToCompletion(self):
    self.clusters_list_mock.Expect(
        request=self.msgs.BigtableadminProjectsInstancesClustersListRequest(
            parent='projects/{0}/instances/{1}'.format(self.Project(),
                                                       'theinstance')),
        response=self.msgs.ListClustersResponse(clusters=[
            self.msgs.Cluster(
                name='projects/{0}/instances/{1}/clusters/{2}'.format(
                    self.Project(), 'theinstance', 'cluster0')),
            self.msgs.Cluster(name='projects/{0}/instances/{1}/clusters/{2}'.
                              format(self.Project(), 'theinstance', 'cluster1'))
        ]))

    self.RunCompletion(
        'bigtable app-profiles create myprofile '
        '--instance theinstance --route-to c', ['cluster0', 'cluster1'])


class AppProfileCreateTestsBeta(AppProfileCreateTestsGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class AppProfileCreateTestsAlpha(AppProfileCreateTestsBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
