# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Resources that are shared by two or more tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

beta_messages = core_apis.GetMessagesModule('compute', 'beta')
v1_messages = core_apis.GetMessagesModule('compute', 'v1')


def MakeInterconnectLocation(name='default-name',
                             description='Bell-Canada',
                             peeringdb_facility_id='38',
                             address='111 8th Ave',
                             facility_provider='google-partner-provider',
                             facility_provider_facility_id='111 8th',
                             location_ref=None):

  return v1_messages.InterconnectLocation(
      name=name,
      description=description,
      peeringdbFacilityId=peeringdb_facility_id,
      address=address,
      facilityProvider=facility_provider,
      facilityProviderFacilityId=facility_provider_facility_id,
      selfLink=location_ref.SelfLink(),
  )


def MakeInterconnectBeta(
    name='default-name',
    description='description',
    interconnect_type=beta_messages.Interconnect.
    InterconnectTypeValueValuesEnum.IT_PRIVATE,
    link_type=beta_messages.Interconnect.LinkTypeValueValuesEnum.
    LINK_TYPE_ETHERNET_10G_LR,
    requested_link_count=5,
    operational_status=None,
    admin_enabled=None,
    interconnect_ref=None,
    location=None,
):
  return beta_messages.Interconnect(
      name=name,
      description=description,
      interconnectType=interconnect_type,
      linkType=link_type,
      requestedLinkCount=requested_link_count,
      location=location,
      operationalStatus=operational_status,
      adminEnabled=admin_enabled,
      selfLink=interconnect_ref.SelfLink())


def MakeInterconnectGA(
    name='default-name',
    description='description',
    interconnect_type=v1_messages.Interconnect.InterconnectTypeValueValuesEnum.
    DEDICATED,
    link_type=v1_messages.Interconnect.LinkTypeValueValuesEnum.
    LINK_TYPE_ETHERNET_10G_LR,
    requested_link_count=5,
    operational_status=None,
    admin_enabled=None,
    interconnect_ref=None,
    location=None,
):
  return v1_messages.Interconnect(
      name=name,
      description=description,
      interconnectType=interconnect_type,
      linkType=link_type,
      requestedLinkCount=requested_link_count,
      location=location,
      operationalStatus=operational_status,
      adminEnabled=admin_enabled,
      selfLink=interconnect_ref.SelfLink())


def MakeInterconnectAttachment(name='my-attachment',
                               description='description',
                               interconnect_ref=None,
                               router_ref=None,
                               attachment_ref=None,
                               region='us-central1'):
  return v1_messages.InterconnectAttachment(
      name=name,
      description=description,
      interconnect=interconnect_ref.SelfLink(),
      router=router_ref.SelfLink(),
      region=region,
      selfLink=attachment_ref.SelfLink())
