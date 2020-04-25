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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import tempfile
import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from tests.lib.command_lib.util.apis import yaml_command_base


class ImportCommandTests(yaml_command_base.CommandTestsBase):
  """Tests for import declarative command type."""

  def SetUp(self):
    client = apis.GetClientClass('compute', 'alpha')
    self.mocked_client = apitools_mock.Client(client)
    self.messages = client.MESSAGES_MODULE
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.test_instance = self.messages.Instance(
        canIpForward=None,
        confidentialInstanceConfig=None,
        cpuPlatform=None,
        creationTimestamp=None,
        deletionProtection=None,
        description=None,
        disks=[],
        displayDevice=None,
        eraseWindowsVssSignature=None,
        fingerprint=None,
        guestAccelerators=[],
        hostname=None,
        id=None,
        instanceEncryptionKey=None,
        kind='compute#instance',
        labelFingerprint=None,
        labels=None,
        machineType=None,
        metadata=None,
        minCpuPlatform=None,
        name='test',
        networkInterfaces=[],
        postKeyRevocationActionType=None,
        preservedStateSizeGb=None,
        privateIpv6GoogleAccess=None,
        reservationAffinity=None,
        resourcePolicies=[],
        scheduling=None,
        selfLink=None,
        selfLinkWithId=None,
        serviceAccounts=[],
        shieldedInstanceConfig=None,
        shieldedInstanceIntegrityPolicy=None,
        shieldedVmConfig=None,
        shieldedVmIntegrityPolicy=None,
        sourceMachineImage=None,
        sourceMachineImageEncryptionKey=None,
        startRestricted=None,
        status=None,
        statusMessage=None,
        tags=None,
        zone=None,
    )
    self.test_running_operation = self.messages.Operation(
        id=12345,
        name='operation-12345',
        selfLink='https://compute.googleapis.com/compute/v1/projects/p/zones/z/'
                 'operations/operation-12345',
        error=None,
        status=self.messages.Operation.StatusValueValuesEnum.RUNNING)

    # Set up input file for command to import from.
    temp_path = tempfile.mkdtemp(dir=self.root_path)
    self.Touch(temp_path, 'test.yaml', 'name: test')
    self.input_path = os.path.join(temp_path, 'test.yaml')

  def SetUpMocking(
      self,
      is_update=False,
      is_insert=False,
      is_async=False,
      abort_early=False):
    """Sets client mock to expect Get request and return compute instance."""

    # Mock schema path to avoid validation testing which is handled elsewhere.
    get_schema_mock = self.StartObjectPatch(export_util, 'GetSchemaPath')
    get_schema_mock.side_effect = [None]

    # Mock _GetExistingResource to return matching resource or 404 not found.
    get_existing_resource_mock = self.StartObjectPatch(
        yaml_command_translator.CommandBuilder, '_GetExistingResource')
    if abort_early:
      get_existing_resource_mock.side_effect = [
          self.messages.Instance(name='test')
      ]
    else:
      get_existing_resource_mock.side_effect = apitools_exceptions.HttpError(
          {'status': '404'}, content='not found', url='test')

    # Set up mocking to expect an update request.
    if is_update:
      self.MockUpdate()

    # Set up mocking to expect an insert request.
    if is_insert:
      self.MockInsert()

    # Set up mocking to expect asynchronous behavior.
    if is_async:
      self.MockAsync()

  def MockUpdate(self):
    """Mocks to expect an update request."""
    self.mocked_client.instances.Update.Expect(
        self.messages.ComputeInstancesUpdateRequest(
            instance='test',
            instanceResource=self.test_instance,
            minimalAction=None,
            mostDisruptiveAllowedAction=None,
            project='p',
            requestId=None,
            zone='z',
        ),
        response=self.test_running_operation,
        enable_type_checking=False)

  def MockInsert(self):
    """Mocks to expect an insert request."""
    self.mocked_client.instances.Insert.Expect(
        self.messages.ComputeInstancesInsertRequest(
            instance=self.test_instance,
            project='p',
            requestId=None,
            zone='z',
        ),
        response=self.test_running_operation,
        enable_type_checking=False)

  def MockAsync(self):
    """Mocks to expect asynchronous requests."""
    self.mocked_client.zoneOperations.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-12345',
            project='p',
            zone='z',
        ),
        self.messages.Operation(
            id=12345,
            name='operation-12345',
            selfLink='https://compute.googleapis.com/compute/v1/projects/p/zones/z/'
                     'operations/operation-12345',
            error=None,
            status=self.messages.Operation.StatusValueValuesEnum.DONE))
    self.mocked_client.instances.Get.Expect(
        self.messages.ComputeInstancesGetRequest(
            instance='test',
            project='p',
            zone='z',
        ), self.messages.Instance(name='test', zone='z'))

  def AssertArgsAndExecute(self, d, is_async=False):
    """Asserts that args exist in command and executes command."""
    cli = self.MakeCLI(d)
    args = ['INSTANCE', '--zone', '--source']
    if is_async:
      args.extend(['--async', '--no-async'])
    self.AssertArgs(cli, *args)
    cli.Execute([
        'command', '--project', 'p', '--zone', 'z', '--source', self.input_path,
        'test'
    ])

  def testRunUpdate(self):
    """Tests generic import update command execution."""
    self.SetUpMocking(is_update=True)
    data = self.MakeCommandData()
    d = yaml_command_schema.CommandData('import', data)
    d.request.api_version = 'alpha'
    d.request.method = 'update'
    self.AssertArgsAndExecute(d)
    self.AssertOutputContains(
        textwrap.dedent("""\
          id: '12345'
          name: operation-12345
          selfLink: https://compute.googleapis.com/compute/v1/projects/p/zones/z/operations/operation-12345
          status: RUNNING
          """))

  def testRunCreate(self):
    """Tests import create command execution when resource doesn't exist."""
    self.SetUpMocking(is_insert=True)
    data = self.MakeCommandData()
    import_spec = {
        'create_if_not_exists': True,
        'create_request': {
            'method': 'insert',
            'api_version': 'alpha',
        },
        'create_async': None
    }
    data['import'] = import_spec
    d = yaml_command_schema.CommandData('import', data)
    d.request.api_version = 'alpha'
    d.request.method = 'update'
    d.import_.create_request.method = 'insert'
    self.AssertArgsAndExecute(d)
    self.AssertOutputContains(
        textwrap.dedent("""\
          id: '12345'
          name: operation-12345
          selfLink: https://compute.googleapis.com/compute/v1/projects/p/zones/z/operations/operation-12345
          status: RUNNING
          """))

  def testEarlyAbort(self):
    """Tests early exit behavior if command detects no changes."""
    self.SetUpMocking(abort_early=True)
    data = self.MakeCommandData()
    import_spec = {
        'abort_if_equivalent': True,
    }
    data['import'] = import_spec
    d = yaml_command_schema.CommandData('import', data)
    d.request.api_version = 'alpha'
    d.request.method = 'update'
    self.AssertArgsAndExecute(d)
    self.AssertErrContains('Request not sent for [test]: No changes detected.')

  def testAsync(self):
    """Tests asynchronous calls for update import commands."""
    self.SetUpMocking(is_update=True, is_async=True)
    data = self.MakeCommandData(is_async='zoneOperations')
    d = yaml_command_schema.CommandData('import', data)
    d.async_.state.field = 'status'
    d.async_.state.success_values = ['DONE']
    d.async_.api_version = 'alpha'
    d.async_.method = 'wait'
    d.async_.response_name_field = 'selfLink'
    d.request.api_version = 'alpha'
    d.request.method = 'update'
    self.AssertArgsAndExecute(d, is_async=True)
    self.AssertOutputContains('name: test\nzone: z')

  def testCreateAsync(self):
    """Tests asynchronous behavior for create import commands."""
    self.SetUpMocking(is_insert=True, is_async=True)
    data = self.MakeCommandData(is_async='zoneOperations')
    import_spec = {
        'create_if_not_exists': True,
        'create_request': {
            'method': 'insert',
            'api_version': 'alpha',
        },
        'create_async': {
            'collection': 'compute.zoneOperations',
            'state': {
                'field': 'status',
                'success_values': ['DONE']
            },
            'api_version': 'alpha',
            'method': 'wait',
            'response_name_field': 'selfLink'
        }
    }
    data['import'] = import_spec
    d = yaml_command_schema.CommandData('import', data)
    d.request.api_version = 'alpha'
    d.request.method = 'update'
    self.AssertArgsAndExecute(d, is_async=True)
    self.AssertOutputEquals('name: test\nzone: z\n')
