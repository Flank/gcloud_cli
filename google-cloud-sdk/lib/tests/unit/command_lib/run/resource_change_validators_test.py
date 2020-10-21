# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for resource change validators."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_change_validators
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope import util as calliope_test_util
from tests.lib.surface.run import base

_PROMPT_MESSAGE = (
    'Removing the VPC connector from this service will clear the '
    'VPC egress setting and route outbound traffic to the public internet.')
_CONFIGURATION_ERROR_MESSAGE = (
    'Cannot remove VPC connector with VPC egress set to "all". Set'
    ' `--vpc-egress=private-ranges-only` or run this command '
    'interactively and provide confirmation to continue.')


class ValidateClearVpcConnectorTest(base.ServerlessSurfaceBase,
                                    parameterized.TestCase):

  def SetUp(self):
    self.arg_parser = calliope_test_util.ArgumentParser()
    flags.AddVpcConnectorArg(self.arg_parser)
    flags.AddEgressSettingsFlag(self.arg_parser)
    self.can_prompt = self.StartObjectPatch(console_io, 'CanPrompt')
    self.prompt_continue = self.StartObjectPatch(console_io, 'PromptContinue')
    self.service = service.Service.New(self.mock_serverless_client,
                                       self.namespace.namespacesId)

  def testClearVpcConnectorNotSet_NoVpcEgress_DoesNothing(self):
    args = self.arg_parser.parse_args([])

    resource_change_validators.ValidateClearVpcConnector(self.service, args)

    self.prompt_continue.assert_not_called()

  @parameterized.parameters([
      revision.EGRESS_SETTINGS_ALL, revision.EGRESS_SETTINGS_PRIVATE_RANGES_ONLY
  ])
  def testClearVpcConnectorNotSet_VpcEgressSet_DoesNothing(self, vpc_egress):
    args = self.arg_parser.parse_args([])
    self.service.template_annotations[
        revision.EGRESS_SETTINGS_ANNOTATION] = vpc_egress

    resource_change_validators.ValidateClearVpcConnector(self.service, args)

    self.prompt_continue.assert_not_called()

  def testClearVpcConnectorFalse_NoVpcEgress_DoesNothing(self):
    args = self.arg_parser.parse_args(['--no-clear-vpc-connector'])

    resource_change_validators.ValidateClearVpcConnector(self.service, args)

    self.prompt_continue.assert_not_called()

  @parameterized.parameters([
      revision.EGRESS_SETTINGS_ALL, revision.EGRESS_SETTINGS_PRIVATE_RANGES_ONLY
  ])
  def testClearVpcConnectorFalse_VpcEgressSet_DoesNothing(self, vpc_egress):
    args = self.arg_parser.parse_args(['--no-clear-vpc-connector'])
    self.service.template_annotations[
        revision.EGRESS_SETTINGS_ANNOTATION] = vpc_egress

    resource_change_validators.ValidateClearVpcConnector(self.service, args)

    self.prompt_continue.assert_not_called()

  def testClearVpcConnectorTrue_NoVpcEgress_DoesNothing(self):
    args = self.arg_parser.parse_args(['--clear-vpc-connector'])

    resource_change_validators.ValidateClearVpcConnector(self.service, args)

    self.prompt_continue.assert_not_called()

  def testClearVpcConnectorTrue_ServicePrivateRangesOnly_DoesNothing(self):
    args = self.arg_parser.parse_args(['--clear-vpc-connector'])
    self.service.template_annotations[
        revision.
        EGRESS_SETTINGS_ANNOTATION] = revision.EGRESS_SETTINGS_PRIVATE_RANGES_ONLY

    resource_change_validators.ValidateClearVpcConnector(self.service, args)

    self.prompt_continue.assert_not_called()

  @parameterized.parameters([
      revision.EGRESS_SETTINGS_PRIVATE_RANGES_ONLY, revision.EGRESS_SETTINGS_ALL
  ])
  def testClearVpcConnectorTrue_FlagPrivateRangesOnly_DoesNothing(
      self, service_vpc_egress):
    args = self.arg_parser.parse_args([
        '--clear-vpc-connector', '--vpc-egress',
        revision.EGRESS_SETTINGS_PRIVATE_RANGES_ONLY
    ])
    self.service.template_annotations[
        revision.EGRESS_SETTINGS_ANNOTATION] = service_vpc_egress

    resource_change_validators.ValidateClearVpcConnector(self.service, args)

    self.prompt_continue.assert_not_called()

  @parameterized.parameters([
      revision.EGRESS_SETTINGS_PRIVATE_RANGES_ONLY, revision.EGRESS_SETTINGS_ALL
  ])
  def testClearVpcConnectorTrue_FlagAll_CanPrompt_Prompts_ConfirmSucceeds(
      self, service_vpc_egress):
    self.can_prompt.return_value = True
    self.prompt_continue.return_value = True
    args = self.arg_parser.parse_args(
        ['--clear-vpc-connector', '--vpc-egress', revision.EGRESS_SETTINGS_ALL])
    self.service.template_annotations[
        revision.EGRESS_SETTINGS_ANNOTATION] = service_vpc_egress

    resource_change_validators.ValidateClearVpcConnector(self.service, args)

    self.prompt_continue.assert_called_once_with(
        message=_PROMPT_MESSAGE, default=False, cancel_on_no=True)

  def testClearVpcConnectorTrue_ServiceAll_CanPrompt_Prompts_ConfirmSucceeds(
      self):
    self.can_prompt.return_value = True
    self.prompt_continue.return_value = True
    args = self.arg_parser.parse_args(['--clear-vpc-connector'])
    self.service.template_annotations[
        revision.EGRESS_SETTINGS_ANNOTATION] = revision.EGRESS_SETTINGS_ALL

    resource_change_validators.ValidateClearVpcConnector(self.service, args)

    self.prompt_continue.assert_called_once_with(
        message=_PROMPT_MESSAGE, default=False, cancel_on_no=True)

  @parameterized.parameters([
      revision.EGRESS_SETTINGS_PRIVATE_RANGES_ONLY, revision.EGRESS_SETTINGS_ALL
  ])
  def testClearVpcConnectorTrue_FlagAll_CanPrompt_Prompts_NoConfirmThrows(
      self, service_vpc_egress):
    self.can_prompt.return_value = True
    self.prompt_continue.side_effect = console_io.OperationCancelledError
    args = self.arg_parser.parse_args(
        ['--clear-vpc-connector', '--vpc-egress', revision.EGRESS_SETTINGS_ALL])
    self.service.template_annotations[
        revision.EGRESS_SETTINGS_ANNOTATION] = service_vpc_egress

    with self.assertRaises(console_io.OperationCancelledError):
      resource_change_validators.ValidateClearVpcConnector(self.service, args)

  def testClearVpcConnectorTrue_ServiceAll_CanPrompt_Prompts_NoConfirmThrows(
      self):
    self.can_prompt.return_value = True
    self.prompt_continue.side_effect = console_io.OperationCancelledError
    args = self.arg_parser.parse_args(['--clear-vpc-connector'])
    self.service.template_annotations[
        revision.EGRESS_SETTINGS_ANNOTATION] = revision.EGRESS_SETTINGS_ALL

    with self.assertRaises(console_io.OperationCancelledError):
      resource_change_validators.ValidateClearVpcConnector(self.service, args)

  @parameterized.parameters([
      revision.EGRESS_SETTINGS_PRIVATE_RANGES_ONLY, revision.EGRESS_SETTINGS_ALL
  ])
  def testClearVpcConnectorTrue_FlagAll_NoPrompt_Throws(self,
                                                        service_vpc_egress):
    self.can_prompt.return_value = False
    args = self.arg_parser.parse_args(
        ['--clear-vpc-connector', '--vpc-egress', revision.EGRESS_SETTINGS_ALL])
    self.service.template_annotations[
        revision.EGRESS_SETTINGS_ANNOTATION] = service_vpc_egress

    with self.assertRaisesRegex(
        exceptions.ConfigurationError, _CONFIGURATION_ERROR_MESSAGE):
      resource_change_validators.ValidateClearVpcConnector(self.service, args)

    self.prompt_continue.assert_not_called()

  def testClearVpcConnectorTrue_ServiceAll_NoPrompt_Throws(self):
    self.can_prompt.return_value = False
    args = self.arg_parser.parse_args(['--clear-vpc-connector'])
    self.service.template_annotations[
        revision.EGRESS_SETTINGS_ANNOTATION] = revision.EGRESS_SETTINGS_ALL

    with self.assertRaisesRegex(
        exceptions.ConfigurationError, _CONFIGURATION_ERROR_MESSAGE):
      resource_change_validators.ValidateClearVpcConnector(self.service, args)

    self.prompt_continue.assert_not_called()


if __name__ == '__main__':
  test_case.main()
