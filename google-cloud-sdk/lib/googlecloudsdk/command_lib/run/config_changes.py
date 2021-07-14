# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Class for representing various changes to a Configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import copy

from googlecloudsdk.api_lib.run import container_resource
from googlecloudsdk.api_lib.run import job
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import name_generator
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.run import secrets_mapping
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import repeated

import six


class ConfigChanger(six.with_metaclass(abc.ABCMeta, object)):
  """An abstract class representing configuration changes."""

  @abc.abstractmethod
  def Adjust(self, resource):
    """Adjust the given Service configuration.

    Args:
      resource: the k8s_object to adjust.

    Returns:
      A k8s_object that reflects applying the requested update.
      May be resource after a mutation or a different object.
    """
    return resource


def WithChanges(resource, changes):
  """Apply ConfigChangers to resource.

  It's undefined whether the input resource is modified.

  Args:
    resource: KubernetesObject, probably a Service.
    changes: List of ConfigChangers.

  Returns:
    Changed resource.
  """
  for config_change in changes:
    resource = config_change.Adjust(resource)
  return resource


class LabelChanges(ConfigChanger):
  """Represents the user intent to modify metadata labels."""

  LABELS_NOT_ALLOWED_IN_REVISION = ([service.ENDPOINT_VISIBILITY])

  def __init__(self, diff, copy_to_revision=True):
    super(LabelChanges, self).__init__()
    self._diff = diff
    self._copy_to_revision = copy_to_revision

  def Adjust(self, resource):
    # Currently assumes all "system"-owned labels are applied by the control
    # plane and it's ok for us to clear them on the client.
    update_result = self._diff.Apply(
        k8s_object.Meta(resource.MessagesModule()).LabelsValue,
        resource.metadata.labels)
    maybe_new_labels = update_result.GetOrNone()
    if maybe_new_labels:
      resource.metadata.labels = maybe_new_labels
      if self._copy_to_revision and hasattr(resource.template, 'labels'):
        # Service labels are the source of truth and *overwrite* revision labels
        # See go/run-labels-prd for deets.
        # However, we need to preserve the nonce if there is one.
        nonce = resource.template.labels.get(revision.NONCE_LABEL)
        resource.template.metadata.labels = copy.deepcopy(maybe_new_labels)
        for label_to_remove in self.LABELS_NOT_ALLOWED_IN_REVISION:
          if label_to_remove in resource.template.labels:
            del resource.template.labels[label_to_remove]
        if nonce:
          resource.template.labels[revision.NONCE_LABEL] = nonce
    return resource


class ReplaceServiceChange(ConfigChanger):
  """Represents the user intent to replace the service."""

  def __init__(self, new_service):
    super(ReplaceServiceChange, self).__init__()
    self._service = new_service

  def Adjust(self, resource):
    """Returns a replacement for resource.

    The returned service is the service provided to the constructor. If
    resource.metadata.resourceVersion is not empty to None returned service
    has metadata.resourceVersion set to this value.

    Args:
      resource: service.Service, The service to adjust.
    """
    if resource.metadata.resourceVersion:
      self._service.metadata.resourceVersion = resource.metadata.resourceVersion
      # Knative will complain if you try to edit (incl remove) serving annots.
      # So replicate them here.
      for k, v in resource.annotations.items():
        if k.startswith(k8s_object.SERVING_GROUP):
          self._service.annotations[k] = v
    return self._service


class EndpointVisibilityChange(LabelChanges):
  """Represents the user intent to modify the endpoint visibility.

  Only applies to Cloud Run for Anthos.
  """

  def __init__(self, endpoint_visibility):
    """Determine label changes for modifying endpoint visibility.

    Args:
      endpoint_visibility: bool, True if Cloud Run on GKE service should only be
        addressable from within the cluster. False if it should be publicly
        addressable.
    """
    if endpoint_visibility:
      diff = labels_util.Diff(
          additions={service.ENDPOINT_VISIBILITY: service.CLUSTER_LOCAL})
    else:
      diff = labels_util.Diff(subtractions=[service.ENDPOINT_VISIBILITY])
    # Don't copy this label to the revision because it's not supported there.
    # See b/154664962.
    super(EndpointVisibilityChange, self).__init__(diff, False)


