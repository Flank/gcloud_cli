# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Flags and helpers for the compute forwarding-rules commands."""

import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.addresses import flags as addresses_flags
from googlecloudsdk.command_lib.util import completers


FORWARDING_RULES_OVERVIEW = """\
        A forwarding rule directs traffic that matches a bound IP address to a
        forwarding target (load balancer, VPN gateway or VM instance).

        Forwarding rules can be either global or regional, specified with the
        ``--global'' or ``--region=REGION'' flag. Global forwarding rules work
        with global load balancers, which include target HTTP proxies, target
        HTTPS proxies, target SSL proxies and target TCP proxies; regional
        forwarding rules work with regional or zonal targets, which include
        target pools, target instances and target VPN gateways and backend
        services.

        Forwarding rules can be either external or internal, specified with the
        ``--load-balancing-scheme=[EXTERNAL|INTERNAL]'' flag. External
        forwarding rules are accessible from the internet, while internal
        forwarding rules are only accessible from within their VPC networks. You
        can specify a reserved static external or internal IP address with the
        ``--address=ADDRESS'' flag for the forwarding rule. Otherwise if the
        flag is unspecified, an external forwaring rule will be automatically
        assigned an ephemeral external IP address (global IP addresses for
        global forwarding rules and regional IP addresses for regional
        forwarding rules); an internal forwarding rule will be automatically
        assigned an ephemeral internal IP address from the subnet specified with
        the ``--subnet'' flag.

        There are different types of load balancer working at different layers
        of the OSI networking model
        (http://en.wikipedia.org/wiki/Network_layer). Layer 3 load balancer
        targets include target pools, target SSL proxies, target TCP proxies and
        backend services. Layer 7 load balancer targets include target HTTP
        proxies and target HTTPS proxies. For more information on load
        balancing, see
        https://cloud.google.com/compute/docs/load-balancing-and-autoscaling/.
        """


class ForwardingRulesZonalCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ForwardingRulesZonalCompleter, self).__init__(
        collection='compute.forwardingRules',
        list_command=('compute forwarding-rules list --filter=region:* --uri'),
        **kwargs)


class ForwardingRulesGlobalCompleter(
    compute_completers.GlobalListCommandCompleter):

  def __init__(self, **kwargs):
    super(ForwardingRulesGlobalCompleter, self).__init__(
        collection='compute.globalForwardingRules',
        list_command='compute forwarding-rules list --global --uri',
        **kwargs)


class ForwardingRulesCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(ForwardingRulesCompleter, self).__init__(
        completers=[ForwardingRulesGlobalCompleter,
                    ForwardingRulesZonalCompleter],
        **kwargs)


