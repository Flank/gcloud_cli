# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Common flags for some of the DNS commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.concepts import concept_parsers


class BetaKeyCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(BetaKeyCompleter, self).__init__(
        collection='dns.dnsKeys',
        api_version='v1beta2',
        list_command=('beta dns dns-keys list --format=value(keyTag)'),
        parse_output=True,
        flags=['zone'],
        **kwargs)


class KeyCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(KeyCompleter, self).__init__(
        collection='dns.dnsKeys',
        api_version='v1',
        list_command=('dns dns-keys list --format=value(keyTag)'),
        parse_output=True,
        flags=['zone'],
        **kwargs)


class ManagedZoneCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ManagedZoneCompleter, self).__init__(
        collection='dns.managedZones',
        list_command='dns managed-zones list --uri',
        **kwargs)


def GetKeyArg(help_text='The DNS key identifier.', is_beta=False):
  return base.Argument(
      'key_id',
      metavar='KEY-ID',
      completer=BetaKeyCompleter if is_beta else KeyCompleter,
      help=help_text)


def GetDnsZoneArg(help_text):
  return base.Argument(
      'dns_zone', metavar='ZONE_NAME',
      completer=ManagedZoneCompleter,
      help=help_text)


def ZoneAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='zone',
      help_text='The Cloud DNS zone for the {resource}.')


