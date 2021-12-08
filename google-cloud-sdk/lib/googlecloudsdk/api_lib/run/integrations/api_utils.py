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
"""Functionality related to Cloud Run Integration API clients."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import encoding


API_NAME = 'runapps'
API_VERSION = 'v1alpha1'

# Max wait time before timing out
_POLLING_TIMEOUT_MS = 180000
# Max wait time between poll retries before timing out
_RETRY_TIMEOUT_MS = 1000


def GetMessages():
  """Returns the messages module for the Runapps API.

  Returns:
    Module containing the definitions of messages for the Runapps API.
  """
  return apis.GetMessagesModule(API_NAME, API_VERSION)


def GetApplication(client, app_ref):
  """Calls ApplicationGet API of Runapps of the specificed reference.

  Args:
    client: GAPIC API client, the api client to use.
    app_ref: googlecloudsdk.core.resources.Resource, the resource reference of
      the application.

  Returns:
    The Application object. Or None if not found.
  """
  request = client.MESSAGES_MODULE.RunappsProjectsLocationsApplicationsGetRequest(
      name=app_ref.RelativeName())
  try:
    return client.projects_locations_applications.Get(request)
  except api_exceptions.HttpNotFoundError:
    return None


def CreateApplication(client, app_ref, application):
  """Calls ApplicationCreate API of Runapps of the specificed reference.

  Args:
    client: GAPIC API client, the api client to use.
    app_ref: googlecloudsdk.core.resources.Resource, the resource reference of
      the application.
    application: run_apps.v1alpha1.Application, the application to create

  Returns:
    run_apps.v1alpha1.Operation, the LRO of this request.
  """
  return client.projects_locations_applications.Create(
      client.MESSAGES_MODULE.RunappsProjectsLocationsApplicationsCreateRequest(
          application=application,
          applicationId=application.name,
          parent=app_ref.Parent().RelativeName()))


def PatchApplication(client, app_ref, application, update_mask=None):
  """Calls ApplicationPatch API of Runapps of the specificed reference.

  Args:
    client: GAPIC API client, the api client to use.
    app_ref: googlecloudsdk.core.resources.Resource, the resource reference of
      the application.
    application: run_apps.v1alpha1.Application, the application to patch
    update_mask: str, comma separated string listing the fields to be updated.

  Returns:
    run_apps.v1alpha1.Operation, the LRO of this request.
  """
  return client.projects_locations_applications.Patch(
      client.MESSAGES_MODULE.RunappsProjectsLocationsApplicationsPatchRequest(
          application=application,
          updateMask=update_mask,
          name=app_ref.RelativeName()))


def CreateDeployment(client, app_ref, deployment, validate_only=False):
  """Calls ApplicationDeploymentCreate API of Runapps.

  Args:
    client: GAPIC API client, the api client to use.
    app_ref: googlecloudsdk.core.resources.Resource, the resource reference of
      the application the deployment belongs to
    deployment: run_apps.v1alpha1.Deployment, the deployment object
    validate_only: bool, whether to only validate the deployment

  Returns:
    run_apps.v1alpha1.Operation, the LRO of this request.
  """
  return client.projects_locations_applications_deployments.Create(
      client.MESSAGES_MODULE
      .RunappsProjectsLocationsApplicationsDeploymentsCreateRequest(
          parent=app_ref.RelativeName(),
          deployment=deployment,
          deploymentId=deployment.name,
          validateOnly=validate_only)
      )


def WaitForOperation(client, operation, message):
  """Wait for an operation to complete.

  Args:
    client:  the client used to make requests.
    operation: the operation object to wait for.
    message: the message to display during the wait.

  Returns:
    The resulting application.
  """

  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name,
      collection='{}.projects.locations.operations'.format(API_NAME))
  poller = waiter.CloudOperationPoller(client.projects_locations_applications,
                                       client.projects_locations_operations)
  try:
    return waiter.WaitFor(
        poller,
        operation_ref,
        message,
        max_wait_ms=_POLLING_TIMEOUT_MS,
        wait_ceiling_ms=_RETRY_TIMEOUT_MS)
  except waiter.OperationError:
    operation = poller.Poll(operation_ref)
    raise exceptions.IntegrationsOperationError(
        'OperationError: code={0}, message={1}'.format(
            operation.error.code, encoding.Decode(operation.error.message)))
