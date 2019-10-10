# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Unit tests for Cloud IOT resource args."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from tests.lib import completer_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base
from tests.lib.command_lib.util.concepts import resource_completer_test_base
from tests.lib.surface.cloudiot import base


class ResourceArgCompletersTest(
    completer_test_base.FlagCompleterBase,
    resource_completer_test_base.ResourceCompleterBase,
    base.CloudIotRegistryBase,
    base.CloudIotDeviceBase,
    concepts_test_base.ConceptsTestBase,
    parameterized.TestCase):

  @parameterized.named_parameters(
      ('Alpha', calliope_base.ReleaseTrack.ALPHA),
      ('Beta', calliope_base.ReleaseTrack.BETA))
  def testCompletersExist(self, track):
    self.track = track
    # Device anchor.
    self.AssertCommandArgResourceCompleter(
        command='{} iot devices describe'.format(track.prefix),
        arg='device')
    # Non-anchor.
    self.AssertCommandArgResourceCompleter(
        command='{} iot devices describe'.format(track.prefix),
        arg='--registry')
    # Registry
    self.AssertCommandArgResourceCompleter(
        command='{} iot registries describe'.format(track.prefix),
        arg='registry')

  def testRunDeviceCompleter(self):
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r0'),
                            field_mask='name', registry='r0')

    resource_spec = resource_args.GetDeviceResourceSpec()
    attribute_name = 'device'
    args = {'--region': 'us-central1', '--registry': 'r0'}
    expected_completions = ['d0', 'd1']
    self.RunResourceCompleter(
        resource_spec,
        attribute_name,
        args=args,
        expected_completions=expected_completions)

  @parameterized.named_parameters(
      ('Flags', 'flags', ['d0 --registry=r0', 'd1 --registry=r0',
                          'd0 --registry=r1']),
      ('GRI', 'gri', ['d0:r0', 'd1:r0', 'd0:r1']))
  def testRunDeviceCompleterProjectOnly(self, style, expected_completions):
    properties.VALUES.core.enable_gri.Set(True)
    properties.VALUES.core.resource_completion_style.Set(style)
    self._ExpectListRegistries(self._MakeRegistries(n=2))
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r0'),
                            field_mask='name', registry='r0')
    self._ExpectListDevices(self._MakeDevices(n=1, registry='r1'),
                            field_mask='name', registry='r1')

    resource_spec = resource_args.GetDeviceResourceSpec()
    attribute_name = 'device'
    args = {'--region': 'us-central1'}
    self.RunResourceCompleter(
        resource_spec,
        attribute_name,
        args=args,
        expected_completions=expected_completions)

  @parameterized.named_parameters(
      ('Flags', 'flags', ['d0 --project=p0 --registry=r0',
                          'd1 --project=p0 --registry=r0',
                          'd0 --project=p0 --registry=r1',
                          'd1 --project=p0 --registry=r1',
                          'd0 --project=p1 --registry=r0']),
      ('GRI', 'gri', ['d0:r0:us-central1:p0',
                      'd1:r0:us-central1:p0',
                      'd0:r1:us-central1:p0',
                      'd1:r1:us-central1:p0',
                      'd0:r0:us-central1:p1']))
  def testRunDeviceCompleterAllFlags(self, style, expected_completions):
    properties.VALUES.core.enable_gri.Set(True)
    properties.VALUES.core.resource_completion_style.Set(style)
    self.UnsetProject()
    self._ExpectListRegistries(self._MakeRegistries(n=2, project='p0'),
                               project='p0')
    self._ExpectListRegistries(self._MakeRegistries(n=1, project='p1'),
                               project='p1')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r0'),
                            field_mask='name', project='p0', registry='r0')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r1'),
                            field_mask='name', project='p0', registry='r1')
    self._ExpectListDevices(self._MakeDevices(n=1, registry='r0'),
                            field_mask='name', project='p1', registry='r0')

    resource_spec = resource_args.GetDeviceResourceSpec()
    attribute_name = 'device'
    args = {'--region': 'us-central1'}
    self.RunResourceCompleter(
        resource_spec,
        attribute_name,
        args=args,
        projects=['p0', 'p1'],
        expected_completions=expected_completions)

  @parameterized.named_parameters(
      ('Flags', 'flags', ['r0 --project=p0',
                          'r1 --project=p0',
                          'r0 --project=p1']),
      ('GRI', 'gri', ['r0:us-central1:p0',
                      'r1:us-central1:p0',
                      'r0:us-central1:p1']))
  def testRunDeviceRegistryCompleter(self, style, expected_completions):
    properties.VALUES.core.enable_gri.Set(True)
    properties.VALUES.core.resource_completion_style.Set(style)
    self.UnsetProject()
    self._ExpectListRegistries(self._MakeRegistries(n=2, project='p0'),
                               project='p0')
    self._ExpectListRegistries(self._MakeRegistries(n=1, project='p1'),
                               project='p1')

    resource_spec = resource_args.GetDeviceResourceSpec()
    attribute_name = 'registry'
    args = {'--region': 'us-central1'}
    self.RunResourceCompleter(
        resource_spec,
        attribute_name,
        args=args,
        projects=['p0', 'p1'],
        expected_completions=expected_completions)

  @parameterized.named_parameters(
      ('Flags', 'flags', ['r0 --project=p0',
                          'r1 --project=p0',
                          'r0 --project=p1']),
      ('GRI', 'gri', ['r0:us-central1:p0',
                      'r1:us-central1:p0',
                      'r0:us-central1:p1']))
  def testRunRegistryCompleter(self, style, expected_completions):
    properties.VALUES.core.enable_gri.Set(True)
    properties.VALUES.core.resource_completion_style.Set(style)
    self.UnsetProject()
    self._ExpectListRegistries(self._MakeRegistries(n=2, project='p0'),
                               project='p0')
    self._ExpectListRegistries(self._MakeRegistries(n=1, project='p1'),
                               project='p1')

    resource_spec = resource_args.GetRegistryResourceSpec()
    attribute_name = 'registry'
    args = {'--region': 'us-central1'}
    self.RunResourceCompleter(
        resource_spec,
        attribute_name,
        args=args,
        projects=['p0', 'p1'],
        expected_completions=expected_completions)


