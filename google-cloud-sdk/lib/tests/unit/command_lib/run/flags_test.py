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
"""Unit tests for the Run flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import os

from googlecloudsdk.api_lib.container import kubeconfig
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.run import traffic
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import exceptions as services_exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import name_generator
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.run import base

import mock


class _TestArgumentParser(argparse.ArgumentParser):
  """Overrides error to increase testability.

  Replaces exiting with raising ArgumentError.
  """

  def error(self, message='', context=None, reproduce=False):
    del context, reproduce
    raise flags.ArgumentError(message)


class ServerlessFlagsTest(base.ServerlessSurfaceBase, parameterized.TestCase):

  def testGenerateDefaultServiceName(self):
    self.StartObjectPatch(os.path, 'isdir')
    self.assertEqual(
        'foo', resource_args.GenerateServiceName('gcr.io/images/foo:latest'))

  def testServiceBeginDash(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef('-s3rvice')
    with self.assertRaises(flags.ArgumentError):
      flags.GetService(args)

  def testServiceEndDash(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef('s3rvice-')
    with self.assertRaises(flags.ArgumentError):
      flags.GetService(args)

  def testServiceContainsDash(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef('s3rv-ice')
    self.assertEqual(self._ServiceRef('s3rv-ice'), flags.GetService(args))

  def testServiceOneCharacter(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef('a')
    self.assertEqual(self._ServiceRef('a'), flags.GetService(args))

  def testServiceDigits(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef('123abc123')
    self.assertEqual(self._ServiceRef('123abc123'), flags.GetService(args))

  def testServiceTooLong(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef(
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
    with self.assertRaises(flags.ArgumentError):
      flags.GetService(args)


class GetConfigurationChangesTest(base.ServerlessSurfaceBase,
                                  parameterized.TestCase):

  def SetUp(self):
    self.args = parser_extensions.Namespace(
        update_env_vars=None,
        set_env_vars=None,
        remove_env_vars=None,
        clear_env_vars=None,
        concurrency=None,
        add_cloudsql_instances=None,
        remove_cloudsql_instances=None,
        clear_cloudsql_instances=None,
        set_cloudsql_instances=None,
        cpu=None,
        clear_labels=None,
        update_labels=None,
        remove_labels=None,
        update_secrets=None,
        set_secrets=None,
        remove_secrets=None,
        clear_secrets=None,
        update_config_maps=None,
        set_config_maps=None,
        remove_config_maps=None,
        clear_config_maps=None,
        update_tags=None,
        set_tags=None,
        remove_tags=None,
        clear_tags=None,
        to_latest=None,
        to_revisions=None,
        ingress=None)
    self.service = service.Service.New(self.mock_serverless_client,
                                       self.namespace.namespacesId)
    self.service.name = 'myservice'
    self.metadata = self.service.metadata
    self.StartObjectPatch(
        name_generator,
        'GenerateName',
        side_effect=lambda **kwargs: '{}-genr8d'.format(kwargs['prefix']))

  def _GetAndApplyChanges(self):
    self.changes = flags.GetConfigurationChanges(self.args)
    for change in self.changes:
      change.Adjust(self.service)

  def testCpu(self):
    self.args.cpu = '1m'
    self._GetAndApplyChanges()
    self.assertEqual(len(self.changes), 1)
    self.assertEqual('1m', self.service.template.resource_limits['cpu'])

  def testConcurrencyDefault(self):
    self.args.concurrency = 'default'
    self._GetAndApplyChanges()
    self.assertEqual(len(self.changes), 1)
    self.assertIsNone(self.service.template.concurrency)

  def testServiceAccount(self):
    self.args.service_account = 'test@project.iam.gserviceaccount.com'
    self._GetAndApplyChanges()
    self.assertEqual(len(self.changes), 1)
    self.assertEqual(self.service.template.service_account,
                     self.args.service_account)

  @parameterized.parameters(['0', '1', '3'])
  def testConcurrencyNumeric(self, concurrency):
    self.args.concurrency = concurrency
    self._GetAndApplyChanges()
    self.assertEqual(len(self.changes), 1)
    self.assertEqual(self.service.template.concurrency, int(concurrency))

  @parameterized.parameters('1', '123', '7', '65535', 'default')
  def testConcurrencyValidValues(self, concurrency):
    self.assertTrue(flags._ConcurrencyValue(concurrency))

  @parameterized.parameters('0', '-1', 'bob', '', 'defaults')
  def testConcurrencyInvalidValues(self, concurrency):
    self.assertFalse(flags._ConcurrencyValue(concurrency))

  def testUpdateLabels(self):
    self.args.update_labels = {'asdf': 'tyte'}
    self.args._specified_args['update_labels'] = 'update_labels'
    self._GetAndApplyChanges()
    self.assertEqual(len(self.changes), 1)
    labels = k8s_object.LabelsFromMetadata(self.serverless_messages,
                                           self.metadata)
    self.assertEqual(dict(**labels), {'asdf': 'tyte'})

  def testRemoveLabels(self):
    self.args.remove_labels = ['abc', 'def']
    self.args._specified_args['remove_labels'] = 'remove_labels'
    self.service.labels.update({'abc': 'foo', 'def': 'bar', 'ghi': 'baz'})
    self._GetAndApplyChanges()
    self.assertEqual(len(self.changes), 1)
    labels = k8s_object.LabelsFromMetadata(self.serverless_messages,
                                           self.metadata)
    self.assertEqual(dict(**labels), {'ghi': 'baz'})

  def testImageFlag(self):
    container_image = 'gcr.io/example/image'
    self.args.image = container_image

    self._GetAndApplyChanges()

    self.assertEqual(self.service.template.container.image, container_image)
    self.assertEqual(
        self.service.annotations.get(revision.USER_IMAGE_ANNOTATION),
        container_image)
    self.assertEqual(
        self.service.template.annotations.get(revision.USER_IMAGE_ANNOTATION),
        container_image)

  @parameterized.parameters([('4s', 4), ('8m16s', 8 * 60 + 16)])
  def testValidTimeoutDuration(self, timeout, expect_seconds):
    parser = _TestArgumentParser()
    flags.AddTimeoutFlag(parser)
    parser.parse_args(['--timeout', timeout], self.args)
    self._GetAndApplyChanges()
    self.assertEqual(len(self.changes), 1)
    self.assertEqual(self.service.template.timeout, expect_seconds)

  @parameterized.parameters(['2', '5'])
  def testValidTimeoutNumber(self, timeout):
    parser = _TestArgumentParser()
    flags.AddTimeoutFlag(parser)
    parser.parse_args(['--timeout', timeout], self.args)
    self._GetAndApplyChanges()
    self.assertEqual(len(self.changes), 1)
    self.assertEqual(self.service.template.timeout, int(timeout))

  @parameterized.parameters(['2.0', '@^$%4', 'abcd'])
  def testInvalidTimeoutDurationSyntaxError(self, timeout):
    parser = _TestArgumentParser()
    flags.AddTimeoutFlag(parser)
    with self.assertRaises(flags.ArgumentError):
      parser.parse_args(['--timeout', timeout], self.args)
      self._GetAndApplyChanges()

  @parameterized.parameters(['0', '-1'])
  def testInvalidTimeoutArgError(self, timeout):
    parser = _TestArgumentParser()
    flags.AddTimeoutFlag(parser)
    with self.assertRaises(flags.ArgumentError):
      parser.parse_args(['--timeout', timeout], self.args)
      self._GetAndApplyChanges()

  def testCloudSqlApiEnablement(self):
    properties.VALUES.core.should_prompt_to_enable_api.Set(True)
    self.StartObjectPatch(flags, '_HasCloudSQLChanges', return_value=True)
    self.StartObjectPatch(
        flags, '_EnabledCloudSqlApiRequired', return_value=True)
    api_mock = self.StartObjectPatch(flags, 'PromptToEnableApi')
    self._GetAndApplyChanges()
    api_mock.assert_any_call(flags._CLOUD_SQL_API_SERVICE_TOKEN)
    api_mock.assert_any_call(flags._CLOUD_SQL_ADMIN_API_SERVICE_TOKEN)
    self.assertEqual(2, api_mock.call_count)

  @parameterized.parameters([
      services_exceptions.GetServicePermissionDeniedException('Boom!'),
      http_error.MakeHttpError()
  ])
  def testCloudSqlApiEnablementFailsOpen(self, exception):
    properties.VALUES.core.should_prompt_to_enable_api.Set(True)
    self.StartObjectPatch(flags, '_HasCloudSQLChanges', return_value=True)
    self.StartObjectPatch(
        flags, '_EnabledCloudSqlApiRequired', return_value=True)
    api_mock = self.StartObjectPatch(flags, 'PromptToEnableApi')
    api_mock.side_effect = exception
    self._GetAndApplyChanges()
    api_mock.assert_called_once_with(flags._CLOUD_SQL_API_SERVICE_TOKEN)

  @parameterized.parameters([
      services_exceptions.GetServicePermissionDeniedException('Boom!'),
      http_error.MakeHttpError()
  ])
  def testCloudSqlAdminApiEnablementFailsOpen(self, exception):
    properties.VALUES.core.should_prompt_to_enable_api.Set(True)
    self.StartObjectPatch(flags, '_HasCloudSQLChanges', return_value=True)
    self.StartObjectPatch(
        flags, '_EnabledCloudSqlApiRequired', return_value=True)
    api_mock = self.StartObjectPatch(flags, 'PromptToEnableApi')
    api_mock.side_effect = [None, exception]
    self._GetAndApplyChanges()
    api_mock.assert_any_call(flags._CLOUD_SQL_API_SERVICE_TOKEN)
    api_mock.assert_any_call(flags._CLOUD_SQL_ADMIN_API_SERVICE_TOKEN)
    self.assertEqual(2, api_mock.call_count)

  @parameterized.parameters(['suffix', 'revision-1'])
  def testRevisionSuffix(self, suffix):
    self.args.revision_suffix = suffix
    self._GetAndApplyChanges()
    self.assertEqual(self.service.template.name, 'myservice-{}'.format(suffix))
    self.assertEqual(len(self.changes), 1)

  @parameterized.parameters(['suffix', 'revision-1'])
  def testRevisionSuffixWithPreviousName(self, suffix):
    self.args.revision_suffix = suffix
    self.service.template.name = 'myservice-oldname'
    self._GetAndApplyChanges()
    self.assertEqual(self.service.template.name, 'myservice-{}'.format(suffix))
    self.assertEqual(len(self.changes), 1)

  def testScalingAdd(self):
    additional_properties = (
        self.service.template.metadata.annotations.additionalProperties)
    self.args.min_instances = flags._ScaleValue('1')
    self.args.max_instances = flags._ScaleValue('2')
    self._GetAndApplyChanges()
    got = {a.key: a.value for a in additional_properties}
    self.assertEqual(
        got, {
            u'autoscaling.knative.dev/maxScale': '2',
            u'autoscaling.knative.dev/minScale': '1'
        })

  def testScalingDelete(self):
    additional_properties = (
        self.service.template.metadata.annotations.additionalProperties)
    additional_properties.append(
        self.serverless_messages.ObjectMeta.AnnotationsValue.AdditionalProperty(
            key=u'autoscaling.knative.dev/minScale', value=u'1'))
    additional_properties.append(
        self.serverless_messages.ObjectMeta.AnnotationsValue.AdditionalProperty(
            key=u'autoscaling.knative.dev/maxScale', value=u'2'))
    self.args.min_instances = flags._ScaleValue('default')
    self.args.max_instances = flags._ScaleValue('3')
    self._GetAndApplyChanges()
    got = {a.key: a.value for a in additional_properties}
    self.assertEqual(got, {u'autoscaling.knative.dev/maxScale': '3'})

  def testScalingMinInstances0(self):
    additional_properties = (
        self.service.template.metadata.annotations.additionalProperties)
    additional_properties.append(
        self.serverless_messages.ObjectMeta.AnnotationsValue.AdditionalProperty(
            key=u'autoscaling.knative.dev/minScale', value=u'1'))
    additional_properties.append(
        self.serverless_messages.ObjectMeta.AnnotationsValue.AdditionalProperty(
            key=u'autoscaling.knative.dev/maxScale', value=u'2'))
    self.args.min_instances = flags._ScaleValue('0')
    self.args.max_instances = flags._ScaleValue('3')
    self._GetAndApplyChanges()
    got = {a.key: a.value for a in additional_properties}
    self.assertEqual(got, {u'autoscaling.knative.dev/maxScale': '3'})

  def testTrafficToLatest(self):
    self.service.spec_traffic['r1'] = [
        traffic.NewTrafficTarget(self.serverless_messages, 'r1', 100)
    ]
    self.args.to_latest = True
    self.args.to_revisions = None
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    self._GetAndApplyChanges()
    expect = {
        traffic.LATEST_REVISION_KEY: [
            traffic.NewTrafficTarget(self.serverless_messages,
                                     traffic.LATEST_REVISION_KEY, 100)
        ]
    }
    self.assertEqual(self.service.spec_traffic, expect)

  def testTrafficToRevision(self):
    self.service.spec_traffic[traffic.LATEST_REVISION_KEY] = [
        traffic.NewTrafficTarget(self.serverless_messages,
                                 traffic.LATEST_REVISION_KEY, 100)
    ]
    self.args.to_latest = False
    self.args.to_revisions = {'r1': 60}
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    self._GetAndApplyChanges()
    expect = {
        traffic.LATEST_REVISION_KEY: [
            traffic.NewTrafficTarget(self.serverless_messages,
                                     traffic.LATEST_REVISION_KEY, 40)
        ],
        'r1': [traffic.NewTrafficTarget(self.serverless_messages, 'r1', 60)]
    }
    self.assertEqual(self.service.spec_traffic, expect)

  def testTrafficTagsSet(self):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    change_mock = self.StartObjectPatch(
        config_changes, 'TrafficChanges', autoSpec=True)
    self.args.set_tags = {'latest': 'LATEST', 'prod': 'r1'}
    self._GetAndApplyChanges()
    change_mock.assert_called_once_with({}, False, {
        'latest': 'LATEST',
        'prod': 'r1'
    }, None, True)

  def testTrafficTagsUpdate(self):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    change_mock = self.StartObjectPatch(
        config_changes, 'TrafficChanges', autoSpec=True)
    self.args.update_tags = {'latest': 'LATEST', 'prod': 'r1'}
    self._GetAndApplyChanges()
    change_mock.assert_called_once_with({}, False, {
        'latest': 'LATEST',
        'prod': 'r1'
    }, None, None)

  def testTrafficTagsRemove(self):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    change_mock = self.StartObjectPatch(
        config_changes, 'TrafficChanges', autoSpec=True)
    self.args.remove_tags = ['prod']
    self._GetAndApplyChanges()
    change_mock.assert_called_once_with({}, False, None, ['prod'], None)

  def testTrafficTagsClear(self):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    change_mock = self.StartObjectPatch(
        config_changes, 'TrafficChanges', autoSpec=True)
    self.args.clear_tags = True
    self._GetAndApplyChanges()
    change_mock.assert_called_once_with({}, False, None, None, True)

  def testTrafficSetTagsAndToRevision(self):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    change_mock = self.StartObjectPatch(
        config_changes, 'TrafficChanges', autoSpec=True)
    self.args.set_tags = {'latest': 'LATEST', 'prod': 'r1'}
    self.args.to_latest = False
    self.args.to_revisions = {'r1': 60}
    self._GetAndApplyChanges()
    change_mock.assert_called_once_with({'r1': 60}, False, {
        'latest': 'LATEST',
        'prod': 'r1'
    }, None, True)

  def testTrafficSetTagsAndToTags(self):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    change_mock = self.StartObjectPatch(
        config_changes, 'TrafficChanges', autoSpec=True)
    self.args.set_tags = {'latest': 'LATEST', 'prod': 'r1'}
    self.args.to_latest = False
    self.args.to_tags = {'latest': 60}
    self._GetAndApplyChanges()
    change_mock.assert_called_once_with({'latest': 60}, True, {
        'latest': 'LATEST',
        'prod': 'r1'
    }, None, True)

  def testTrafficUpdateTagsAndToLatest(self):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    change_mock = self.StartObjectPatch(
        config_changes, 'TrafficChanges', autoSpec=True)
    self.args.update_tags = {'latest': 'LATEST', 'prod': 'r1'}
    self.args.to_latest = True
    self._GetAndApplyChanges()
    change_mock.assert_called_once_with({'LATEST': 100}, False, {
        'latest': 'LATEST',
        'prod': 'r1'
    }, None, None)

  def testPromptToEnableApi(self):
    properties.VALUES.core.should_prompt_to_enable_api.Set(True)
    is_enabled_mock = self.StartObjectPatch(
        enable_api, 'IsServiceEnabled', return_value=False)
    enable_mock = self.StartObjectPatch(enable_api, 'EnableService')
    self.WriteInput('y\n')
    flags.PromptToEnableApi('api_token')
    is_enabled_mock.assert_called_once_with('fake-project', 'api_token')
    enable_mock.assert_called_once_with('fake-project', 'api_token')

  def testContainerCommand(self):
    self.args.command = ['some/command']
    self._GetAndApplyChanges()
    self.assertEqual(self.service.template.container.command, ['some/command'])

  def testArgsCommand(self):
    self.args.args = ['--flag', 'value']
    self._GetAndApplyChanges()
    self.assertEqual(self.service.template.container.args, ['--flag', 'value'])

  def testSecrets(self):
    self.args.set_secrets = {'/my/path': 'mysecret', 'VAR': 'mysecret:key'}
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    self._GetAndApplyChanges()
    self.assertDictEqual({'/my/path': 'mysecret-genr8d'},
                         dict(self.service.template.volume_mounts.secrets))
    self.assertDictEqual(
        {
            'mysecret-genr8d':
                self.serverless_messages.SecretVolumeSource(
                    secretName='mysecret')
        }, dict(self.service.template.volumes.secrets))
    self.assertDictEqual(
        {
            'VAR':
                self.serverless_messages.EnvVarSource(
                    secretKeyRef=self.serverless_messages.SecretKeySelector(
                        name='mysecret', key='key'))
        }, dict(self.service.template.env_vars.secrets))

  def testConfigMaps(self):
    self.args.set_config_maps = {'/my/path': 'myconfig', 'VAR': 'myconfig:key'}
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    self._GetAndApplyChanges()
    self.assertDictEqual({'/my/path': 'myconfig-genr8d'},
                         dict(self.service.template.volume_mounts.config_maps))
    self.assertDictEqual(
        {
            'myconfig-genr8d':
                self.serverless_messages.ConfigMapVolumeSource(name='myconfig')
        }, dict(self.service.template.volumes.config_maps))
    self.assertDictEqual(
        {
            'VAR':
                self.serverless_messages.EnvVarSource(
                    configMapKeyRef=self.serverless_messages
                    .ConfigMapKeySelector(name='myconfig', key='key'))
        }, dict(self.service.template.env_vars.config_maps))

  @parameterized.parameters('1', '123', '7', '65535', 'default')
  def testContainerPortValidValues(self, port_str):
    self.assertTrue(flags._PortValue(port_str))

  @parameterized.parameters('0', '-1', 'bob', '65536', '', 'defaults')
  def testContainerPortInvalidValues(self, port_str):
    self.assertFalse(flags._PortValue(port_str))

  @parameterized.parameters('private-ranges-only', 'all')
  def testEgressSettings(self, egress):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    self.args.vpc_egress = egress
    self._GetAndApplyChanges()
    self.assertDictContainsSubset(
        {'run.googleapis.com/vpc-access-egress': egress},
        self.service.template_annotations)

  @parameterized.parameters('all', 'internal',
                            'internal-and-cloud-load-balancing')
  def testIngressFullyManaged(self, ingress):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    properties.VALUES.run.platform.Set('managed')
    self.args.ingress = ingress
    self._GetAndApplyChanges()
    self.assertDictContainsSubset({'run.googleapis.com/ingress': ingress},
                                  self.service.annotations)

  @parameterized.parameters('gke', 'kubernetes')
  def testIngressInternalAnthos(self, platform):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    properties.VALUES.run.platform.Set(platform)
    self.args.ingress = 'internal'
    self._GetAndApplyChanges()
    self.assertDictContainsSubset(
        {'serving.knative.dev/visibility': 'cluster-local'},
        self.service.labels)

  @parameterized.parameters('gke', 'kubernetes')
  def testIngressAllAnthos(self, platform):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    properties.VALUES.run.platform.Set(platform)
    self.service.labels['serving.knative.dev/visibility'] = 'cluster-local'
    self.args.ingress = 'all'
    self._GetAndApplyChanges()
    self.assertNotIn(
        'serving.knative.dev/visibility', self.service.labels)

  @parameterized.parameters('gke', 'kubernetes')
  def testIngressInternalAndCloudLoadBalancingAnthos(self, platform):
    self.StartObjectPatch(self.args, 'IsSpecified', return_value=True)
    properties.VALUES.run.platform.Set(platform)
    self.args.ingress = 'internal-and-cloud-load-balancing'
    with self.assertRaises(exceptions.ConfigurationError):
      self._GetAndApplyChanges()


class GetRegionTest(base.ServerlessBase, cli_test_base.CliTestBase,
                    sdk_test_base.WithFakeAuth):
  """Test getting region under different configs and flags."""

  def SetUp(self):
    properties.VALUES.run.region.Set('serverless-config-region')
    self.args = parser_extensions.Namespace()

  def testGetFromFlag(self):
    self.args.region = 'region1'
    self.assertEqual('region1', flags.GetRegion(self.args, prompt=True))

  def testGetFromServerlessConfig(self):
    self.assertEqual('serverless-config-region', flags.GetRegion(self.args))

  def testGetFromPrompt(self):
    with mock.patch(
        'googlecloudsdk.api_lib.run.global_methods.GetServerlessClientInstance',
        return_value=self.mock_serverless_client):
      with mock.patch(
          'googlecloudsdk.api_lib.run.global_methods.ListRegions',
          return_value=[base.DEFAULT_REGION]):
        properties.VALUES.run.region.Set(None)

        fake_idx = 0
        self.WriteInput('{}\n'.format(fake_idx + 1))

        expected_region = base.DEFAULT_REGION
        actual_region = flags.GetRegion(self.args, prompt=True)
        self.AssertErrContains(
            'To make this the default region, run '
            '`gcloud config set run/region {}`'.format(expected_region))

        self.assertEqual(expected_region, actual_region)


class GetPlatformTestGA(base.ServerlessBase):
  """Test getting the platform."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.args = parser_extensions.Namespace()
    # Set up mock deepest_parser for args.CONCEPTS
    deepest_parser = mock.Mock()
    deepest_parser._calliope_command.ai.concept_handler.return_value = mock.Mock(
    )
    self.args._SetParser(deepest_parser)

    # Set up actual parser
    self.parser = argparse.ArgumentParser()
    flags.AddPlatformArg(self.parser)
    self.args._parsers.append(self.parser)

    properties.VALUES.run.platform.Set(None)

  def testGetFromFlag(self):
    properties.VALUES.run.platform.Set('gke')
    self.parser.parse_args(['--platform', 'managed'], self.args)
    self.assertEqual(
        'managed',
        flags.GetAndValidatePlatform(self.args, self.track, flags.Product.RUN))

  def testGetFromProperty(self):
    properties.VALUES.run.platform.Set('gke')
    self.assertEqual(
        'gke',
        flags.GetAndValidatePlatform(self.args, self.track, flags.Product.RUN))

  def testInvalidProperty(self):
    properties.VALUES.run.platform.Set('invalid')
    with self.assertRaises(flags.ArgumentError):
      flags.GetAndValidatePlatform(self.args, self.track, flags.Product.RUN)

  def testGetFromPrompt(self):
    self.WriteInput('2\n')
    expected_platform = 'gke'
    actual_platform = flags.GetAndValidatePlatform(self.args, self.track,
                                                   flags.Product.RUN)
    self.AssertErrContains(
        'run `gcloud config set run/platform {}`'.format(expected_platform))
    self.assertEqual(expected_platform, actual_platform)

  def testCantGetFromPrompt(self):
    self.is_interactive.return_value = False
    with self.assertRaises(flags.ArgumentError):
      flags.GetAndValidatePlatform(self.args, self.track, flags.Product.RUN)