def GetZoneResourceSpec():
  return concepts.ResourceSpec(
      'dns.managedZones',
      resource_name='zone',
      managedZone=ZoneAttributeConfig(),
      project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetZoneResourceArg(help_text, positional=True, plural=False):
  arg_name = 'zones' if plural else 'zone'
  return concept_parsers.ConceptParser.ForResource(
      arg_name if positional else '--{}'.format(arg_name),
      GetZoneResourceSpec(),
      help_text,
      plural=plural,
      required=True)


def GetZoneArg(help_text=(
    'Name of the managed zone whose record sets you want to manage.'),
               hide_short_zone_flag=False):
  if hide_short_zone_flag:
    zone_group = base.ArgumentGroup(required=True)
    zone_group.AddArgument(
        base.Argument(
            '--zone',
            completer=ManagedZoneCompleter,
            help=help_text))
    zone_group.AddArgument(
        base.Argument(
            '-z',
            dest='zone',
            completer=ManagedZoneCompleter,
            help=help_text,
            hidden=True))
    return zone_group
  else:
    return base.Argument(
        '--zone',
        '-z',
        completer=ManagedZoneCompleter,
        help=help_text,
        required=True)


def GetManagedZonesDnsNameArg():
  return base.Argument(
      '--dns-name',
      required=True,
      help='The DNS name suffix that will be managed with the created zone.')


def GetZoneIdArg(
    help_text=(
        'The unique system generated id for the peering zone to deactivate.')):
  return base.Argument('--zone-id', required=True, help=help_text)


def GetPeeringZoneListArg():
  return base.Argument(
      '--target-network',
      required=True,
      help='The network url of the Google Compute Engine private network '
      'to forward queries to.')


def GetManagedZonesDescriptionArg(required=False):
  return base.Argument(
      '--description',
      required=required,
      help='Short description for the managed-zone.')


def GetDnsSecStateFlagMapper(messages):
  return arg_utils.ChoiceEnumMapper(
      '--dnssec-state', messages.ManagedZoneDnsSecConfig.StateValueValuesEnum,
      custom_mappings={
          'off': ('off', 'Disable DNSSEC for the managed zone.'),
          'on': ('on', 'Enable DNSSEC for the managed zone.'),
          'transfer': ('transfer', ('Enable DNSSEC and allow '
                                    'transferring a signed zone in '
                                    'or out.'))
      },
      help_str='The DNSSEC state for this managed zone.')


def GetDoeFlagMapper(messages):
  return arg_utils.ChoiceEnumMapper(
      '--denial-of-existence',
      messages.ManagedZoneDnsSecConfig.NonExistenceValueValuesEnum,
      help_str='Requires DNSSEC enabled.')


def GetKeyAlgorithmFlag(key_type, messages):
  return arg_utils.ChoiceEnumMapper(
      '--{}-algorithm'.format(key_type),
      messages.DnsKeySpec.AlgorithmValueValuesEnum,
      help_str='String mnemonic specifying the DNSSEC algorithm of the '
               'key-signing key. Requires DNSSEC enabled')


def AddCommonManagedZonesDnssecArgs(parser, messages):
  """Add Common DNSSEC flags for the managed-zones group."""
  GetDnsSecStateFlagMapper(messages).choice_arg.AddToParser(parser)
  GetDoeFlagMapper(messages).choice_arg.AddToParser(parser)
  GetKeyAlgorithmFlag('ksk', messages).choice_arg.AddToParser(parser)
  GetKeyAlgorithmFlag('zsk', messages).choice_arg.AddToParser(parser)
  parser.add_argument(
      '--ksk-key-length',
      type=int,
      help='Length of the key-signing key in bits. Requires DNSSEC enabled.')
  parser.add_argument(
      '--zsk-key-length',
      type=int,
      help='Length of the zone-signing key in bits. Requires DNSSEC enabled.')


def GetManagedZoneVisibilityArg():
  return base.Argument(
      '--visibility',
      choices=['public', 'private'],
      default='public',
      help='Visibility of the zone. Public zones are visible to the public '
      'internet. Private zones are only visible in your internal '
      'networks denoted by the `--networks` flag.')


def GetManagedZoneNetworksArg():
  return base.Argument(
      '--networks',
      metavar='NETWORK',
      type=arg_parsers.ArgList(),
      help='List of networks that the zone should be visible in if the zone '
      'visibility is [private].')


def GetManagedZoneGkeClustersArg():
  return base.Argument(
      '--gkeclusters',
      metavar='GKECLUSTERS',
      type=arg_parsers.ArgList(),
      help='List of GKE clusters that the zone should be visible in if the zone '
      'visibility is [private].')


def GetDnsPeeringArgs():
  """Return arg group for DNS Peering flags."""
  peering_group = base.ArgumentGroup(required=False)
  target_network_help_text = (
      'Network ID of the Google Compute Engine private network to forward'
      ' queries to.')
  target_project_help_text = (
      'Project ID of the Google Compute Engine private network to forward'
      ' queries to.')
  peering_group.AddArgument(
      base.Argument(
          '--target-network',
          required=True,
          help=target_network_help_text))
  peering_group.AddArgument(
      base.Argument(
          '--target-project',
          required=True,
          help=target_project_help_text))
  return peering_group


def GetForwardingTargetsArg():
  return base.Argument(
      '--forwarding-targets',
      type=arg_parsers.ArgList(),
      metavar='IP_ADDRESSES',
      help=('List of IPv4 addresses of target name servers that the zone '
            'will forward queries to. Ignored for `public` visibility. '
            'Non-RFC1918 addresses will forward to the target through the '
            'Internet. RFC1918 addresses will forward through the VPC.'))


def GetPrivateForwardingTargetsArg():
  return base.Argument(
      '--private-forwarding-targets',
      type=arg_parsers.ArgList(),
      metavar='IP_ADDRESSES',
      help=(
          'List of IPv4 addresses of target name servers that the zone '
          'will forward queries to. Ignored for `public` visibility. '
          'All addresses specified for this parameter will be reached through the VPC.'
      ))


def GetReverseLookupArg():
  return base.Argument(
      '--managed-reverse-lookup',
      action='store_true',
      default=None,
      help='Whether this zone is a managed reverse lookup zone, required for '
      'Cloud DNS to correctly resolve Non-RFC1918 PTR records.')


def GetServiceDirectoryArg():
  return base.Argument(
      '--service-directory-namespace',
      required=False,
      help='The fully qualified URL of the service directory namespace that '
      'should be associated with the zone. Ignored for `public` visibility '
      'zones.')


# Policy Flags
def GetPolicyDescriptionArg(required=False):
  return base.Argument(
      '--description', required=required, help='A description of the policy.')


def GetPolicyNetworksArg(required=False):
  return base.Argument(
      '--networks',
      type=arg_parsers.ArgList(),
      metavar='NETWORKS',
      required=required,
      help=('The comma separated list of network names to associate with '
            'the policy.'))


def GetPolicyInboundForwardingArg():
  return base.Argument(
      '--enable-inbound-forwarding',
      action='store_true',
      help=('Specifies whether to allow networks bound to this policy to '
            'receive DNS queries sent by VMs or applications over VPN '
            'connections. Defaults to False.'))


def GetPolicyLoggingArg():
  return base.Argument(
      '--enable-logging',
      action='store_true',
      help='Specifies whether to enable query logging. Defaults to False.')


def GetPolicyAltNameServersArg():
  return base.Argument(
      '--alternative-name-servers',
      type=arg_parsers.ArgList(),
      metavar='NAME_SERVERS',
      help=('List of alternative name servers to forward to. Non-RFC1918 '
            'addresses will forward to the target through the Internet.'
            'RFC1918 addresses will forward through the VPC.'))


def GetPolicyPrivateAltNameServersArg():
  return base.Argument(
      '--private-alternative-name-servers',
      type=arg_parsers.ArgList(),
      metavar='NAME_SERVERS',
      help=(
          'List of alternative name servers to forward to. '
          'All addresses specified for this parameter will be reached through the VPC.'
      ))


## ResourceRecordSets flags.
def GetResourceRecordSetsNameArg():
  return base.Argument(
      'name',
      metavar='DNS_NAME',
      help='DNS or domain name of the record-set.')


def GetResourceRecordSetsTypeArg(required=False):
  return base.Argument(
      '--type',
      required=required,
      help='DNS record type of the record-set (e.g. A, AAAA, MX etc.).')


def GetResourceRecordSetsTtlArg(required=False):
  return base.Argument(
      '--ttl',
      type=int,
      required=required,
      help='TTL (time to live) for the record-set.')


def GetResourceRecordSetsRrdatasArg(required=False):
  return base.Argument(
      '--rrdatas',
      metavar='RRDATA',
      required=required,
      type=arg_parsers.ArgList(),
      help='DNS data (Address/CNAME/MX info, etc.) of the record-set. '
      'This is RDATA; the format of this information varies depending '
      'on the type and class of the resource record.')


def GetResourceRecordSetsRrdatasArgGroup():
  """Returns arg group for rrdatas flags.

  This group is defined with required=True and mutex=True, meaning that exactly
  one of these two arg configurations must be specified:
    --rrdatas
    --routing_policy_type AND --routing_policy_data
  """
  # Declare optional routing policy group. If group specified, must contain
  # both routing_policy_type and routing_policy_data args.
  policy_group = base.ArgumentGroup(
      required=False,
      help='Routing policy arguments. If you specify one of --routing_policy_data or --routing_policy_type, you must specify both.'
  )
  policy_group.AddArgument(
      GetResourceRecordSetsRoutingPolicyTypeArg(required=True))
  policy_group.AddArgument(
      GetResourceRecordSetsRoutingPolicyDataArg(required=True))

  rrdatas_group = base.ArgumentGroup(
      required=True,
      mutex=True,
      help='Resource record sets arguments. Can specify either --rrdatas or both --routing_policy_data and --routing_policy_type.'
  )
  rrdatas_group.AddArgument(GetResourceRecordSetsRrdatasArg(required=False))
  rrdatas_group.AddArgument(policy_group)

  return rrdatas_group


def GetResourceRecordSetsRoutingPolicyTypeArg(required=False):
  return base.Argument(
      '--routing_policy_type',
      metavar='ROUTING_POLICY_TYPE',
      required=required,
      choices=['GEO', 'WRR'],
      help='Indicates what type of routing policy is being specified. As of '
      'this time, this field can take on either "WRR" for weighted round '
      'robin, or "GEO" for geo location. This field cannot be modified - once '
      'a policy has chosen a type, the only way to change it is to delete the '
      'policy and add a new one with the different type.')


def GetResourceRecordSetsRoutingPolicyDataArg(required=False):
  """Returns --routing_policy_data command line arg value."""

  def RoutingPolicyDataArgType(routing_policy_data_value):
    """Converts --routing_policy_data flag value to a list of policy data items.

    Args:
      routing_policy_data_value: String value specified in the
        --routing_policy_data flag.

    Returns:
      A list of policy data items in the format below:

    [
        { 'key': <routing_policy_data_key1>, 'rrdatas': <IP address list> },
        { 'key': <routing_policy_data_key2>, 'rrdatas': <IP address list> },
        ...
    ]

    Where <routing_policy_data_key> is either a weight or location name,
    depending on whether the user specified --routing_policy_type == WRR or
    --routing_policy_type == GEO, respectively. We keep
    <routing_policy_data_key> a string value, even in the case of weights
    (which will eventually be interpereted as floats). This is to keep this
    flag type generic between WRR and GEO types.
    """
    routing_policy_data = []

    # Grab each policy data item, split by ';'
    policy_items = routing_policy_data_value.split(';')
    for policy_item in policy_items:
      # Grab key and value from policy_item, split by ':'
      key_value_split = policy_item.split('=')

      # Ensure that there is only one key and value from the string split on ':'
      if len(key_value_split) != 2:
        raise arg_parsers.ArgumentTypeError(
            'Must specify exactly one "=" inside each policy data item')
      key = key_value_split[0]
      value = key_value_split[1]

      # Grab list of IPs from value, split by ','
      ip_list = value.split(',')
      routing_policy_data.append({'key': key, 'rrdatas': ip_list})

    return routing_policy_data

  return base.Argument(
      '--routing_policy_data',
      metavar='ROUTING_POLICY_DATA',
      required=required,
      type=RoutingPolicyDataArgType,
      help='The routing policy data supports one of two formats below, '
      'depending on the choice of routing_policy_type.\n\n'
      'For --routing_policy_type = "WRR" this flag indicates the weighted '
      'round robin policy data. The field accepts a semicolon-delimited list '
      'of the format "${weight_percent}:${rrdata},${rrdata}". Specify weight '
      'as a non-negative number (0 is allowed). Ratio of traffic '
      'routed to the target is calculated from the ratio of individual weight '
      'over the total across all weights.\n\n'
      'For --routing_policy_type = "GEO" this flag indicates the geo-locations '
      'policy data. The field accepts a semicolon-delimited list of the format '
      '"${region}:${rrdata},${rrdata}".')


# Response Policy Flags
def GetResponsePolicyDescriptionArg(required=False):
  return base.Argument(
      '--description', required=required,
      help='A description of the response policy.')


def GetResponsePolicyNetworksArg(required=False):
  return base.Argument(
      '--networks',
      type=arg_parsers.ArgList(),
      required=required,
      metavar='NETWORKS',
      help='The comma-separated list of network names to associate with '
            'the response policy.')
CHANGES_FORMAT = 'table(id, startTime, status)'
RESOURCERECORDSETS_FORMAT = 'table(name, type, ttl, rrdatas.list():label=DATA)'


def GetResponsePolicyGkeClustersArg(required=False):
  return base.Argument(
      '--gkeclusters',
      type=arg_parsers.ArgList(),
      required=required,
      metavar='GKECLUSTERS',
      help='The comma-separated list of GKE cluster names to associate with '
            'the response policy.')


# Response Policy Rule Flags
def GetResponsePolicyRulesBehaviorFlagMapper(messages):
  return arg_utils.ChoiceEnumMapper(
      '--behavior',
      messages.ResponsePolicyRule.BehaviorValueValuesEnum,
      include_filter=lambda x: x != 'behaviorUnspecified',
      help_str='The response policy rule query behavior.')


def AddResponsePolicyRulesBehaviorFlagArgs(parser, messages):
  GetResponsePolicyRulesBehaviorFlagMapper(messages).choice_arg.AddToParser(
      parser)


def GetLocalDataResourceRecordSets():
  return base.Argument(
      '--local-data',
      type=arg_parsers.ArgDict(spec={
          'name': str,
          'type': str,
          'ttl': int,
          'rrdatas': str
      }),
      metavar='LOCAL_DATA',
      action='append',
      help="""\
    All resource record sets for this selector, one per resource record
    type. The name must match the dns_name.

    This is a repeated argument that can be specified multiple times to specify
    multiple local data rrsets.
    (e.g. --local-data=name="zone.com.",type="A",ttl=21600,rrdata="1.2.3.4 "
    --local-data=name="www.zone.com.",type="CNAME",ttl=21600,rrdata="1.2.3.4|5.6.7.8")

    *name*::: The DnsName of a resource record set.

    *type*::: Type of all resource records in this set. For example, A, AAAA, SOA, MX,
    NS, TXT ...

    *ttl*::: Number of seconds that this ResourceRecordSet can be cached by resolvers.

    *rrdatas*::: The list of datas for this record, split by "|".
    """)


def GetResponsePolicyRuleBehavior():
  return base.Argument('--behavior', type=enumerate)
