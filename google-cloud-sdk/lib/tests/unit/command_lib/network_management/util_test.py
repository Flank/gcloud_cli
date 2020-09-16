# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Unit tests for `gcloud network-management` utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.command_lib.network_management import util
from tests.lib import sdk_test_base
import mock


class ValidationTestBase(sdk_test_base.SdkBase):

  def SetUp(self):
    self.ref = mock.Mock()
    self.request = mock.Mock()

  def createArgs(self, arg_name, arg_value):

    def IsSpecified(name):
      return name == arg_name

    args = argparse.Namespace()
    setattr(args, arg_name, arg_value)
    args.IsSpecified = IsSpecified
    return args


class ValidateInstanceNamesTest(ValidationTestBase):

  def validateInstance(self, flag_name, flag_value):
    args = self.createArgs(flag_name, flag_value)
    return util.ValidateInstanceNames(self.ref, args, self.request)

  def shouldAcceptInstanceName(self, instance_name):
    result = self.validateInstance("source_instance", instance_name)
    self.assertEqual(result, self.request)

    result = self.validateInstance("destination_instance", instance_name)
    self.assertEqual(result, self.request)

  def shouldRejectInstanceName(self, instance_name):
    with self.assertRaises(util.InvalidInputError):
      self.validateInstance("destination_instance", instance_name)
    with self.assertRaises(util.InvalidInputError):
      self.validateInstance("source_instance", instance_name)

  def testValidateInstanceNames(self):
    self.shouldAcceptInstanceName(
        "projects/google.com:project/zones/us-central1-a/instances/instance")
    self.shouldAcceptInstanceName(
        "projects/project/zones/us-central1-a/instances/instance")
    self.shouldRejectInstanceName("projects/project/instances/instance")
    self.shouldRejectInstanceName(
        "projects/project/zones/us-central1-a/instance/instance")
    self.shouldRejectInstanceName("instance-name")


class ValidateNetworkURIsTest(ValidationTestBase):

  def validateNetwork(self, flag_name, flag_value):
    args = self.createArgs(flag_name, flag_value)
    return util.ValidateNetworkURIs(self.ref, args, self.request)

  def shouldAcceptNetworkURI(self, network_name):
    result = self.validateNetwork("source_network", network_name)
    self.assertEqual(result, self.request)

    result = self.validateNetwork("destination_network", network_name)
    self.assertEqual(result, self.request)

  def shouldRejectNetworkURI(self, network_name):
    with self.assertRaises(util.InvalidInputError):
      self.validateNetwork("destination_network", network_name)
    with self.assertRaises(util.InvalidInputError):
      self.validateNetwork("source_network", network_name)

  def testValidateNetworkURIs(self):
    self.shouldAcceptNetworkURI("projects/project/global/networks/default")
    self.shouldAcceptNetworkURI(
        "projects/google.com:project/global/networks/default")
    self.shouldRejectNetworkURI("projects/project/networks/default")
    self.shouldRejectNetworkURI("projects/project/network/default")
    self.shouldRejectNetworkURI("default")


class ValidateGKEMasterClustersURIsTest(ValidationTestBase):

  def validateGKEMasterCluster(self, flag_name, flag_value):
    args = self.createArgs(flag_name, flag_value)
    return util.ValidateGKEMasterClustersURIs(self.ref, args, self.request)

  def shouldAcceptGKEMasterClustersURI(self, cluster_uri):
    result = self.validateGKEMasterCluster("source_gke_master_cluster",
                                           cluster_uri)
    self.assertEqual(result, self.request)

    result = self.validateGKEMasterCluster("destination_gke_master_cluster",
                                           cluster_uri)
    self.assertEqual(result, self.request)

  def shouldRejectGKEMasterClustersURI(self, cluster_uri):
    with self.assertRaises(util.InvalidInputError):
      self.validateGKEMasterCluster("source_gke_master_cluster", cluster_uri)
    with self.assertRaises(util.InvalidInputError):
      self.validateGKEMasterCluster("destination_gke_master_cluster",
                                    cluster_uri)

  def testValidateGKEMasterCluster(self):
    self.shouldAcceptGKEMasterClustersURI(
        "projects/google.com:project/locations/us-central1/clusters/cluster-1")
    self.shouldAcceptGKEMasterClustersURI(
        "projects/project/locations/us-central1-a/clusters/cluster-1")
    self.shouldAcceptGKEMasterClustersURI(
        "projects/project/zones/us-central1-a/clusters/cluster-1")
    self.shouldRejectGKEMasterClustersURI("projects/project/clusters/cluster-1")
    self.shouldRejectGKEMasterClustersURI("cluster-1")


class ValidateCloudSQLInstancesURIsTest(ValidationTestBase):

  def validateCloudSQLInstance(self, flag_name, flag_value):
    args = self.createArgs(flag_name, flag_value)
    return util.ValidateCloudSQLInstancesURIs(self.ref, args, self.request)

  def shouldAcceptCloudSQLInstancesURI(self, cluster_uri):
    result = self.validateCloudSQLInstance("source_cloud_sql_instance",
                                           cluster_uri)
    self.assertEqual(result, self.request)

    result = self.validateCloudSQLInstance("destination_cloud_sql_instance",
                                           cluster_uri)
    self.assertEqual(result, self.request)

  def shouldRejectCloudSQLInstancesURI(self, cluster_uri):
    with self.assertRaises(util.InvalidInputError):
      self.validateCloudSQLInstance("source_cloud_sql_instance", cluster_uri)
    with self.assertRaises(util.InvalidInputError):
      self.validateCloudSQLInstance("destination_cloud_sql_instance",
                                    cluster_uri)

  def testValidateCloudSQLInstance(self):
    self.shouldAcceptCloudSQLInstancesURI(
        "projects/my-project/instances/my-instance")
    self.shouldRejectCloudSQLInstancesURI(
        "projects/my-project/locations/loc/instances/my-instance")
    self.shouldRejectCloudSQLInstancesURI("my-instance")
