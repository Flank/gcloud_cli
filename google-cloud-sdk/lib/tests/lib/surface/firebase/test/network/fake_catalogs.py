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
"""Fake network-profiles catalogs for testing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

TESTING_MESSAGES = apis.GetMessagesModule('testing', 'v1')


def EmptyNetworkConfigCatalog():
  """Returns a fake network configuration catalog containing no configs."""
  return TESTING_MESSAGES.NetworkConfigurationCatalog(configurations=[])


def FakeNetworkConfigCatalog():
  """Returns a fake network configuration catalog containing two configs."""
  config1 = TESTING_MESSAGES.NetworkConfiguration(
      id='LTE',
      upRule=TESTING_MESSAGES.TrafficRule(
          delay='1',
          packetLossRatio=0.2,
          packetDuplicationRatio=0.3,
          bandwidth=4.4,
          burst=5.5),
      downRule=TESTING_MESSAGES.TrafficRule(
          delay='6',
          packetLossRatio=0.7,
          packetDuplicationRatio=0.8,
          bandwidth=9.9,
          burst=10))
  config2 = TESTING_MESSAGES.NetworkConfiguration(
      id='EDGE',
      upRule=TESTING_MESSAGES.TrafficRule(
          delay='10',
          packetLossRatio=0.02,
          packetDuplicationRatio=0.03,
          bandwidth=0.44,
          burst=0.55),
      downRule=TESTING_MESSAGES.TrafficRule(
          delay='60',
          packetLossRatio=0.07,
          packetDuplicationRatio=0.08,
          bandwidth=0.99,
          burst=1.0))
  return TESTING_MESSAGES.NetworkConfigurationCatalog(
      configurations=[config1, config2])
