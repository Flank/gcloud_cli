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

"""Test completer instances for testing the completer scaffolding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util import completers


class ListCommandCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ListCommandCompleter, self).__init__(
        collection='compute.instances',
        list_command='compute instances list --uri',
        timeout=60,
        **kwargs)


class ListCommandWithNoUriCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ListCommandWithNoUriCompleter, self).__init__(
        collection='compute.instances',
        list_command='compute instances list --complete-me',
        timeout=60,
        **kwargs)


class ListCommandWithFormatCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ListCommandWithFormatCompleter, self).__init__(
        collection='compute.instances',
        list_command='compute instances list --format=value(id)',
        timeout=60,
        **kwargs)


class ListCommandWithQuietCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ListCommandWithQuietCompleter, self).__init__(
        collection='compute.instances',
        list_command='compute instances list --quiet',
        timeout=60,
        **kwargs)


class ListCommandWithFlagsCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ListCommandWithFlagsCompleter, self).__init__(
        collection='compute.instances',
        list_command='compute instances list --uri',
        flags=['--flag'],
        timeout=60,
        **kwargs)


class ListCommandCompleterGoodApiVersion(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ListCommandCompleterGoodApiVersion, self).__init__(
        collection='compute.instances',
        api_version='v1',
        list_command='compute instances list --uri',
        timeout=60,
        **kwargs)


class ListCommandCompleterBadApiVersion(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ListCommandCompleterBadApiVersion, self).__init__(
        collection='compute.instances',
        api_version='v0',
        list_command='compute instances list --uri',
        timeout=60,
        **kwargs)


class ResourceParamCompleter(completers.ResourceParamCompleter):

  def __init__(self, **kwargs):
    super(ResourceParamCompleter, self).__init__(
        collection='compute.zones',
        list_command='compute zones list --uri',
        param='zone',
        timeout=60,
        **kwargs)


class ResourceSearchCompleter(completers.ResourceSearchCompleter):

  def __init__(self, **kwargs):
    super(ResourceSearchCompleter, self).__init__(
        collection='compute.instances',
        timeout=60,
        **kwargs)


class MultiResourceCompleterPart1(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(MultiResourceCompleterPart1, self).__init__(
        collection='compute.regions',
        list_command=(
            'compute regions list --uri'),
        timeout=60,
        **kwargs)


class MultiResourceCompleterPart2(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(MultiResourceCompleterPart2, self).__init__(
        collection='compute.zones',
        list_command=(
            'compute zones list --uri'),
        timeout=60,
        **kwargs)


class MultiResourceCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(MultiResourceCompleter, self).__init__(
        completers=[MultiResourceCompleterPart1,
                    MultiResourceCompleterPart2],
        **kwargs)


class NoCacheCompleter(completers.NoCacheCompleter):

  def Complete(self, prefix, parameter_info):
    return ['role/major', 'role/minor']
