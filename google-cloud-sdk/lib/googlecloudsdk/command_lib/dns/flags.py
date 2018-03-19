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

"""Common flags for some of the DNS commands."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.apis import arg_utils


_DNSEC_MAP = arg_utils.ChoiceEnumMapper(
    '--dnssec-state', (apis.GetMessagesModule('dns', 'v1beta2')
                       .ManagedZoneDnsSecConfig.StateValueValuesEnum),
    custom_mappings={
        'off': ('off', 'Disable DNSSEC for the managed zone.'),
        'on': ('on', 'Enable DNSSEC for the managed zone.'),
        'transfer': ('transfer', ('Enable DNSSEC and allow '
                                  'transferring a signed zone in '
                                  'or out.'))
    },
    help_str='The DNSSEC state for this managed zone.')

_DOE_MAP = arg_utils.ChoiceEnumMapper(
    '--denial-of-existence',
    (apis.GetMessagesModule('dns', 'v2beta1')
     .ManagedZoneDnsSecConfig.NonExistenceValueValuesEnum),
    help_str='Requires DNSSEC enabled.')


class KeyCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(KeyCompleter, self).__init__(
        # TODO(b/63443157): dnsKeys not found on server.
        # Uncomment the next 3 lines when b/63443157 is fixed.
        # collection='dns.dnsKeys',
        # api_version='v2beta1',
        # list_command=('beta dns dnskeys list --flatten=value(keyTag)'),
        # Delete the next line (a workaround hack) when b/63443157 is fixed.
        list_command='beta dns dnskeys list --format=value(keyTag)',
        parse_output=True,
        flags=['zone'],
        **kwargs)


class ManagedZoneCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ManagedZoneCompleter, self).__init__(
        collection='dns.managedZones',
        list_command='dns managed-zones list --uri',
        **kwargs)


def GetKeyArg(help_text='The DNS key identifier.'):
  return base.Argument(
      'key_id',
      metavar='KEY-ID',
      completer=KeyCompleter,
      help=help_text)


def GetDnsZoneArg(help_text):
  return base.Argument(
      'dns_zone', metavar='ZONE_NAME',
      completer=ManagedZoneCompleter,
      help=help_text)


def GetZoneArg(help_text=(
    'Name of the managed-zone whose record-sets you want to manage.')):
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


def GetManagedZonesDescriptionArg(required=False):
  return base.Argument(
      '--description',
      required=required,
      help='Short description for the managed-zone.')


def GetDnsSecStateFlagMapper():
  return _DNSEC_MAP


def GetDoeFlagMapper():
  return _DOE_MAP


def AddCommonManagedZonesDnssecArgs(parser):
  """Add Common DNSSEC flags for the managed-zones group."""
  _DNSEC_MAP.choice_arg.AddToParser(parser)
  _DOE_MAP.choice_arg.AddToParser(parser)
  parser.add_argument(
      '--ksk-algorithm',
      help='String mnemonic specifying the DNSSEC algorithm of the '
           'key-signing key. Requires DNSSEC enabled. Example algorithms: '
           'RSASHA1, RSASHA256, RSASHA512, ECDSAP256SHA256, ECDSAP384SHA384')
  parser.add_argument(
      '--zsk-algorithm',
      help='String mnemonic specifying the DNSSEC algorithm of the '
           'zone-signing key. Requires DNSSEC enabled. Example algorithms: '
           'RSASHA1, RSASHA256, RSASHA512, ECDSAP256SHA256, ECDSAP384SHA384')
  parser.add_argument(
      '--ksk-key-length',
      type=int,
      help='Length of the key-signing key in bits. Requires DNSSEC enabled.')
  parser.add_argument(
      '--zsk-key-length',
      type=int,
      help='Length of the zone-signing key in bits. Requires DNSSEC enabled.')


CHANGES_FORMAT = 'table(id, startTime, status)'
