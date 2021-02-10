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
"""Deny command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import copy
import itertools

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import exceptions
from googlecloudsdk.command_lib.org_policies import interfaces
from googlecloudsdk.command_lib.org_policies import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Deny(interfaces.OrgPolicyGetAndUpdateCommand):
  r"""Add (or remove) values to the list of denied values for a list constraint, or optionally deny all values.

  Adds (or removes) values to the list of denied values for a list constraint,
  or optionally denies all values. Specify no values when calling this command
  to deny all values. If values are being added and the policy does not exist,
  the policy will be created. Cannot be used with conditional policies.

  ## EXAMPLES
  To add 'us-east1' and 'us-west1' to the list of denied values on the policy
  associated with the constraint 'gcp.resourceLocations' and the Project
  'foo-project', run:

    $ {command} gcp.resourceLocations us-east1 us-west1 --project=foo-project
  """

  @staticmethod
  def Args(parser):
    super(Deny, Deny).Args(parser)
    arguments.AddValueArgToParser(parser)
    parser.add_argument(
        '--remove',
        action='store_true',
        help='Remove the specified values from the list of denied values instead of adding them.'
    )

  def Run(self, args):
    """Extends the superclass method to do validation and disable creation of a new policy if --remove is specified.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The updated policy.
    """
    if not args.value and args.remove:
      raise exceptions.InvalidInputError(
          'One or more values need to be specified if --remove is specified.')

    if args.remove:
      self.disable_create = True

    return super(Deny, self).Run(args)

  def UpdatePolicy(self, policy, args):
    """Adds (or removes) values to the list of denied values or denies all values on the policy.

    If one or more values are specified and --remove is specified, then a
    workflow for removing values is used. This workflow searches
    for and removes the specified values from the lists of denied values on the
    rules. Any modified rule with empty lists of allowed values and denied
    values after this operation is deleted.

    If one or more values are specified and --remove is not specified, then a
    workflow for adding values is used. This workflow first executes the remove
    workflow, except it removes values from the lists of allowed values instead
    of the lists of denied values. It then checks to see if the policy already
    has all the specified values. If not, it searches for all rules that without
    conditions. If one of the rules has denyAll set to True, the policy is
    returned as is. If no rule is found, a new rule is created. The list of
    denied values on the found or created rule is updated to include the
    missing values. Duplicate values specified by the user are pruned.

    If no values are specified, then a workflow for denying all values is used.
    A new rule is created. The denyAll field on the created rule is set to True.

    Args:
      policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
        updated.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The updated policy.
    """
    if not args.value:
      return self._DenyAllValues(policy)

    if args.remove:
      return utils.RemoveDeniedValuesFromPolicy(policy, args,
                                                self.ReleaseTrack())

    return self._AddValues(policy, args)

  def _AddValues(self, policy, args):
    """Adds values to an eligible policy rule.

    This first searches for and removes the specified values from the
    lists of allowed values on those rules. Any modified rule with empty lists
    of allowed values and denied values after this operation is deleted. This
    then checks to see if the policy already has all the specified values. If
    not, it searches for all rules that without conditions. If one of the rules
    has denyAll set to True, the policy is returned as is. If no rule is found,
    a new rule is created. The list of denied values on the found or created
    rule is updated to include the missing values. Duplicate values specified by
    the user are pruned.

    Args:
      policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
        updated.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The updated policy.
    """
    new_policy = copy.deepcopy(policy)
    new_policy = utils.RemoveAllowedValuesFromPolicy(new_policy, args,
                                                     self.ReleaseTrack())

    missing_values = self._GetMissingDeniedValuesFromRules(
        new_policy.spec.rules, args.value)
    if not missing_values:
      return new_policy

    if not new_policy.spec.rules:
      rule_to_update, new_policy = utils.CreateRuleOnPolicy(
          new_policy, self.ReleaseTrack())
    else:
      for rule in new_policy.spec.rules:
        if rule.denyAll:
          return new_policy

      rule_to_update = new_policy.spec.rules[0]
      # Unset allowAll and denyAll in case they are False.
      rule_to_update.allowAll = None
      rule_to_update.denyAll = None

    if rule_to_update.values is None:
      rule_to_update.values = self.org_policy_api.BuildPolicySpecPolicyRuleStringValues(
      )
    rule_to_update.values.deniedValues += list(missing_values)

    return new_policy

  def _DenyAllValues(self, policy):
    """Denies all values by removing old rules and creating a new rule with denyAll set to True.

    Args:
      policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
        updated.

    Returns:
      The updated policy.
    """
    new_rule = self.org_policy_api.BuildPolicySpecPolicyRule()
    new_rule.denyAll = True

    new_policy = copy.deepcopy(policy)
    new_policy.spec.rules = [new_rule]

    return new_policy

  def _GetMissingDeniedValuesFromRules(self, rules, values):
    """Returns a list of unique values missing from the set of denied values aggregated across the specified rules.

    Args:
      rules: [messages.GoogleCloudOrgpolicyV2alpha1PolicyPolicyRule], The list
        of policy rules to aggregate the missing denied values from.
      values: [str], The list of values to check the existence of.

    Returns:
      Missing allowed values.
    """
    if rules is None:
      rules = []

    # Create a set out of all the denied values on all the specified rules.
    existing_value_lists = [
        rule.values.deniedValues for rule in rules if rule.values
    ]
    existing_values = set(itertools.chain.from_iterable(existing_value_lists))

    # Aggregate the new values that are missing from the set of existing values.
    missing_values = collections.OrderedDict.fromkeys(
        value for value in values if value not in existing_values)
    return list(missing_values)
