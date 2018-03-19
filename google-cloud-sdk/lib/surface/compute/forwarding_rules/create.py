# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Command for creating forwarding rules."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import forwarding_rules_utils as utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import flags
from googlecloudsdk.core import log
import ipaddress
import six


def _Args(parser, include_beta, include_alpha=False):
  """Argument parsing."""
  flags.AddUpdateArgs(parser, include_beta=include_beta,
                      include_alpha=include_alpha)
  flags.AddIPProtocols(parser)
  flags.AddDescription(parser)
  flags.AddPortsAndPortRange(parser)
  flags.AddNetworkTier(parser, include_alpha=include_alpha, for_update=False)
  if include_alpha:
    parser.add_argument(
        '--service-label',
        help='(Only for Internal Load Balancing): '
             'https://cloud.google.com/compute/docs/load-balancing/internal/\n'
             'The DNS label to use as the prefix of the fully qualified domain '
             'name for this forwarding rule. The full name will be internally '
             'generated and output as dnsName. If this field is not specified, '
             'no DNS record will be generated and no DNS name will be output. ')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  FORWARDING_RULE_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    _Args(parser, include_beta=False, include_alpha=False)
    flags.AddAddressesAndIPVersions(parser, required=False)
    cls.FORWARDING_RULE_ARG.AddArgument(parser, operation_type='create')
    parser.display_info.AddCacheUpdater(flags.ForwardingRulesCompleter)

  def ConstructProtocol(self, messages, args):
    if args.ip_protocol:
      return messages.ForwardingRule.IPProtocolValueValuesEnum(
          args.ip_protocol)
    else:
      return

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args, supports_network_tier=False, validate_alpha_args=False):
    """Issues requests necessary to create Forwarding Rules."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    forwarding_rule_ref = self.FORWARDING_RULE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    if forwarding_rule_ref.Collection() == 'compute.globalForwardingRules':
      requests = self._CreateGlobalRequests(client, holder.resources, args,
                                            forwarding_rule_ref)
    elif forwarding_rule_ref.Collection() == 'compute.forwardingRules':
      requests = self._CreateRegionalRequests(
          client, holder.resources, args, forwarding_rule_ref,
          supports_network_tier=supports_network_tier,
          validate_alpha_args=validate_alpha_args)

    return client.MakeRequests(requests)

  def _CreateGlobalRequests(self, client, resources, args, forwarding_rule_ref):
    """Create a globally scoped request."""
    port_range = _ResolvePortRange(args.port_range, args.ports)
    if not port_range:
      raise exceptions.ToolException(
          '[--ports] is required for global forwarding rules.')
    target_ref = utils.GetGlobalTarget(resources, args)
    protocol = self.ConstructProtocol(client.messages, args)

    if args.address is None or args.ip_version:
      ip_version = client.messages.ForwardingRule.IpVersionValueValuesEnum(
          args.ip_version or 'IPV4')
    else:
      ip_version = None

    address = self._ResolveAddress(resources, args,
                                   compute_flags.compute_scope.ScopeEnum.GLOBAL,
                                   forwarding_rule_ref)

    forwarding_rule = client.messages.ForwardingRule(
        description=args.description,
        name=forwarding_rule_ref.Name(),
        IPAddress=address,
        IPProtocol=protocol,
        portRange=port_range,
        target=target_ref.SelfLink(),
        ipVersion=ip_version,
        loadBalancingScheme=_GetLoadBalancingScheme(args, client.messages))

    request = client.messages.ComputeGlobalForwardingRulesInsertRequest(
        forwardingRule=forwarding_rule,
        project=forwarding_rule_ref.project)

    return [(client.apitools_client.globalForwardingRules, 'Insert', request)]

  def ConstructNetworkTier(self, messages, args):
    if args.network_tier:
      network_tier = args.network_tier.upper()
      if network_tier in constants.NETWORK_TIER_CHOICES_FOR_INSTANCE:
        return messages.ForwardingRule.NetworkTierValueValuesEnum(
            args.network_tier)
      else:
        raise exceptions.InvalidArgumentException(
            '--network-tier',
            'Invalid network tier [{tier}]'.format(tier=network_tier))
    else:
      return

  def _CreateRegionalRequests(self, client, resources, args,
                              forwarding_rule_ref, supports_network_tier=False,
                              validate_alpha_args=False):
    """Create a regionally scoped request."""
    target_ref, region_ref = utils.GetRegionalTarget(
        client, resources, args, forwarding_rule_ref,
        include_alpha=validate_alpha_args)
    if not args.region and region_ref:
      args.region = region_ref
    protocol = self.ConstructProtocol(client.messages, args)

    address = self._ResolveAddress(resources, args,
                                   compute_flags.compute_scope.ScopeEnum.REGION,
                                   forwarding_rule_ref)

    forwarding_rule = client.messages.ForwardingRule(
        description=args.description,
        name=forwarding_rule_ref.Name(),
        IPAddress=address,
        IPProtocol=protocol,
        loadBalancingScheme=_GetLoadBalancingScheme(args, client.messages))

    if supports_network_tier:
      network_tier = self.ConstructNetworkTier(client.messages, args)
      forwarding_rule.networkTier = network_tier

    if (target_ref.Collection() == 'compute.regionBackendServices'
       ) or (target_ref.Collection() == 'compute.targetInstances' and
             args.load_balancing_scheme == 'INTERNAL'):
      forwarding_rule.portRange = (
          str(args.port_range) if args.port_range else None)
      if target_ref.Collection() == 'compute.regionBackendServices':
        forwarding_rule.backendService = target_ref.SelfLink()
      else:
        forwarding_rule.target = target_ref.SelfLink()
      if args.ports:
        forwarding_rule.portRange = None
        forwarding_rule.ports = [str(p) for p in _GetPortList(args.ports)]
      if args.subnet is not None:
        if not args.subnet_region:
          args.subnet_region = forwarding_rule_ref.region
        forwarding_rule.subnetwork = flags.SUBNET_ARG.ResolveAsResource(
            args, resources).SelfLink()
      if args.network is not None:
        forwarding_rule.network = flags.NETWORK_ARG.ResolveAsResource(
            args, resources).SelfLink()
    else:
      forwarding_rule.portRange = (
          _ResolvePortRange(args.port_range, args.ports))
      forwarding_rule.target = target_ref.SelfLink()
    if hasattr(args, 'service_label'):
      forwarding_rule.serviceLabel = args.service_label
    request = client.messages.ComputeForwardingRulesInsertRequest(
        forwardingRule=forwarding_rule,
        project=forwarding_rule_ref.project,
        region=forwarding_rule_ref.region)

    return [(client.apitools_client.forwardingRules, 'Insert', request)]

  def _ResolveAddress(self, resources, args, scope, forwarding_rule_ref):
    # Address takes either an ip address or an address resource. If parsing as
    # an IP address fails, then we resolve as a resource.
    address = args.address
    if address is not None:
      try:
        # ipaddress only allows unicode input
        ipaddress.ip_address(six.text_type(args.address))
      except ValueError:
        # TODO(b/37086838): Make sure global/region settings are inherited by
        # address resource.
        if scope == compute_flags.compute_scope.ScopeEnum.REGION:
          if not args.global_address and not args.address_region:
            if forwarding_rule_ref.Collection() == 'compute.forwardingRules':
              args.address_region = forwarding_rule_ref.region
        address_ref = flags.ADDRESS_ARG.ResolveAsResource(
            args, resources,
            default_scope=scope)
        address = address_ref.SelfLink()

    return address


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    _Args(parser, include_beta=True, include_alpha=False)
    flags.AddAddressesAndIPVersions(parser, required=False)
    cls.FORWARDING_RULE_ARG.AddArgument(parser, operation_type='create')
    parser.display_info.AddCacheUpdater(flags.ForwardingRulesCompleter)

  def _CreateGlobalRequests(self, client, resources, args, forwarding_rule_ref):
    """Create a globally scoped request."""
    port_range = _ResolvePortRange(args.port_range, args.ports)
    if not port_range:
      raise exceptions.ToolException(
          '[--ports] is required for global forwarding rules.')
    target_ref = utils.GetGlobalTarget(resources, args)
    protocol = self.ConstructProtocol(client.messages, args)

    if args.address is None or args.ip_version:
      ip_version = client.messages.ForwardingRule.IpVersionValueValuesEnum(
          args.ip_version or 'IPV4')
    else:
      ip_version = None

    address = self._ResolveAddress(resources, args,
                                   compute_flags.compute_scope.ScopeEnum.GLOBAL,
                                   forwarding_rule_ref)

    forwarding_rule = client.messages.ForwardingRule(
        description=args.description,
        name=forwarding_rule_ref.Name(),
        IPAddress=address,
        IPProtocol=protocol,
        portRange=port_range,
        target=target_ref.SelfLink(),
        ipVersion=ip_version,
        loadBalancingScheme=_GetLoadBalancingScheme(args, client.messages))

    request = client.messages.ComputeGlobalForwardingRulesInsertRequest(
        forwardingRule=forwarding_rule,
        project=forwarding_rule_ref.project)

    return [(client.apitools_client.globalForwardingRules, 'Insert', request)]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    _Args(parser, include_beta=True, include_alpha=True)
    flags.AddAddressesAndIPVersions(parser, required=False)
    cls.FORWARDING_RULE_ARG.AddArgument(parser, operation_type='create')
    parser.display_info.AddCacheUpdater(flags.ForwardingRulesCompleter)

  def Run(self, args):
    return self._Run(args, supports_network_tier=True, validate_alpha_args=True)

  def _CreateGlobalRequests(self, client, resources, args, forwarding_rule_ref):
    """Create a globally scoped request."""
    port_range = _ResolvePortRange(args.port_range, args.ports)
    if not port_range:
      raise exceptions.ToolException(
          '[--ports] is required for global forwarding rules.')
    target_ref = utils.GetGlobalTarget(resources, args)
    protocol = self.ConstructProtocol(client.messages, args)
    network_tier = self.ConstructNetworkTier(client.messages, args)

    if args.address is None or args.ip_version:
      ip_version = client.messages.ForwardingRule.IpVersionValueValuesEnum(
          args.ip_version or 'IPV4')
    else:
      ip_version = None

    address = self._ResolveAddress(resources, args,
                                   compute_flags.compute_scope.ScopeEnum.GLOBAL,
                                   forwarding_rule_ref)

    forwarding_rule = client.messages.ForwardingRule(
        description=args.description,
        name=forwarding_rule_ref.Name(),
        IPAddress=address,
        IPProtocol=protocol,
        portRange=port_range,
        target=target_ref.SelfLink(),
        ipVersion=ip_version,
        networkTier=network_tier,
        loadBalancingScheme=_GetLoadBalancingScheme(args, client.messages))

    request = client.messages.ComputeGlobalForwardingRulesInsertRequest(
        forwardingRule=forwarding_rule,
        project=forwarding_rule_ref.project)

    return [(client.apitools_client.globalForwardingRules, 'Insert', request)]


Create.detailed_help = {
    'DESCRIPTION': ("""\
        *{{command}}* is used to create a forwarding rule. {overview}

        When creating a forwarding rule, exactly one of  ``--target-instance'',
        ``--target-pool'', ``--target-http-proxy'', ``--target-https-proxy'',
        ``--target-ssl-proxy'', ``--target-tcp-proxy'', ``--target-vpn-gateway''
        or ``--backend-service'' must be specified."""
                    .format(overview=flags.FORWARDING_RULES_OVERVIEW)),
    'EXAMPLES': """\
        To create a global forwarding rule that will forward all traffic on port
        8080 for IP address ADDRESS to a target http proxy PROXY, run:

          $ {command} RULE_NAME --global --target-http-proxy PROXY --ports 8080 --address ADDRESS

        To create a regional forwarding rule for the subnet SUBNET_NAME on the
        default network that will forward all traffic on ports 80-82 to a
        backend service SERVICE_NAME, run:

          $ {command} RULE_NAME --load-balancing-scheme INTERNAL --backend-service SERVICE_NAME --subnet SUBNET_NAME --network default --region REGION --ports 80-82
    """
}


CreateBeta.detailed_help = Create.detailed_help
CreateAlpha.detailed_help = Create.detailed_help


def _GetPortRange(ports_range_list):
  """Return single range by combining the ranges."""
  if not ports_range_list:
    return None, None
  ports = sorted(ports_range_list)
  combined_port_range = ports.pop(0)
  for port_range in ports_range_list:
    try:
      combined_port_range = combined_port_range.Combine(port_range)
    except arg_parsers.Error:
      raise exceptions.InvalidArgumentException(
          '--ports', 'Must specify consecutive ports at this time.')
  return combined_port_range


def _ResolvePortRange(port_range, port_range_list):
  """Reconciles deprecated port_range value and list of port ranges."""
  if port_range:
    log.warning('The --port-range flag is deprecated. Use equivalent --ports=%s'
                ' flag.', port_range)
  elif port_range_list:
    port_range = _GetPortRange(port_range_list)
  return str(port_range) if port_range else None


def _GetPortList(range_list):
  ports = []
  for port_range in range_list:
    ports.extend(range(port_range.start, port_range.end + 1))
  return sorted(ports)


def _GetLoadBalancingScheme(args, messages):
  if args.load_balancing_scheme == 'INTERNAL':
    return messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.INTERNAL
  elif args.load_balancing_scheme == 'EXTERNAL':
    return messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.EXTERNAL
  return None
