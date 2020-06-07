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
"""Tests for Bigtable snapshots library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import clusters
from googlecloudsdk.core import resources
from tests.lib.surface.bigtable import base


class ClustersClientTest(base.BigtableV2TestBase):

  def SetUp(self):
    cluster_id = 'my-cluster'
    instance_id = 'my-instance'

    self.instance_ref = resources.REGISTRY.Parse(
        instance_id,
        params={'projectsId': self.Project()},
        collection='bigtableadmin.projects.instances')

    self.cluster_ref = resources.REGISTRY.Parse(
        cluster_id,
        params={
            'projectsId': self.Project(),
            'instancesId': instance_id
        },
        collection='bigtableadmin.projects.instances.clusters')

    self.zone_ref = 'projects/{0}/locations/my-zone'.format(self.Project())

  def testCreate(self):
    cluster = self.msgs.Cluster(
        location=self.zone_ref,
        defaultStorageType=self.msgs.Cluster.DefaultStorageTypeValueValuesEnum
        .STORAGE_TYPE_UNSPECIFIED,
        serveNodes=3)
    response = self.msgs.Operation()
    self.client.projects_instances_clusters.Create.Expect(
        request=self.msgs.BigtableadminProjectsInstancesClustersCreateRequest(
            cluster=cluster,
            clusterId=self.cluster_ref.Name(),
            parent=self.instance_ref.RelativeName()),
        response=response)
    self.assertEqual(clusters.Create(self.cluster_ref, cluster), response)

  def testCreateWithParams(self):
    cluster = self.msgs.Cluster(
        location=self.zone_ref,
        defaultStorageType=self.msgs.Cluster.DefaultStorageTypeValueValuesEnum
        .STORAGE_TYPE_UNSPECIFIED,
        serveNodes=4)
    response = self.msgs.Operation()
    self.client.projects_instances_clusters.Create.Expect(
        request=self.msgs.BigtableadminProjectsInstancesClustersCreateRequest(
            cluster=cluster,
            clusterId=self.cluster_ref.Name(),
            parent=self.instance_ref.RelativeName()),
        response=response)
    self.assertEqual(
        clusters.Create(self.cluster_ref, cluster), response)

  def testDelete(self):
    response = self.msgs.Empty()
    self.client.projects_instances_clusters.Delete.Expect(
        request=self.msgs.BigtableadminProjectsInstancesClustersDeleteRequest(
            name=self.cluster_ref.RelativeName()),
        response=response)
    self.assertEqual(clusters.Delete(self.cluster_ref), None)
