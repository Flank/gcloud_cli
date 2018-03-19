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
"""Command for creating Google Compute Engine routers."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.networks import flags as network_flags
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.command_lib.compute.routers import router_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class CreateWithCustomAdvertisements(base.CreateCommand):
  """Create a Google Compute Engine router.

     *{command}* is used to create a router to provide dynamic routing to VPN
     tunnels and interconnects.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    """See base.CreateCommand."""

    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.NETWORK_ARG = network_flags.NetworkArgumentForOtherResource(
        'The network for this router')
    cls.NETWORK_ARG.AddArgument(parser)
    cls.ROUTER_ARG = flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser, operation_type='create')
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddCreateRouterArgs(parser)
    flags.AddReplaceCustomAdvertisementArgs(parser, 'router')
    parser.display_info.AddCacheUpdater(flags.RoutersCompleter)

  def Run(self, args):
    """See base.CreateCommand."""

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    service = holder.client.apitools_client.routers

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)
    network_ref = self.NETWORK_ARG.ResolveAsResource(args, holder.resources)

    router_resource = messages.Router(
        name=router_ref.Name(),
        description=args.description,
        network=network_ref.SelfLink(),
        bgp=messages.RouterBgp(asn=args.asn))

    if router_utils.HasReplaceAdvertisementFlags(args):
      mode, groups, ranges = router_utils.ParseAdvertisements(
          messages=messages, resource_class=messages.RouterBgp, args=args)

      attrs = {
          'advertiseMode': mode,
          'advertisedGroups': groups,
          'advertisedIpRanges': ranges,
      }

      for attr, value in attrs.iteritems():
        if value is not None:
          setattr(router_resource.bgp, attr, value)

    result = service.Insert(
        messages.ComputeRoutersInsertRequest(
            router=router_resource,
            region=router_ref.region,
            project=router_ref.project))

    operation_ref = resources.REGISTRY.Parse(
        result.name,
        collection='compute.regionOperations',
        params={
            'project': router_ref.project,
            'region': router_ref.region,
        })

    if args.async:
      # Override the networks list format with the default operations format
      if not args.IsSpecified('format'):
        args.format = 'none'
      log.CreatedResource(
          operation_ref,
          kind='router [{0}]'.format(router_ref.Name()),
          async=True,
          details='Run the [gcloud compute operations describe] command '
          'to check the status of this operation.')
      return result

    target_router_ref = holder.resources.Parse(
        router_ref.Name(),
        collection='compute.routers',
        params={
            'project': router_ref.project,
            'region': router_ref.region,
        })

    operation_poller = poller.Poller(service, target_router_ref)
    return waiter.WaitFor(operation_poller, operation_ref,
                          'Creating router [{0}]'.format(router_ref.Name()))
