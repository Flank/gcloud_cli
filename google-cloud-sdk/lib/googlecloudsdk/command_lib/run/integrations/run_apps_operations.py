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
"""Allows you to write surfaces in terms of logical RunApps operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import datetime
import re

from apitools.base.py import encoding
from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.run.integrations import api_utils
from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

# Max wait time before timing out
_POLLING_TIMEOUT_MS = 180000
# Max wait time between poll retries before timing out
_RETRY_TIMEOUT_MS = 1000

_CONFIG_KEY = 'config'
_RESOURCES_KEY = 'resources'

_DEFAULT_APP_NAME = 'default'


@contextlib.contextmanager
def Connect(conn_context):
  """Provide a RunAppsOperations instance to use.

  Arguments:
    conn_context: a context manager that yields a ConnectionInfo and manages a
      dynamic context.

  Yields:
    A RunAppsOperations instance.
  """
  # pylint: disable=protected-access
  client = apis.GetClientInstance(
      conn_context.api_name,
      conn_context.api_version)

  yield RunAppsOperations(client, conn_context.api_version, conn_context.region)


class RunAppsOperations(object):
  """Client used by Cloud Run Integrations to communicate with the API."""

  def __init__(self, client, api_version, region):
    """Inits RunAppsOperations with given API clients.

    Args:
      client: The API client for interacting with RunApps APIs.
      api_version: Version of resources & clients (v1alpha1, v1beta1)
      region: str, The region of the control plane.
    """

    self._client = client
    self._api_version = api_version
    self._region = region

  @property
  def client(self):
    return self._client

  @property
  def messages(self):
    return self._client.MESSAGES_MODULE

  def ApplyAppConfig(self,
                     appname,
                     appconfig,
                     message=None,
                     match_type_names=None,
                     etag=None):
    """Applies the application config.

    Args:
      appname:  name of the application.
      appconfig: config of the application.
      message: the message to display when waiting for API call to finish.
        If not given, default messages will be used.
      match_type_names: array of type/name pairs used for create selector.
      etag: the etag of the application if it's an incremental patch.
    """
    app_ref = self.GetAppRef(appname)
    application = self.messages.Application(
        name=appname, config=appconfig, etag=etag)
    is_patch = etag or api_utils.GetApplication(self._client, app_ref)
    if is_patch:
      operation = api_utils.PatchApplication(self._client, app_ref, application)
      if message is None:
        message = 'Updating Application [{}]'.format(appname)
    else:
      operation = api_utils.CreateApplication(self._client, app_ref,
                                              application)
      if message is None:
        message = 'Creating Application [{}]'.format(appname)
    api_utils.WaitForApplicationOperation(self._client, operation, message)
    deployment_name = self._GetDeploymentName(appname)
    if match_type_names is None:
      match_type_names = [{'type': '*', 'name': '*'}]
    deployment = self.messages.Deployment(
        name=deployment_name,
        createSelector={'matchTypeNames': match_type_names})
    deployment_ops = api_utils.CreateDeployment(self._client, app_ref,
                                                deployment)

    dep_response = api_utils.WaitForDeploymentOperation(
        self._client, deployment_ops, 'Configuring Integration')
    self.CheckDeploymentState(dep_response)

  def _GetDeploymentName(self, appname):
    return '{}-{}'.format(
        appname,
        datetime.datetime.now().strftime('%Y%m%d%H%M%S'))

  def GetIntegrationTypeFromConfig(self, resource_config):
    """Gets the integration type.

    The input is converted from proto with "oneof" property. Thus the dictionary
    is expected to have only one key, matching the type of the matching oneof.

    Args:
      resource_config: dict, the resource configuration.

    Returns:
      str, the integration type.
    """
    keys = list(resource_config.keys())
    if len(keys) != 1:
      raise exceptions.ConfigurationError(
          'resource config is invalid: {}.'.format(resource_config))
    return keys[0]

  def GetIntegration(self, name):
    """Get an integration.

    Args:
      name: str, the name of the resource.

    Raises:
      IntegrationNotFoundError: If the integration is not found.

    Returns:
      The integration config.
    """
    try:
      return self._GetDefaultAppDict()[_CONFIG_KEY][_RESOURCES_KEY][name]
    except KeyError:
      raise exceptions.IntegrationNotFoundError(
          'Integration [{}] cannot be found'.format(name))

  def GetIntegrationStatus(self, name):
    """Get status of an integration.

    Args:
      name: str, the name of the resource.

    Returns:
      The ResourceStatus of the integration, or None if not found
    """
    try:
      application_status = api_utils.GetApplicationStatus(
          self._client, self.GetAppRef(_DEFAULT_APP_NAME), name)
      app_status_dict = encoding.MessageToDict(application_status)
      integration_status = app_status_dict.get('resources', {}).get(name)
      if integration_status:
        return integration_status
      return None
    except KeyError:
      return None
    except api_exceptions.HttpError:
      return None

  def CreateIntegration(self, integration_type, parameters, service, name=None):
    """Create an integration.

    Args:
      integration_type:  type of the integration.
      parameters: parameter dictionary from args.
      service: the service to attach to the new integration.
      name: name of the integration, if empty, a defalt one will be generated.

    Returns:
      The deployment.
    """
    app_dict = self._GetDefaultAppDict()
    resources_map = app_dict[_CONFIG_KEY][_RESOURCES_KEY]
    if not name:
      name = self._NewIntegrationName(integration_type, service, parameters,
                                      app_dict)

    resource_type = self._GetResourceType(integration_type)

    if name in resources_map:
      raise exceptions.ArgumentError(
          'Integration with name [{}] already exists.'.format(name))

    resource_config = self._GetResourceConfig(resource_type, parameters,
                                              service, None, {})
    resources_map[name] = resource_config
    match_type_names = [{'type': resource_type, 'name': name}]
    if service:
      self._EnsureServiceConfig(resources_map, service)
      match_type_names.append({'type': 'service', 'name': service})
    application = encoding.DictToMessage(app_dict, self.messages.Application)
    return self.ApplyAppConfig(
        appname=_DEFAULT_APP_NAME,
        appconfig=application.config,
        message='Saving Configuration for Integration [{}]'.format(name),
        match_type_names=match_type_names,
        etag=application.etag)

  def UpdateIntegration(self,
                        name,
                        parameters,
                        add_service=None,
                        remove_service=None):
    """Update an integration.

    Args:
      name:  str, the name of the resource to update.
      parameters: dict, the parameters from args.
      add_service: the service to attach to the integration.
      remove_service: the service to remove from the integration.

    Raises:
      IntegrationNotFoundError: If the integration is not found.

    Returns:
      The deployment.
    """
    app_dict = self._GetDefaultAppDict()
    resources_map = app_dict[_CONFIG_KEY][_RESOURCES_KEY]
    existing_resource = resources_map.get(name)
    if existing_resource is None:
      raise exceptions.IntegrationNotFoundError(
          'Integration [{}] cannot be found'.format(name))

    resource_type = self.GetIntegrationTypeFromConfig(existing_resource)
    resource_config = self._GetResourceConfig(resource_type, parameters,
                                              add_service, remove_service,
                                              existing_resource)
    resources_map[name] = resource_config
    match_type_names = [{'type': resource_type, 'name': name}]
    if add_service:
      self._EnsureServiceConfig(resources_map, add_service)
      match_type_names.append({'type': 'service', 'name': add_service})
    application = encoding.DictToMessage(app_dict, self.messages.Application)
    return self.ApplyAppConfig(
        appname=_DEFAULT_APP_NAME,
        appconfig=application.config,
        message='Updating Integration [{}]'.format(name),
        match_type_names=match_type_names,
        etag=application.etag)

  def ListIntegrationTypes(self):
    """Returns the list of integration type definitions.

    Returns:
      An array of integration type definitions.
    """
    return types_utils.IntegrationTypes(self._client)

  def GetIntegrationTypeDefinition(self, type_name):
    """Returns the integration type definition of the given name.

    Args:
      type_name: name of the integration type

    Returns:
      An integration type definition. None if no matching type.
    """
    int_types = types_utils.IntegrationTypes(self._client)
    for t in int_types:
      if t['name'] == type_name:
        return t
    return None

  def GetIntegrationType(self, resource_type):
    """Returns the integration type associated to the given resource type.

    Args:
      resource_type: string, the resource type.

    Returns:
      The integration type.
    """
    int_types = types_utils.IntegrationTypes(self._client)
    for t in int_types:
      if t['resource_name'] == resource_type:
        return t['name']
    return resource_type

  def ListIntegrations(self, integration_type_filter, service_name_filter):
    """Returns the list of integrations.

    Args:
      integration_type_filter: str, if populated integration type to filter by.
      service_name_filter: str, if populated service name to filter by.

    Returns:
      Dict of str[str] with keys name, type, and services.

    """

    app = api_utils.GetApplication(self._client,
                                   self.GetAppRef(_DEFAULT_APP_NAME))
    if not app:
      raise exceptions.IntegrationNotFoundError('No Integrations Found.')

    app_dict = encoding.MessageToDict(app)
    app_resources = app_dict.get('config', {}).get('resources')
    if not app_resources:
      raise exceptions.IntegrationNotFoundError('No Integrations Found.')

    # Filter by type and/or service.
    output = []
    for name, resource in app_resources.items():
      integration_type = self.GetIntegrationTypeFromConfig(resource)
      services = self._GetRefServicesRouter(resource)

      # Convert from internal resource naming to external integration naming.
      integration_type = self.GetIntegrationType(integration_type)

      # Remove invalid integrations.
      if integration_type is None:
        continue

      # Always remove services.
      if integration_type == 'service':
        continue

      # TODO(b/217744072): Support Cloud SDK topic filtering.
      # Optionally filter by type.
      if (integration_type_filter and
          integration_type != integration_type_filter):
        continue

      # Optionally filter by service.
      if service_name_filter and service_name_filter not in services:
        continue

      # Assemble for Cloud SDK table formater.
      resource = {
          'name': name,
          'type': integration_type,
          'services': ','.join(services)
      }
      output.append(resource)

    return output

  def _GetRefServicesRouter(self, resource):
    """Get referenced services from Router/GCLB.

    Args:
      resource: ResourceConfig, from which to determine type.

    Returns:
      list(str), of referenced services or None if no refs found.
    """
    # Right now ingress bindings are only created from ingress to service. As
    # such have to look each paths of router.
    output = []
    if resource.get('router') is not None:
      if resource.get('router', {}).get('default-route', {}).get('ref'):
        output.append(resource['router']['default-route']['ref'].replace(
            'service/', ''))

      if resource.get('router', {}).get('routes'):
        for route in resource['router']['routes']:
          if route.get('ref'):
            output.append(route['ref'].replace('service/', ''))

    return output

  def _GetDefaultAppDict(self):
    """Returns the default application as a dict.

    Returns:
      dict representing the application.
    """
    application = api_utils.GetApplication(self._client,
                                           self.GetAppRef(_DEFAULT_APP_NAME))
    if not application:
      application = self.messages.Application(
          name=_DEFAULT_APP_NAME, config={_RESOURCES_KEY: {}})
    app_dict = encoding.MessageToDict(application)
    app_dict.setdefault(_CONFIG_KEY, {})
    app_dict[_CONFIG_KEY].setdefault(_RESOURCES_KEY, {})
    return app_dict

  def _GetResourceConfig(self, res_type, parameters, add_service,
                         remove_service, res_config):
    """Returns a new resource config according to the parameters.

    Args:
      res_type: type of the resource.
      parameters: parameter dictionary from args.
      add_service: the service to attach to the integration.
      remove_service: the service to remove from the integration.
      res_config: previous resource config. If given, changes will be made based
        on it.

    Returns:
      A new resource config
    """
    if res_config is not None and res_type in res_config:
      config = dict(res_config[res_type])
    else:
      config = {}

    if res_type == 'router':
      if 'dns-zone' in parameters:
        config['dns-zone'] = parameters['dns-zone']
      if 'domain' in parameters:
        config['domain'] = parameters['domain']
      if remove_service:
        ref = 'service/{}'.format(remove_service)
        config['routes'] = [x for x in config['routes'] if x['ref'] != ref]
      if add_service:
        route = {'ref': 'service/{}'.format(add_service)}
        if 'paths' in parameters:
          route['paths'] = parameters['paths']
          if 'routes' not in config:
            config['routes'] = []
          config['routes'].append(route)
        else:
          config['default-route'] = route
      return {res_type: config}

    raise exceptions.ArgumentError(
        'Unsupported integration type [{}]'.format(res_type))

  def _EnsureServiceConfig(self, resources_map, service_name):
    if service_name not in resources_map:
      resources_map[service_name] = {'service': {}}

  def _GetResourceType(self, integration_type):
    type_def = self.GetIntegrationTypeDefinition(integration_type)
    if type_def is not None:
      res_name = type_def['resource_name']
      if res_name is not None:
        return res_name
    return integration_type

  def _NewIntegrationName(self, integration_type, service, parameters,
                          app_dict):
    """Returns a new name for an integration.

    It makes sure the new name does not exist in the given app_dict.

    Args:
      integration_type:  str, name of the integration type.
      service: str, name of the service.
      parameters: parameter dictionary from args.
      app_dict: dict, the dictionary that represents the application.

    Returns:
      str, the new name.

    """
    if integration_type == 'custom-domain':
      domain = parameters['domain']
      if not domain:
        raise exceptions.ArgumentError('domain is required in "PARAMETERS" '
                                       'for integration type "custom-domain"')
      return 'domain-{}'.format(domain.replace('.', '-'))

    name = '{}-{}'.format(integration_type, service)
    while name in app_dict[_CONFIG_KEY][_RESOURCES_KEY]:
      count = 1
      match = re.search(r'(.+)-(\d+)$', name)
      if match:
        name = match.group(1)
        count = int(match.group(2)) + 1
      name = '{}-{}'.format(name, count)
    return name

  def GetAppRef(self, name):
    """Returns the application resource object.

    Args:
      name:  name of the application.

    Returns:
      The application resource object
    """
    project = properties.VALUES.core.project.Get(required=True)
    location = self._region
    app_ref = resources.REGISTRY.Parse(
        name,
        params={
            'projectsId': project,
            'locationsId': location
        },
        collection='runapps.projects.locations.applications')
    return app_ref

  def CheckDeploymentState(self, response):
    """Throws any unexpected states contained within deployment reponse.

    Args:
      response: run_apps.v1alpha1.deployment, response to check
    """
    # Short hand refference of deployment/job state
    dep_state = self.messages.DeploymentStatus.StateValueValuesEnum
    job_state = self.messages.JobDetails.StateValueValuesEnum

    if response.status.state == dep_state.SUCCEEDED:
      return

    if response.status.state == dep_state.FAILED:
      if not response.status.errorMessage:
        raise exceptions.IntegrationsOperationError('Configuration failed.')

      # Look for job that failed. It should always be last job, but this is not
      # guaranteed behavior.
      url = ''
      for job in response.status.jobDetails[::-1]:
        if job.state == job_state.FAILED:
          url = job.jobUri
          break

      error_msg = 'Configuration failed with error: {}.'.format(
          response.status.errorMessage)
      if url:
        error_msg += ' Logs are available at {}'.format(url)

      raise exceptions.IntegrationsOperationError(error_msg)

    else:
      raise exceptions.IntegrationsOperationError(
          'Configuration returned in unexpected state "{}".'.format(
              response.status.state.name))

  def IsValidIntegrationType(self, type_str):
    """Check if integration type is supported.

    Args:
      type_str: str, of type to verify

    Returns:
      bool, True if valid
    """

    for integration in types_utils.IntegrationTypes(self._client):
      if integration['name'] == type_str:
        return True

    return False
