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
"""Utilities for the blueprints API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker

_API_NAME = 'config'
_ALPHA_API_VERSION = 'v1alpha1'

RELEASE_TRACK_TO_API_VERSION = {
    base.ReleaseTrack.ALPHA: 'v1alpha1',
}


def GetMessagesModule(release_track=base.ReleaseTrack.ALPHA):
  """Returns the messages module for Blueprints Controller.

  Args:
    release_track: The desired value of the enum
      googlecloudsdk.calliope.base.ReleaseTrack.

  Returns:
    Module containing the definitions of messages for Blueprints Controller.
  """
  return apis.GetMessagesModule(_API_NAME,
                                RELEASE_TRACK_TO_API_VERSION[release_track])


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA, use_http=True):
  """Returns an instance of the Blueprints Controller client.

  Args:
    release_track: The desired value of the enum
      googlecloudsdk.calliope.base.ReleaseTrack.
    use_http: bool, True to create an http object for this client.

  Returns:
    base_api.BaseApiClient, An instance of the Cloud Build client.
  """
  return apis.GetClientInstance(
      _API_NAME,
      RELEASE_TRACK_TO_API_VERSION[release_track],
      no_http=(not use_http))


def GetRevision(name):
  """Calls into the GetRevision API.

  Args:
    name: the fully qualified name of the revision, e.g.
      "projects/p/locations/l/deployments/d/revisions/r".

  Returns:
    A messages.Revision.

  Raises:
    HttpNotFoundError: if the revision didn't exist.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_deployments_revisions.Get(
      messages.ConfigProjectsLocationsDeploymentsRevisionsGetRequest(name=name))


def GetDeployment(name):
  """Calls into the GetDeployment API.

  Args:
    name: the fully qualified name of the deployment, e.g.
      "projects/p/locations/l/deployments/d".

  Returns:
    A messages.Deployment.

  Raises:
    HttpNotFoundError: if the deployment didn't exist.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_deployments.Get(
      messages.ConfigProjectsLocationsDeploymentsGetRequest(name=name))


def CreateDeployment(deployment, deployment_id, location):
  """Calls into the CreateDeployment API.

  Args:
    deployment: a messages.Deployment resource (containing properties like the
      blueprint).
    deployment_id: the ID of the deployment, e.g. "my-deployment" in
      "projects/p/locations/l/deployments/my-deployment".
    location: the location in which to create the deployment.

  Returns:
    A messages.OperationMetadata representing the long-running operation.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_deployments.Create(
      messages.ConfigProjectsLocationsDeploymentsCreateRequest(
          parent=location, deployment=deployment, deploymentId=deployment_id))


def UpdateDeployment(deployment, deployment_full_name):
  """Calls into the UpdateDeployment API.

  Args:
    deployment: a messages.Deployment resource (containing properties like the
      blueprint).
    deployment_full_name: the fully qualified name of the deployment.

  Returns:
    A messages.OperationMetadata representing the long-running operation.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_deployments.Patch(
      messages.ConfigProjectsLocationsDeploymentsPatchRequest(
          deployment=deployment, name=deployment_full_name, updateMask=None))


def DeleteDeployment(deployment_full_name):
  """Calls into the DeleteDeployment API.

  Args:
    deployment_full_name: the fully qualified name of the deployment.

  Returns:
    A messages.OperationMetadata representing the long-running operation.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_deployments.Delete(
      messages.ConfigProjectsLocationsDeploymentsDeleteRequest(
          name=deployment_full_name,
          # Delete all child revisions.
          force=True))


def WaitForDeleteDeploymentOperation(operation):
  """Waits for the given "delete deployment" LRO to complete.

  Args:
    operation: the operation to poll.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error

  Returns:
    An Operation.ResponseValue instance
  """
  client = GetClientInstance()
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name, collection='config.projects.locations.operations')
  poller = waiter.CloudOperationPollerNoResources(
      client.projects_locations_operations)

  return waiter.WaitFor(poller, operation_ref, 'Deleting the deployment')


