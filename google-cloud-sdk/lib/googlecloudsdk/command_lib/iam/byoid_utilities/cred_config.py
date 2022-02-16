# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Generators for Credential Config Files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import enum
import json

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files
import six


class ConfigType(enum.Enum):
  WORKLOAD_IDENTITY_POOLS = 1
  WORKFORCE_POOLS = 2


RESOURCE_TYPE = 'credential configuration file'


def create_credential_config(args, config_type):
  """Creates the byoid credential config based on CLI arguments."""
  try:
    generator = get_generator(args, config_type)
    output = {
        'type': 'external_account',
        'audience': '//iam.googleapis.com/' + args.audience,
        'subject_token_type': generator.get_token_type(args.subject_token_type),
        'token_url': 'https://sts.googleapis.com/v1/token',
        'credential_source': generator.get_source(args),
    }

    if config_type is ConfigType.WORKFORCE_POOLS:
      output['workforce_pool_user_project'] = args.workforce_pool_user_project

    if args.service_account:
      output['service_account_impersonation_url'] = ''.join((
          'https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/',
          args.service_account, ':generateAccessToken'))

    files.WriteFileContents(args.output_file, json.dumps(output, indent=2))
    log.CreatedResource(args.output_file, RESOURCE_TYPE)
  except GeneratorError as cce:
    log.CreatedResource(args.output_file, RESOURCE_TYPE, failed=cce.message)


def get_generator(args, config_type):
  """Determines the type of credential output based on CLI arguments."""
  if args.credential_source_file:
    return FileCredConfigGenerator(config_type, args.credential_source_file)
  if args.credential_source_url:
    return UrlCredConfigGenerator(config_type, args.credential_source_url,
                                  args.credential_source_headers)
  if args.aws:
    return AwsCredConfigGenerator()
  if args.azure:
    return AzureCredConfigGenerator(args.app_id_uri, args.audience)


class CredConfigGenerator(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for generating Credential Config files."""

  def __init__(self, config_type):
    self.config_type = config_type

  def get_token_type(self, subject_token_type):
    """Returns the type of token that this credential config uses."""

    default_token_type = 'urn:ietf:params:oauth:token-type:jwt'
    if self.config_type is ConfigType.WORKFORCE_POOLS:
      default_token_type = 'urn:ietf:params:oauth:token-type:id_token'

    return subject_token_type or default_token_type

  def _get_format(self, credential_source_type, credential_source_field_name):
    """Returns an optional dictionary indicating the format of the token.

    This is a shared method, that several different token types need access to.

    Args:
      credential_source_type: The format of the token, either 'json' or 'text'.
      credential_source_field_name: The field name of a JSON object containing
        the text version of the token.

    Raises:
      GeneratorError: if an invalid token format is specified, or no field name
      is specified for a json token.

    """
    if not credential_source_type:
      return None

    credential_source_type = credential_source_type.lower()
    if credential_source_type not in ('json', 'text'):
      raise GeneratorError(
          '--credential-source-type must be either "json" or "text"')

    token_format = {'type': credential_source_type}
    if credential_source_type == 'json':
      if not credential_source_field_name:
        raise GeneratorError(
            '--credential-source-field-name required for JSON formatted tokens')
      token_format['subject_token_field_name'] = credential_source_field_name

    return token_format

  def _format_already_defined(self, credential_source_type):
    if credential_source_type:
      raise GeneratorError(
          '--credential-source-type is not supported with --azure or --aws')

  @abc.abstractmethod
  def get_source(self, args):
    """Gets the credential source info used for this credential config."""
    pass


class FileCredConfigGenerator(CredConfigGenerator):
  """The generator for File-based credential configs."""

  def __init__(self, config_type, credential_source_file):
    super(FileCredConfigGenerator, self).__init__(config_type)
    self.credential_source_file = credential_source_file

  def get_source(self, args):
    credential_source = {'file': self.credential_source_file}
    token_format = self._get_format(args.credential_source_type,
                                    args.credential_source_field_name)
    if token_format:
      credential_source['format'] = token_format
    return credential_source


class UrlCredConfigGenerator(CredConfigGenerator):
  """The generator for Url-based credential configs."""

  def __init__(self, config_type, credential_source_url,
               credential_source_headers):
    super(UrlCredConfigGenerator, self).__init__(config_type)
    self.credential_source_url = credential_source_url
    self.credential_source_headers = credential_source_headers

  def get_source(self, args):
    credential_source = {'url': self.credential_source_url}
    if self.credential_source_headers:
      credential_source['headers'] = self.credential_source_headers
    token_format = self._get_format(args.credential_source_type,
                                    args.credential_source_field_name)
    if token_format:
      credential_source['format'] = token_format
    return credential_source


class AwsCredConfigGenerator(CredConfigGenerator):
  """The generator for AWS-based credential configs."""

  def __init__(self):
    super(AwsCredConfigGenerator,
          self).__init__(ConfigType.WORKLOAD_IDENTITY_POOLS)

  def get_token_type(self, subject_token_type):
    return 'urn:ietf:params:aws:token-type:aws4_request'

  def get_source(self, args):
    self._format_already_defined(args.credential_source_type)
    credential_source = {
        'environment_id':
            'aws1',
        'region_url':
            'http://169.254.169.254/latest/meta-data/placement/availability-zone',
        'url':
            'http://169.254.169.254/latest/meta-data/iam/security-credentials',
        'regional_cred_verification_url':
            'https://sts.{region}.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15'
    }

    if args.calliope_command.ReleaseTrack(
    ) == calliope_base.ReleaseTrack.ALPHA and args.include_aws_session_token_url:
      credential_source[
          'aws_session_token_url'] = 'http://169.254.169.254/latest/api/token'

    return credential_source


class AzureCredConfigGenerator(CredConfigGenerator):
  """The generator for Azure-based credential configs."""

  def __init__(self, app_id_uri, audience):
    super(AzureCredConfigGenerator,
          self).__init__(ConfigType.WORKLOAD_IDENTITY_POOLS)
    self.app_id_uri = app_id_uri
    self.audience = audience

  def get_token_type(self, subject_token_type):
    return 'urn:ietf:params:oauth:token-type:jwt'

  def get_source(self, args):
    self._format_already_defined(args.credential_source_type)
    return {
        'url':
            'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource='
            +
            (self.app_id_uri or 'https://iam.googleapis.com/' + self.audience),
        'headers': {
            'Metadata': 'True'
        },
        'format': {
            'type': 'json',
            'subject_token_field_name': 'access_token'
        }
    }


class GeneratorError(Exception):

  def __init__(self, message):
    super(GeneratorError, self).__init__()
    self.message = message