class SetAnnotationChange(ConfigChanger):
  """Represents the user intent to set an annotation."""

  def __init__(self, key, value):
    super(SetAnnotationChange, self).__init__()
    self._key = key
    self._value = value

  def Adjust(self, resource):
    resource.annotations[self._key] = self._value
    return resource


class DeleteAnnotationChange(ConfigChanger):
  """Represents the user intent to delete an annotation."""

  def __init__(self, key):
    super(DeleteAnnotationChange, self).__init__()
    self._key = key

  def Adjust(self, resource):
    annotations = resource.annotations
    if self._key in annotations:
      del annotations[self._key]
    return resource


class SetTemplateAnnotationChange(ConfigChanger):
  """Represents the user intent to set a template annotation."""

  def __init__(self, key, value):
    super(SetTemplateAnnotationChange, self).__init__()
    self._key = key
    self._value = value

  def Adjust(self, resource):
    resource.template.annotations[self._key] = self._value
    return resource


class DeleteTemplateAnnotationChange(ConfigChanger):
  """Represents the user intent to delete a template annotation."""

  def __init__(self, key):
    super(DeleteTemplateAnnotationChange, self).__init__()
    self._key = key

  def Adjust(self, resource):
    annotations = resource.template.annotations
    if self._key in annotations:
      del annotations[self._key]
    return resource


class SetLaunchStageAnnotationChange(ConfigChanger):
  """Sets a VPC connector annotation on the service."""

  def __init__(self, launch_stage):
    super(SetLaunchStageAnnotationChange, self).__init__()
    self._launch_stage = launch_stage

  def Adjust(self, resource):
    if self._launch_stage == base.ReleaseTrack.GA:
      return resource
    else:
      resource.annotations[
          k8s_object.LAUNCH_STAGE_ANNOTATION] = self._launch_stage.id
      return resource


class SetClientNameAndVersionAnnotationChange(ConfigChanger):
  """Sets the client name and version annotations."""

  def __init__(self, client_name, client_version):
    super(SetClientNameAndVersionAnnotationChange, self).__init__()
    self._client_name = client_name
    self._client_version = client_version

  def Adjust(self, resource):
    if self._client_name is not None:
      resource.annotations[
          k8s_object.CLIENT_NAME_ANNOTATION] = self._client_name
      resource.template.annotations[
          k8s_object.CLIENT_NAME_ANNOTATION] = self._client_name
    if self._client_version is not None:
      resource.annotations[
          k8s_object.CLIENT_VERSION_ANNOTATION] = self._client_version
      resource.template.annotations[
          k8s_object.CLIENT_VERSION_ANNOTATION] = self._client_version
    return resource


class SandboxChange(ConfigChanger):
  """Sets a sandbox annotation on the service."""

  def __init__(self, sandbox):
    super(SandboxChange, self).__init__()
    self._sandbox = sandbox

  def Adjust(self, resource):
    resource.template.annotations[
        container_resource.SANDBOX_ANNOTATION] = self._sandbox
    return resource


class VpcConnectorChange(ConfigChanger):
  """Sets a VPC connector annotation on the service."""

  def __init__(self, connector_name):
    super(VpcConnectorChange, self).__init__()
    self._connector_name = connector_name

  def Adjust(self, resource):
    resource.template.annotations[
        container_resource.VPC_ACCESS_ANNOTATION] = self._connector_name
    return resource


class ClearVpcConnectorChange(ConfigChanger):
  """Clears a VPC connector annotation on the service."""

  def Adjust(self, resource):
    annotations = resource.template.annotations
    if container_resource.VPC_ACCESS_ANNOTATION in annotations:
      del annotations[container_resource.VPC_ACCESS_ANNOTATION]
    if container_resource.EGRESS_SETTINGS_ANNOTATION in annotations:
      del annotations[container_resource.EGRESS_SETTINGS_ANNOTATION]
    return resource


class ImageChange(ConfigChanger):
  """A Cloud Run container deployment."""

  deployment_type = 'container'

  def __init__(self, image):
    super(ImageChange, self).__init__()
    self.image = image

  def Adjust(self, resource):
    resource.annotations[container_resource.USER_IMAGE_ANNOTATION] = (
        self.image)
    if hasattr(resource.template, 'annotations'):
      resource.template.annotations[
          container_resource.USER_IMAGE_ANNOTATION] = (
              self.image)
    resource.image = self.image
    return resource


