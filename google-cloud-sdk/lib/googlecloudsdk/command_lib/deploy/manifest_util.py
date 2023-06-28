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
"""Utilities for parsing the cloud deploy resource to yaml definition."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.command_lib.deploy import automation_util
from googlecloudsdk.command_lib.deploy import deploy_util
from googlecloudsdk.command_lib.deploy import exceptions
from googlecloudsdk.command_lib.deploy import target_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

PIPELINE_UPDATE_MASK = '*,labels'
DELIVERY_PIPELINE_KIND_V1BETA1 = 'DeliveryPipeline'
TARGET_KIND_V1BETA1 = 'Target'
AUTOMATION_KIND = 'Automation'
API_VERSION_V1BETA1 = 'deploy.cloud.google.com/v1beta1'
API_VERSION_V1 = 'deploy.cloud.google.com/v1'
USAGE_CHOICES = ['RENDER', 'DEPLOY']
# If changing these fields also change them in the UI code.
NAME_FIELD = 'name'
ADVANCE_ROLLOUT_FIELD = 'advanceRollout'
PROMOTE_RELEASE_FIELD = 'promoteRelease'
WAIT_FIELD = 'wait'
LABELS_FIELD = 'labels'
ANNOTATIONS_FIELD = 'annotations'
METADATA_FIELDS = [ANNOTATIONS_FIELD, LABELS_FIELD]
EXCLUDE_FIELDS = [
    'createTime',
    'etag',
    'uid',
    'updateTime',
    NAME_FIELD,
] + METADATA_FIELDS


def ParseDeployConfig(messages, manifests, region):
  """Parses the declarative definition of the resources into message.

  Args:
    messages: module containing the definitions of messages for Cloud Deploy.
    manifests: [str], the list of parsed resource yaml definitions.
    region: str, location ID.

  Returns:
    A dictionary of resource kind and message.
  Raises:
    exceptions.CloudDeployConfigError, if the declarative definition is
    incorrect.
  """
  resource_dict = {
      DELIVERY_PIPELINE_KIND_V1BETA1: [],
      TARGET_KIND_V1BETA1: [],
      AUTOMATION_KIND: [],
  }
  project = properties.VALUES.core.project.GetOrFail()
  for manifest in manifests:
    if manifest.get('apiVersion') is None:
      raise exceptions.CloudDeployConfigError(
          'missing required field .apiVersion')
    if manifest.get('kind') is None:
      raise exceptions.CloudDeployConfigError('missing required field .kind')
    api_version = manifest['apiVersion']
    if api_version in {API_VERSION_V1BETA1, API_VERSION_V1}:
      _ParseV1Config(messages, manifest['kind'], manifest, project, region,
                     resource_dict)
    else:
      raise exceptions.CloudDeployConfigError(
          'api version {} not supported'.format(api_version))

  return resource_dict


def _ParseV1Config(messages, kind, manifest, project, region, resource_dict):
  """Parses the Cloud Deploy v1 and v1beta1 resource specifications into message.

       This specification version is KRM complied and should be used after
       private review.

  Args:
     messages: module containing the definitions of messages for Cloud Deploy.
     kind: str, name of the resource schema.
     manifest: dict[str,str], cloud deploy resource yaml definition.
     project: str, gcp project.
     region: str, ID of the location.
     resource_dict: dict[str,optional[message]], a dictionary of resource kind
       and message.

  Raises:
    exceptions.CloudDeployConfigError, if the declarative definition is
    incorrect.
  """
  metadata = manifest.get('metadata')
  if not metadata or not metadata.get(NAME_FIELD):
    raise exceptions.CloudDeployConfigError(
        'missing required field .metadata.name in {}'.format(kind))
  if kind == DELIVERY_PIPELINE_KIND_V1BETA1:
    resource_type = deploy_util.ResourceType.DELIVERY_PIPELINE
    resource, resource_ref = _CreateDeliveryPipelineResource(
        messages, metadata[NAME_FIELD], project, region
    )
  elif kind == TARGET_KIND_V1BETA1:
    resource_type = deploy_util.ResourceType.TARGET
    resource, resource_ref = _CreateTargetResource(
        messages, metadata[NAME_FIELD], project, region
    )
  elif kind == AUTOMATION_KIND:
    resource_type = deploy_util.ResourceType.AUTOMATION
    resource, resource_ref = _CreateAutomationResource(
        messages, metadata[NAME_FIELD], project, region
    )
  else:
    raise exceptions.CloudDeployConfigError(
        'kind {} not supported'.format(kind))

  if '/' in resource_ref.Name():
    raise exceptions.CloudDeployConfigError(
        'resource ID "{}" contains /.'.format(resource_ref.Name()))

  for field in manifest:
    if field not in ['apiVersion', 'kind', 'metadata', 'deliveryPipeline']:
      value = manifest.get(field)
      if field == 'executionConfigs':
        SetExecutionConfig(messages, resource, value)
        continue
      if field == 'deployParameters' and kind == TARGET_KIND_V1BETA1:
        SetDeployParametersForTarget(messages, resource, value)
        continue
      if field == 'serialPipeline' and kind == DELIVERY_PIPELINE_KIND_V1BETA1:
        serial_pipeline = manifest.get('serialPipeline')
        stages = serial_pipeline.get('stages')
        for stage in stages:
          SetDeployParametersForPipelineStage(messages, stage)
      if field == 'selector' and kind == AUTOMATION_KIND:
        SetAutomationSelector(messages, resource, value)
        continue
      if field == 'rules' and kind == AUTOMATION_KIND:
        SetAutomationRules(messages, resource, value)
        continue
      setattr(resource, field, value)

  # Sets the properties in metadata.
  for field in metadata:
    if field not in [NAME_FIELD, ANNOTATIONS_FIELD, LABELS_FIELD]:
      setattr(resource, field, metadata.get(field))
  deploy_util.SetMetadata(
      messages,
      resource,
      resource_type,
      metadata.get(ANNOTATIONS_FIELD),
      metadata.get(LABELS_FIELD),
  )

  resource_dict[kind].append(resource)


def _CreateTargetResource(messages, target_name_or_id, project, region):
  """Creates target resource with full target name and the resource reference."""
  resource = messages.Target()
  resource_ref = target_util.TargetReference(target_name_or_id, project, region)
  resource.name = resource_ref.RelativeName()

  return resource, resource_ref


def _CreateDeliveryPipelineResource(messages, delivery_pipeline_name, project,
                                    region):
  """Creates delivery pipeline resource with full delivery pipeline name and the resource reference."""
  resource = messages.DeliveryPipeline()
  resource_ref = resources.REGISTRY.Parse(
      delivery_pipeline_name,
      collection='clouddeploy.projects.locations.deliveryPipelines',
      params={
          'projectsId': project,
          'locationsId': region,
          'deliveryPipelinesId': delivery_pipeline_name,
      })
  resource.name = resource_ref.RelativeName()

  return resource, resource_ref


def _CreateAutomationResource(messages, name, project, region):
  resource = messages.Automation()
  resource_ref = automation_util.AutomationReference(name, project, region)
  resource.name = resource_ref.RelativeName()

  return resource, resource_ref


def ProtoToManifest(resource, resource_ref, kind):
  """Converts a resource message to a cloud deploy resource manifest.

  The manifest can be applied by 'deploy apply' command.

  Args:
    resource: message in googlecloudsdk.generated_clients.apis.clouddeploy.
    resource_ref: cloud deploy resource object.
    kind: kind of the cloud deploy resource

  Returns:
    A dictionary that represents the cloud deploy resource.
  """
  manifest = collections.OrderedDict(
      apiVersion=API_VERSION_V1, kind=kind, metadata={})

  for k in METADATA_FIELDS:
    v = getattr(resource, k)
    # Skips the 'zero' values in the message.
    if v:
      manifest['metadata'][k] = v
  # Sets the name to resource ID instead of the full name.
  manifest['metadata'][NAME_FIELD] = resource_ref.Name()

  for f in resource.all_fields():
    if f.name in EXCLUDE_FIELDS:
      continue
    v = getattr(resource, f.name)
    # Skips the 'zero' values in the message.
    if v:
      manifest[f.name] = v

  return manifest


def SetExecutionConfig(messages, target, execution_configs):
  """Sets the executionConfigs field of cloud deploy resource message.

  Args:
    messages: module containing the definitions of messages for Cloud Deploy.
    target:  googlecloudsdk.generated_clients.apis.clouddeploy.Target message.
    execution_configs:
      [googlecloudsdk.generated_clients.apis.clouddeploy.ExecutionConfig], list
      of ExecutionConfig messages.

  Raises:
    arg_parsers.ArgumentTypeError: if usage is not a valid enum.
  """
  for config in execution_configs:
    execution_config_message = messages.ExecutionConfig()
    for field in config:
      # the value of usages field has enum, which needs special treatment.
      if field != 'usages':
        setattr(execution_config_message, field, config.get(field))
    usages = config.get('usages') or []
    for usage in usages:
      execution_config_message.usages.append(
          # converts a string literal in executionConfig.usages to an Enum.
          arg_utils.ChoiceToEnum(
              usage,
              messages.ExecutionConfig.UsagesValueListEntryValuesEnum,
              valid_choices=USAGE_CHOICES))

    target.executionConfigs.append(execution_config_message)


def SetDeployParametersForPipelineStage(messages, stage):
  """Sets the deployParameter field of cloud deploy delivery pipeline stage message.

  Args:
   messages: module containing the definitions of messages for Cloud Deploy.
   stage:
    dict[str,str], cloud deploy stage yaml definition.
  """

  deploy_parameters = stage.get('deployParameters')
  if deploy_parameters is None:
    return

  dps_message = getattr(messages, 'DeployParameters')
  dps_values = []

  for dp in deploy_parameters:
    dps_value = dps_message()
    values = dp.get('values')
    if values:
      values_message = dps_message.ValuesValue
      values_dict = values_message()

      for key, value in values.items():
        values_dict.additionalProperties.append(
            values_message.AdditionalProperty(
                key=key,
                value=value))
      dps_value.values = values_dict

    match_target_labels = dp.get('matchTargetLabels')
    if match_target_labels:
      mtls_message = dps_message.MatchTargetLabelsValue
      mtls_dict = mtls_message()

      for key, value in match_target_labels.items():
        mtls_dict.additionalProperties.append(
            mtls_message.AdditionalProperty(
                key=key,
                value=value))
      dps_value.matchTargetLabels = mtls_dict

    dps_values.append(dps_value)

  stage['deployParameters'] = dps_values


def SetDeployParametersForTarget(messages,
                                 target, deploy_parameters=None):
  """Sets the deployParameters field of cloud deploy target message.

  Args:
   messages: module containing the definitions of messages for Cloud Deploy.
   target: googlecloudsdk.generated_clients.apis.clouddeploy.Target message.
   deploy_parameters:
    dict[str,str], a dict of deploy parameters (key,value) pairs.
  """

  if deploy_parameters is None:
    return

  dps_message = getattr(messages,
                        deploy_util.ResourceType.TARGET.value
                        ).DeployParametersValue
  dps_value = dps_message()
  for key, value in deploy_parameters.items():
    dps_value.additionalProperties.append(
        dps_message.AdditionalProperty(
            key=key,
            value=value))
  target.deployParameters = dps_value


def SetAutomationSelector(messages, automation, selectors):
  """Sets the selectors field of cloud deploy automation resource message.

  Args:
    messages: module containing the definitions of messages for Cloud Deploy.
    automation:  googlecloudsdk.generated_clients.apis.clouddeploy.Automation
      message.
    selectors:
      [googlecloudsdk.generated_clients.apis.clouddeploy.TargetAttributes], list
      of TargetAttributes messages.
  """
  automation.selector = messages.AutomationResourceSelector()
  for selector in selectors:
    target_attribute = messages.TargetAttribute()
    message = selector.get('target')
    for field in message:
      value = message.get(field)
      if field == 'id':
        setattr(target_attribute, field, value)
      if field == LABELS_FIELD:
        deploy_util.SetMetadata(
            messages,
            target_attribute,
            deploy_util.ResourceType.TARGET_ATTRIBUTE,
            None,
            value,
        )
    automation.selector.targets.append(target_attribute)


def SetAutomationRules(messages, automation, rules):
  """Sets the rules field of cloud deploy automation resource message.

  Args:
    messages: module containing the definitions of messages for Cloud Deploy.
    automation:  googlecloudsdk.generated_clients.apis.clouddeploy.Automation
      message.
    rules: [automation rule message], list of messages that are usd to create
      googlecloudsdk.generated_clients.apis.clouddeploy.AutomationRule messages.
  """
  for rule in rules:
    automation_rule = messages.AutomationRule()
    if rule.get(PROMOTE_RELEASE_FIELD):
      message = rule.get(PROMOTE_RELEASE_FIELD)
      promote_release = messages.PromoteReleaseRule(
          id=message.get(NAME_FIELD),
          wait=message.get(WAIT_FIELD),
          targetId=message.get('toTargetId'),
          phase=message.get('toPhase'),
      )
      automation_rule.promoteReleaseRule = promote_release
    if rule.get(ADVANCE_ROLLOUT_FIELD):
      message = rule.get(ADVANCE_ROLLOUT_FIELD)
      advance_rollout = messages.AdvanceRolloutRule(
          id=message.get(NAME_FIELD),
          wait=message.get(WAIT_FIELD),
          phases=message.get('fromPhases'),
      )
      automation_rule.advanceRolloutRule = advance_rollout
    automation.rules.append(automation_rule)
