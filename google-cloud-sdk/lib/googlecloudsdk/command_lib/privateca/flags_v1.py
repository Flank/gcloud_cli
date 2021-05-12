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
"""Helpers for parsing flags and arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ipaddress
import re

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import preset_profiles
from googlecloudsdk.command_lib.privateca import text_utils
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core.util import times

import six

_EMAIL_SAN_REGEX = re.compile('^[^@]+@[^@]+$')
# Any number of labels (any character that is not a dot) concatenated by dots
_DNS_SAN_REGEX = re.compile(r'^([^.]+\.)*[^.]+$')

# Flag definitions

PUBLISH_CA_CERT_CREATE_HELP = """
If this is enabled, the following will happen:
1) The CA certificates will be written to a known location within the CA distribution point.
2) The AIA extension in all issued certificates will point to the CA cert URL in that distribition point.

Note that the same bucket may be used for the CRLs if --publish-crl is set.
"""

PUBLISH_CA_CERT_UPDATE_HELP = """
If this is enabled, the following will happen:
1) The CA certificates will be written to a known location within the CA distribution point.
2) The AIA extension in all issued certificates will point to the CA cert URL in that distribution point.

If this gets disabled, the AIA extension will not be written to any future certificates issued
by this CA. However, an existing bucket will not be deleted, and the CA certificates will not
be removed from that bucket.

Note that the same bucket may be used for the CRLs if --publish-crl is set.
"""

PUBLISH_CRL_CREATE_HELP = """
If this gets enabled, the following will happen:
1) CRLs will be written to a known location within the CA distribution point.
2) The CDP extension in all future issued certificates will point to the CRL URL in that distribution point.

Note that the same bucket may be used for the CA cert if --publish-ca-cert is set.

CRL publication is not supported for CAs in the DevOps tier.
"""

PUBLISH_CRL_UPDATE_HELP = """
If this gets enabled, the following will happen:
1) CRLs will be written to a known location within the CA distribution point.
2) The CDP extension in all future issued certificates will point to the CRL URL in that distribution point.

If this gets disabled, the CDP extension will not be written to any future certificates issued
by CAs in this pool, and new CRLs will not be published to that bucket (which affects existing certs).
However, an existing bucket will not be deleted, and any existing CRLs will not be removed
from that bucket.

Note that the same bucket may be used for the CA cert if --publish-ca-cert is set.