def _PruneMapping(mapping, keys_to_remove, clear_others):
  if clear_others:
    mapping.clear()
  else:
    for var_or_path in keys_to_remove:
      if var_or_path in mapping:
        del mapping[var_or_path]


class EnvVarLiteralChanges(ConfigChanger):
  """Represents the user intent to modify environment variables string literals."""

  def __init__(self, updates, removes, clear_others):
    """Initialize a new EnvVarLiteralChanges object.

    Args:
      updates: {str, str}, Update env var names and values.
      removes: [str], List of env vars to remove.
      clear_others: bool, If true, clear all non-updated env vars.
    """
    super(EnvVarLiteralChanges, self).__init__()
    self._updates = updates
    self._removes = removes
    self._clear_others = clear_others

  def Adjust(self, resource):
    """Mutates the given config's env vars to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the source of an
        existing environment variable whose source is of a different type
        (e.g. env var's secret source can't be replaced with a config map
        source).
    """
    _PruneMapping(resource.template.env_vars.literals, self._removes,
                  self._clear_others)

    try:
      resource.template.env_vars.literals.update(self._updates)
    except KeyError as e:
      raise exceptions.ConfigurationError(
          'Cannot update environment variable [{}] to string literal '
          'because it has already been set with a different type.'.format(
              e.args[0]))
    return resource


class SecretEnvVarChanges(ConfigChanger):
  """Represents the user intent to modify environment variable secrets."""

  def __init__(self, updates, removes, clear_others):
    """Initialize a new SecretEnvVarChanges object.

    Args:
      updates: {str: ReachableSecret}, Update env var names and values.
      removes: [str], List of env vars to remove.
      clear_others: bool, If true, clear all non-updated env vars.

    Raises:
      ConfigurationError if a key hasn't been provided for a source.
    """
    super(SecretEnvVarChanges, self).__init__()
    self._updates = updates
    self._removes = removes
    self._clear_others = clear_others

  def Adjust(self, resource):
    """Mutates the given config's env vars to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the source of an
        existing environment variable whose source is of a different type
        (e.g. env var's secret source can't be replaced with a config map
        source).
    """
    env_vars = resource.template.env_vars.secrets
    _PruneMapping(env_vars, self._removes, self._clear_others)

    for name, reachable_secret in self._updates.items():
      try:
        env_vars[name] = reachable_secret.AsEnvVarSource(resource)
      except KeyError:
        raise exceptions.ConfigurationError(
            'Cannot update environment variable [{}] to the given type '
            'because it has already been set with a different type.'.format(
                name))
    secrets_mapping.PruneAnnotation(resource)
    return resource


class ConfigMapEnvVarChanges(ConfigChanger):
  """Represents the user intent to modify environment variable config maps."""

  def __init__(self, updates, removes, clear_others):
    """Initialize a new ConfigMapEnvVarChanges object.

    Args:
      updates: {str, str}, Update env var names and values.
      removes: [str], List of env vars to remove.
      clear_others: bool, If true, clear all non-updated env vars.

    Raises:
      ConfigurationError if a key hasn't been provided for a source.
    """
    super(ConfigMapEnvVarChanges, self).__init__()
    self._updates = {}
    for name, v in updates.items():
      # Split the given values into 2 parts:
      #    [env var source name, source data item key]
      value = v.split(':', 1)
      if len(value) < 2:
        value.append(self._OmittedSecretKeyDefault(name))
      self._updates[name] = value
    self._removes = removes
    self._clear_others = clear_others

  def _OmittedSecretKeyDefault(self, name):
    if platforms.IsManaged():
      return 'latest'
    raise exceptions.ConfigurationError(
        'Missing required item key for environment variable [{}].'.format(name))

  def Adjust(self, resource):
    """Mutates the given config's env vars to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the source of an
        existing environment variable whose source is of a different type
        (e.g. env var's secret source can't be replaced with a config map
        source).
    """
    env_vars = resource.template.env_vars.config_maps
    _PruneMapping(env_vars, self._removes, self._clear_others)

    for name, (source_name, source_key) in self._updates.items():
      try:
        env_vars[name] = self._MakeEnvVarSource(resource.MessagesModule(),
                                                source_name, source_key)
      except KeyError:
        raise exceptions.ConfigurationError(
            'Cannot update environment variable [{}] to the given type '
            'because it has already been set with a different type.'.format(
                name))
    return resource

  def _MakeEnvVarSource(self, messages, name, key):
    return messages.EnvVarSource(
        configMapKeyRef=messages.ConfigMapKeySelector(
            name=name,
            key=key))


