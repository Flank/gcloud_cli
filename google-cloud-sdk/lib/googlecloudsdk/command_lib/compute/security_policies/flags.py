# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute security policies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util import completers


class GlobalSecurityPoliciesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(GlobalSecurityPoliciesCompleter, self).__init__(
        collection='compute.securityPolicies',
        list_command='compute security-policies list --uri',
        **kwargs)


class RegionalSecurityPoliciesCompleter(compute_completers.ListCommandCompleter
                                       ):

  def __init__(self, **kwargs):
    super(RegionalSecurityPoliciesCompleter, self).__init__(
        collection='compute.regionSecurityPolicies',
        list_command=('compute security-policies list '
                      '--filter=region:* --uri'),
        **kwargs)


class SecurityPoliciesCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(SecurityPoliciesCompleter, self).__init__(
        completers=[
            GlobalSecurityPoliciesCompleter, RegionalSecurityPoliciesCompleter
        ],
        **kwargs)


def SecurityPolicyArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      completer=SecurityPoliciesCompleter,
      plural=plural,
      custom_plural='security policies',
      required=required,
      global_collection='compute.securityPolicies')


def SecurityPolicyMultiScopeArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      completer=SecurityPoliciesCompleter,
      plural=plural,
      custom_plural='security policies',
      required=required,
      global_collection='compute.securityPolicies',
      regional_collection='compute.regionSecurityPolicies')


def SecurityPolicyArgumentForTargetResource(resource, required=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      name='--security-policy',
      completer=SecurityPoliciesCompleter,
      plural=False,
      required=required,
      global_collection='compute.securityPolicies',
      short_help=('The security policy that will be set for this {0}.'.format(
          resource)))


def SecurityPolicyMultiScopeArgumentForTargetResource(resource, required=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      name='--security-policy',
      completer=SecurityPoliciesCompleter,
      plural=False,
      required=required,
      global_collection='compute.securityPolicies',
      regional_collection='compute.regionSecurityPolicies',
      short_help=(
          ('The security policy that will be set for this {0}. To remove the '
           'policy from this {0} set the policy to an empty string.'
          ).format(resource)))


def EdgeSecurityPolicyArgumentForTargetResource(resource, required=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      name='--edge-security-policy',
      completer=SecurityPoliciesCompleter,
      plural=False,
      required=required,
      global_collection='compute.securityPolicies',
      short_help=(
          ('The edge security policy that will be set for this {0}. To remove '
           'the policy from this {0} set the policy to an empty string.'
          ).format(resource)))


def SecurityPolicyArgumentForRules(required=False):
  return compute_flags.ResourceArgument(
      resource_name='security policy',
      name='--security-policy',
      completer=SecurityPoliciesCompleter,
      plural=False,
      required=required,
      global_collection='compute.securityPolicies',
      short_help='The security policy that this rule belongs to.')


def AddCloudArmorAdaptiveProtection(parser, required=False):
  """Adds the cloud armor adaptive protection arguments to the argparse."""
  parser.add_argument(
      '--enable-layer7-ddos-defense',
      action='store_true',
      default=None,
      required=required,
      help=('Whether to enable Cloud Armor Layer 7 DDoS Defense Adaptive '
            'Protection.'))
  parser.add_argument(
      '--layer7-ddos-defense-rule-visibility',
      choices=['STANDARD', 'PREMIUM'],
      type=lambda x: x.upper(),
      required=required,
      metavar='VISIBILITY_TYPE',
      help=('The visibility type indicates whether the rules are opaque or '
            'transparent.'))


def AddAdvancedOptions(parser, required=False):
  """Adds the cloud armor advanced options arguments to the argparse."""
  parser.add_argument(
      '--json-parsing',
      choices=['DISABLED', 'STANDARD'],
      type=lambda x: x.upper(),
      required=required,
      help=('The JSON parsing behavior for this rule. '
            'Must be one of the following values: [DISABLED, STANDARD].'))
  parser.add_argument(
      '--log-level',
      choices=['NORMAL', 'VERBOSE'],
      type=lambda x: x.upper(),
      required=required,
      help='The level of detail to display for WAF logging.')


def AddDdosProtectionConfig(parser, required=False):
  """Adds the cloud armor DDoS protection config arguments to the argparse."""
  parser.add_argument(
      '--ddos-protection',
      choices=['STANDARD', 'ADVANCED'],
      type=lambda x: x.upper(),
      required=required,
      help=(
          'The DDoS protection level for network load balancing and instances '
          'with external IPs'))
