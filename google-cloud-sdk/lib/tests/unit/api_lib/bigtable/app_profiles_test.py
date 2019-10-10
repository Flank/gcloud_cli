# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for Bigtable app-profiles library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import app_profiles
from googlecloudsdk.api_lib.bigtable import util
from tests.lib.surface.bigtable import base


class AppProfilesClientTest(base.BigtableV2TestBase):

  def SetUp(self):
    self.instance_id = 'my-instance'
    self.app_profile_id = 'my-app-profile'
    self.cluster_id = 'my-cluster'

    self.instance_relative_name = 'projects/fake-project/instances/my-instance'
    self.app_profile_relative_name = (
        self.instance_relative_name + '/appProfiles/my-app-profile')

    self.app_profile_ref = util.GetAppProfileRef(self.instance_id,
                                                 self.app_profile_id)
    self.instance_ref = util.GetInstanceRef(self.instance_id)

  def testDescribe(self):
    response = self.msgs.AppProfile()
    self.client.projects_instances_appProfiles.Get.Expect(
        request=self.msgs.BigtableadminProjectsInstancesAppProfilesGetRequest(
            name=self.app_profile_relative_name),
        response=response)
    self.assertEquals(app_profiles.Describe(self.app_profile_ref), response)

  def testDelete(self):
    response = self.msgs.Empty()
    self.client.projects_instances_appProfiles.Delete.Expect(
        request=self.msgs.
        BigtableadminProjectsInstancesAppProfilesDeleteRequest(
            name=self.app_profile_relative_name, ignoreWarnings=False),
        response=response)
    self.assertEquals(
        app_profiles.Delete(self.app_profile_ref), self.msgs.Empty())

  def testCreate(self):
    response = self.msgs.AppProfile()
    app_profile_to_create = self.msgs.AppProfile(
        description='my-description',
        singleClusterRouting=self.msgs.SingleClusterRouting(
            clusterId=self.cluster_id, allowTransactionalWrites=True))

    self.client.projects_instances_appProfiles.Create.Expect(
        request=self.msgs.
        BigtableadminProjectsInstancesAppProfilesCreateRequest(
            appProfile=app_profile_to_create,
            appProfileId=self.app_profile_id,
            parent=self.instance_relative_name,
            ignoreWarnings=False),
        response=response)
    self.assertEquals(
        app_profiles.Create(
            self.app_profile_ref,
            self.cluster_id,
            description='my-description',
            transactional_writes=True), response)

  def testCreateMultiCluster(self):
    response = self.msgs.AppProfile()
    app_profile_to_create = self.msgs.AppProfile(
        description='my-description', multiClusterRoutingUseAny={})

    self.client.projects_instances_appProfiles.Create.Expect(
        request=self.msgs.
        BigtableadminProjectsInstancesAppProfilesCreateRequest(
            appProfile=app_profile_to_create,
            appProfileId=self.app_profile_id,
            parent=self.instance_relative_name,
            ignoreWarnings=False),
        response=response)
    self.assertEquals(
        app_profiles.Create(
            self.app_profile_ref,
            multi_cluster=True,
            description='my-description'), response)

  def testCreateRequiresRoutingPolicy(self):
    with self.AssertRaisesExceptionRegexp(
        ValueError, 'Must specify either --route-to or --route-any'):
      app_profiles.Create(self.app_profile_ref, description='my-description')

  def testCreateRequiresOnlyOneRoutingPolicy(self):
    with self.AssertRaisesExceptionRegexp(
        ValueError, 'Must specify either --route-to or --route-any'):
      app_profiles.Create(
          self.app_profile_ref,
          description='my-description',
          cluster=self.cluster_id,
          multi_cluster=True)

  def testList(self):
    app_profiles_list = [self.msgs.AppProfile()]
    response = self.msgs.ListAppProfilesResponse(appProfiles=app_profiles_list)
    self.client.projects_instances_appProfiles.List.Expect(
        request=self.msgs.BigtableadminProjectsInstancesAppProfilesListRequest(
            parent=self.instance_relative_name),
        response=response)
    self.assertEquals(
        # Actual response from api_lib is a generator - realize into a list
        list(app_profiles.List(self.instance_ref)),
        app_profiles_list)

  def testUpdate(self):
    response = self.msgs.Operation()
    app_profile_to_update = self.msgs.AppProfile(
        singleClusterRouting=self.msgs.SingleClusterRouting(
            clusterId=self.cluster_id, allowTransactionalWrites=False),
        description='new-description')
    update_mask = 'singleClusterRouting,description'
    self.client.projects_instances_appProfiles.Patch.Expect(
        request=self.msgs.BigtableadminProjectsInstancesAppProfilesPatchRequest(
            name=self.app_profile_relative_name,
            appProfile=app_profile_to_update,
            updateMask=update_mask,
            ignoreWarnings=False),
        response=response)
    self.assertEquals(
        app_profiles.Update(
            self.app_profile_ref,
            cluster=self.cluster_id,
            description='new-description'), response)

  def testUpdateMultiClusterUseAny(self):
    response = self.msgs.Operation()
    app_profile_to_update = self.msgs.AppProfile(multiClusterRoutingUseAny={})
    update_mask = 'multiClusterRoutingUseAny'
    self.client.projects_instances_appProfiles.Patch.Expect(
        request=self.msgs.BigtableadminProjectsInstancesAppProfilesPatchRequest(
            name=self.app_profile_relative_name,
            appProfile=app_profile_to_update,
            updateMask=update_mask,
            ignoreWarnings=False),
        response=response)
    self.assertEquals(
        app_profiles.Update(self.app_profile_ref, multi_cluster=True), response)

  def testUpdateRequiresClusterOrMultiClusterUseAny(self):
    with self.AssertRaisesExceptionRegexp(
        ValueError, 'Cannot update both --route-to and --route-any'):
      app_profiles.Update(
          self.app_profile_ref,
          description='my-description',
          cluster=self.cluster_id,
          multi_cluster=True)