class ResourceChanges(ConfigChanger):
  """Represents the user intent to update resource limits."""

  def __init__(self, memory=None, cpu=None):
    super(ResourceChanges, self).__init__()
    self._memory = memory
    self._cpu = cpu

  def Adjust(self, resource):
    """Mutates the given config's resource limits to match what's desired."""
    if self._memory is not None:
      resource.template.resource_limits['memory'] = self._memory
    if self._cpu is not None:
      resource.template.resource_limits['cpu'] = self._cpu
    return resource


class CloudSQLChanges(ConfigChanger):
  """Represents the intent to update the Cloug SQL instances."""

  def __init__(self, project, region, args):
    """Initializes the intent to update the Cloud SQL instances.

    Args:
      project: Project to use as the default project for Cloud SQL instances.
      region: Region to use as the default region for Cloud SQL instances
      args: Args to the command.
    """
    super(CloudSQLChanges, self).__init__()
    self._project = project
    self._region = region
    self._args = args

  # Here we are a proxy through to the actual args to set some extra augmented
  # information on each one, so each cloudsql instance gets the region and
  # project.
  @property
  def add_cloudsql_instances(self):
    return self._AugmentArgs('add_cloudsql_instances')

  @property
  def remove_cloudsql_instances(self):
    return self._AugmentArgs('remove_cloudsql_instances')

  @property
  def set_cloudsql_instances(self):
    return self._AugmentArgs('set_cloudsql_instances')

  @property
  def clear_cloudsql_instances(self):
    return getattr(self._args, 'clear_cloudsql_instances', None)

  def _AugmentArgs(self, arg_name):
    val = getattr(self._args, arg_name, None)
    if val is None:
      return None
    return [self._Augment(i) for i in val]

  def Adjust(self, resource):
    def GetCurrentInstances():
      annotation_val = resource.template.annotations.get(
          container_resource.CLOUDSQL_ANNOTATION)
      if annotation_val:
        return annotation_val.split(',')
      return []

    instances = repeated.ParsePrimitiveArgs(
        self, 'cloudsql-instances', GetCurrentInstances)
    if instances is not None:
      resource.template.annotations[
          container_resource.CLOUDSQL_ANNOTATION] = ','.join(instances)
    return resource

  def _Augment(self, instance_str):
    instance = instance_str.split(':')
    if len(instance) == 3:
      ret = tuple(instance)
    elif len(instance) == 1:
      if not self._project:
        raise exceptions.CloudSQLError(
            'To specify a Cloud SQL instance by plain name, you must specify a '
            'project.')
      if not self._region:
        raise exceptions.CloudSQLError(
            'To specify a Cloud SQL instance by plain name, you must be '
            'deploying to a managed Cloud Run region.')
      ret = self._project, self._region, instance[0]
    else:
      raise exceptions.CloudSQLError(
          'Malformed CloudSQL instance string: {}'.format(
              instance_str))
    return ':'.join(ret)


class ConcurrencyChanges(ConfigChanger):
  """Represents the user intent to update concurrency preference."""

  def __init__(self, concurrency):
    super(ConcurrencyChanges, self).__init__()
    self._concurrency = None if concurrency == 'default' else int(concurrency)

  def Adjust(self, resource):
    """Mutates the given config's resource limits to match what's desired."""
    resource.template.concurrency = self._concurrency
    return resource


class TimeoutChanges(ConfigChanger):
  """Represents the user intent to update request duration."""

  def __init__(self, timeout):
    super(TimeoutChanges, self).__init__()
    self._timeout = timeout

  def Adjust(self, resource):
    """Mutates the given config's timeout to match what's desired."""
    resource.template.timeout = self._timeout
    return resource


