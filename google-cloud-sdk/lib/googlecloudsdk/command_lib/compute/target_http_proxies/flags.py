# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Flags and helpers for the compute target-http-proxies commands."""

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      urlMap.basename()
    )"""


class TargetHttpProxiesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(TargetHttpProxiesCompleter, self).__init__(
        collection='compute.targetHttpProxies',
        list_command='compute target-http-proxies list --uri',
        **kwargs)


def TargetHttpProxyArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='target HTTP proxy',
      completer=TargetHttpProxiesCompleter,
      plural=plural,
      custom_plural='target HTTP proxies',
      required=required,
      global_collection='compute.targetHttpProxies')
