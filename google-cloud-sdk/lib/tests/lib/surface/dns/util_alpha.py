# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Testing resources for Alpha DNS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib.surface.dns import util


def GetMessages():
  return util.GetMessages("v1alpha2")


def GetManagedZoneBeforeCreation(messages,
                                 dns_sec_config=False,
                                 visibility_dict=None,
                                 forwarding_config=None,
                                 peering_config=None,
                                 service_directory_config=None,
                                 zone_id=None):
  """Generate a create message for a managed zone."""
  m = messages
  mzone = m.ManagedZone(
      creationTime=None,
      description="Zone!",
      dnsName="zone.com.",
      kind=u"dns#managedZone",
      name="mz",
      forwardingConfig=forwarding_config,
      peeringConfig=peering_config,
      serviceDirectoryConfig=service_directory_config,
      id=zone_id)

  if dns_sec_config:
    nonexistence = m.ManagedZoneDnsSecConfig.NonExistenceValueValuesEnum.nsec3
    mzone.dnssecConfig = m.ManagedZoneDnsSecConfig(
        defaultKeySpecs=[],
        kind=u"dns#managedZoneDnsSecConfig",
        nonExistence=nonexistence,
        state=m.ManagedZoneDnsSecConfig.StateValueValuesEnum.on,
    )

  if visibility_dict:
    mzone.visibility = visibility_dict["visibility"]
    if mzone.visibility == m.ManagedZone.VisibilityValueValuesEnum("private"):
      mzone.privateVisibilityConfig = visibility_dict["privateVisibilityConfig"]
  elif hasattr(messages.ManagedZone, "VisibilityValueValuesEnum"):
    mzone.visibility = messages.ManagedZone.VisibilityValueValuesEnum.public

  return mzone


def PeeringConfig(target_project, target_network):
  """Returns ManagedZonePeeringConfig."""
  messages = GetMessages()

  peering_network = ("https://www.googleapis.com/compute/v1/projects/{}/global"
                     "/networks/{}".format(target_project, target_network))
  target_network = messages.ManagedZonePeeringConfigTargetNetwork(
      networkUrl=peering_network)
  peering_config = messages.ManagedZonePeeringConfig(
      targetNetwork=target_network)
  return peering_config