class ServiceAccountChanges(ConfigChanger):
  """Represents the user intent to change service account for the revision."""

  def __init__(self, service_account):
    super(ServiceAccountChanges, self).__init__()
    self._service_account = service_account

  def Adjust(self, resource):
    """Mutates the given config's service account to match what's desired."""
    resource.template.service_account = self._service_account
    return resource


_MAX_RESOURCE_NAME_LENGTH = 63


class RevisionNameChanges(ConfigChanger):
  """Represents the user intent to change revision name."""

  def __init__(self, revision_suffix):
    super(RevisionNameChanges, self).__init__()
    self._revision_suffix = revision_suffix

  def Adjust(self, resource):
    """Mutates the given config's revision name to match what's desired."""
    max_prefix_length = (
        _MAX_RESOURCE_NAME_LENGTH - len(self._revision_suffix) - 1)
    resource.template.name = '{}-{}'.format(resource.name[:max_prefix_length],
                                            self._revision_suffix)
    return resource


def _GenerateVolumeName(prefix):
  """Randomly generated name with the given prefix."""
  return name_generator.GenerateName(sections=3, separator='-', prefix=prefix)


def _UniqueVolumeName(source_name, existing_volumes):
  """Generate unique volume name.

  The names that connect volumes and mounts must be unique even if their
  source volume names match.

  Args:
    source_name: (Potentially clashing) name.
    existing_volumes: Names in use.

  Returns:
    Unique name.
  """
  volume_name = None
  while volume_name is None or volume_name in existing_volumes:
    volume_name = _GenerateVolumeName(source_name)
  return volume_name


def _PruneVolumes(volume_mounts, volumes):
  """Delete all volumes no longer being mounted.

  Args:
    volume_mounts: resource.template.volume_mounts
    volumes: resource.template.volumes
  """
  for volume in list(volumes):
    if volume not in volume_mounts.values():
      del volumes[volume]


class SecretVolumeChanges(ConfigChanger):
  """Represents the user intent to change volumes with secret source types."""

  def __init__(self, updates, removes, clear_others):
    """Initialize a new SecretVolumeChanges object.

    Args:
      updates: {str: ReachableSecret}, Update mount path and volume fields.
      removes: [str], List of mount paths to remove.
      clear_others: bool, If true, clear all non-updated volumes and mounts of
        the given [volume_type].
    """
    super(SecretVolumeChanges, self).__init__()
    self._updates = updates
    self._removes = removes
    self._clear_others = clear_others

  def Adjust(self, resource):
    """Mutates the given config's volumes to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the volume a mount
        points to whose existing volume has a source of a different type than
        the new volume (e.g. mount that points to a volume with a secret source
        can't be replaced with a volume that has a config map source).
    """
    volume_mounts = resource.template.volume_mounts.secrets
    volumes = resource.template.volumes.secrets

    # TODO(b/182412304): This is not going to work on secrets in the same dir
    # (but it could be made to work if they're versions of one secret.)
    if platforms.IsManaged():
      removes = [p.rsplit('/', 1)[0] for p in self._removes]
    else:
      removes = self._removes

    _PruneMapping(volume_mounts, removes, self._clear_others)

    for file_path, reachable_secret in self._updates.items():
      volume_name = _UniqueVolumeName(reachable_secret.secret_name,
                                      resource.template.volumes)

      # volume_mounts is a special mapping that filters for the current kind
      # of mount and KeyErrors on existing keys with other types.
      try:
        mount_point = file_path
        if platforms.IsManaged():
          # TODO(b/182412304): SubPath handling is not ready.
          mount_point = file_path.rsplit('/', 1)[0]
        volume_mounts[mount_point] = volume_name
      except KeyError:
        raise exceptions.ConfigurationError(
            'Cannot update mount [{}] because its mounted volume '
            'is of a different source type.'.format(file_path))
      volumes[volume_name] = reachable_secret.AsSecretVolumeSource(resource)

    _PruneVolumes(volume_mounts, volumes)
    secrets_mapping.PruneAnnotation(resource)
    return resource


