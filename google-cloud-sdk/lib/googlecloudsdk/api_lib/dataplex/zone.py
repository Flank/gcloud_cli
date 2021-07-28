# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Client for interaction with ZONE API CRUD DATAPLEX."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.command_lib.iam import iam_util


def SetIamPolicy(zone_ref, policy):
  """Set Iam Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesZonesSetIamPolicyRequest(
      resource=zone_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule()
      .GoogleIamV1SetIamPolicyRequest(policy=policy))
  return dataplex_api.GetClientInstance(
  ).projects_locations_lakes_zones.SetIamPolicy(set_iam_policy_req)


def GetIamPolicy(zone_ref):
  """Get Iam Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesZonesGetIamPolicyRequest(
      resource=zone_ref.RelativeName())
  return dataplex_api.GetClientInstance(
  ).projects_locations_lakes_zones.GetIamPolicy(get_iam_policy_req)


def AddIamPolicyBinding(zone_ref, member, role):
  """Add iam policy binding request."""
  policy = GetIamPolicy(zone_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role)
  return SetIamPolicy(zone_ref, policy)


def RemoveIamPolicyBinding(lake_ref, member, role):
  """Remove iam policy binding request."""
  policy = GetIamPolicy(lake_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return SetIamPolicy(lake_ref, policy)


def SetIamPolicyFromFile(zone_ref, policy_file):
  """Set iam policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file,
      dataplex_api.GetMessageModule().GoogleIamV1Policy)
  return SetIamPolicy(zone_ref, policy)


def GenerateZoneForCreateRequest(description, display_name, labels, zone_type,
                                 discovery_spec_enabled, schedule,
                                 bigquery_enabled, dataset_name,
                                 metastore_enabled, database_name,
                                 location_type):
  """Create Zone for Message Create Requests."""
  module = dataplex_api.GetMessageModule()
  return module.GoogleCloudDataplexV1Zone(
      description=description,
      displayName=display_name,
      labels=labels,
      type=module.GoogleCloudDataplexV1Zone.TypeValueValuesEnum(zone_type),
      discoverySpec=module.GoogleCloudDataplexV1ZoneDiscoverySpec(
          enabled=discovery_spec_enabled,
          schedule=schedule,
          publishing=module
          .GoogleCloudDataplexV1ZoneDiscoverySpecMetadataPublishing(
              bigquery=module
              .GoogleCloudDataplexV1ZoneDiscoverySpecMetadataPublishingBigQuery(
                  enabled=bigquery_enabled, datasetName=dataset_name),
              metastore=module.
              GoogleCloudDataplexV1ZoneDiscoverySpecMetadataPublishingMetastore(
                  enabled=metastore_enabled, databaseName=database_name))),
      resourceSpec=module.GoogleCloudDataplexV1ZoneResourceSpec(
          locationType=module.GoogleCloudDataplexV1ZoneResourceSpec
          .LocationTypeValueValuesEnum(location_type)))


def GenerateZoneForUpdateRequest(description, display_name, labels,
                                 discovery_spec_enabled, schedule,
                                 bigquery_enabled, metastore_enabled):
  """Create Zone for Message Update Requests."""
  module = dataplex_api.GetMessageModule()
  module.GoogleCloudDataplexV1Zone(
      description=description,
      displayName=display_name,
      labels=labels,
      discoverySpec=module.GoogleCloudDataplexV1ZoneDiscoverySpec(
          enabled=discovery_spec_enabled,
          schedule=schedule,
          publishing=module
          .GoogleCloudDataplexV1ZoneDiscoverySpecMetadataPublishing(
              bigquery=module
              .GoogleCloudDataplexV1ZoneDiscoverySpecMetadataPublishingBigQuery(
                  enabled=bigquery_enabled),
              metastore=module.
              GoogleCloudDataplexV1ZoneDiscoverySpecMetadataPublishingMetastore(
                  enabled=metastore_enabled))))


def WaitForOperation(operation):
  """Waits for the given google.longrunning.Operation to complete."""
  return dataplex_api.WaitForOperation(
      operation,
      dataplex_api.GetClientInstance().projects_locations_lakes_zones)
