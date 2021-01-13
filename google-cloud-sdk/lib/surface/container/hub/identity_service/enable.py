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
"""The command to enable Identity Service Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Enable(base.EnableCommand):
  """Enable Identity Service Feature.

  This command enables the Identity Service Feature in Hub.

  ## Examples

  Enable Identity Service Feature:

    $ {command}
  """

  FEATURE_NAME = 'identityservice'
  FEATURE_DISPLAY_NAME = 'Identity Service'

  @classmethod
  def Args(cls, parser):
    pass

  def Run(self, args):
    project = args.project or properties.VALUES.core.project.Get(required=True)
    EnableService(project, 'anthosidentityservice.googleapis.com')
    return self.RunCommand(args, identityserviceFeatureSpec=(
        base.CreateIdentityServiceFeatureSpec()))


def EnableService(project, service_name):
  """Enables a given service.

  Args:
    project: GCP project in which to enable service.
    service_name: service to enable (e.g. ****.googleapis.com).

  Raises:
    exceptions.GetServicePermissionDeniedException: when getting service fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The service configuration.
  """
  if enable_api.IsServiceEnabled(project, service_name):
    log.status.Print(
        'Service {0} is already enabled for Project {1}'
        .format(service_name, project))
    return
  op = serviceusage.EnableApiCall(project, service_name)
  log.status.Print('Enabling service {0}'.format(service_name))
  if op.done:
    return
  op = services_util.WaitOperation(op.name, serviceusage.GetOperation)
  services_util.PrintOperation(op)