def WaitForApplyDeploymentOperation(operation, progress_message):
  """Waits for the given "apply deployment" LRO to complete.

  Args:
    operation: the operation to poll.
    progress_message: string to display for default progress_tracker.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error

  Returns:
    A messages.Deployment resource.
  """
  client = GetClientInstance()
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name, collection='config.projects.locations.operations')
  poller = waiter.CloudOperationPoller(client.projects_locations_deployments,
                                       client.projects_locations_operations)

  return WaitForApplyDeploymentLROWithStagedTracker(poller, operation_ref,
                                                    progress_message)


def ApplyDeploymentProgressStages():
  """Gets an OrderedDict of progress_tracker.Stage keys to message mappings.

  Returns:
    An OrderedDict where the keys are the respective stage keys and the values
    are the messages to show for the particular stage.
  """
  messages = GetMessagesModule()
  step_enum = messages.DeploymentOperationMetadata.StepValueValuesEnum
  stages = collections.OrderedDict()
  stages[step_enum.PREPARING_STORAGE_BUCKET.name] = (
      'Preparing storage bucket (this can take up to 7 minutes on the '
      'first deployment).')
  stages[step_enum.PREPARING_CONFIG_CONTROLLER.name] = (
      'Preparing Config Controller instance (this can take up to 20 '
      'minutes on the first deployment).')
  # TODO(b/195148906): Add Cloud Build log URL to pipeline and apply messages.
  stages[step_enum.RUNNING_PIPELINE
         .name] = 'Processing blueprint through kpt pipeline.'
  stages[
      step_enum.RUNNING_APPLY.name] = 'Applying blueprint to Config Controller.'
  return stages


def WaitForApplyDeploymentLROWithStagedTracker(poller, operation_ref, message):
  """Waits for an "apply" deployment LRO using a StagedProgressTracker.

  This function is a wrapper around waiter.PollUntilDone that uses a
  progress_tracker.StagedProgressTracker to display the individual steps of
  an apply deployment LRO.

  Args:
    poller: a waiter.Poller instance
    operation_ref: Reference to the operation to poll on.
    message: string containing the main progress message to display.

  Returns:
    A messages.Deployment resource.
  """
  messages = GetMessagesModule()
  state_enum = messages.Deployment.StateValueValuesEnum
  stages = []
  progress_stages = ApplyDeploymentProgressStages()
  for key, msg in progress_stages.items():
    stages.append(progress_tracker.Stage(msg, key))

  with progress_tracker.StagedProgressTracker(
      message=message, stages=stages,
      tracker_id='meta.deployment_progress') as tracker:

    def _StatusUpdate(result, status):
      """Updates poller.detailed_message on every tick with an appropriate message.

      Args:
        result: the latest messages.Operation object.
        status: unused.
      """
      del status  # Unused by this logic

      # Need to encode to JSON and then decode to Message to be able to
      # reasonably access attributes.
      json = encoding.MessageToJson(result.metadata)
      deployment_metadata = encoding.JsonToMessage(messages.OperationMetadata,
                                                   json).deploymentMetadata

      if deployment_metadata is not None and progress_stages.get(
          deployment_metadata.step.name) is not None:
        tracker.StartStage(deployment_metadata.step.name)

        # Complete all previous stages.
        ordered_stages = list(progress_stages.keys())
        current_index = ordered_stages.index(deployment_metadata.step.name)
        for i in range(current_index):
          if not tracker.IsComplete(ordered_stages[i]):
            tracker.CompleteStage(ordered_stages[i])

    operation = waiter.PollUntilDone(
        poller, operation_ref, status_update=_StatusUpdate)
    result = poller.GetResult(operation)

    if result is not None and result.state == state_enum.ACTIVE:
      for stage in stages:
        if not tracker.IsComplete(stage.key):
          tracker.CompleteStage(stage.key)

    return result