def ForwardingRuleArgument(required=True):
  return compute_flags.ResourceArgument(
      resource_name='forwarding rule',
      completer=ForwardingRulesCompleter,
      required=required,
      regional_collection='compute.forwardingRules',
      global_collection='compute.globalForwardingRules',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def ForwardingRuleArgumentPlural(required=True):
  return compute_flags.ResourceArgument(
      resource_name='forwarding rule',
      completer=ForwardingRulesCompleter,
      plural=True,
      required=required,
      regional_collection='compute.forwardingRules',
      global_collection='compute.globalForwardingRules',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
    name='--backend-service',
    required=False,
    resource_name='backend service',
    regional_collection='compute.regionBackendServices',
    global_collection='compute.targetBackendServices',
    short_help='The target backend service that will receive the traffic.',
    region_explanation=('If not specified it will be set the'
                        ' region of the forwarding rule.'))

NETWORK_ARG = compute_flags.ResourceArgument(
    name='--network',
    required=False,
    resource_name='networks',
    global_collection='compute.networks',
    short_help='The network that this forwarding rule applies to.',
    detailed_help="""\
        (Only for --load-balancing-scheme=INTERNAL) The network that this
        forwarding rule applies to. If this field is not specified, the default
        network will be used. In the absence of the default network, this field
        must be specified.
        """)

SUBNET_ARG = compute_flags.ResourceArgument(
    name='--subnet',
    required=False,
    resource_name='subnetwork',
    regional_collection='compute.subnetworks',
    short_help='The subnet that this forwarding rule applies to.',
    detailed_help="""\
        (Only for --load-balancing-scheme=INTERNAL) The subnetwork that this
        forwarding rule applies to. If the network configured for this
        forwarding rule is in auto subnet mode, this flag is optional and the
        subnet in the same region of the forwarding rule will be used. However,
        if the network is in custom subnet mode, a subnetwork must be specified.
        """,
    region_explanation=('If not specified it will be set the'
                        ' region of the forwarding rule.'))

TARGET_HTTP_PROXY_ARG = compute_flags.ResourceArgument(
    name='--target-http-proxy',
    required=False,
    resource_name='http proxy',
    global_collection='compute.targetHttpProxies',
    short_help='The target HTTP proxy that will receive the traffic.',
    detailed_help=('The target HTTP proxy that will receive the traffic. '
                   'Acceptable values for --ports flag are: 80, 8080.'))

TARGET_HTTPS_PROXY_ARG = compute_flags.ResourceArgument(
    name='--target-https-proxy',
    required=False,
    resource_name='https proxy',
    global_collection='compute.targetHttpsProxies',
    short_help='The target HTTPS proxy that will receive the traffic.',
    detailed_help=('The target HTTPS proxy that will receive the traffic. '
                   'Acceptable values for --ports flag are: 443.'))

TARGET_INSTANCE_ARG = compute_flags.ResourceArgument(
    name='--target-instance',
    required=False,
    resource_name='target instance',
    zonal_collection='compute.targetInstances',
    short_help='The name of the target instance that will receive the traffic.',
    detailed_help=textwrap.dedent("""\
      The name of the target instance that will receive the traffic. The
      target instance must be in a zone that's in the forwarding rule's
      region. Global forwarding rules may not direct traffic to target
      instances.
      """) + compute_flags.ZONE_PROPERTY_EXPLANATION)

TARGET_POOL_ARG = compute_flags.ResourceArgument(
    name='--target-pool',
    required=False,
    resource_name='target pool',
    regional_collection='compute.targetPools',
    short_help='The target pool that will receive the traffic.',
    detailed_help="""\
      The target pool that will receive the traffic. The target pool
      must be in the same region as the forwarding rule. Global
      forwarding rules may not direct traffic to target pools.
      """,
    region_explanation=('If not specified it will be set the'
                        ' region of the forwarding rule.'))

TARGET_SSL_PROXY_ARG = compute_flags.ResourceArgument(
    name='--target-ssl-proxy',
    required=False,
    resource_name='ssl proxy',
    global_collection='compute.targetSslProxies',
    short_help='The target SSL proxy that will receive the traffic.',
    detailed_help=('The target SSL proxy that will receive the traffic. '
                   'Acceptable values for --ports flag are: '
                   '25, 43, 110, 143, 195, 443, 465, 587, '
                   '700, 993, 995, 1883, 5222.'))

TARGET_TCP_PROXY_ARG = compute_flags.ResourceArgument(
    name='--target-tcp-proxy',
    required=False,
    resource_name='tcp proxy',
    global_collection='compute.targetTcpProxies',
    short_help='The target TCP proxy that will receive the traffic.',
    detailed_help=('The target TCP proxy that will receive the traffic. '
                   'Acceptable values for --ports flag are: '
                   '25, 43, 110, 143, 195, 443, 465, 587, '
                   '700, 993, 995, 1883, 5222.'))

TARGET_VPN_GATEWAY_ARG = compute_flags.ResourceArgument(
    name='--target-vpn-gateway',
    required=False,
    resource_name='VPN gateway',
    regional_collection='compute.targetVpnGateways',
    short_help='The target VPN gateway that will receive forwarded traffic.',
    detailed_help=(
        'The target VPN gateway that will receive forwarded traffic. '
        'Acceptable values for --ports flag are: 500, 4500.'),
    region_explanation=('If not specified it will be set the'
                        ' region of the forwarding rule.'))


ADDRESS_ARG = compute_flags.ResourceArgument(
    name='--address',
    required=False,
    resource_name='address',
    completer=addresses_flags.AddressesCompleter,
    regional_collection='compute.addresses',
    global_collection='compute.globalAddresses',
    region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION,
    short_help='The IP address that the forwarding rule will serve.',
    detailed_help="""\
      The IP address that the forwarding rule will serve. All
      traffic sent to this IP address is directed to the target
      pointed to by the forwarding rule. Assigned IP addresses can be
      reserved or unreserved.

      IP addresses are restricted based on the forwarding rule's load balancing
      scheme (EXTERNAL or INTERNAL) and scope (global or regional).

      When the --load-balancing-scheme is EXTERNAL, if the address is reserved,
      it must either (1) reside in the global scope if the forwarding rule is
      being configured to point to a global target (target HTTP proxy, target
      HTTPS proxy, target SSL proxy and target TCP proxy) or (2) reside in the
      same region as the forwarding rule if the forwarding rule is being
      configured to point to a regional target (target pool) or zonal target
      (target instance). If this flag is omitted, an ephemeral external IP
      address is automatically assigned.

      When the --load-balancing-scheme is INTERNAL, this can only be an RFC 1918
      IP address belonging to the network/subnet configured for the forwarding
      rule. If this flag is omitted, an ephemeral internal IP address will be
      automatically allocated from the IP range of the subnet or network
      configured for this forwarding rule.

      Note: An IP address must be specified if the traffic is being forwarded to
      a VPN.

      This flag can be specified either by a literal IP address or a reference
      to an existing Address resource. The following examples are all valid:
      - 100.1.2.3
      - https://www.googleapis.com/compute/v1/projects/project-1/regions/us-central1/addresses/address-1
      - projects/project-1/regions/us-central1/addresses/address-1
      - regions/us-central1/addresses/address-1
      - global/addresses/address-1
      - address-1
      """)


def AddUpdateArgs(parser, include_beta=False, include_alpha=False):
  """Adds common flags for mutating forwarding rule targets."""
  del include_alpha
  del include_beta
  target = parser.add_mutually_exclusive_group(required=True)

  TARGET_HTTP_PROXY_ARG.AddArgument(parser, mutex_group=target)
  TARGET_HTTPS_PROXY_ARG.AddArgument(parser, mutex_group=target)
  TARGET_INSTANCE_ARG.AddArgument(parser, mutex_group=target)
  TARGET_POOL_ARG.AddArgument(parser, mutex_group=target)
  TARGET_SSL_PROXY_ARG.AddArgument(parser, mutex_group=target)
  TARGET_TCP_PROXY_ARG.AddArgument(parser, mutex_group=target)
  TARGET_VPN_GATEWAY_ARG.AddArgument(parser, mutex_group=target)

  BACKEND_SERVICE_ARG.AddArgument(parser, mutex_group=target)
  NETWORK_ARG.AddArgument(parser)
  SUBNET_ARG.AddArgument(parser)

  parser.add_argument(
      '--load-balancing-scheme',
      choices={
          'EXTERNAL':
              'External load balancing or forwarding, used with one of '
              '--target-http-proxy, --target-https-proxy, --target-tcp-proxy, '
              '--target-ssl-proxy, --target-pool, --target-vpn-gateway, '
              '--target-instance.',
          'INTERNAL': 'Internal load balancing or forwarding, used with '
                      '--backend-service.',
      },
      type=lambda x: x.upper(),
      default='EXTERNAL',
      help='This signifies what the forwarding rule will be used for.')


def AddIPProtocols(parser):
  """Adds IP protocols flag, with values available in the given version."""

  protocols = ['AH', 'ESP', 'ICMP', 'SCTP', 'TCP', 'UDP']

  parser.add_argument(
      '--ip-protocol',
      choices=protocols,
      type=lambda x: x.upper(),
      help='The IP protocol that the rule will serve. The default is TCP.')


def AddIpVersionGroup(parser):
  """Adds IP versions flag in a mutually exclusive group."""
  parser.add_argument(
      '--ip-version',
      choices=['IPV4', 'IPV6'],
      type=lambda x: x.upper(),
      help="""\
      The version of the IP address to be allocated if no --address is given.
      The default is IPv4.
      """)


def AddAddressesAndIPVersions(parser, required=True):
  """Adds Addresses and IP versions flag."""
  group = parser.add_mutually_exclusive_group(required=required)
  AddIpVersionGroup(group)
  ADDRESS_ARG.AddArgument(parser, mutex_group=group)


def AddDescription(parser):
  """Adds description flag."""

  parser.add_argument(
      '--description',
      help='An optional textual description for the forwarding rule.')


def AddPortsAndPortRange(parser):
  """Adds ports and port range flags."""

  ports_scope = parser.add_mutually_exclusive_group()
  ports_scope.add_argument(
      '--ports',
      metavar='[PORT | START_PORT-END_PORT]',
      type=arg_parsers.ArgList(
          min_length=1, element_type=arg_parsers.Range.Parse),
      default=[],
      help="""\
      If specified, only packets addressed to ports in the specified
      list will be forwarded. If not specified for regional forwarding
      rules, all ports are matched. This flag is required for global
      forwarding rules and accepts a single continuous set of ports.

      Some forwarding targets have restriction on acceptable ports, e.g., if
      --target-http-proxy is specified, the acceptable values for --ports are:
      80, 8080.

      Individual ports and ranges can be specified,
      for example (`--ports 8000-8004` or `--ports 80`).
      """)

  ports_scope.add_argument(
      '--port-range',
      type=arg_parsers.Range.Parse,
      metavar='[PORT | START_PORT-END_PORT]',
      help="""\
      DEPRECATED, use --ports. If specified, only packets addressed to ports in
      the specified range will be forwarded. If not specified for regional
      forwarding rules, all ports are matched. This flag is required for global
      forwarding rules.

      Either an individual port (`--port-range 80`) or a range of ports
      (`--port-range 3000-3100`) may be specified.
      """)


def AddNetworkTier(parser, include_alpha, for_update):
  """Adds network tier flag."""

  # This arg is a string simulating enum NetworkTier because one of the
  # option SELECT is hidden since it's not advertised to all customers.
  if include_alpha:
    if for_update:
      parser.add_argument(
          '--network-tier',
          type=lambda x: x.upper(),
          help="""\
          Update the network tier of a forwarding rule. It does not allow to
          change from `PREMIUM` to `STANDARD` and visa versa.
          """)
    else:
      parser.add_argument(
          '--network-tier',
          type=lambda x: x.upper(),
          help="""\
          The network tier to assign to the forwarding rules. ``NETWORK_TIER''
          must be one of: `PREMIUM`, `STANDARD`. The default value is `PREMIUM`.
          """)