class ConfigMapVolumeChanges(ConfigChanger):
  """Represents the user intent to change volumes with config map source types."""

  def __init__(self, updates, removes, clear_others):
    """Initialize a new ConfigMapVolumeChanges object.

    Args:
      updates: {str, [str, str]}, Update mount path and volume fields.
      removes: [str], List of mount paths to remove.
      clear_others: bool, If true, clear all non-updated volumes and mounts of
        the given [volume_type].
    """
    super(ConfigMapVolumeChanges, self).__init__()
    self._updates = {}
    for k, v in updates.items():
      # Split the given values into 2 parts:
      #    [volume source name, data item key]
      update_value = v.split(':', 1)
      # Pad with None if no data item key specified
      if len(update_value) < 2:
        update_value.append(None)
      self._updates[k] = update_value
    self._removes = removes
    self._clear_others = clear_others

  def Adjust(self, resource):
    """Mutates the given config's volumes to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the volume a mount
        points to whose existing volume has a source of a different type than
        the new volume (e.g. mount that points to a volume with a secret source
        can't be replaced with a volume that has a config map source).
    """
    volume_mounts = resource.template.volume_mounts.config_maps
    volumes = resource.template.volumes.config_maps

    _PruneMapping(volume_mounts, self._removes, self._clear_others)

    for path, (source_name, source_key) in self._updates.items():
      volume_name = _UniqueVolumeName(source_name, resource.template.volumes)

      # volume_mounts is a special mapping that filters for the current kind
      # of mount and KeyErrors on existing keys with other types.
      try:
        volume_mounts[path] = volume_name
      except KeyError:
        raise exceptions.ConfigurationError(
            'Cannot update mount [{}] because its mounted volume '
            'is of a different source type.'.format(path))
      volumes[volume_name] = self._MakeVolumeSource(resource.MessagesModule(),
                                                    source_name, source_key)

    _PruneVolumes(volume_mounts, volumes)

    return resource

  def _MakeVolumeSource(self, messages, name, key=None):
    source = messages.ConfigMapVolumeSource(name=name)
    if key is not None:
      source.items.append(messages.KeyToPath(key=key, path=key))
    return source


class NoTrafficChange(ConfigChanger):
  """Represents the user intent to block traffic for a new revision."""

  def Adjust(self, resource):
    """Removes LATEST from the services traffic assignments."""
    if resource.configuration:
      raise exceptions.UnsupportedOperationError(
          'This service is using an old version of Cloud Run for Anthos '
          'that does not support traffic features. Please upgrade to 0.8 '
          'or later.')

    if not resource.generation:
      raise exceptions.ConfigurationError(
          '--no-traffic not supported when creating a new service.')

    resource.spec_traffic.ZeroLatestTraffic(
        resource.status.latestReadyRevisionName)
    return resource


class TrafficChanges(ConfigChanger):
  """Represents the user intent to change a service's traffic assignments."""

  def __init__(self,
               new_percentages,
               by_tag=False,
               tags_to_update=None,
               tags_to_remove=None,
               clear_other_tags=False):
    super(TrafficChanges, self).__init__()
    self._new_percentages = new_percentages
    self._by_tag = by_tag
    self._tags_to_update = tags_to_update or {}
    self._tags_to_remove = tags_to_remove or []
    self._clear_other_tags = clear_other_tags

  def Adjust(self, resource):
    """Mutates the given service's traffic assignments."""
    if self._tags_to_update or self._tags_to_remove or self._clear_other_tags:
      resource.spec_traffic.UpdateTags(self._tags_to_update,
                                       self._tags_to_remove,
                                       self._clear_other_tags)
    if self._new_percentages:
      if self._by_tag:
        tag_to_key = resource.spec_traffic.TagToKey()
        percentages = {}
        for tag in self._new_percentages:
          try:
            percentages[tag_to_key[tag]] = self._new_percentages[tag]
          except KeyError:
            raise exceptions.ConfigurationError(
                'There is no revision tagged with [{}] in the traffic allocation for [{}].'
                .format(tag, resource.name))
      else:
        percentages = self._new_percentages
      resource.spec_traffic.UpdateTraffic(percentages)
    return resource


class TagOnDeployChange(ConfigChanger):
  """The intent to provide a tag for the revision you're currently deploying."""

  def __init__(self, tag):
    super(TagOnDeployChange, self).__init__()
    self._tag = tag

  def Adjust(self, resource):
    """Gives the revision that's being created the given tag."""
    tags_to_update = {self._tag: resource.template.name}
    resource.spec_traffic.UpdateTags(tags_to_update, [], False)
    return resource


