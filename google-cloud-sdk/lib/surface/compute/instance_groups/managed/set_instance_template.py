# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Command for setting instance template of managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


class SetInstanceTemplate(base.Command):
  r"""Set instance template for managed instance group.

    *{command}* updates the instance template for an existing managed instance
  group.

  The new template won't apply to existing instances in the group unless they
  are recreated using the recreate-instances command. But the new template does
  apply to all new instances added to the managed instance group.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument('--template',
                        required=True,
                        help=('Compute Engine instance template resource '
                              'to be used.'))
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    igm_ref = (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.
               ResolveAsResource)(
                   args, holder.resources,
                   default_scope=compute_scope.ScopeEnum.ZONE,
                   scope_lister=flags.GetDefaultScopeLister(client))
    template_ref = holder.resources.Parse(
        args.template,
        params={
            'project': igm_ref.project,
        },
        collection='compute.instanceTemplates')

    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      service = client.apitools_client.instanceGroupManagers
      request = (client.messages.
                 ComputeInstanceGroupManagersSetInstanceTemplateRequest(
                     instanceGroupManager=igm_ref.Name(),
                     instanceGroupManagersSetInstanceTemplateRequest=(
                         client.messages.
                         InstanceGroupManagersSetInstanceTemplateRequest(
                             instanceTemplate=template_ref.SelfLink())),
                     project=igm_ref.project,
                     zone=igm_ref.zone))
    else:
      service = client.apitools_client.regionInstanceGroupManagers
      request = (
          client.messages.
          ComputeRegionInstanceGroupManagersSetInstanceTemplateRequest(
              instanceGroupManager=igm_ref.Name(),
              regionInstanceGroupManagersSetTemplateRequest=(
                  client.messages.RegionInstanceGroupManagersSetTemplateRequest(
                      instanceTemplate=template_ref.SelfLink())),
              project=igm_ref.project,
              region=igm_ref.region))

    return client.MakeRequests([(service, 'SetInstanceTemplate', request)])
