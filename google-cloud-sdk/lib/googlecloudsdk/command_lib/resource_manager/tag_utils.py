# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Utilities for defining Tag resource manager arguments on a parser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py.exceptions import HttpForbiddenError
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.resource_manager import tags
from googlecloudsdk.api_lib.resource_manager.exceptions import ResourceManagerError
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.core import exceptions as core_exceptions


class InvalidInputError(ResourceManagerError):
  """Exception for invalid input."""


GetResourceFns = {
    'tagKeys': tags.TagMessages().CloudresourcemanagerTagKeysGetRequest,
    'tagValues': tags.TagMessages().CloudresourcemanagerTagValuesGetRequest
}

ListResourceFns = {
    'tagKeys': tags.TagMessages().CloudresourcemanagerTagKeysListRequest,
    'tagValues': tags.TagMessages().CloudresourcemanagerTagValuesListRequest,
    'tagBindings': tags.TagMessages().CloudresourcemanagerTagBindingsListRequest
}

ServiceFns = {
    'tagKeys': tags.TagKeysService,
    'tagValues': tags.TagValuesService,
    'tagBindings': tags.TagBindingsService
}

MAX_TAG_KEYS = 300


def GetTagKeyFromNamespacedName(namespaced_name):
  """Gets the tag key from the namespaced name.

  Args:
    namespaced_name: Could be the resource name or namespaced name

  Returns:
    TagKey resource

  Raises:
    InvalidInputError: bad input
  """
  service = ServiceFns['tagKeys']()

  parts = namespaced_name.split('/')
  if len(parts) != 2:
    raise InvalidInputError(
        'TagKey namespaced name [{}] invalid'.format(namespaced_name))

  name = '/'.join(['organizations', parts[0]])
  req = ListResourceFns['tagKeys'](parent=name, pageSize=MAX_TAG_KEYS)

  try:
    response = service.List(req)
  except HttpForbiddenError:
    print('TagKey [{}] does not exist or user does not have permissions to '
          'resolve namespaced name. Retry using tagKey\'s resource name, such '
          'as tagKeys/123.'.format(namespaced_name))
    raise

  for key in response.tagKeys:
    if key.namespacedName == namespaced_name:
      return key

  raise InvalidInputError('TagKey [{}] not found'.format(namespaced_name))


def GetTagValueFromNamespacedName(namespaced_name):
  """Gets the tag value from the namespaced name.

  Args:
    namespaced_name: Could be the resource name or namespaced name

  Returns:
    TagValue resource

  Raises:
    InvalidInputError: bad input
  """

  service = ServiceFns['tagValues']()

  parts = namespaced_name.split('/')
  if len(parts) != 3:
    raise InvalidInputError(
        'TagValue namespaced name [{}] invalid'.format(namespaced_name))

  name = GetTagKeyFromNamespacedName('/'.join(parts[:2])).name

  req = ListResourceFns['tagValues'](parent=name)
  response = service.List(req)

  for value in response.tagValues:
    if value.namespacedName == namespaced_name:
      return value

  raise InvalidInputError('TagValue [{}] not found'.format(namespaced_name))


def GetResourceFromNamespacedName(namespaced_name, resource_type):
  """Gets the resource from the namespaced name.

  Args:
    namespaced_name: Could be the resource name or namespaced name
    resource_type: the type of the resource ie: 'tagKeys', 'tagValues'. Used to
      determine which GET function to call

  Returns:
    resource
  """
  service = ServiceFns[resource_type]()
  req = GetResourceFns[resource_type](name=namespaced_name)
  response = service.Get(req)

  return response


def ProjectNameToBinding(project_name, tag_value, location=None):
  """Returns the binding name given a project name and tag value.

  Requires binding list permission.

  Args:
    project_name: project name provided, fully qualified resource name
    tag_value: tag value to match the binding name to
    location: region or zone

  Returns:
    binding_name

  Raises:
    InvalidInputError: project not found
  """
  service = ServiceFns['tagBindings']()
  with endpoints.CrmEndpointOverrides(location):
    req = ListResourceFns['tagBindings'](parent=project_name)

    response = service.List(req)

    for bn in response.tagBindings:
      if bn.tagValue == tag_value:
        return bn.name

    raise InvalidInputError(
        'Binding not found for parent [{}], tagValue [{}]'.format(
            project_name, tag_value))


def GetCanonicalResourceName(resource_name, location, release_track):
  """Returns the correct canonical name for the given resource.

  Args:
    resource_name: name of the resource
    location: location in which the resource lives
    release_track: release stage of current endpoint

  Returns:
    resource_name: either the original resource name, or correct canonical name
  """

  # [a-z]([-a-z0-9]*[a-z0-9] is the instance name regex, as per
  # https://cloud.google.com/compute/docs/reference/rest/v1/instances

  gce_compute_instance_name_pattern = r'compute.googleapis.com/projects/([^/]+)/.*instances/([^/]+)'
  gce_search = re.search(gce_compute_instance_name_pattern, resource_name)

  if gce_search:
    if not location:
      raise exceptions.InvalidArgumentException(
          '--location',
          'Please specify an appropriate cloud location with the --location flag.'
      )
    project_identifier, instance_identifier = gce_search.group(
        1), gce_search.group(2)
    # call compute instance's describe api to get canonical resource name
    # use that instead of the instance name that's in the parent

    if not project_identifier.isdigit():
      # if we have a project id, translate it to project number by calling
      # project's describe endpoint.
      project_name = project_identifier
      project_identifier = _GetProjectCanonicalName(project_name)
      resource_name = resource_name.replace('projects/%s' % project_name,
                                            'projects/%s' % project_identifier)
    if re.search('([a-z]([-a-z0-9]*[a-z0-9])?)', instance_identifier):
      resource_name = resource_name.replace(
          'instances/%s' % instance_identifier,
          'instances/%s' % _GetGceInstanceCanonicalName(
              project_identifier, instance_identifier, location, release_track))
  return resource_name


def _GetProjectCanonicalName(project_identifier):
  """Returns the correct canonical name for the given project.

  Args:
    project_identifier: project id

  Returns:
    projectNumber: returns the projectNumber
  """
  project_ref = command_lib_util.ParseProject(project_identifier)
  response = projects_api.Get(project_ref)
  return str(response.projectNumber)


def _GetGceInstanceCanonicalName(project_identifier, instance_identifier,
                                 location, release_track):
  """Returns the correct canonical name for the given gce compute instance.

  Args:
    project_identifier: project number of the compute instance
    instance_identifier: name of the instance
    location: location in which the resource lives
    release_track: release stage of current endpoint

  Returns:
    instance_id: returns the canonical instance id
  """
  compute_holder = base_classes.ComputeApiHolder(release_track)
  client = compute_holder.client
  request = (client.apitools_client.instances, 'Get',
             client.messages.ComputeInstancesGetRequest(
                 instance=instance_identifier,
                 project=project_identifier,
                 zone=location))
  errors_to_collect = []
  instances = client.MakeRequests([request],
                                  errors_to_collect=errors_to_collect)
  if errors_to_collect:
    raise core_exceptions.MultiError(errors_to_collect)
  return str(instances[0].id)
