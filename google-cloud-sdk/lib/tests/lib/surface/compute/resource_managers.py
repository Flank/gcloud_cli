# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Utils for creating and cleaning up resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import traceback

from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import encoding
from tests.lib import e2e_resource_managers


class Instance(e2e_resource_managers.CreateDeleteResourceContexManagerBase):
  """Manages creation and clean up of instances."""

  @property
  def _command_group(self):
    return 'compute instances'


class UnmanagedInstanceGroup(
    e2e_resource_managers.CreateDeleteResourceContexManagerBase):
  """Manages creation and clean up of instances groups."""

  @property
  def _command_group(self):
    return 'compute instance-groups unmanaged'


class TargetInstance(
    e2e_resource_managers.CreateDeleteResourceContexManagerBase):
  """Manages creation and clean up of target instances."""

  @property
  def _command_group(self):
    return 'compute target-instances'


class HealthCheck(e2e_resource_managers.CreateDeleteResourceContexManagerBase):
  """Manages creation and clean up of health checks."""

  @property
  def _command_group(self):
    return 'compute health-checks'

  def _GetCreateCommand(self):
    return '{} create tcp {} {}'.format(
        self._command_group, self.ref.SelfLink(),
        self._GetExtraCreationFlagsString())


class BackendService(
    e2e_resource_managers.CreateDeleteResourceContexManagerBase):
  """Manages creation and clean up of backend services."""

  @property
  def _command_group(self):
    return 'compute backend-services'


class ForwardingRule(
    e2e_resource_managers.CreateDeleteResourceContexManagerBase):
  """Manages creation and clean up of forwarding rules."""

  @property
  def _command_group(self):
    return 'compute forwarding-rules'


class SecurityPolicy(
    e2e_resource_managers.CreateDeleteResourceContexManagerBase):
  """Manages creation and clean up of security policies."""

  @property
  def _command_group(self):
    return 'compute security-policies'


class SoleTenancyHost(object):
  """Manages creation and clean up of sole tenancy hosts."""

  def __init__(self, zone, host_type, name_generator, run):
    self._host_type = host_type
    self._name_generator = name_generator
    self._run = run
    self._zone = zone

  @property
  def name(self):
    return self._name

  @property
  def zone(self):
    return self._zone

  def __enter__(self):
    self._name = next(self._name_generator)
    self._run("""\
        compute sole-tenancy hosts create {}
        --host-type {}
        --zone {}
        """.format(
            self._name, self._host_type, self._zone))
    return self

  def __exit__(self, prev_exc_type, prev_exc_val, prev_exc_trace):
    try:
      self._run('compute sole-tenancy hosts delete {} --zone {} --quiet'.format(
          self._name, self._zone))
    except:  # pylint: disable=bare-except
      if not prev_exc_type:
        raise
      message = ('Got exception {0}'
                 'while another exception was active {1} [{2}]'.format(
                     encoding.Decode(traceback.format_exc()), prev_exc_type,
                     encoding.Decode(prev_exc_val)))
      exceptions.reraise(prev_exc_type(message), tb=prev_exc_trace)
    # always return False so any exceptions will be re-raised
    return False
