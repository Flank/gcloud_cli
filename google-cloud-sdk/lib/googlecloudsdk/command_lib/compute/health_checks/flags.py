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

"""Flags and helpers for the compute health-checks commands."""

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      type:label=PROTOCOL
    )"""


def HealthCheckArgument(
    protocol_string, name=None, required=True, plural=False):
  return compute_flags.ResourceArgument(
      name=name,
      resource_name='{} health check'.format(protocol_string),
      completer=compute_completers.HealthChecksCompleter,
      plural=plural,
      required=required,
      global_collection='compute.healthChecks')
