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
"""Delete command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import utils
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  r"""Delete an organization policy.

  Deletes an organization policy.

  ## EXAMPLES

  To delete the policy associated with the constraint 'gcp.resourceLocations'
  and the Project 'foo-project', run:

   $ {command} gcp.resourceLocations --project=foo-project
  """

  @staticmethod
  def Args(parser):
    arguments.AddConstraintArgToParser(parser)
    arguments.AddResourceFlagsToParser(parser)

  def Run(self, args):
    """Deletes an organization policy.

    The policy is deleted using DeletePolicy.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
       If the policy is deleted, then messages.GoogleProtobufEmpty.
    """
    policy_service = org_policy_service.PolicyService()
    org_policy_messages = org_policy_service.OrgPolicyMessages()

    policy_name = utils.GetPolicyNameFromArgs(args)

    delete_request = org_policy_messages.OrgpolicyPoliciesDeleteRequest(
        name=policy_name)
    delete_response = policy_service.Delete(delete_request)
    log.DeletedResource(policy_name, 'policy')
    return delete_response
