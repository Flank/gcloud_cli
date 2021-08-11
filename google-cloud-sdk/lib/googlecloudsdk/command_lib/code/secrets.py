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
"""Library for the Secret Manager integration in the local environment."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py import encoding_helper
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.code import kubernetes

SECRETS_MESSAGE_MODULE = apis.GetMessagesModule('secretmanager', 'v1')
RUN_MESSAGE_MODULE = apis.GetMessagesModule('run', 'v1')


def BuildSecrets(project_name, secret_map, namespace, client=None):
  """Fetch secrets from Secret Manager and create k8s secrets with the data."""
  if client is None:
    client = _SecretsClient()
  secrets = []
  for secret, versions in secret_map.items():
    secrets.append(
        _BuildSecret(client, project_name, secret, versions, namespace))
  return secrets


def _BuildSecret(client, project, secret_name, versions, namespace):
  if None in versions:
    # TODO(b/187972361): Do we need to load all secret versions for the secret?
    raise ValueError('local development requires you to specify all secret '
                     'versions that you need to use.')
  secrets = {}
  for version in versions:
    secrets[version] = client.GetSecretData(project, secret_name, version)
  return _BuildK8sSecret(secret_name, secrets, namespace)


def _BuildK8sSecret(secret_name, secrets, namespace):
  """Turn a map of SecretManager responses into a k8s secret."""
  data_value = RUN_MESSAGE_MODULE.Secret.DataValue(additionalProperties=[])
  k8s_secret = RUN_MESSAGE_MODULE.Secret(
      metadata=RUN_MESSAGE_MODULE.ObjectMeta(
          name=secret_name, namespace=namespace),
      data=data_value)
  for version, secret in secrets.items():
    k8s_secret.data.additionalProperties.append(
        RUN_MESSAGE_MODULE.Secret.DataValue.AdditionalProperty(
            key=version, value=secret.payload.data))
  d = encoding_helper.MessageToDict(k8s_secret)
  # RUN_MESSAGE_MODULE.Secret doesn't have fields for apiVersion and Kind so we
  # need to add that here
  d['apiVersion'] = 'v1'
  d['kind'] = 'Secret'
  return d


def _DeleteSecrets(secret_map, namespace, context_name):
  kubernetes.DeleteResources('secret', list(secret_map.keys()), namespace,
                             context_name)


class _SecretsClient(object):

  def __init__(self):
    self.secrets_client = apis.GetClientInstance('secretmanager', 'v1')

  def GetSecretData(self, project, secret_name, version):
    resource_template = 'projects/{}/secrets/{}/versions/{}'
    return self.secrets_client.projects_secrets_versions.Access(
        SECRETS_MESSAGE_MODULE
        .SecretmanagerProjectsSecretsVersionsAccessRequest(
            name=resource_template.format(project, secret_name, version)))
