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
"""Shared flags for Cloud Domains commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.apis import arg_utils


def AddConfigureDNSSettingsFlagsToParser(parser):
  """Get flags for changing DNS settings.

  Args:
    parser: argparse parser to which to add these flags.
  """
  _AddDNSSettingsFlagsToParser(parser, allow_from_file=True)

  base.Argument(  # This is not a go/gcloud-style#commonly-used-flags.
      '--unsafe-dns-update',
      default=False,
      action='store_true',
      help='Use this flag to allow DNS changes that may make '
      'your domain stop serving.').AddToParser(parser)


def AddConfigureContactsSettingsFlagsToParser(parser):
  """Get flags for changing contact settings.

  Args:
    parser: argparse parser to which to add these flags.
  """
  _AddContactSettingsFlagsToParser(parser, is_update=True)

  base.Argument(  # This is not a go/gcloud-style#commonly-used-flags.
      '--notices',
      help='Notices about special properties of contacts.',
      metavar='NOTICE',
      type=arg_parsers.ArgList(
          element_type=str,
          choices=CONTACT_NOTICE_ENUM_MAPPER.choices)).AddToParser(parser)


def AddRegisterFlagsToParser(parser):
  """Get flags for registering a domain.

  Args:
    parser: argparse parser to which to add these flags.
  """
  _AddDNSSettingsFlagsToParser(parser, allow_from_file=False)
  _AddContactSettingsFlagsToParser(parser, is_update=False)
  base.Argument(  # This is not a go/gcloud-style#commonly-used-flags.
      '--yearly-price',
      help=('You have to accept the yearly price of the domain, either in the '
            'interactive flow or using this flag. The expected format is a '
            'number followed by a currency code, e.g. "12.00USD". You can get '
            'the price using the get-register-parameters command.'),
  ).AddToParser(parser)

  notice_choices = CONTACT_NOTICE_ENUM_MAPPER.choices.copy()
  notice_choices.update({
      'hsts-preloaded':
          ('By sending this notice you acknowledge that the domain is '
           'preloaded on the HTTP Strict Transport Security list in browsers. '
           'Serving a website on such domain will require an SSL certificate. '
           'See https://support.google.com/domains/answer/7638036 for details.')
  })
  base.Argument(  # This is not a go/gcloud-style#commonly-used-flags.
      '--notices',
      help='Notices about special properties of certain domains or contacts.',
      metavar='NOTICE',
      type=arg_parsers.ArgList(element_type=str,
                               choices=notice_choices)).AddToParser(parser)


def _AddDNSSettingsFlagsToParser(parser, allow_from_file):
  """Get flags for providing DNS settings.

  Args:
    parser: argparse parser to which to add these flags.
    allow_from_file: If true, --dns-settings-from-file will also be added.
  """
  dns_group = base.ArgumentGroup(
      mutex=True,
      help=('Set the addresses of authoritative name servers for the given '
            'domain.'),
      category=base.COMMONLY_USED_FLAGS)
  dns_group.AddArgument(
      base.Argument(
          '--name-servers',
          help='List of DNS name servers for the domain.',
          metavar='NAME_SERVER',
          type=arg_parsers.ArgList(str, min_length=2)))
  dns_group.AddArgument(
      base.Argument(
          '--cloud-dns-zone',
          help=(
              'The name of the Cloud DNS managed-zone to set as the name '
              'server for the domain.\n'
              'If it\'s in the same project, you can use short name. If not, '
              'use the full resource name, e.g.: --cloud-dns-zone='
              'projects/example-project/managedZones/example-zone.\n'
              'DNS Security (DNSSEC) is turned on by default (if possible).')))
  dns_group.AddArgument(
      base.Argument(
          '--use-google-domains-dns',
          help=('Use free name servers provided by Google Domains. \n'
                'DNS Security (DNSSEC) is turned on by default.'),
          default=False,
          action='store_true'))
  if allow_from_file:
    dns_group.AddArgument(
        base.Argument(
            '--dns-settings-from-file',
            help=("""\
        A YAML file containing the required DNS settings.
        If specified, its content will replace the values currently used in the
        registration resource. It means, that if the file is missing some of the
        dns_settings field, they will be cleared.

        Examples of file contents:

        ```
        googleDomainsDns:
          dsState: DS_RECORDS_PUBLISHED
        glueRecords:
        - hostName: ns1.example.com
          ipv4Addresses:
          - 8.8.8.8
        - hostName: ns2.example.com
          ipv4Addresses:
          - 8.8.8.8
        ```

        ```
        customDns:
          nameServers:
          - new.ns1.com
          - new.ns2.com
          dsRecords:
          - keyTag: 24
            algorithm: RSASHA1
            digestType: SHA256
            digest: 2e1cfa82b035c26cbbbdae632cea070514eb8b773f616aaeaf668e2f0be8f10d
          - keyTag: 42
            algorithm: RSASHA1
            digestType: SHA256
            digest: 2e1cfa82bf35c26cbbbdae632cea070514eb8b773f616aaeaf668e2f0be8f10d
        ```

        Warning: Do not change name servers if ds_records is non-empty. Clear
        ds_records first and wait 24 hours before changing name servers.
        Otherwise your domain may stop serving.
            """)))
  dns_group.AddToParser(parser)
  base.Argument(
      '--disable-dnssec',
      help="""\
      When using Cloud DNS Zone or Google Domains nameservers the DNS Security
      (DNSSEC) will be enabled for the domain (unless the zone is not signed).
      Use this flag to disable DNSSEC.
      """,
      default=False,
      action='store_true').AddToParser(parser)


def _AddContactSettingsFlagsToParser(parser, is_update):
  """Get flags for providing Contact settings.

  Args:
    parser: argparse parser to which to add these flags.
    is_update: Set to True for the update command and to False for Register or
      Transfer commands.
  """
  help_text = """\
    A YAML file containing the required contact data. It can specify contact data with label
    'allContacts' (it means that a single contact will be used for registrant, admin and technical
    contacts) or separate contact data with labels 'registrantContact', 'adminContact' and
    'technicalContact'.
    {}
    If specified, each contact data must contain values for all required fields: email,
    phoneNumber and postalAddress in google.type.PostalAddress format.

    For more guidance on how to specify postalAddress, please see:
    https://support.google.com/business/answer/6397478

    Examples of file contents:

    ```
    allContacts:
      email: 'example@example.com'
      phoneNumber: '+1.8005550123'
      postalAddress:
        regionCode: 'US'
        postalCode: '94043'
        administrativeArea: 'CA'
        locality: 'Mountain View'
        addressLines: ['1600 Amphitheatre Pkwy']
        recipients: ['Jane Doe']
    ```
    {}
    ```
    registrantContact:
      email: 'registrant@example.com'
      phoneNumber: '+1.8005550123'
      postalAddress:
        regionCode: 'US'
        postalCode: '94043'
        administrativeArea: 'CA'
        locality: 'Mountain View'
        addressLines: ['1600 Amphitheatre Pkwy']
        recipients: ['Registrant Jane Doe']
    adminContact:
      email: 'admin@example.com'
      phoneNumber: '+1.8005550123'
      postalAddress:
        regionCode: 'US'
        postalCode: '94043'
        administrativeArea: 'CA'
        locality: 'Mountain View'
        addressLines: ['1600 Amphitheatre Pkwy']
        recipients: ['Admin Jane Doe']
    technicalContact:
      email: 'technical@example.com'
      phoneNumber: '+1.8005550123'
      postalAddress:
        regionCode: 'US'
        postalCode: '94043'
        administrativeArea: 'CA'
        locality: 'Mountain View'
        addressLines: ['1600 Amphitheatre Pkwy']
        recipients: ['Technic Jane Doe']
    ```
    """
  if is_update:
    help_text = help_text.format(
        """
    If 'registrantContact', 'adminContact' or 'technicalContact' labels are used
    then only the specified contact is updated.
    """, """
    ```
    adminContact:
      email: 'admin@example.com'
      phoneNumber: '+1.8005550123'
      postalAddress:
        regionCode: 'US'
        postalCode: '94043'
        administrativeArea: 'CA'
        locality: 'Mountain View'
        addressLines: ['1600 Amphitheatre Pkwy']
        recipients: ['Admin Jane Doe']
    ```
        """)
  else:
    help_text = help_text.format('', '')

  base.Argument(
      '--contact-data-from-file',
      help=help_text,
      category=base.COMMONLY_USED_FLAGS).AddToParser(parser)

  def _ChoiceValueType(value):
    """Copy of base._ChoiceValueType."""
    return value.replace('_', '-').lower()

  base.Argument(
      '--contact-privacy',
      choices=CONTACT_PRIVACY_ENUM_MAPPER.choices,
      type=_ChoiceValueType,
      help='The contact privacy mode to use. Supported privacy modes depend on the domain.',
      required=False,
      category=base.COMMONLY_USED_FLAGS).AddToParser(parser)


def AddValidateOnlyFlagToParser(parser, verb):
  """Adds validate_only flag as go/gcloud-style#commonly-used-flags."""
  base.Argument(
      '--validate-only',
      help='Don\'t actually {} registration. Only validate arguments.'.format(
          verb),
      default=False,
      action='store_true',
      category=base.COMMONLY_USED_FLAGS).AddToParser(parser)


