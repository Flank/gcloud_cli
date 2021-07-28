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
"""Flags and helpers for the compute reservations commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


def GetDescriptionFlag():
  return base.Argument(
      '--description',
      help='An optional description of the reservation to create.')


def GetRequireSpecificAllocation():
  help_text = """\
  Indicates whether the reservation can be consumed by VMs with "any reservation"
  defined. If enabled, then only VMs that target this reservation by name using
  `--reservation-affinity=specific` can consume from this reservation.
  """
  return base.Argument(
      '--require-specific-reservation', action='store_true', help=help_text)


def GetVmCountFlag(required=True):
  help_text = """\
  The number of VM instances that are allocated to this reservation.
  The value of this field must be an int in the range [1, 1000].
  """
  return base.Argument(
      '--vm-count', required=required, type=int, help=help_text)


def GetMinCpuPlatform():
  """Gets the --min-cpu-platform flag."""
  return base.Argument(
      '--min-cpu-platform',
      help='Optional minimum CPU platform of the reservation to create.')


def GetLocationHint():
  """Gets the --location-hint flag."""
  return base.Argument(
      '--location-hint',
      hidden=True,
      help="""\
      Used by internal tools to control sub-zone location of the instance.
      """)


def GetMachineType(required=True):
  """Gets the --machine-type flag."""
  help_text = """\
  The type of machine (name only) which has a fixed number of vCPUs and a fixed
  amount of memory. This also includes specifying custom machine type following
  `custom-number_of_CPUs-amount_of_memory` pattern, e.g. `custom-32-29440`.
  """
  return base.Argument('--machine-type', required=required, help=help_text)


def GetLocalSsdFlag(custom_name=None):
  """Gets the --local-ssd flag."""
  help_text = """\
  Manage the size and the interface of local SSD to use. See
  https://cloud.google.com/compute/docs/disks/local-ssd for more information.
  *interface*::: The kind of disk interface exposed to the VM for this SSD. Valid
  values are `scsi` and `nvme`. SCSI is the default and is supported by more
  guest operating systems. NVME may provide higher performance.
  *size*::: The size of the local SSD in base-2 GB.
  """
  return base.Argument(
      custom_name if custom_name else '--local-ssd',
      type=arg_parsers.ArgDict(spec={
          'interface': (lambda x: x.upper()),
          'size': int,
      }),
      action='append',
      help=help_text)


def GetAcceleratorFlag(custom_name=None):
  """Gets the --accelerator flag."""
  help_text = """\
  Manage the configuration of the type and number of accelerator cards attached.
  *count*::: The number of accelerators to attach to each instance in the reservation.
  *type*::: The specific type (e.g. `nvidia-tesla-k80` for nVidia Tesla K80) of
  accelerator to attach to instances in the reservation. Use `gcloud compute accelerator-types list`
  to learn about all available accelerator types.
  """
  return base.Argument(
      custom_name if custom_name else '--accelerator',
      type=arg_parsers.ArgDict(
          spec={
              'count': int,
              'type': str,
          }, required_keys=['count', 'type']),
      action='append',
      help=help_text)


def GetSharedSettingFlag(custom_name=None):
  """Gets the --share-setting flag."""
  help_text = """\
  Specify if this reservation is shared; and if so, the type of sharing:
  share with all projects in the organization or share with specific projects or
  folders.
  """
  return base.Argument(
      custom_name if custom_name else '--share-setting',
      choices=['organization', 'projects', 'folders'],
      help=help_text)


def GetShareWithFlag(custom_name=None):
  """Gets the --share-with flag."""
  help_text = """\
  A list of specific projects or folders this reservation should be shared with.
  List must contain all project ID's or all folder ID's--depending on what the
  share-setting is set to.
  """
  return base.Argument(
      custom_name if custom_name else '--share-with',
      type=arg_parsers.ArgList(min_length=1),
      metavar='PROJECT',
      help=help_text)


def AddCreateFlags(parser,
                   support_location_hint=False,
                   support_fleet=False,
                   support_share_setting=False):
  """Adds all flags needed for the create command."""
  GetDescriptionFlag().AddToParser(parser)

  group = base.ArgumentGroup(
      'Manage the specific SKU reservation properties.', required=True)

  group.AddArgument(GetRequireSpecificAllocation())
  group.AddArgument(GetVmCountFlag())
  group.AddArgument(GetMinCpuPlatform())
  group.AddArgument(GetMachineType())
  group.AddArgument(GetLocalSsdFlag())
  group.AddArgument(GetAcceleratorFlag())
  if support_location_hint:
    group.AddArgument(GetLocationHint())
  if support_fleet:
    group.AddArgument(instance_flags.AddMaintenanceFreezeDuration())
    group.AddArgument(instance_flags.AddMaintenanceInterval())
  group.AddToParser(parser)

  if support_share_setting:
    share_group = base.ArgumentGroup(
        'Manage the properties of a shared reservation.', required=False)
    share_group.AddArgument(GetSharedSettingFlag())
    share_group.AddArgument(GetShareWithFlag())
    share_group.AddToParser(parser)
