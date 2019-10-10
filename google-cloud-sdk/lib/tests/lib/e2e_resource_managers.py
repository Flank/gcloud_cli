# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Base classes for managing resource creaton and clean up in e2e tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import copy
import sys

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources
from tests.lib import e2e_utils


class ResourceParameters(object):
  """Parameters of resource managed by a ResourceContexManager."""

  def __init__(
      self, prefix_ref=None, suffix_generator=None, extra_creation_flags=None):
    """Store & validate parameters of a resources.

    It must be safe to use one config to create resources with multiple context
    managers, possibly modifying the ResourceParameters object in the mean time.
    To do this differently would cause some painful debugging in the future. So
    when generators are to be used this should create generator and return fruit
    of its work to caller (rather than say storing parameters of generator and
    rebuilding it every time). Also if it returns something it mustn't be a
    reference to field this object (to avoid mess when it's modified and changes
    for a context manager using the reference).

    Note that this does not store info about resource type - its held by type of
    object manging the resource. Might want to add some type info for
    consistency checking in the future.

    Args:
      prefix_ref: googlecloudsdk.core.resources.Resource, its project, and scope
                  will be used by resources created by resource manager. Its
                  name will be used as a prefix for generated resouce names.
      suffix_generator: generator of resource name suffixes.
      extra_creation_flags: list of (str, str) pairs, first item of each pair is
                            name of the flag, second item is value of the flag.
                            Flags will be passed to create command in order
                            they're  appearing. If flag name starts with '--'
                            name of the flag will be followed by space and value
                            of the flag. Otherwise just value of the flag will
                            be passed.
    """
    if suffix_generator:
      self._suffix_generator = suffix_generator
    else:
      self._suffix_generator = e2e_utils.GetResourceNameGenerator(
          sequence_start=1)
    self._prefix_ref = prefix_ref
    self._extra_creation_flags = extra_creation_flags

  def GetUrl(self):
    return self._prefix_ref.SelfLink() + next(self._suffix_generator)

  def GetExtraCreationFlags(self):
    return copy.deepcopy(self._extra_creation_flags)


class ResourceContexManagerBase(object):
  """Base class for resource-specific resource managers.

  Resource mangers create resources when going into scope, let test access
  properties of resources while in scope and clean up resource when going out of
  scope.


  (this needs to be rewritten as proper help before submiting)
  Goals:
  - Create & clean up resources in e2e tests.
  - Handle errors properly:
    - Clean up resources even when test fails
    - Fail test when resource deletion fails
    - Report all the exceptions

  Context managers seem a way to do that. More goals after picking contexts
  managers:
  - Avoid code duplication

  Discovered needs from such lib:
  - Take generator for name generation?
    - Alternative: take name core and build generator internally (to make usage
      easier in simple cases).
      - Better than allowing hard coded strings (avoids name conflicts).
  - Take extra args @ creation (e.g. size of a disk or network of a subnetwork).
  - Expose name and scope.

  Guidlines:
  - It looks like here are going to be a lot of parameters, maybe group them
    into config objects?

  Args:
      runner: callback that runs gcloud command.
      resource_parameters: ResourceParameters, defines object to be managed.
  """

  def __init__(self, runner, resource_parameters, custom_resources=None):
    res = custom_resources if custom_resources else resources.REGISTRY
    self._runner = runner
    self._ref = res.Parse(resource_parameters.GetUrl())
    self._extra_creation_flags = resource_parameters.GetExtraCreationFlags()

  def _GetExtraCreationFlagsString(self):
    """Returns a string with extra flags for resource creation."""
    if self._extra_creation_flags is None:
      return ''

    def PrepareFlagForCommandline(flag):
      name, value = flag
      if name.startswith('--'):
        return '{} {}'.format(name, value)
      return value

    flags = [PrepareFlagForCommandline(f) for f in self._extra_creation_flags]
    return ' '.join(flags)

  def __enter__(self):
    self._runner(self._GetCreateCommand())
    return self

  def __exit__(self, prev_exc_type, prev_exc_val, prev_exc_trace):
    try:
      self._runner(self._GetDeleteCommand())
    except:  # pylint: disable=bare-except
      exceptions.RaiseWithContext(
          prev_exc_type, prev_exc_val, prev_exc_trace, *sys.exc_info())
    # Always return False so any previous exception will be re-raised.
    return False

  @abc.abstractmethod
  def _GetCreateCommand(self):
    pass

  @abc.abstractmethod
  def _GetDeleteCommand(self):
    pass

  @property
  def ref(self):
    return self._ref

  def GetExtraCreationFlag(self, flag):
    return [
        f[1] for f in self._extra_creation_flags if f[0] == flag]


class CreateDeleteResourceContexManagerBase(ResourceContexManagerBase):
  """Base class for managing resources using create and delete commands."""

  def _GetCreateCommand(self):
    return '{} create {} {}'.format(
        self._command_group, self.ref.SelfLink(),
        self._GetExtraCreationFlagsString())

  def _GetDeleteCommand(self):
    return '{} delete {}'.format(self._command_group, self.ref.SelfLink())

  @abc.abstractproperty
  def _command_group(self):
    raise NotImplementedError()