def AddAsyncFlagToParser(parser):
  """Adds async flag. It's not marked as go/gcloud-style#commonly-used-flags."""
  base.ASYNC_FLAG.AddToParser(parser)


def AddManagementSettingsFlagsToParser(parser):
  """Get flags for configure management command.

  Args:
    parser: argparse parser to which to add these flags.
  """

  TRANSFER_LOCK_ENUM_MAPPER.choice_arg.AddToParser(parser)


def _GetContactPrivacyEnum():
  """Get Contact Privacy Enum from api messages."""
  messages = apis.GetMessagesModule('domains', 'v1alpha2')
  return messages.ContactSettings.PrivacyValueValuesEnum


CONTACT_PRIVACY_ENUM_MAPPER = arg_utils.ChoiceEnumMapper(
    '--contact-privacy',
    _GetContactPrivacyEnum(),
    custom_mappings={
        'PRIVATE_CONTACT_DATA':
            ('private-contact-data',
             ('Your contact info won\'t be available to the public. To help '
              'protect your info and prevent spam, a third party provides '
              'alternate (proxy) contact info for your domain in the public '
              'directory at no extra cost. They will forward received messages '
              'to you.')),
        'REDACTED_CONTACT_DATA': ('redacted-contact-data', (
            'Limited personal info will be available to the public. The actual '
            'information redacted depends on the domain. For more information '
            'see https://support.google.com/domains/answer/3251242?hl=en.')),
        'PUBLIC_CONTACT_DATA':
            ('public-contact-data',
             ('All the data from contact config is publicly available.')),
    },
    required=False,
    help_str=('The contact privacy mode to use. Supported privacy modes '
              'depend on the domain.'))


