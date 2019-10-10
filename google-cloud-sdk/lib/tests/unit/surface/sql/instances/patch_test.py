# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests that exercise operations listing and executing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.api_lib.sql import instances as instances_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseInstancePatchTest(object):
  # pylint:disable=g-tzinfo-datetime

  def _ExpectPatchClearMaintenanceWindow(self, expect_final_get=True):
    diff = {
        'name': 'patch-instance4',
        'settings': {
            'maintenanceWindow': self.messages.MaintenanceWindow(day=1, hour=2)
        }
    }
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    diff.update({'settings': {'maintenanceWindow': None}})
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    if expect_final_get:
      self.ExpectInstanceGet(self.GetV2Instance(), diff)

  def testClearMaintenanceWindow(self):
    self._ExpectPatchClearMaintenanceWindow()
    self.Run('sql instances patch patch-instance4 --quiet '
             '--maintenance-window-any --diff')
    self.AssertOutputContains(
        '-settings.maintenanceWindow.day: 1', normalize_space=True)
    self.AssertOutputContains(
        '-settings.maintenanceWindow.hour: 2', normalize_space=True)

    # TODO(b/122660263): Remove when V1 instances are no longer supported.
    # This is a V2 instance, so check that the deprecation message is not shown.
    self.AssertErrNotContains(
        'Upgrade your First Generation instance to Second Generation')

  def testClearMaintenanceWindowAsync(self):
    # No reason to choose this over any other patch scenario for testing async,
    # but we need the coverage.
    self._ExpectPatchClearMaintenanceWindow(expect_final_get=False)
    self.Run('sql instances patch patch-instance4 --quiet '
             '--maintenance-window-any --async')

  def testMaintenanceWindowRequirements(self):
    diff = {
        'name': 'patch-instance4',
    }
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    with self.assertRaises(argparse.ArgumentError):
      self.Run('sql instances patch patch-instance4 --maintenance-window-day '
               'FRI')

  def testClearNetworks(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    diff = {
        'name': 'patch-instance3',
        'settings': {
            'ipConfiguration':
                self.messages.IpConfiguration(
                    authorizedNetworks=[
                        self.messages.AclEntry(
                            expirationTime=None,
                            kind='sql#aclEntry',
                            name='',
                            value='0.0.0.0/0',
                        ),
                    ],
                    ipv4Enabled=False,
                    requireSsl=False,
                )
        }
    }
    self.ExpectInstanceGet(self.GetV1Instance(), diff)
    diff.update({
        'settings': {
            'ipConfiguration':
                self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=None,
                    requireSsl=None,)
        }
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)

    self.Run('sql instances patch patch-instance3 --quiet '
             '--clear-authorized-networks --diff')
    self.assertEqual(prompt_mock.call_count, 0)
    self.AssertOutputContains(
        '-settings.ipConfiguration.authorizedNetworks[0].value: 0.0.0.0/0',
        normalize_space=True)
    self.AssertErrContains('{"ipConfiguration": {"authorizedNetworks": []}}')

    # TODO(b/122660263): Remove when V1 instances are no longer supported.
    # This is a V1 instance, so check that the deprecation message is shown.
    self.AssertErrContains(
        'Upgrade your First Generation instance to Second Generation')

  def testPatchAuthorizedNetworks(self):
    overwrite_prompt_mock = self.StartObjectPatch(
        instances_util.InstancesV1Beta4,
        'PrintAndConfirmAuthorizedNetworksOverwrite')
    diff = {
        'name': 'patch-instance3',
        'settings': {
            'ipConfiguration':
                self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=None,
                    requireSsl=None,)
        }
    }
    self.ExpectInstanceGet(self.GetV1Instance(), diff)
    diff.update({
        'settings': {
            'ipConfiguration':
                self.messages.IpConfiguration(
                    authorizedNetworks=[
                        self.messages.AclEntry(
                            expirationTime=None,
                            kind='sql#aclEntry',
                            name=None,
                            value='0.0.0.0/0',
                        ),
                    ],
                    ipv4Enabled=None,
                    requireSsl=None,
                )
        }
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)

    self.Run('sql instances patch patch-instance3 --quiet '
             '--authorized-networks=0.0.0.0/0 --diff')
    self.assertEqual(overwrite_prompt_mock.call_count, 1)
    self.AssertOutputContains(
        '+settings.ipConfiguration.authorizedNetworks[0].value: 0.0.0.0',
        normalize_space=True)
    self.AssertErrContains('{"authorizedNetworks": [{"value": "0.0.0.0/0"}]}}')

  def testPatchAuthorizedNetworksNoConfirmsCancel(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql instances patch custom-instance '
               '--authorized-networks=0.0.0.0/0')

  def testPatchAuthorizedNetworksBadCidr(self):
    self.WriteInput('n\n')
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                r'argument --authorized-networks: Bad value '
                                r'\[abc\]: Must be specified in CIDR '
                                r'notation'):
      self.Run('sql instances patch custom-instance '
               '--authorized-networks abc')

  def testAssignIp(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    diff = {
        'name': 'patch-instance3',
        'settings': {
            'ipConfiguration':
                self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=None,
                    requireSsl=None,)
        }
    }
    self.ExpectInstanceGet(self.GetV1Instance(), diff)
    diff.update({
        'settings': {
            'ipConfiguration':
                self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=True,
                    requireSsl=None,)
        }
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)

    self.Run('sql instances patch patch-instance3 --assign-ip')
    self.assertEqual(prompt_mock.call_count, 0)
    self.AssertErrContains('{"ipConfiguration": {"ipv4Enabled": true}}')

  def testPatchTierDiff(self):
    diff = {
        'name': 'mock-instance',
        'settings': {
            'tier': 'D1',
            'settingsVersion': 22
        }
    }
    self.ExpectInstanceGet(self.GetPatchRequestInstance(), diff)
    diff.update({'settings': {'tier': 'D0'}})
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()

    # Should look like the back-end has incremented the version number.
    diff['settings'].update({'settingsVersion': 23})
    self.ExpectInstanceGet(self.GetPatchRequestInstance(), diff)

    self.Run('sql instances patch mock-instance --tier=D0 --quiet --diff')
    self.AssertOutputContains(
        """\
-settings.settingsVersion: 22
-settings.tier: D1
+settings.settingsVersion: 23
+settings.tier: D0
""",
        normalize_space=True)

  def testPatchCustomMachineDiff(self):
    diff = {'name': 'custom-instance', 'settings': {'tier': 'db-custom-1-1024'}}
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)
    diff.update({'settings': {'tier': 'db-custom-3-3072'}})
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)

    self.Run('sql instances patch custom-instance --memory=3072MiB --cpu=3 '
             '--quiet --diff')
    self.AssertOutputContains(
        """\
-settings.tier:                                    db-custom-1-1024
+settings.tier:                                    db-custom-3-3072
""",
        normalize_space=True)

  def _ExpectDatabaseFlagsUpdate(self, instance):
    diff = {
        'name': 'custom-instance',
        'settings': {
            'databaseFlags': [
                self.messages.DatabaseFlags(
                    name='second',
                    value='2',
                ),
                self.messages.DatabaseFlags(
                    name='first',
                    value='one',
                ),
            ]
        }
    }
    self.ExpectInstanceGet(instance, diff)
    diff['settings'].update({
        'databaseFlags': [
            self.messages.DatabaseFlags(
                name='second',
                value='two',
            ),
            self.messages.DatabaseFlags(
                name='third',
                value='thr33',
            ),
        ]
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(instance, diff)
    self.Run('sql instances patch custom-instance '
             '--database-flags=second=two,third=thr33')

  def testUpdateMysqlDatabaseFlags(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self._ExpectDatabaseFlagsUpdate(self.GetV2Instance())

    prompt_mock.assert_called_with(
        'WARNING: This patch modifies database flag values, which may require '
        'your instance to be restarted. Check the list of supported flags - '
        'https://cloud.google.com/sql/docs/mysql/flags - to see if your '
        'instance will be restarted when this patch is submitted.')

  def testUpdatePostgresDatabaseFlags(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self._ExpectDatabaseFlagsUpdate(self.GetPostgresInstance())

    prompt_mock.assert_called_with(
        'WARNING: This patch modifies database flag values, which may require '
        'your instance to be restarted. Check the list of supported flags - '
        'https://cloud.google.com/sql/docs/postgres/flags - to see if your '
        'instance will be restarted when this patch is submitted.')

  def testUpdateSqlServerDatabaseFlags(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self._ExpectDatabaseFlagsUpdate(self.GetSqlServerInstance())

    prompt_mock.assert_called_with(
        'WARNING: This patch modifies database flag values, which may require '
        'your instance to be restarted. Check the list of supported flags - '
        'https://cloud.google.com/sql/docs/sqlserver/flags - to see if your '
        'instance will be restarted when this patch is submitted.')

  def _ExpectDatabaseFlagsClear(self, instance):
    diff = {
        'name': 'custom-instance',
        'settings': {
            'databaseFlags': [
                self.messages.DatabaseFlags(
                    name='first',
                    value='one',
                ),
                self.messages.DatabaseFlags(
                    name='second',
                    value='2',
                ),
            ]
        }
    }
    self.ExpectInstanceGet(instance, diff)
    diff['settings'].update({
        'databaseFlags': []
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(instance, diff)
    self.Run('sql instances patch custom-instance '
             '--clear-database-flags')

  def testClearMysqlDatabaseFlags(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self._ExpectDatabaseFlagsClear(self.GetV2Instance())

    prompt_mock.assert_called_with(
        'WARNING: This patch modifies database flag values, which may require '
        'your instance to be restarted. Check the list of supported flags - '
        'https://cloud.google.com/sql/docs/mysql/flags - to see if your '
        'instance will be restarted when this patch is submitted.')

  def testClearPostgresDatabaseFlags(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self._ExpectDatabaseFlagsClear(self.GetPostgresInstance())

    prompt_mock.assert_called_with(
        'WARNING: This patch modifies database flag values, which may require '
        'your instance to be restarted. Check the list of supported flags - '
        'https://cloud.google.com/sql/docs/postgres/flags - to see if your '
        'instance will be restarted when this patch is submitted.')

  def testClearSqlServerDatabaseFlags(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self._ExpectDatabaseFlagsClear(self.GetSqlServerInstance())

    prompt_mock.assert_called_with(
        'WARNING: This patch modifies database flag values, which may require '
        'your instance to be restarted. Check the list of supported flags - '
        'https://cloud.google.com/sql/docs/sqlserver/flags - to see if your '
        'instance will be restarted when this patch is submitted.')

  def testDisableBackup(self):
    diff = {
        'name': 'custom-instance',
        'settings': {
            'backupConfiguration':
                self.messages.BackupConfiguration(
                    binaryLogEnabled=True,
                    enabled=True,
                    kind='sql#backupConfiguration',
                    startTime='23:00',
                )
        }
    }
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    diff['settings'].update({
        'backupConfiguration':
            self.messages.BackupConfiguration(
                binaryLogEnabled=True,
                enabled=False,
                kind='sql#backupConfiguration',
                startTime='23:00',
            )
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances patch custom-instance --no-backup')

  def testConflictingBackupFlagsError(self):
    diff = {
        'name': 'custom-instance'
    }
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    with self.assertRaises(exceptions.ToolException):
      self.Run('sql instances patch custom-instance --no-backup '
               '--enable-bin-log')

  def testPatchRemoveHighAvailability(self):
    instance_name = 'custom-instance'
    diff = {
        'name': instance_name,
        'databaseVersion': 'POSTGRES_9_6',
        'settings': {
            'availabilityType': 'REGIONAL',
            'tier': 'db-custom-1-1024'
        }
    }
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)
    update_diff = {
        'name': instance_name,
        'settings': {
            'availabilityType': 'ZONAL'
        }
    }
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), update_diff)
    self.ExpectDoneUpdateOperationGet()
    diff['settings'].update(update_diff['settings'])
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)

    self.Run('sql instances patch custom-instance --availability-type=ZONAL '
             '--quiet --diff')
    self.AssertOutputContains(
        """\
-settings.availabilityType: REGIONAL
+settings.availabilityType: ZONAL
""",
        normalize_space=True)


class InstancesPatchGATest(_BaseInstancePatchTest, base.SqlMockTestGA):
  pass


class _BaseInstancePatchBetaTest(_BaseInstancePatchTest):

  def testSetAutoIncreaseLimitToUnlimited(self):
    diff = {
        'name': 'custom-instance',
        'settings': {
            'storageAutoResize': True,
            'storageAutoResizeLimit': 1000
        }
    }
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)
    diff.update({
        'settings': {
            'storageAutoResize': None,
            'storageAutoResizeLimit': 0
        }
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)

    self.Run('sql instances patch custom-instance '
             '--storage-auto-increase-limit=unlimited')

  def testUpdateWithStorageAutoIncreaseLimitWithIncreaseEnabled(self):
    diff = {
        'name': 'custom-instance',
        'settings': {
            'storageAutoResize': True,
        }
    }
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)
    diff.update({
        'settings': {
            'storageAutoResize': None,
            'storageAutoResizeLimit': 100
        }
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    diff['settings'].update({'storageAutoResize': True})
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)

    self.Run('sql instances patch custom-instance '
             '--storage-auto-increase-limit=100')

  def testUpdateWithStorageAutoIncreaseLimitWithIncreaseNotEnabled(self):
    self.ExpectInstanceGet(self.GetPostgresInstance(), {
        'name': 'custom-instance',
        'settings': {
            'storageAutoResize': None
        }
    })

    with self.AssertRaisesExceptionRegexp(exceptions.RequiredArgumentException,
                                          r'Missing required argument '
                                          r'\[--storage-auto-increase\]'):
      self.Run('sql instances patch custom-instance '
               '--storage-auto-increase-limit=100')

  def testUpdateLabelsPatch(self):
    diff = {
        'name': 'custom-instance',
        'settings': {
            'userLabels':
                self.messages.Settings.UserLabelsValue(
                    additionalProperties=[
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='bar',
                            value='something',),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='foo',
                            value='two',),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='test',
                            value='again',),
                    ],)
        }
    }
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)
    diff.update({
        'settings': {
            'userLabels':
                self.messages.Settings.UserLabelsValue(
                    additionalProperties=[
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='bar',
                            value='value',),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='baz',
                            value='qux',),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='foo',
                            value=None,),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='test',
                            value='again',),
                    ],)
        }
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)

    self.Run('sql instances patch custom-instance '
             '--update-labels=bar=value,baz=qux --remove-labels=foo')

  def testClearLabelsPatch(self):
    diff = {
        'name': 'custom-instance',
        'settings': {
            'userLabels':
                self.messages.Settings.UserLabelsValue(
                    additionalProperties=[
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='bar',
                            value='something',),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='foo',
                            value='two',),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='test',
                            value='again',),
                    ],)
        }
    }
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)
    diff.update({
        'settings': {
            'userLabels':
                self.messages.Settings.UserLabelsValue(
                    additionalProperties=[
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='bar',
                            value=None,),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='foo',
                            value=None,),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='test',
                            value=None,),
                    ],)
        }
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)
    self.Run('sql instances patch custom-instance --clear-labels')

  def testClearAndUpdateLabelsPatch(self):
    diff = {
        'name': 'custom-instance',
        'settings': {
            'userLabels':
                self.messages.Settings.UserLabelsValue(
                    additionalProperties=[
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='bar',
                            value='something',),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='foo',
                            value='two',),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='test',
                            value='again',),
                    ],)
        }
    }
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)
    diff.update({
        'settings': {
            'userLabels':
                self.messages.Settings.UserLabelsValue(
                    additionalProperties=[
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='bar',
                            value=None,),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='foo',
                            value='bar',),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='test',
                            value=None,),
                    ],)
        }
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)
    self.Run('sql instances patch custom-instance --clear-labels '
             '--update-labels foo=bar')

  def testBadLabelsFlags(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('sql instances patch custom-instance '
               '--remove-labels=foo --clear-labels')

  def testAddPrivateNetwork(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    diff = {
        'name': 'patch-instance3',
        'settings': {
            'ipConfiguration':
                self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=False,
                    requireSsl=False,
                    privateNetwork=None)
        }
    }
    self.ExpectInstanceGet(self.GetV1Instance(), diff)
    diff.update({
        'settings': {
            'ipConfiguration':
                self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=None,
                    requireSsl=None,
                    privateNetwork=('https://compute.googleapis.com/compute/v1/'
                                    'projects/fake-project/global/networks/'
                                    'somenetwork'))
        }
    })
    self.ExpectInstancePatch(self.GetPatchRequestInstance(), diff)
    self.ExpectDoneUpdateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)

    self.Run('sql instances patch patch-instance3 --quiet '
             '--network=somenetwork --diff')
    self.assertEqual(prompt_mock.call_count, 0)
    self.AssertErrContains(
        '{"ipConfiguration": {"privateNetwork": "https://compute.googleapis.com/'
        'compute/v1/projects/fake-project/global/networks/somenetwork"}}')


class InstancesPatchBetaTest(_BaseInstancePatchBetaTest, base.SqlMockTestBeta):
  pass


class InstancesPatchAlphaTest(_BaseInstancePatchBetaTest,
                              base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
