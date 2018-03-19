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
"""Flags for the compute sole-tenancy host-types commands."""

from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.sole_tenancy.hosts import flags as hosts_flags


def MakeHostTypeArg():
  return compute_flags.ResourceArgument(
      resource_name='host type',
      completer=hosts_flags.HostTypesCompleter,
      zonal_collection='compute.hostTypes',
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)