CRL publication is not supported for CAs in the DevOps tier.
"""

_VALID_KEY_USAGES = [
    'digital_signature', 'content_commitment', 'key_encipherment',
    'data_encipherment', 'key_agreement', 'cert_sign', 'crl_sign',
    'encipher_only', 'decipher_only'
]
_VALID_EXTENDED_KEY_USAGES = [
    'server_auth', 'client_auth', 'code_signing', 'email_protection',
    'time_stamping', 'ocsp_signing'
]


def AddPublishCrlFlag(parser, use_update_help_text=False):
  help_text = PUBLISH_CRL_UPDATE_HELP if use_update_help_text else PUBLISH_CRL_CREATE_HELP
  base.Argument(
      '--publish-crl',
      help=help_text,
      action='store_true',
      required=False,
      default=True).AddToParser(parser)


def AddPublishCaCertFlag(parser, use_update_help_text=False):
  help_text = PUBLISH_CA_CERT_UPDATE_HELP if use_update_help_text else PUBLISH_CA_CERT_CREATE_HELP
  base.Argument(
      '--publish-ca-cert',
      help=help_text,
      action='store_true',
      required=False,
      default=True).AddToParser(parser)


def _StripVal(val):
  return six.text_type(val).strip()


def AddUsePresetProfilesFlag(parser):
  base.Argument(
      '--use-preset-profile',
      help='The name of an existing preset profile used to encapsulate X.509 parameter values.',
      required=False).AddToParser(parser)


def _AddSubjectAlternativeNameFlags(parser):
  """Adds the Subject Alternative Name (san) flags.

  This will add --ip-san, --email-san, --dns-san, and --uri-san to the parser.

  Args:
    parser: The parser to add the flags to.
  """
  base.Argument(
      '--email-san',
      help='One or more comma-separated email Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='EMAIL_SAN').AddToParser(parser)
  base.Argument(
      '--ip-san',
      help='One or more comma-separated IP Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='IP_SAN').AddToParser(parser)
  base.Argument(
      '--dns-san',
      help='One or more comma-separated DNS Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='DNS_SAN').AddToParser(parser)
  base.Argument(
      '--uri-san',
      help='One or more comma-separated URI Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='URI_SAN').AddToParser(parser)


def _AddSubjectFlag(parser, required):
  base.Argument(
      '--subject',
      required=required,
      metavar='SUBJECT',
      help='X.501 name of the certificate subject. Example: --subject '
      '"C=US,ST=California,L=Mountain View,O=Google LLC,CN=google.com"',
      type=arg_parsers.ArgDict(key_type=_StripVal,
                               value_type=_StripVal)).AddToParser(parser)


def AddSubjectFlags(parser, subject_required=False):
  """Adds subject flags to the parser including subject string and SAN flags.

  Args:
    parser: The parser to add the flags to.
    subject_required: Whether the subject flag should be required.
  """
  _AddSubjectFlag(parser, subject_required)
  _AddSubjectAlternativeNameFlags(parser)


def AddValidityFlag(parser,
                    resource_name,
                    default_value='P10Y',
                    default_value_text='10 years'):
  base.Argument(
      '--validity',
      help='The validity of this {}, as an ISO8601 duration. Defaults to {}.'
      .format(resource_name, default_value_text),
      default=default_value).AddToParser(parser)


def AddCaPoolIssuancePolicyFlag(parser):
  base.Argument(
      '--issuance-policy',
      action='store',
      type=arg_parsers.YAMLFileContents(),
      help=("A YAML file describing this CA Pool's issuance "
            'policy.')).AddToParser(parser)


def AddBucketFlag(parser):
  base.Argument(
      '--bucket',
      help='The name of an existing storage bucket to use for storing the CA '
      'certificates and CRLs for CAs in this pool. If omitted, a new bucket will'
      'be created and managed by the service on your behalf.',
      required=False).AddToParser(parser)


def AddIgnoreActiveCertificatesFlag(parser):
  base.Argument(
      '--ignore-active-certificates',
      help='If this flag is set, the Certificate Authority will be '
      'scheduled for deletion even if the Certificate Authority has '
      'un-revoked or un-expired certificates.',
      action='store_true',
      default=False,
      required=False).AddToParser(parser)


def AddInlineX509ParametersFlags(parser, is_ca_command,
                                 default_max_chain_length=None):
  """Adds flags for providing inline x509 parameters.

  Args:
    parser: The parser to add the flags to.
    is_ca_command: Whether the current command is on a CA. This influences the
      help text, and whether the --is-ca-cert flag is added.
    default_max_chain_length: optional, The default value for maxPathLength to
      use if an explicit value is not specified. If this is omitted or set to
      None, no default max path length will be added.
  """
  resource_name = 'CA' if is_ca_command else 'certificate'
  group = base.ArgumentGroup()
  group.AddArgument(
      base.Argument(
          '--key-usages',
          metavar='KEY_USAGES',
          help='The list of key usages for this {}. This can only be provided if `--use-preset-profile` is not provided.'
          .format(resource_name),
          type=arg_parsers.ArgList(
              element_type=_StripVal, choices=_VALID_KEY_USAGES)))
  group.AddArgument(
      base.Argument(
          '--extended-key-usages',
          metavar='EXTENDED_KEY_USAGES',
          help='The list of extended key usages for this {}. This can only be provided if `--use-preset-profile` is not provided.'
          .format(resource_name),
          type=arg_parsers.ArgList(
              element_type=_StripVal, choices=_VALID_EXTENDED_KEY_USAGES)))
  group.AddArgument(
      base.Argument(
          '--max-chain-length',
          help='Maximum depth of subordinate CAs allowed under this CA for a CA certificate. This can only be provided if `--use-preset-profile` is not provided.',
          default=default_max_chain_length))

  if not is_ca_command:
    group.AddArgument(
        base.Argument(
            '--is-ca-cert',
            help='Whether this certificate is for a CertificateAuthority or not. Indicates the Certificate Authority field in the x509 basic constraints extension.',
            required=False,
            default=False,
            action='store_true'))
  group.AddToParser(parser)


# Flag parsing


def ParseSubject(args):
  """Parses a dictionary with subject attributes into a API Subject type.

  Args:
    args: The argparse namespace that contains the flag values.

  Returns:
    Subject: the Subject type represented in the api.
  """
  subject_args = args.subject
  remap_args = {
      'CN': 'commonName',
      'C': 'countryCode',
      'ST': 'province',
      'L': 'locality',
      'O': 'organization',
      'OU': 'organizationalUnit'
  }

  mapped_args = {}
  for key, val in subject_args.items():
    if key in remap_args:
      mapped_args[remap_args[key]] = val
    else:
      mapped_args[key] = val

  try:
    return messages_util.DictToMessageWithErrorCheck(
        mapped_args,
        privateca_base.GetMessagesModule('v1').Subject)
  except messages_util.DecodeError:
    raise exceptions.InvalidArgumentException(
        '--subject', 'Unrecognized subject attribute.')


def ParseSanFlags(args):
  """Validates the san flags and creates a SubjectAltNames message from them.

  Args:
    args: The parser that contains the flags.

  Returns:
    The SubjectAltNames message with the flag data.
  """
  email_addresses, dns_names, ip_addresses, uris = [], [], [], []

  if args.IsSpecified('email_san'):
    email_addresses = list(map(ValidateEmailSanFlag, args.email_san))
  if args.IsSpecified('dns_san'):
    dns_names = list(map(ValidateDnsSanFlag, args.dns_san))
  if args.IsSpecified('ip_san'):
    ip_addresses = list(map(ValidateIpSanFlag, args.ip_san))
  if args.IsSpecified('uri_san'):
    uris = args.uri_san

  return privateca_base.GetMessagesModule('v1').SubjectAltNames(
      emailAddresses=email_addresses,
      dnsNames=dns_names,
      ipAddresses=ip_addresses,
      uris=uris)


def ValidateSubjectConfig(subject_config, is_ca):
  """Validates a SubjectConfig object."""
  san_names = []
  if subject_config.subjectAltName:
    san_names = [
        subject_config.subjectAltName.emailAddresses,
        subject_config.subjectAltName.dnsNames,
        subject_config.subjectAltName.ipAddresses,
        subject_config.subjectAltName.uris
    ]
  if not subject_config.subject.commonName and all(
      [not elem for elem in san_names]):
    raise exceptions.InvalidArgumentException(
        '--subject',
        'The certificate you are creating does not contain a common name or a subject alternative name.'
    )

  if is_ca and not subject_config.subject.organization:
    raise exceptions.InvalidArgumentException(
        '--subject',
        'An organization must be provided for a certificate authority certificate.'
    )


def ParseSubjectFlags(args, is_ca):
  """Parses subject flags into a subject config.

  Args:
    args: The parser that contains all the flag values
    is_ca: Whether to parse this subject as a CA or not.

  Returns:
    A subject config representing the parsed flags.
  """
  messages = privateca_base.GetMessagesModule('v1')
  subject_config = messages.SubjectConfig(
      subject=messages.Subject(), subjectAltName=messages.SubjectAltNames())

  if args.IsSpecified('subject'):
    subject_config.subject = ParseSubject(args)
  if SanFlagsAreSpecified(args):
    subject_config.subjectAltName = ParseSanFlags(args)

  ValidateSubjectConfig(subject_config, is_ca=is_ca)

  return subject_config


def SanFlagsAreSpecified(args):
  """Returns true if any san flags are specified."""
  return any([
      flag in vars(args) and args.IsSpecified(flag)
      for flag in ['dns_san', 'email_san', 'ip_san', 'uri_san']
  ])


def ParseIssuancePolicy(args):
  """Parses an IssuancePolicy proto message from the args."""
  if not args.IsSpecified('issuance_policy'):
    return None
  try:
    return messages_util.DictToMessageWithErrorCheck(
        args.issuance_policy,
        privateca_base.GetMessagesModule('v1').IssuancePolicy)
  # TODO(b/77547931): Catch `AttributeError` until upstream library takes the
  # fix.
  except (messages_util.DecodeError, AttributeError):
    raise exceptions.InvalidArgumentException(
        '--issuance-policy', 'Unrecognized field in the Issuance Policy.')


def ParsePublishingOptions(args):
  """Parses the PublshingOptions proto message from the args."""
  messages = privateca_base.GetMessagesModule('v1')
  publish_ca_cert = args.publish_ca_cert
  publish_crl = args.publish_crl

  tier = ParseTierFlag(args)
  if tier == messages.CaPool.TierValueValuesEnum.DEVOPS:
    if args.IsSpecified('publish_crl') and publish_crl:
      raise exceptions.InvalidArgumentException(
          '--publish-crl',
          'CRL publication is not supported in the DevOps tier.')
    # It's not explicitly set to True, so change the default to False here.
    publish_crl = False

  return messages.PublishingOptions(
      publishCaCert=publish_ca_cert, publishCrl=publish_crl)


# Flag validation helpers


def ValidateEmailSanFlag(san):
  if not re.match(_EMAIL_SAN_REGEX, san):
    raise exceptions.InvalidArgumentException('--email-san',
                                              'Invalid email address.')
  return san


def ValidateDnsSanFlag(san):
  if not re.match(_DNS_SAN_REGEX, san):
    raise exceptions.InvalidArgumentException('--dns-san',
                                              'Invalid domain name value')
  return san


def ValidateIpSanFlag(san):
  try:
    ipaddress.ip_address(san)
  except ValueError:
    raise exceptions.InvalidArgumentException('--ip-san',
                                              'Invalid IP address value.')
  return san


_REVOCATION_MAPPING = {
    'REVOCATION_REASON_UNSPECIFIED': 'unspecified',
    'KEY_COMPROMISE': 'key-compromise',
    'CERTIFICATE_AUTHORITY_COMPROMISE': 'certificate-authority-compromise',
    'AFFILIATION_CHANGED': 'affiliation-changed',
    'SUPERSEDED': 'superseded',
    'CESSATION_OF_OPERATION': 'cessation-of-operation',
    'CERTIFICATE_HOLD': 'certificate-hold',
    'PRIVILEGE_WITHDRAWN': 'privilege-withdrawn',
    'ATTRIBUTE_AUTHORITY_COMPROMISE': 'attribute-authority-compromise'
}

_REVOCATION_REASON_MAPPER = arg_utils.ChoiceEnumMapper(
    arg_name='--reason',
    default='unspecified',
    help_str='Revocation reason to include in the CRL.',
    message_enum=privateca_base.GetMessagesModule(
        'v1').RevokeCertificateRequest.ReasonValueValuesEnum,
    custom_mappings=_REVOCATION_MAPPING)

_TIER_MAPPING = {
    'ENTERPRISE': 'enterprise',
    'DEVOPS': 'devops',
}

_TIER_MAPPER = arg_utils.ChoiceEnumMapper(
    arg_name='--tier',
    default='enterprise',
    help_str='The tier for the Certificate Authority.',
    message_enum=privateca_base.GetMessagesModule(
        'v1').CaPool.TierValueValuesEnum,
    custom_mappings=_TIER_MAPPING)

_KEY_ALGORITHM_MAPPING = {
    'RSA_PSS_2048_SHA256': 'rsa-pss-2048-sha256',
    'RSA_PSS_3072_SHA256': 'rsa-pss-3078-sha256',
    'RSA_PSS_4096_SHA256': 'rsa-pss-4096-sha256',
    'RSA_PKCS1_2048_SHA256': 'rsa-pkcs1-2048-sha256',
    'RSA_PKCS1_3072_SHA256': 'rsa-pkcs1-3072-sha256',
    'RSA_PKCS1_4096_SHA256': 'rsa-pkcs1-4096-sha256',
    'EC_P256_SHA256': 'ec-p256-sha256',
    'EC_P384_SHA384': 'ec-p384-sha384',
}

_KEY_ALGORITHM_MAPPER = arg_utils.ChoiceEnumMapper(
    arg_name='--key-algorithm',
    help_str='The crypto algorithm to use for creating a managed KMS key for '
    'the Certificate Authority.',
    message_enum=privateca_base.GetMessagesModule(
        'v1').KeyVersionSpec.AlgorithmValueValuesEnum,
    custom_mappings=_KEY_ALGORITHM_MAPPING)


def AddRevocationReasonFlag(parser):
  """Add a revocation reason enum flag to the parser.

  Args:
    parser: The argparse parser to add the flag to.
  """
  _REVOCATION_REASON_MAPPER.choice_arg.AddToParser(parser)


def ParseRevocationChoiceToEnum(choice):
  """Return the apitools revocation reason enum value from the string choice.

  Args:
    choice: The string value of the revocation reason.

  Returns:
    The revocation enum value for the choice text.
  """
  return _REVOCATION_REASON_MAPPER.GetEnumForChoice(choice)


def ParseValidityFlag(args):
  """Parses the validity from args."""
  return times.FormatDurationForJson(times.ParseDuration(args.validity))


def AddTierFlag(parser):
  _TIER_MAPPER.choice_arg.AddToParser(parser)


def ParseTierFlag(args):
  return _TIER_MAPPER.GetEnumForChoice(args.tier)


def AddKeyAlgorithmFlag(parser_group, default='rsa-pkcs1-4096-sha256'):
  _KEY_ALGORITHM_MAPPER.choice_arg.AddToParser(parser_group)
  _KEY_ALGORITHM_MAPPER.choice_arg.SetDefault(parser_group, default)


def ParseKeySpec(args):
  """Parses a specified KMS key version or algorithm to get a KeyVersionSpec."""
  messages = privateca_base.GetMessagesModule('v1')
  if args.IsSpecified('kms_key_version'):
    kms_key_version_ref = args.CONCEPTS.kms_key_version.Parse()
    return messages.KeyVersionSpec(
        cloudKmsKeyVersion=kms_key_version_ref.RelativeName())

  return messages.KeyVersionSpec(
      algorithm=_KEY_ALGORITHM_MAPPER.GetEnumForChoice(args.key_algorithm))


def ParseX509Parameters(args, is_ca_command):
  """Parses the X509 parameters flags into an API X509Parameters.

  Args:
    args: The parsed argument values.
    is_ca_command: Whether the current command is on a CA. If so, certSign and
      crlSign key usages are added.

  Returns:
    An X509Parameters object.
  """
  preset_profile_set = args.IsKnownAndSpecified('use_preset_profile')
  # TODO(b/183243757): Change to args.IsSpecified once --use-preset-profile flag
  # is registered.
  has_inline_values = any([
      args.IsKnownAndSpecified(flag) for flag in
      ['key_usages', 'extended_key_usages', 'max_chain_length', 'is_ca_cert']
  ])

  if preset_profile_set and has_inline_values:
    raise exceptions.InvalidArgumentException(
        '--use-preset-profile',
        '--use-preset-profile may not be specified if one or more of '
        '--key-usages, --extended-key-usages or --max-chain-length are '
        'specified.')
  if preset_profile_set:
    return preset_profiles.GetPresetX509Parameters(args.use_preset_profile)

  base_key_usages = args.key_usages or []
  is_ca = is_ca_command or (args.IsKnownAndSpecified('is_ca_cert') and
                            args.is_ca_cert)
  if is_ca:
    # A CA should have these KeyUsages to be RFC 5280 compliant.
    base_key_usages.extend(['cert_sign', 'crl_sign'])
  key_usage_dict = {}
  for key_usage in base_key_usages:
    key_usage = text_utils.SnakeCaseToCamelCase(key_usage)
    key_usage_dict[key_usage] = True
  extended_key_usage_dict = {}
  for extended_key_usage in args.extended_key_usages or []:
    extended_key_usage = text_utils.SnakeCaseToCamelCase(extended_key_usage)
    extended_key_usage_dict[extended_key_usage] = True

  messages = privateca_base.GetMessagesModule('v1')
  return messages.X509Parameters(
      keyUsage=messages.KeyUsage(
          baseKeyUsage=messages_util.DictToMessageWithErrorCheck(
              key_usage_dict, messages.KeyUsageOptions),
          extendedKeyUsage=messages_util.DictToMessageWithErrorCheck(
              extended_key_usage_dict, messages.ExtendedKeyUsageOptions)),
      caOptions=messages.CaOptions(
          isCa=is_ca,
          # Don't include maxIssuerPathLength if it's None.
          maxIssuerPathLength=int(args.max_chain_length)
          if is_ca and args.max_chain_length is not None else None))
