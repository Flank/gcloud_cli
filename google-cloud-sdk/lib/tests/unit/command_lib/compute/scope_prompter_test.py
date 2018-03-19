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

"""Unit tests for the compute scope prompter module."""

import collections

from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute import scope_prompter
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import gce as c_gce
from tests.lib import sdk_test_base
from tests.lib import test_case


class ScopePrompterTests(sdk_test_base.WithOutputCapture, test_case.WithInput):

  def testSingleScope(self):
    resource_name = 'forwarding rule'
    underspecified_names = ['salmon', 'herring']
    scopes = [compute_scope.ScopeEnum.REGION]
    default_scope = None

    resource = collections.namedtuple('Resource', ['name'])
    def ScopeLister(scopes, unused_underspecified_names):
      self.assertEquals([compute_scope.ScopeEnum.REGION], scopes)
      return {
          compute_scope.ScopeEnum.REGION:
              [resource(name='north-sea'), resource(name='baltic')]
      }

    self.WriteInput('1')
    result = scope_prompter.PromptForScope(
        resource_name, underspecified_names,
        scopes, default_scope, scope_lister=ScopeLister)

    self.AssertErrEquals("""\
        For the following forwarding rules:
          - [herring]
          - [salmon]
        choose a region:
          [1] baltic
          [2] north-sea
        Please enter your numeric choice:
        """, normalize_space=True)
    self.assertEquals((compute_scope.ScopeEnum.REGION, 'baltic'), result)

  def testMultiScope(self):
    resource_name = 'forwarding rule'
    underspecified_names = ['salmon', 'herring']
    scopes = [compute_scope.ScopeEnum.GLOBAL, compute_scope.ScopeEnum.REGION]
    default_scope = None

    resource = collections.namedtuple('Resource', ['name'])

    def ScopeLister(scopes, unused_underspecified_names):
      self.assertEquals(
          {compute_scope.ScopeEnum.REGION, compute_scope.ScopeEnum.GLOBAL},
          set(scopes))
      return {
          compute_scope.ScopeEnum.REGION:
              [resource(name='atlantic'), resource(name='indian')],
          compute_scope.ScopeEnum.GLOBAL:
              [resource(name='')]
      }

    self.WriteInput('1')
    result = scope_prompter.PromptForScope(
        resource_name, underspecified_names,
        scopes, default_scope, scope_lister=ScopeLister)

    self.AssertErrEquals("""\
        For the following forwarding rules:
          - [herring]
          - [salmon]
        choose a region or global:
          [1] global
          [2] region: atlantic
          [3] region: indian
        Please enter your numeric choice:
        """, normalize_space=True)

    self.assertEquals((compute_scope.ScopeEnum.GLOBAL, ''), result)

  def testSingleScope_WithRegionGce(self):
    resource_name = 'forwarding rule'
    underspecified_names = ['salmon', 'herring']
    scopes = [compute_scope.ScopeEnum.REGION]
    default_scope = None

    properties.VALUES.core.check_gce_metadata.Set(True)
    if c_gce.Metadata().connected:
      region = c_gce.Metadata().Region()
    else:
      region = 'north-sea'
      self.StartObjectPatch(c_gce._GCEMetadata, 'Region', return_value=region)

    self.WriteInput('Y')
    result = scope_prompter.PromptForScope(
        resource_name, underspecified_names,
        scopes, default_scope, scope_lister=None)
    self.AssertErrEquals("""\
         Did you mean region [{0}] for forwarding rule: \
         [salmon, herring] (Y/n)?
         """.format(region), normalize_space=True)
    self.assertEquals((compute_scope.ScopeEnum.REGION, region), result)

  def testSingleScope_WithZoneGce(self):
    resource_name = 'forwarding rule'
    underspecified_names = ['salmon', 'herring']
    scopes = [compute_scope.ScopeEnum.ZONE]
    default_scope = None

    properties.VALUES.core.check_gce_metadata.Set(True)
    if c_gce.Metadata().connected:
      zone = c_gce.Metadata().Zone()
    else:
      zone = 'skagerrak'
      self.StartObjectPatch(c_gce._GCEMetadata, 'Zone', return_value=zone)

    self.WriteInput('Y')
    result = scope_prompter.PromptForScope(
        resource_name, underspecified_names,
        scopes, default_scope, scope_lister=None)
    self.AssertErrEquals("""\
         Did you mean zone [{0}] for forwarding rule: \
         [salmon, herring] (Y/n)?
         """.format(zone), normalize_space=True)
    self.assertEquals((compute_scope.ScopeEnum.ZONE, zone), result)

  def testSingleScope_WithNoGceResolution(self):
    resource_name = 'forwarding rule'
    underspecified_names = ['salmon', 'herring']
    scopes = [compute_scope.ScopeEnum.ZONE]
    default_scope = None

    zone = 'skagerrak'
    resource = collections.namedtuple('Resource', ['name'])
    def ScopeLister(unused_scopes, unused_underspecified_names):
      return {compute_scope.ScopeEnum.ZONE: [resource(name=zone)]}

    result = scope_prompter.PromptForScope(
        resource_name, underspecified_names,
        scopes, default_scope, scope_lister=ScopeLister)
    self.AssertErrEquals("""\
         No zone specified. Using zone [{0}] \
         for forwarding rules: [salmon, herring].
         """.format(zone), normalize_space=True)
    self.assertEquals((compute_scope.ScopeEnum.ZONE, zone), result)


if __name__ == '__main__':
  test_case.main()
