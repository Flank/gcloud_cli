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
"""Resources that are shared by two or more forwarding rules tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')
messages = core_apis.GetMessagesModule('compute', 'v1')

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'


def MakeForwardingRules(msgs, api):
  """Make regional forwarding rule test resources for the given api version."""
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.ForwardingRule(
          name='forwarding-rule-1',
          IPAddress='162.222.178.83',
          IPProtocol=msgs.ForwardingRule.IPProtocolValueValuesEnum.TCP,
          portRange='1-65535',
          region=(prefix + '/projects/my-project/regions/region-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'regions/region-1/forwardingRules/forwarding-rule-1'),
          target=(prefix + '/projects/my-project/'
                  'zones/zone-1/targetInstances/target-1')),

      msgs.ForwardingRule(
          name='forwarding-rule-2',
          IPAddress='162.222.178.84',
          IPProtocol=msgs.ForwardingRule.IPProtocolValueValuesEnum.UDP,
          portRange='1-65535',
          region=(prefix + '/projects/my-project/'
                  'regions/region-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'regions/region-1/forwardingRules/forwarding-rule-2'),
          target=(prefix + '/projects/my-project/'
                  'regions/region-1/targetPools/target-2')),
  ]


def MakeGlobalForwardingRules(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.ForwardingRule(
          name='global-forwarding-rule-1',
          IPAddress='162.222.178.85',
          IPProtocol=msgs.ForwardingRule.IPProtocolValueValuesEnum.TCP,
          portRange='1-65535',
          selfLink=(prefix + '/projects/my-project/'
                    'global/forwardingRules/global-forwarding-rule-1'),
          target=(prefix + '/projects/my-project/'
                  'global/targetHttpProxies/proxy-1')),

      msgs.ForwardingRule(
          name='global-forwarding-rule-2',
          IPAddress='162.222.178.86',
          IPProtocol=msgs.ForwardingRule.IPProtocolValueValuesEnum.UDP,
          portRange='1-65535',
          selfLink=(prefix + '/projects/my-project/'
                    'global/forwardingRules/global-forwarding-rule-2'),
          target=(prefix + '/projects/my-project/'
                  'global/targetHttpProxies/proxy-2')),
  ]

FORWARDING_RULES_ALPHA = MakeForwardingRules(alpha_messages, 'alpha')
FORWARDING_RULES_BETA = MakeForwardingRules(beta_messages, 'beta')
FORWARDING_RULES_V1 = MakeForwardingRules(messages, 'v1')

GLOBAL_FORWARDING_RULES_ALPHA = MakeGlobalForwardingRules(
    alpha_messages, 'alpha')
GLOBAL_FORWARDING_RULES_BETA = MakeGlobalForwardingRules(beta_messages, 'beta')
GLOBAL_FORWARDING_RULES_V1 = MakeGlobalForwardingRules(messages, 'v1')
