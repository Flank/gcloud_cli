# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Support library for managing deployments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import numbers

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import extra_types
from googlecloudsdk.api_lib.config_manager import configmanager_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
import six


def UpdateDeploymentDeleteRequestWithForce(unused_ref, unused_args, request):
  """UpdateDeploymentDeleteRequestWithForce adds force flag to delete request."""

  request.force = True
  return request


def _CreateTFBlueprint(
    messages,
    gcs_source,
    git_source_repo,
    git_source_directory,
    git_source_ref,
    input_values,
):
  """Returns the TerraformBlueprint message.

  Args:
    messages: ModuleType, the messages module that lets us form blueprints API
      messages based on our protos.
    gcs_source:  URI of an object in Google Cloud Storage. e.g.
      `gs://{bucket}/{object}`
    git_source_repo: Repository URL.
    git_source_directory: Subdirectory inside the git repository.
    git_source_ref: Git branch or tag.
    input_values: Input variable values for the Terraform blueprint. It only
      accepts (key, value) pairs where value is a scalar value.

  Returns:
    A messages.TerraformBlueprint to use with deployment operation.
  """

  terraform_blueprint = messages.TerraformBlueprint(
      inputValues=input_values,
  )

  if gcs_source is not None:
    terraform_blueprint.gcsSource = gcs_source
  else:
    terraform_blueprint.gitSource = messages.GitSource(
        repo=git_source_repo,
        directory=git_source_directory,
        ref=git_source_ref,
    )

  return terraform_blueprint


def Apply(
    messages,
    async_,
    deployment_full_name,
    service_account,
    import_existing_resources=None,
    artifacts_gcs_bucket=None,
    worker_pool=None,
    gcs_source=None,
    git_source_repo=None,
    git_source_directory=None,
    git_source_ref=None,
    input_values=None,
    labels=None,
):
  """Updates the deployment if one exists, otherwise creates a deployment.

  Args:
    messages: ModuleType, the messages module that lets us form blueprints API
      messages based on our protos.
    async_: bool, if True, gcloud will return immediately, otherwise it will
      wait on the long-running operation.
    deployment_full_name: string, the fully qualified name of the deployment,
      e.g. "projects/p/locations/l/deployments/d".
    service_account: User-specified Service Account (SA) to be used as
      credential to manage resources. e.g.
      `projects/{projectID}/serviceAccounts/{serviceAccount}` The default Cloud
      Build SA will be used initially if this field is not set.
    import_existing_resources: By default, Cloud Config Manager will return a
      failure when Terraform encounters a 409 code (resource conflict error)
      during actuation. If this flag is set to true, Cloud Config Manager will
      instead attempt to automatically import the resource into the Terraform
      state (for supported resource types) and continue actuation.
    artifacts_gcs_bucket: User-defined location of Cloud Build logs, artifacts,
      and Terraform state files in Google Cloud Storage. e.g.
      `gs://{bucket}/{folder}` A default bucket will be bootstrapped if the
      field is not set or empty
    worker_pool: The User-specified Worker Pool resource in which the Cloud
      Build job will execute. If this field is unspecified, the default Cloud
      Build worker pool will be used. e.g.
      projects/{project}/locations/{location}/workerPools/{workerPoolId}
    gcs_source:  URI of an object in Google Cloud Storage. e.g.
      `gs://{bucket}/{object}`
    git_source_repo: Repository URL.
    git_source_directory: Subdirectory inside the git repository.
    git_source_ref: Git branch or tag.
    input_values: Input variable values for the Terraform blueprint. It only
      accepts (key, value) pairs where value is a scalar value.
    labels: User-defined metadata for the deployment.

  Returns:
    The resulting Deployment resource or, in the case that async_ is True, a
      long-running operation.

  Raises:
    InvalidArgumentException: If an invalid set of flags is provided (e.g.
      trying to run with --target-git-subdir but without --target-git).
  """

  labels_message = {}
  # Whichever labels the user provides will become the full set of labels in the
  # resulting deployment.
  if labels is not None:
    labels_message = messages.Deployment.LabelsValue(
        additionalProperties=[
            messages.Deployment.LabelsValue.AdditionalProperty(
                key=key, value=value
            )
            for key, value in six.iteritems(labels)
        ]
    )

  tf_input_values = {}
  if input_values is not None:
    additional_properties = []
    for key, value in six.iteritems(input_values):
      additional_properties.append(
          messages.TerraformBlueprint.InputValuesValue.AdditionalProperty(
              key=key,
              value=messages.TerraformVariable(
                  inputValue=_PythonValueToJsonValue(value)
              ),
          )
      )

    tf_input_values = messages.TerraformBlueprint.InputValuesValue(
        additionalProperties=additional_properties
    )

  tf_blueprint = _CreateTFBlueprint(
      messages,
      gcs_source,
      git_source_repo,
      git_source_directory,
      git_source_ref,
      tf_input_values,
  )

  deployment = messages.Deployment(
      name=deployment_full_name,
      serviceAccount=service_account,
      importExistingResources=import_existing_resources,
      workerPool=worker_pool,
      terraformBlueprint=tf_blueprint,
      labels=labels_message,
  )

  if artifacts_gcs_bucket is not None:
    deployment.artifactGcsBucket = artifacts_gcs_bucket

  # Check if a deployment with the given name already exists. If it does, we'll
  # update that deployment. If not, we'll create it.
  try:
    existing_deployment = configmanager_util.GetDeployment(deployment_full_name)
  except apitools_exceptions.HttpNotFoundError:
    existing_deployment = None

  is_creating_deployment = existing_deployment is None
  op = None

  deployment_ref = resources.REGISTRY.Parse(
      deployment_full_name, collection='config.projects.locations.deployments'
  )
  # Get just the ID from the fully qualified name.
  deployment_id = deployment_ref.Name()

  if is_creating_deployment:
    op = _CreateDeploymentOp(deployment, deployment_full_name)
  else:
    op = _UpdateDeploymentOp(
        deployment, existing_deployment, deployment_full_name, labels
    )

  log.debug('LRO: %s', op.name)

  # If the user chose to run asynchronously, then we'll match the output that
  # the automatically-generated Delete command issues and return immediately.
  if async_:
    log.status.Print(
        '{0} request issued for: [{1}]'.format(
            'Create' if is_creating_deployment else 'Update', deployment_id
        )
    )

    log.status.Print('Check operation [{}] for status.'.format(op.name))

    return op

  progress_message = '{} the deployment'.format(
      'Creating' if is_creating_deployment else 'Updating'
  )

  applied_deployment = configmanager_util.WaitForApplyDeploymentOperation(
      op, progress_message
  )

  if (
      applied_deployment.state
      == messages.Deployment.StateValueValuesEnum.FAILED
  ):
    log.error(applied_deployment.stateDetail)

  return applied_deployment