class GetPlatformTestBeta(GetPlatformTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class GetPlatformTestAlpha(GetPlatformTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class ValidationsTestGA(test_case.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.StartObjectPatch(
        parser_extensions.Namespace, 'IsSpecified', return_value=True)

  def testVerifyGKEFlagsAllowUnauthenticated(self):
    args = parser_extensions.Namespace(allow_unauthenticated=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.allow_unauthenticated = True
      flags.VerifyGKEFlags(args, self.track, flags.Product.RUN)

  def testVerifyGKEFlagsConnectivityAndIngress(self):
    args = parser_extensions.Namespace(connectivity=None, ingress=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.connectivity = 'internal'
      args.ingress = 'internal'
      flags.VerifyGKEFlags(args, self.track, flags.Product.RUN)

  def testVerifyGKEFlagsRegion(self):
    args = parser_extensions.Namespace(region=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.region = 'us-central1'
      flags.VerifyGKEFlags(args, self.track, flags.Product.RUN)

  def testVerifyGKEFlagsKubeconfig(self):
    args = parser_extensions.Namespace(kubeconfig=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.kubeconfig = '~/.kube/config'
      flags.VerifyGKEFlags(args, self.track, flags.Product.RUN)

  def testVerifyGKEFlagsNoTraffic(self):
    args = parser_extensions.Namespace(no_traffic=None)
    args.no_traffic = True
    flags.VerifyGKEFlags(args, self.track, flags.Product.RUN)

  def testVerifyGKEFlagsClearSecrets(self):
    args = parser_extensions.Namespace(clear_secrets=None)
    args.clear_secrets = True
    flags.VerifyGKEFlags(args, self.track, flags.Product.RUN)

  def testVerifyGKEFlagsMinInstance(self):
    args = parser_extensions.Namespace(min_instances=None)
    args.min_instances = 3
    flags.VerifyGKEFlags(args, self.track, flags.Product.RUN)

  def testVerifyGKEFlagsContext(self):
    args = parser_extensions.Namespace(context=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.context = 'some-context'
      flags.VerifyGKEFlags(args, self.track, flags.Product.RUN)

  def testVerifyGKEFlagsEgressSettings(self):
    args = parser_extensions.Namespace(vpc_egress='private-ranges-only')
    with self.assertRaises(exceptions.ConfigurationError):
      flags.VerifyGKEFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsConnectivity(self):
    args = parser_extensions.Namespace(connectivity=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.connectivity = True
      flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsCpu(self):
    args = parser_extensions.Namespace(cpu=None)
    args.cpu = 2
    flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsCluster(self):
    args = parser_extensions.Namespace(cluster=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.cluster = 'cluster-1'
      flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsLocation(self):
    args = parser_extensions.Namespace(cluster_location=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.cluster_location = 'us-central1-a'
      flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsKubeconfig(self):
    args = parser_extensions.Namespace(kubeconfig=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.kubeconfig = '~/.kube/config'
      flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsContext(self):
    args = parser_extensions.Namespace(context=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.context = 'some-context'
      flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsMinInstance(self):
    args = parser_extensions.Namespace(min_instances=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.min_instances = 3
      flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsNoTraffic(self):
    args = parser_extensions.Namespace(no_traffic=None)
    args.no_traffic = True
    flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsTimeout(self):
    parser = argparse.ArgumentParser()
    flags.AddTimeoutFlag(parser)
    args = parser.parse_args(['--timeout', '1h'],
                             parser_extensions.Namespace(timeout=None))
    with self.assertRaises(exceptions.ConfigurationError):
      flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsTimeoutGAOk(self):
    parser = argparse.ArgumentParser()
    flags.AddTimeoutFlag(parser)
    args = parser.parse_args(['--timeout', '15m'],
                             parser_extensions.Namespace(timeout=None))
    flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsEgressSettings(self):
    args = parser_extensions.Namespace(vpc_egress='private-ranges-only')
    flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyKubernetesFlagsAllowUnauthenticated(self):
    args = parser_extensions.Namespace(allow_unauthenticated=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.allow_unauthenticated = True
      flags.VerifyKubernetesFlags(args, self.track, flags.Product.RUN)

  def testVerifyKubernetesFlagsConnectivityAndIngress(self):
    args = parser_extensions.Namespace(connectivity=None, ingress=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.connectivity = 'internal'
      args.ingress = 'internal'
      flags.VerifyKubernetesFlags(args, self.track, flags.Product.RUN)

  def testVerifyKubernetesFlagsRegion(self):
    args = parser_extensions.Namespace(region=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.region = 'us-central1'
      flags.VerifyKubernetesFlags(args, self.track, flags.Product.RUN)

  def testVerifyKubernetesFlagsCluster(self):
    args = parser_extensions.Namespace(cluster=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.cluster = 'cluster-1'
      flags.VerifyKubernetesFlags(args, self.track, flags.Product.RUN)

  def testVerifyKubernetesFlagsLocation(self):
    args = parser_extensions.Namespace(cluster_location=None)
    with self.assertRaises(exceptions.ConfigurationError):
      args.cluster_location = 'us-central1-a'
      flags.VerifyKubernetesFlags(args, self.track, flags.Product.RUN)

  def testVerifyKubernetesFlagsEgressSettings(self):
    args = parser_extensions.Namespace(vpc_egress='private-ranges-only')
    with self.assertRaises(exceptions.ConfigurationError):
      flags.VerifyKubernetesFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsEventsIsAlphaOnly(self):
    # The "gcloud events" subcommand is alpha only for --platform=managed
    args = parser_extensions.Namespace()
    with self.assertRaises(exceptions.ConfigurationError):
      flags.VerifyOnePlatformFlags(args, self.track, flags.Product.EVENTS)


class ValidationsTestBeta(ValidationsTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testVerifyOnePlatformFlagsTimeout(self):
    parser = argparse.ArgumentParser()
    flags.AddTimeoutFlag(parser)
    args = parser.parse_args(['--timeout', '45m'],
                             parser_extensions.Namespace(timeout=None))
    flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)


class ValidationsTestAlpha(ValidationsTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testVerifyOnePlatformFlagsMinInstance(self):
    args = parser_extensions.Namespace(min_instances=None)
    args.min_instances = 3
    flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsTimeout(self):
    parser = argparse.ArgumentParser()
    flags.AddTimeoutFlag(parser)
    args = parser.parse_args(['--timeout', '1h'],
                             parser_extensions.Namespace(timeout=None))
    flags.VerifyOnePlatformFlags(args, self.track, flags.Product.RUN)

  def testVerifyOnePlatformFlagsEventsIsAlphaOnly(self):
    # The "gcloud events" subcommand is alpha only for --platform=managed
    args = parser_extensions.Namespace()
    flags.VerifyOnePlatformFlags(args, self.track, flags.Product.EVENTS)


class GetKubeconfigTest(test_case.TestCase):

  def SetUp(self):
    self.args = parser_extensions.Namespace()

  def testGetFromArgs(self):
    expected_config = kubeconfig.Kubeconfig.Default()
    expected_config.SetCurrentContext('context')
    self.StartObjectPatch(
        kubeconfig.Kubeconfig, 'LoadFromFile', return_value=expected_config)
    path = '/some/path'
    self.args.kubeconfig = path
    self.assertEqual(expected_config, flags.GetKubeconfig(self.args))
    kubeconfig.Kubeconfig.LoadFromFile.assert_called_once_with(path)

  def testGetFromDefault(self):
    expected_config = kubeconfig.Kubeconfig.Default()
    expected_config.SetCurrentContext('context')
    self.StartObjectPatch(
        kubeconfig.Kubeconfig, 'LoadFromFile', return_value=expected_config)
    self.assertEqual(expected_config, flags.GetKubeconfig(self.args))
    path_args, _ = kubeconfig.Kubeconfig.LoadFromFile.call_args
    self.assertTrue(path_args[0].endswith('/.kube/config'))

  def _SetUpEnvTest(self):
    config1 = kubeconfig.Kubeconfig.Default()
    cluster1 = kubeconfig.Cluster(
        'cluster1', 'https://1.1.1.1', ca_data='FAKE_CA_DATA')
    cluster2 = kubeconfig.Cluster('cluster2', 'https://2.2.2.2', ca_data=None)
    user = kubeconfig.User(
        'user', cert_data='FAKECERTDATA', key_data='FAKE_KEY_DATA')
    context = kubeconfig.Context('context', 'cluster1', 'user')
    config1.clusters['cluster1'] = cluster1
    config1.clusters['cluster2'] = cluster2
    config1.users['user'] = user
    config1.contexts['context'] = context
    config1.SetCurrentContext('context')

    config2 = kubeconfig.Kubeconfig.Default()
    modified_cluster1 = kubeconfig.Cluster(
        'cluster1', 'https://2.2.2.2', ca_data=None)
    other_cluster2 = kubeconfig.Cluster(
        'other_cluster2', 'https://3.3.3.3', ca_data='FAKE_CA_DATA')
    user = kubeconfig.User(
        'user', cert_data='FAKECERTDATA', key_data='FAKE_KEY_DATA')
    other_context = kubeconfig.Context('other_context', 'cluster1', 'user')
    config2.clusters['cluster1'] = modified_cluster1
    config2.clusters['other_cluster2'] = other_cluster2
    config2.users['user'] = user
    config2.contexts['other_context'] = other_context
    config2.SetCurrentContext('other_context')

    self.expected_configs = {'/some/path1': config1, '/some/path2': config2}

    def _KubeconfigLoadFromFile(path):
      if path in self.expected_configs:
        return self.expected_configs[path]
      else:
        raise kubeconfig.Error('Invalid path', path)

    self.StartObjectPatch(
        kubeconfig.Kubeconfig,
        'LoadFromFile',
        side_effect=_KubeconfigLoadFromFile)

  def testGetFromEnvVar(self):
    self._SetUpEnvTest()
    path = '/some/path1'
    self.StartDictPatch(os.environ, {'KUBECONFIG': path})
    self.assertEqual(self.expected_configs[path],
                     flags.GetKubeconfig(self.args))
    kubeconfig.Kubeconfig.LoadFromFile.assert_called_once_with(path)

  def testGetFromEnvVarInvalidPath(self):
    self._SetUpEnvTest()
    self.StartDictPatch(os.environ, {'KUBECONFIG': '/invalid/path'})
    with self.assertRaises(flags.KubeconfigError):
      flags.GetKubeconfig(self.args)

  def testGetFromEnvVarPartiallyInvalidPath(self):
    self._SetUpEnvTest()
    path = '/some/path1'
    self.StartDictPatch(os.environ, {
        'KUBECONFIG':
            '/invalid/path{sep}{path}'.format(sep=os.pathsep, path=path)
    })
    self.assertEqual(self.expected_configs[path],
                     flags.GetKubeconfig(self.args))
    kubeconfig.Kubeconfig.LoadFromFile.assert_any_call('/invalid/path')
    kubeconfig.Kubeconfig.LoadFromFile.assert_any_call(path)
    self.assertEqual(2, kubeconfig.Kubeconfig.LoadFromFile.call_count)

  def testGetFromEnvVarMerge(self):
    self._SetUpEnvTest()
    path_1 = '/some/path1'
    path_2 = '/some/path2'
    self.StartDictPatch(
        os.environ, {
            'KUBECONFIG':
                '{path_1}{sep}{path_2}'.format(
                    path_1=path_1, sep=os.pathsep, path_2=path_2)
        })
    expected_config = self.expected_configs[path_1]
    expected_config.Merge(self.expected_configs[path_2])
    self.assertEqual(expected_config, flags.GetKubeconfig(self.args))
    kubeconfig.Kubeconfig.LoadFromFile.assert_any_call(path_1)
    kubeconfig.Kubeconfig.LoadFromFile.assert_any_call(path_2)
    self.assertEqual(2, kubeconfig.Kubeconfig.LoadFromFile.call_count)