class ResourceArgConceptTest(
    base.CloudIotRegistryBase,
    base.CloudIotDeviceBase,
    concepts_test_base.ConceptsTestBase):

  def testCreateDevicePresentationSpecDefaults(self):
    expected_spec = presentation_specs.ResourcePresentationSpec(
        '--device',
        resource_args.GetDeviceResourceSpec(),
        'The device to test.',
        required=False,
        prefixes=True
    )
    actual_spec = resource_args.CreateDevicePresentationSpec('to test')
    self.assertEqual(expected_spec, actual_spec)

  def testCreateDevicePresentationSpecAllParams(self):
    expected_spec = presentation_specs.ResourcePresentationSpec(
        'another-device',
        resource_args.GetDeviceResourceSpec('another-device'),
        'The other device to test.',
        required=True,
        prefixes=True
    )
    actual_spec = resource_args.CreateDevicePresentationSpec(
        'to test',
        help_text='The other device {}.',
        name='another-device',
        required=True,
        prefixes=True,
        positional=True)
    self.assertEqual(expected_spec, actual_spec)

  def testAddBindResourceArgsToParser(self):
    resource_args.AddBindResourceArgsToParser(self.parser)
    # Parse Args
    args = self.parser.parser.parse_args(
        ['--gateway', 'my-gateway',
         '--gateway-region', 'us-central-1',
         '--gateway-registry', 'my-registry',
         '--device', 'my-device',
         '--device-region', 'us-central-2',
         '--device-registry', 'my-other-registry'])

    device_ref = args.CONCEPTS.device.Parse()
    gateway_ref = args.CONCEPTS.gateway.Parse()

    self.assertEqual(('https://cloudiot.googleapis.com/v1/projects/'
                      'fake-project/locations/us-central-2/registries'
                      '/my-other-registry/devices/my-device'),
                     device_ref.SelfLink())
    self.assertEqual(('https://cloudiot.googleapis.com/v1/projects/'
                      'fake-project/locations/us-central-1/registries'
                      '/my-registry/devices/my-gateway'),
                     gateway_ref.SelfLink())


if __name__ == '__main__':
  test_case.main()
