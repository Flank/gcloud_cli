# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Shared resource flags for Cloud Run commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import os
import re

from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class PromptFallthrough(deps.Fallthrough):
  """Fall through to reading from an interactive prompt."""

  def __init__(self, hint):
    super(PromptFallthrough, self).__init__(function=None, hint=hint)

  @abc.abstractmethod
  def _Prompt(self, parsed_args):
    pass

  def _Call(self, parsed_args):
    if not console_io.CanPrompt():
      return None
    return self._Prompt(parsed_args)


def GenerateServiceName(source_ref):
  """Produce a valid default service name.

  Converts a file path or image path into a reasonable default service name by
  stripping file path delimeters, image tags, and image hashes.
  For example, the image name 'gcr.io/myproject/myimage:latest' would produce
  the service name 'myimage'.

  Args:
    source_ref: SourceRef, The app's source directory or container path.

  Returns:
    A valid Cloud Run service name.
  """
  base_name = os.path.basename(source_ref.source_path.rstrip(os.sep))
  base_name = base_name.split(':')[0]  # Discard image tag if present.
  base_name = base_name.split('@')[0]  # Disacard image hash if present.
  # Remove non-supported special characters.
  return re.sub(r'[^a-zA-Z0-9-]', '', base_name).strip('-').lower()


class ServicePromptFallthrough(PromptFallthrough):
  """Fall through to reading the service name from an interactive prompt."""

  def __init__(self):
    super(ServicePromptFallthrough, self).__init__(
        'specify the service name from an interactive prompt')

  def _Prompt(self, parsed_args):
    source_ref = None
    if hasattr(parsed_args, 'source') or hasattr(parsed_args, 'image'):
      source_ref = flags.GetSourceRef(parsed_args.source, parsed_args.image)
    message = 'Service name'
    if source_ref:
      default_name = GenerateServiceName(source_ref)
      service_name = console_io.PromptWithDefault(
          message=message, default=default_name)
    else:
      service_name = console_io.PromptResponse(message='{}: '.format(message))
    return service_name


class DefaultFallthrough(deps.Fallthrough):
  """Use the namespace "default".

  For Knative only.

  For Cloud Run, raises an ArgumentError if project not set.
  """

  def __init__(self):
    super(DefaultFallthrough, self).__init__(
        function=None,
        hint='For Cloud Run on Kubernetes Engine, defaults to "default". '
        'Otherwise, defaults to project ID.')

  def _Call(self, parsed_args):
    if (getattr(parsed_args, 'cluster', None) or
        properties.VALUES.run.cluster.Get()) or (
            getattr(parsed_args, 'cluster_location', None) or
            properties.VALUES.run.cluster_location.Get()):
      return 'default'
    elif not (getattr(parsed_args, 'project', None) or
              properties.VALUES.core.project.Get()):
      # HACK: Compensate for how "namespace" is actually "project" in Cloud Run
      # by providing an error message explicitly early here.
      raise flags.ArgumentError(
          'The [project] resource is not properly specified. '
          'Please specify the argument [--project] on the command line or '
          'set the property [core/project].')
    return None


def NamespaceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='namespace',
      help_text='Specific to Cloud Run on Kubernetes Engine: '
      'Kubernetes namespace for the {resource}',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.run.namespace),
          DefaultFallthrough(),
          deps.ArgFallthrough('project'),
          deps.PropertyFallthrough(properties.VALUES.core.project),
      ])


def ServiceAttributeConfig(prompt=False):
  """Attribute config with fallthrough prompt only if requested."""
  if prompt:
    fallthroughs = [ServicePromptFallthrough()]
  else:
    fallthroughs = []
  return concepts.ResourceParameterAttributeConfig(
      name='service',
      help_text='Service for the {resource}.',
      fallthroughs=fallthroughs)


def ConfigurationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='configuration',
      help_text='Configuration for the {resource}.')


def RouteAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='route',
      help_text='Route for the {resource}.')


def RevisionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='revision',
      help_text='Revision for the {resource}.')


def DomainAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='domain',
      help_text='Name of the domain to be mapped to.')


class ClusterPromptFallthrough(PromptFallthrough):
  """Fall through to reading the cluster name from an interactive prompt."""

  def __init__(self):
    super(ClusterPromptFallthrough, self).__init__(
        'specify the cluster from a list of available clusters')

  def _Prompt(self, parsed_args):
    """Fallthrough to reading the cluster name from an interactive prompt.

    Only prompt for cluster name if cluster location is already defined.

    Args:
      parsed_args: Namespace, the args namespace.

    Returns:
      A cluster name string
    """
    cluster_location = (
        getattr(parsed_args, 'cluster_location', None) or
        properties.VALUES.run.cluster_location.Get())

    if cluster_location:
      clusters = global_methods.ListClusters(cluster_location)
      if not clusters:
        raise exceptions.ConfigurationError(
            'No clusters found for cluster location [{}]. '
            'Ensure your clusters have Cloud Run on GKE enabled.'
            .format(cluster_location))
      cluster_names = [c.name for c in clusters]
      idx = console_io.PromptChoice(
          cluster_names,
          message='GKE cluster name:',
          cancel_option=True)
      name = cluster_names[idx]
      log.status.Print('To make this the default cluster, run '
                       '`gcloud config set run/cluster {}`.\n'.format(name))
      return name


def ClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster',
      help_text='Specific to Cloud Run on Kubernetes Engine: '
      'Name of the Kubernetes Engine cluster to use. Alternatively, set the'
      ' property [run/cluster].',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.run.cluster),
          ClusterPromptFallthrough()
      ])


class ClusterLocationPromptFallthrough(PromptFallthrough):
  """Fall through to reading the cluster name from an interactive prompt."""

  def __init__(self):
    super(ClusterLocationPromptFallthrough, self).__init__(
        'specify the cluster location from a list of available zones')

  def _Prompt(self, parsed_args):
    """Fallthrough to reading the cluster location from an interactive prompt.

    Only prompt for cluster location name if cluster name is already defined.

    Args:
      parsed_args: Namespace, the args namespace.

    Returns:
      A cluster location string
    """
    cluster_name = (
        getattr(parsed_args, 'cluster', None) or
        properties.VALUES.run.cluster.Get())
    if cluster_name:
      clusters = [
          c for c in global_methods.ListClusters() if c.name == cluster_name
      ]
      if not clusters:
        raise exceptions.ConfigurationError(
            'No cluster locations found for cluster [{}]. '
            'Ensure your clusters have Cloud Run on GKE enabled.'
            .format(cluster_name))
      cluster_locations = [c.zone for c in clusters]
      idx = console_io.PromptChoice(
          cluster_locations,
          message='GKE cluster location for [{}]:'.format(
              cluster_name),
          cancel_option=True)
      location = cluster_locations[idx]
      log.status.Print(
          'To make this the default cluster location, run '
          '`gcloud config set run/cluster_location {}`.\n'.format(location))
      return location


def ClusterLocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Specific to Cloud Run on Kubernetes Engine: '
      'Zone in which the {resource} is located. Alternatively, set the '
      'property [run/cluster_location].',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.run.cluster_location),
          ClusterLocationPromptFallthrough()
      ])


def GetClusterResourceSpec():
  return concepts.ResourceSpec(
      'container.projects.zones.clusters',
      projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      zone=ClusterLocationAttributeConfig(),
      clusterId=ClusterAttributeConfig(),
      resource_name='cluster')


def GetServiceResourceSpec(prompt=False):
  return concepts.ResourceSpec(
      'run.namespaces.services',
      namespacesId=NamespaceAttributeConfig(),
      servicesId=ServiceAttributeConfig(prompt),
      resource_name='service')


def GetConfigurationResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.configurations',
      namespacesId=NamespaceAttributeConfig(),
      configurationsId=ConfigurationAttributeConfig(),
      resource_name='configuration')


def GetRouteResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.routes',
      namespacesId=NamespaceAttributeConfig(),
      routesId=RouteAttributeConfig(),
      resource_name='route')


def GetRevisionResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.revisions',
      namespacesId=NamespaceAttributeConfig(),
      revisionsId=RevisionAttributeConfig(),
      resource_name='revision')


def GetDomainMappingResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.domainmappings',
      namespacesId=NamespaceAttributeConfig(),
      domainmappingsId=DomainAttributeConfig(),
      resource_name='DomainMapping')


def GetNamespaceResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces',
      namespacesId=NamespaceAttributeConfig(),
      resource_name='namespace')


class RegionWildcardFallthrough(deps.Fallthrough):
  """Fall through to returning the wildcard '-' for region."""

  def __init__(self):
    super(RegionWildcardFallthrough, self).__init__(
        function=None,
        hint='wild card matching all regions')

  def _Call(self, parsed_args):
    return '-'


def RegionWithWildcardAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text='Region for the {resource}.',
      fallthroughs=[RegionWildcardFallthrough()])


def GetOnePlatformLocationResourceSpec():
  return concepts.ResourceSpec(
      'run.projects.locations',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionWithWildcardAttributeConfig(),
      resource_name='location')

CLOUD_RUN_LOCATION_PRESENTATION = presentation_specs.ResourcePresentationSpec(
    '--region',
    GetOnePlatformLocationResourceSpec(),
    'Location to list or \'-\' for all locations.',
    required=False,
    prefixes=False)

CLUSTER_PRESENTATION = presentation_specs.ResourcePresentationSpec(
    '--cluster',
    GetClusterResourceSpec(),
    'Specific to Cloud Run on Kubernetes Engine: '
    'Kubernetes Engine cluster to connect to.',
    required=False,
    prefixes=True)