def _CreateDeploymentOp(
    deployment,
    deployment_full_name,
):
  """Initiates and returns a CreateDeployment operation.

  Args:
    deployment: A partially filled messages.Deployment. The deployment will be
      filled with other details before the operation is initiated.
    deployment_full_name: string, the fully qualified name of the deployment,
      e.g. "projects/p/locations/l/deployments/d".

  Returns:
    The CreateDeployment operation.
  """
  deployment_ref = resources.REGISTRY.Parse(
      deployment_full_name, collection='config.projects.locations.deployments'
  )
  location_ref = deployment_ref.Parent()
  # Get just the ID from the fully qualified name.
  deployment_id = deployment_ref.Name()

  log.info('Creating the deployment')
  return configmanager_util.CreateDeployment(
      deployment, deployment_id, location_ref.RelativeName()
  )


def _UpdateDeploymentOp(
    deployment,
    existing_deployment,
    deployment_full_name,
    labels,
):
  """Initiates and returns an UpdateDeployment operation.

  Args:
    deployment: A partially filled messages.Deployment. The deployment will be
      filled with its target (e.g. configController, gitTarget, etc.) before the
      operation is initiated.
    existing_deployment: A messages.Deployment. The existing deployment to
      update.
    deployment_full_name: string, the fully qualified name of the deployment,
      e.g. "projects/p/locations/l/deployments/d".
    labels: dictionary of string → string, labels to be associated with the
      deployment.

  Returns:
    The UpdateDeployment operation.
  """

  log.info('Updating the existing deployment')

  # If the user didn't specify labels here, then we don't want to overwrite
  # the existing labels on the deployment, so we provide them back to the
  # underlying API.
  if labels is None:
    deployment.labels = existing_deployment.labels

  return configmanager_util.UpdateDeployment(deployment, deployment_full_name)


_MAXINT64 = 2 << 63 - 1
_MININT64 = -(2 << 63)


# Mostly taken from extra_types._PythonValueToJsonValue
def _PythonValueToJsonValue(py_value):
  """Convert the given python value to a JsonValue. Works for scalar values.

  Args:
    py_value: scalar python value.

  Returns:
    Equivalent JsonValue.
  """
  if py_value is None:
    return extra_types.JsonValue(is_null=True)
  if isinstance(py_value, bool):
    return extra_types.JsonValue(boolean_value=py_value)
  if isinstance(py_value, six.string_types):
    return extra_types.JsonValue(string_value=py_value)
  if isinstance(py_value, numbers.Number):
    if isinstance(py_value, six.integer_types):
      if _MININT64 < py_value < _MAXINT64:
        return extra_types.JsonValue(integer_value=py_value)
    return extra_types.JsonValue(double_value=float(py_value))
  raise apitools_exceptions.InvalidDataError(
      'Cannot convert "%s" to JsonValue' % py_value
  )
