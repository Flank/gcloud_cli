# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Main function for the OS Config Troubleshooter."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import metadata_setup
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import service_enablement
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import utils


def Troubleshoot(client, instance_ref, release_track):
  """Main troubleshoot function for testing prerequisites."""
  response_message = (
      'OS Config troubleshooter tool is checking if there are '
      'issues with the VM Manager setup for this VM instance.\n\n')

  # Service enablement check.
  service_enablement_response = service_enablement.Check(
      instance_ref, release_track)
  response_message += service_enablement_response.response_message

  if not service_enablement_response.continue_flag:
    return response_message

  exception = None
  project = None
  instance = None
  try:
    project = utils.GetProject(client, instance_ref.project)
    instance = utils.GetInstance(client, instance_ref)
  except apitools_exceptions.HttpError as e:
    exception = e

  # Metadata setup check.
  metadata_setup_response = metadata_setup.Check(project, instance,
                                                 release_track, exception)
  response_message += metadata_setup_response.response_message

  if not metadata_setup_response.continue_flag:
    return response_message

  return response_message