class ContainerCommandChange(ConfigChanger):
  """Represents the user intent to change the 'command' for the container."""

  def __init__(self, command):
    super(ContainerCommandChange, self).__init__()
    self._commands = command

  def Adjust(self, resource):
    resource.template.container.command = self._commands
    return resource


class ContainerArgsChange(ConfigChanger):
  """Represents the user intent to change the 'args' for the container."""

  def __init__(self, args):
    super(ContainerArgsChange, self).__init__()
    self._args = args

  def Adjust(self, resource):
    resource.template.container.args = self._args
    return resource


_HTTP2_NAME = 'h2c'
_DEFAULT_PORT = 8080


class ContainerPortChange(ConfigChanger):
  """Represents the user intent to change the port name and/or number."""

  def __init__(self, port=None, use_http2=None):
    """Initialize a ContainerPortChange.

    Args:
      port: str, the port number to set the port to, "default" to unset the
        containerPort field, or None to not modify the port number.
      use_http2: bool, True to set the port name for http/2, False to unset it,
        or None to not modify the port name.
    """
    super(ContainerPortChange, self).__init__()
    self._port = port
    self._http2 = use_http2

  def Adjust(self, resource):
    """Modify an existing ContainerPort or create a new one."""
    port_msg = (
        resource.template.container.ports[0]
        if resource.template.container.ports else
        resource.MessagesModule().ContainerPort())
    # Set port to given value or clear field
    if self._port == 'default':
      port_msg.reset('containerPort')
    elif self._port is not None:
      port_msg.containerPort = int(self._port)
    # Set name for http/2 or clear field
    if self._http2:
      port_msg.name = _HTTP2_NAME
    elif self._http2 is not None:
      port_msg.reset('name')
    # A port number must be specified
    if port_msg.name and not port_msg.containerPort:
      port_msg.containerPort = _DEFAULT_PORT

    # Use the ContainerPort iff it's not empty
    if port_msg.containerPort:
      resource.template.container.ports = [port_msg]
    else:
      resource.template.container.reset('ports')
    return resource


class SpecChange(ConfigChanger):
  """Represents the user intent to update field in the resource's spec."""

  def __init__(self, field, value):
    super(SpecChange, self).__init__()
    self._field = field
    self._value = value

  def Adjust(self, resource):
    setattr(resource.spec, self._field, self._value)
    return resource


class JobMaxRetriesChange(ConfigChanger):
  """Represents the user intent to update a job's restart policy."""

  def __init__(self, max_retries):
    super(JobMaxRetriesChange, self).__init__()
    self._max_retries = max_retries

  def Adjust(self, resource):
    if self._max_retries == 0:
      resource.template.restart_policy = job.RestartPolicy.NEVER
      resource.backoff_limit = 0
    else:
      resource.template.restart_policy = job.RestartPolicy.ON_FAILURE
      resource.backoff_limit = self._max_retries
    return resource


class JobInstanceDeadlineChange(ConfigChanger):
  """Represents the user intent to update a job's instance deadline."""

  def __init__(self, deadline_seconds):
    super(JobInstanceDeadlineChange, self).__init__()
    self._deadline_seconds = deadline_seconds

  def Adjust(self, resource):
    resource.template.spec.activeDeadlineSeconds = self._deadline_seconds
    return resource


class CpuThrottlingChange(ConfigChanger):
  """Sets the cpu-throttling annotation on the service."""

  def __init__(self, throttling):
    super(CpuThrottlingChange, self).__init__()
    self._throttling = throttling

  def Adjust(self, resource):
    resource.template.annotations[
        container_resource.CPU_THROTTLE_ANNOTATION] = str(self._throttling)
    return resource


class ConfidentialChange(ConfigChanger):
  """Sets the confidential annotation on the service."""

  def __init__(self, confidential):
    super(ConfidentialChange, self).__init__()
    self._confidential = confidential

  def Adjust(self, resource):
    resource.template.annotations[
        container_resource.CONFIDENTIAL_ANNOTATION] = str(self._confidential)
    return resource