def PrivacyChoiceStrength(privacy):
  """Returns privacy strength (stronger privacy means higher returned value)."""
  if privacy == 'public-contact-data':
    return 0
  if privacy == 'redacted-contact-data':
    return 1
  if privacy == 'private-contact-data':
    return 2


def _GetContactNoticeEnum():
  """Get ContactNoticeEnum from api messages."""
  messages = apis.GetMessagesModule('domains', 'v1alpha2')
  return messages.ConfigureContactSettingsRequest.ContactNoticesValueListEntryValuesEnum


CONTACT_NOTICE_ENUM_MAPPER = arg_utils.ChoiceEnumMapper(
    '--notices',
    _GetContactNoticeEnum(),
    custom_mappings={
        'PUBLIC_CONTACT_DATA_ACKNOWLEDGEMENT':
            ('public-contact-data-acknowledgement',
             ('By sending this notice you acknowledge that using '
              'public-contact-data contact privacy makes all the data '
              'from contact config publicly available.')),
    },
    required=False,
    help_str=('Notices about special properties of contacts.'))


def _GetTransferLockEnum():
  """Get TransferLockStateValueValuesEnum from api messages."""
  messages = apis.GetMessagesModule('domains', 'v1alpha2')
  return messages.ManagementSettings.TransferLockStateValueValuesEnum


TRANSFER_LOCK_ENUM_MAPPER = arg_utils.ChoiceEnumMapper(
    '--transfer-lock-state',
    _GetTransferLockEnum(),
    custom_mappings={
        'LOCKED': ('locked', ('The transfer lock is locked.')),
        'UNLOCKED': ('unlocked', ('The transfer lock is unlocked.')),
    },
    required=False,
    help_str=('Transfer Lock of a registration. It needs to be unlocked '
              'in order to transfer the domain to another registrar.'))
