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
import getpass

from googlecloudsdk.api_lib.sql import exceptions as sql_exceptions
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.sql import base


# TODO(b/73729091): Update naming conventions for clarity.
class _BaseInstancesCreateTest(object):
  # pylint:disable=g-tzinfo-datetime

  def testSimpleCreate(self):
    diff = {
        'name': 'create-instance1',
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create create-instance1')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-instance1 MYSQL_5_7        us-central db-n1-standard-1 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  # LINT.IfChange(version_tests)
  def testCreateMySql56(self):
    diff = {
        'name':
            'instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_6,
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance1 --database-version=MYSQL_5_6')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance1 MYSQL_5_6        us-central db-n1-standard-1 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreateMySql57(self):
    diff = {
        'name':
            'instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance1 --database-version=MYSQL_5_7')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance1 MYSQL_5_7        us-central db-n1-standard-1 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreatePostgres96(self):
    diff = {
        'name':
            'instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .POSTGRES_9_6,
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance1 --database-version=POSTGRES_9_6')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance1 POSTGRES_9_6      us-central db-n1-standard-1 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreatePostgres10(self):
    diff = {
        'name':
            'instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .POSTGRES_10,
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance1 --database-version=POSTGRES_10')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance1 POSTGRES_10      us-central db-n1-standard-1 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreatePostgres11(self):
    diff = {
        'name':
            'instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .POSTGRES_11,
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance1 --database-version=POSTGRES_11')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance1 POSTGRES_11      us-central db-n1-standard-1 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreatePostgres12(self):
    diff = {
        'name':
            'instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .POSTGRES_12,
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance1 --database-version=POSTGRES_12')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance1 POSTGRES_12      us-central db-n1-standard-1 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreateSqlServer2017Express(self):
    diff = {
        'name':
            'instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .SQLSERVER_2017_EXPRESS,
        'rootPassword':
            'password',
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance1 '
             '--database-version=SQLSERVER_2017_EXPRESS '
             '--root-password=password')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance1 SQLSERVER_2017_EXPRESS   us-central db-n1-standard-1 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreateSqlServer2017Web(self):
    diff = {
        'name':
            'instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .SQLSERVER_2017_WEB,
        'rootPassword':
            'password',
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance1 '
             '--database-version=SQLSERVER_2017_WEB '
             '--root-password=password')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance1 SQLSERVER_2017_WEB   us-central db-n1-standard-1 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreateSqlServer2017Standard(self):
    diff = {
        'name':
            'instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .SQLSERVER_2017_STANDARD,
        'rootPassword':
            'password',
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance1 '
             '--database-version=SQLSERVER_2017_STANDARD '
             '--root-password=password')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance1 SQLSERVER_2017_STANDARD   us-central db-n1-standard-1 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreateSqlServer2017Enterprise(self):
    diff = {
        'name':
            'instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .SQLSERVER_2017_ENTERPRISE,
        'rootPassword':
            'password',
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance1 '
             '--database-version=SQLSERVER_2017_ENTERPRISE '
             '--root-password=password')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance1 SQLSERVER_2017_ENTERPRISE   us-central db-n1-standard-1 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)
  # LINT.ThenChange(:ga_version_test)

  def testCreateActivationPolicy(self):
    diff = {
        'name': 'create-instance1',
        'settings': {
            'tier':
                'db-n1-standard-1',
            'activationPolicy':
                self.messages.Settings.ActivationPolicyValueValuesEnum.ON_DEMAND
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create create-instance1 --activation-policy '
             'ON_DEMAND --tier=db-n1-standard-1')
    self.AssertOutputContains(
        """\
NAME DATABASE_VERSION LOCATION TIER PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-instance1 MYSQL_5_7 us-central db-n1-standard-1 0.0.0.0 - RUNNABLE
""",
        normalize_space=True)

  def testSimpleAsyncCreate(self):
    diff = {
        'name': 'create-instance1',
        'settings': {
            'tier': 'db-n1-standard-1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.Run('sql instances create create-instance1 --async '
             '--tier=db-n1-standard-1')
    self.AssertOutputContains("""\
endTime: '2014-08-12T19:39:26.601000+00:00'
insertTime: '2014-08-12T19:38:39.415000+00:00'
kind: sql#operation
name: 344acb84-0000-1111-2222-1e71c6077b34
operationType: CREATE
selfLink: https://sqladmin.googleapis.com/sql/v1beta4/projects/fake-project/operations/sample
startTime: '2014-08-12T19:38:39.525000+00:00'
status: DONE
targetId: create-instance1
targetLink: https://sqladmin.googleapis.com/sql/v1beta4/projects/fake-project
targetProject: fake-project
user: test@sample.gserviceaccount.com
""")

  def testProjectInstance(self):
    with self.AssertRaisesToolExceptionRegexp(
        "Instance names cannot contain the ':' character. If you meant to "
        'indicate the\nproject for \\[create-instance1\\], use only '
        "'create-instance1' for the argument, and either add\n"
        "'--project myproject' to the command line or first run\n"
        '  \\$ gcloud config set project myproject'):
      self.Run('sql instances create myproject:create-instance1')

  def testCreateBinLog(self):
    diff = {
        'name': 'clone-instance-7',
        'settings': {
            'backupConfiguration':
                self.messages.BackupConfiguration(
                    binaryLogEnabled=True,
                    enabled=True,
                    kind='sql#backupConfiguration',
                    startTime='23:00',
                ),
            'tier':
                'db-n1-standard-1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create clone-instance-7 --enable-bin-log '
             '--backup-start-time=23:00 --tier=db-n1-standard-1')
    self.AssertOutputContains(
        """\
NAME DATABASE_VERSION LOCATION TIER PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
clone-instance-7 MYSQL_5_7 us-central db-n1-standard-1 0.0.0.0 - RUNNABLE
""",
        normalize_space=True)

  def testCreateBinLogWithBackupFlagNoStartTime(self):
    diff = {
        'name': 'clone-instance-7',
        'settings': {
            'backupConfiguration':
                self.messages.BackupConfiguration(
                    binaryLogEnabled=True,
                    enabled=True,
                    kind='sql#backupConfiguration',
                    startTime='00:00',
                ),
            'tier':
                'db-n1-standard-1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create clone-instance-7 --enable-bin-log '
             '--backup --tier=db-n1-standard-1')
    self.AssertOutputContains(
        """\
NAME DATABASE_VERSION LOCATION TIER PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
clone-instance-7 MYSQL_5_7 us-central db-n1-standard-1 0.0.0.0 - RUNNABLE
""",
        normalize_space=True)

  def testCreateNoBackup(self):
    diff = {
        'name': 'backupless-instance1',
        'settings': {
            'backupConfiguration':
                self.messages.BackupConfiguration(
                    binaryLogEnabled=None,
                    enabled=False,
                    kind='sql#backupConfiguration',
                    startTime='00:00',
                ),
            'tier':
                'db-n1-standard-1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)

    self.Run('sql instances create backupless-instance1 --no-backup '
             '--tier=db-n1-standard-1')
    self.AssertOutputContains(
        """\
NAME DATABASE_VERSION LOCATION TIER PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
backupless-instance1 MYSQL_5_7 us-central db-n1-standard-1 0.0.0.0 - RUNNABLE
""",
        normalize_space=True)

  def testCreateBackupStartTime(self):
    diff = {
        'name': 'instance-1',
        'settings': {
            'backupConfiguration':
                self.messages.BackupConfiguration(
                    kind='sql#backupConfiguration',
                    enabled=True,
                    startTime='23:00',
                ),
        },
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance-1 --backup-start-time=23:00')
    self.AssertOutputContains(
        """\
NAME DATABASE_VERSION LOCATION TIER PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance-1 MYSQL_5_7 us-central db-n1-standard-1 0.0.0.0 - RUNNABLE
""",
        normalize_space=True)

  def testCreateBackupLocation(self):
    diff = {
        'name': 'instance-1',
        'settings': {
            'backupConfiguration':
                self.messages.BackupConfiguration(
                    kind='sql#backupConfiguration',
                    enabled=True,
                    location='us',
                    startTime='00:00',
                ),
        },
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance-1 --backup-location=us')
    self.AssertOutputContains(
        """\
NAME DATABASE_VERSION LOCATION TIER PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance-1 MYSQL_5_7 us-central db-n1-standard-1 0.0.0.0 - RUNNABLE
""",
        normalize_space=True)

  def testCreateBackupSettings(self):
    diff = {
        'name': 'instance-1',
        'settings': {
            'backupConfiguration':
                self.messages.BackupConfiguration(
                    kind='sql#backupConfiguration',
                    enabled=True,
                    location='us',
                    startTime='23:00',
                ),
        },
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create instance-1 --backup-start-time=23:00 '
             '--backup-location=us')
    self.AssertOutputContains(
        """\
NAME DATABASE_VERSION LOCATION TIER PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
instance-1 MYSQL_5_7 us-central db-n1-standard-1 0.0.0.0 - RUNNABLE
""",
        normalize_space=True)

  def testCreateReadReplica(self):
    # This test ensures that the replica adopts the db version, tier, and
    # region from the main to the replica without being specified.

    main_diff = {
        'name':
            'create-instance1',
        'settings': {
            'tier':
                'db-n1-standard-2',
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
    }
    replica_diff = {
        'name':
            'create-replica1',
        'settings': {
            'tier':
                'db-n1-standard-2',
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
        'mainInstanceName':
            'create-instance1'
    }
    self.ExpectInstanceGet(self.GetV2Instance(), main_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)

    self.Run('sql instances create create-replica1 --main-instance-name '
             'create-instance1')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION  LOCATION TIER              PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-replica1  MYSQL_5_7         us-west1 db-n1-standard-2  0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)
    # Ensure that the CMEK messaging doesn't show up by default.
    self.AssertErrNotContains('customer-managed encryption key')

  def testCreateCrossRegionReplica(self):
    # This test ensures that the replica adopts the db version, tier gets
    # automatically copied from the main to the replica without being
    # specified, but that region is overriden.

    main_diff = {
        'name': 'create-instance1',
        'settings': {
            'tier': 'db-n1-standard-2',
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region': 'us-west1',
    }
    replica_diff = {
        'name': 'create-replica1',
        'settings': {
            'tier': 'db-n1-standard-2',
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region': 'us-east1',
        'mainInstanceName': 'create-instance1',
    }
    self.ExpectInstanceGet(self.GetV2Instance(), main_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)

    self.Run('sql instances create create-replica1 --main-instance-name '
             'create-instance1 --region=us-east1')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION  LOCATION TIER              PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-replica1  MYSQL_5_7         us-east1 db-n1-standard-2  0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)
    # Ensure that the CMEK messaging doesn't show up by default.
    self.AssertErrNotContains('customer-managed encryption key')

  def testCreateReadReplicaV1(self):
    # This test ensures that the creating a V1 read replica fails now that
    # they've been deprecated.

    self.ExpectInstanceGet(self.GetV1Instance('create-instance1'))
    with self.AssertRaisesExceptionRegexp(
        sql_exceptions.ArgumentError,
        r'First Generation instances can no longer be created\.'):
      self.Run('sql instances create create-replica1 --main-instance-name '
               'create-instance1')

  def testCreateReadReplicaOverridingTier(self):
    # This test ensures that the user is able to specify a tier different than
    # the tier of the main.

    main_diff = {
        'name':
            'create-instance1',
        'settings': {
            'tier':
                'db-n1-standard-2',
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
    }
    replica_diff = {
        'name':
            'create-replica1',
        'settings': {
            'tier':
                'db-n1-standard-4',
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
        'mainInstanceName':
            'create-instance1',
    }
    self.ExpectInstanceGet(self.GetV2Instance(), main_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)

    self.Run('sql instances create create-replica1 --main-instance-name '
             'create-instance1 --tier=db-n1-standard-4')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION  LOCATION TIER              PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-replica1  MYSQL_5_7         us-west1 db-n1-standard-4  0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreateReadReplicaOverridingCustomMachineType(self):
    # This test ensures that the user is able to specify a custom machine type
    # different than the custom machine type of the main.

    main_diff = {
        'name':
            'create-instance1',
        'settings': {
            'tier':
                'db-custom-1-4096',
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .POSTGRES_9_6,
        'region':
            'us-west1',
    }
    replica_diff = {
        'name':
            'create-replica1',
        'settings': {
            'tier':
                'db-custom-2-7680',
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .POSTGRES_9_6,
        'region':
            'us-west1',
        'mainInstanceName':
            'create-instance1',
    }
    self.ExpectInstanceGet(self.GetV2Instance(), main_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)

    self.Run('sql instances create create-replica1 --main-instance-name '
             'create-instance1  --cpu=2 --memory=7680MiB')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION  LOCATION TIER              PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-replica1  POSTGRES_9_6      us-west1 db-custom-2-7680  0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreateReadReplicaWithCmek(self):
    # This test ensures that a warning shows up when a replica of a instance
    # with a customer-managed encryption key is being created.
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)

    main_diff = {
        'name':
            'create-instance1',
        'diskEncryptionConfiguration':
            self.messages.DiskEncryptionConfiguration(
                kind='sql#diskEncryptionConfiguration', kmsKeyName='some-key'),
        'settings': {
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
    }
    replica_diff = {
        'name':
            'create-replica1',
        'settings': {
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'mainInstanceName':
            'create-instance1'
    }
    self.ExpectInstanceGet(self.GetV2Instance(), main_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)

    self.Run('sql instances create create-replica1 --main-instance-name '
             'create-instance1')
    # Check that the CMEK warning was displayed.
    self.assertEqual(prompt_mock.call_count, 0)
    self.AssertErrContains(
        'Your replica will be encrypted with the main instance\'s '
        'customer-managed encryption key. If anyone destroys this key, all '
        'data encrypted with it will be permanently lost.')

  def testCreateCrossRegionReplicaWithCmek(self):
    # This test ensures that the create warning shows up when a replica of an
    # instance with a customer-managed encryption key is being created,
    # instead of the message indicating that the key will be inherited from
    # the main instance.
    key = 'projects/example/locations/us-east1/keyRings/somekey/cryptoKeys/a'
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)

    main_diff = {
        'name': 'create-instance1',
        'diskEncryptionConfiguration':
            self.messages.DiskEncryptionConfiguration(
                kind='sql#diskEncryptionConfiguration', kmsKeyName='some-key'),
        'settings': {
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
    }
    replica_diff = {
        'name': 'create-replica1',
        'region': 'us-east1',
        'diskEncryptionConfiguration':
            self.messages.DiskEncryptionConfiguration(
                kind='sql#diskEncryptionConfiguration', kmsKeyName=key),
        'settings': {
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'mainInstanceName': 'create-instance1',
    }
    self.ExpectInstanceGet(self.GetV2Instance(), main_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)

    self.Run(
        'sql instances create create-replica1 --main-instance-name '
        'create-instance1 --region us-east1 --disk-encryption-key="{}"'.format(
            key))
    # Check that the CMEK warning was displayed.
    self.assertEqual(prompt_mock.call_count, 0)
    self.AssertErrContains(
        'Your replica will be encrypted with a customer-managed key. If anyone '
        'destroys this key, all data encrypted with it will be permanently '
        'lost.')

  def testCreateCrossRegionReplicaMissingCmek(self):
    # This test ensures that the a disk encryption key has been provided when
    # creating a cross-region replica of a CMEK instance.
    main_diff = {
        'name': 'create-instance1',
        'diskEncryptionConfiguration':
            self.messages.DiskEncryptionConfiguration(
                kind='sql#diskEncryptionConfiguration', kmsKeyName='some-key'),
        'settings': {
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
    }
    self.ExpectInstanceGet(self.GetV2Instance(), main_diff)
    with self.AssertRaisesExceptionRegexp(exceptions.RequiredArgumentException,
                                          r'Missing required argument '
                                          r'\[--disk-encryption-key\]'):
      self.Run(
          'sql instances create create-replica1 --main-instance-name '
          'create-instance1 --region us-east1')

  def testCreateCrossRegionReplicaExtraneousCmek(self):
    # This test ensures that the a disk encryption key has not been provided
    # when creating a cross-region replica of a non-CMEK instance.
    key = 'projects/example/locations/us-east1/keyRings/somekey/cryptoKeys/a'
    main_diff = {
        'name':
            'create-instance1',
        'settings': {
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
    }
    self.ExpectInstanceGet(self.GetV2Instance(), main_diff)
    with self.AssertRaisesExceptionRegexp(
        sql_exceptions.ArgumentError,
        r'`--disk-encryption-key` cannot be specified when creating a replica '
        'of an instance without customer-managed encryption.'):
      self.Run('sql instances create create-replica1 --main-instance-name '
               'create-instance1 --region us-east1 --disk-encryption-key="{}"'
               .format(key))

  def testCreateNoMain(self):
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='main-name',
            project=self.Project(),),
        exception=http_error.MakeHttpError(
            code=409,
            reason='notAuthorized',))

    with self.AssertRaisesHttpExceptionRegexp(r'You are either not authorized '
                                              'to access the main instance or'
                                              ' it does not exist.'):
      self.Run('sql instances create replica-name --main-instance-name='
               'main-name')

  def testCreateSecondGenFlags(self):
    diff = {
        'name': 'create-secondgen1',
        'settings': {
            'dataDiskSizeGb':
                15,
            'maintenanceWindow':
                self.messages.MaintenanceWindow(
                    day=1,
                    hour=5,
                    updateTrack=self.messages.MaintenanceWindow
                    .UpdateTrackValueValuesEnum.canary,
                    kind='sql#maintenanceWindow'),
            'tier':
                'db-n1-standard-1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create create-secondgen1 --storage-size 15gb '
             '--maintenance-window-day MON --maintenance-window-hour 5 '
             '--maintenance-release-channel preview --tier=db-n1-standard-1')

  def testMaintenanceWindowRequirements(self):
    with self.assertRaises(argparse.ArgumentError):
      self.Run('sql instances create create-badargs1 --maintenance-window-day '
               'FRI')

  def testCreate_AuthorizedNetworks(self):
    diff = {
        'name': 'create-instance1',
        'settings': {
            'ipConfiguration':
                self.messages.IpConfiguration(
                    authorizedNetworks=[
                        self.messages.AclEntry(
                            kind='sql#aclEntry', value='10.10.10.1/16')
                    ],
                    ipv4Enabled=None,
                    requireSsl=None),
            'tier':
                'db-n1-standard-1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)

    self.Run('sql instances create create-instance1 '
             '--authorized-networks=10.10.10.1/16 --tier=db-n1-standard-1')
    self.AssertOutputContains(
        """\
NAME DATABASE_VERSION LOCATION TIER PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-instance1 MYSQL_5_7 us-central db-n1-standard-1 0.0.0.0 - RUNNABLE
""",
        normalize_space=True)

  def testCreateCustomMachine(self):
    diff = {
        'name':
            'custom-instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .POSTGRES_9_6,
        'settings': {
            'tier': 'db-custom-1-1024'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)
    self.Run('sql instances create custom-instance1 '
             '--database-version=POSTGRES_9_6 --memory=1024MiB --cpu=1')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
custom-instance1 POSTGRES_9_6     us-central db-custom-1-1024 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreateOverInstanceLimit(self):
    msg = ('Failed to create instance because the project or creator has '
           'reached the max instance per project/creator limit.')

    self.mocked_client.instances.Insert.Expect(
        self.messages.DatabaseInstance(
            currentDiskSize=None,
            databaseVersion=None,
            etag=None,
            name='create-instance1',
            ipAddresses=[],
            kind='sql#instance',
            maxDiskSize=None,
            project=self.Project(),
            region='us-central',
            serverCaCert=None,
            settings=self.messages.Settings(
                activationPolicy=None,
                authorizedGaeApplications=[],
                backupConfiguration=None,
                databaseFlags=[],
                ipConfiguration=None,
                kind='sql#settings',
                locationPreference=None,
                pricingPlan=self.messages.Settings.PricingPlanValueValuesEnum
                .PER_USE,
                replicationType=self.messages.Settings
                .ReplicationTypeValueValuesEnum.SYNCHRONOUS,
                settingsVersion=None,
                tier='db-n1-standard-1',
            ),
            state=None,
        ),
        exception=http_error.MakeHttpError(
            code=409,
            message=msg,
            reason='errorMaxInstancePerLabel',
        ))

    with self.AssertRaisesHttpExceptionRegexp(r'Failed to create instance '
                                              'because the project or creator '
                                              'has reached the max instance '
                                              'per project/creator limit.'):
      self.Run('sql instances create create-instance1 --tier=db-n1-standard-1')

    self.AssertErrNotContains('already exists')

  def testInvalidInstanceName(self):
    with self.AssertRaisesArgumentErrorRegexp('Bad value'):
      self.Run('sql instances create 1invalidINSTANCE')

  def testCreateWithTier(self):
    diff = {
        'name': 'tiered-instance',
        'settings': {
            'tier': 'db-n1-standard-2'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)

    self.Run('sql instances create tiered-instance --tier db-n1-standard-2')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME            DATABASE_VERSION LOCATION   TIER             PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
tiered-instance MYSQL_5_7        us-central db-n1-standard-2 0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreateWithRegion(self):
    updated_fields = {'name': 'created-instance', 'region': 'europe-west1'}
    self.ExpectInstanceInsert(self.GetRequestInstance(), updated_fields)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), updated_fields)
    self.Run('sql instances create created-instance --region europe-west1')

    # Ensure that no zone warning is shown for misuse of region and zone flags.
    self.AssertErrNotContains('WARNING')

  def testCreateWithZone(self):
    updated_fields = {
        'name': 'created-instance',
        'region': 'europe-west1',
        'settings': {
            'locationPreference':
                self.messages.LocationPreference(
                    kind='sql#locationPreference', zone='europe-west1-b')
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), updated_fields)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), updated_fields)
    self.Run('sql instances create created-instance --zone europe-west1-b')

    # Ensure that a warning is not shown for use of `--zone` over `--gce-zone`.
    self.AssertErrNotContains('WARNING')

  def testCreateWithDeprecatedGceZone(self):
    updated_fields = {
        'name': 'created-instance',
        'region': 'europe-west1',
        'settings': {
            'locationPreference':
                self.messages.LocationPreference(
                    kind='sql#locationPreference', zone='europe-west1-b')
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), updated_fields)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), updated_fields)
    self.Run('sql instances create created-instance --gce-zone europe-west1-b')

    # Ensure that a warning is shown for use of `--gce-zone`.
    self.AssertErrContains(
        'WARNING: Flag `--gce-zone` is deprecated and will be removed by '
        'release 255.0.0. Use `--zone` instead.')

  def testCreateWithoutLocationWarning(self):
    # Check for a warning when neither --region nor --gce-zone are used.
    updated_fields = {'name': 'created-instance'}
    self.ExpectInstanceInsert(self.GetRequestInstance(), updated_fields)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), updated_fields)
    self.Run('sql instances create created-instance')
    self.AssertErrContains('you will need to specify either a region or a zone')

  def testCreateHighAvailabilityInstance(self):
    diff = {
        'name':
            'custom-instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .POSTGRES_9_6,
        'settings': {
            'availabilityType':
                self.messages.Settings.AvailabilityTypeValueValuesEnum.REGIONAL,
            'tier':
                'db-custom-1-1024'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)

    self.Run('sql instances create custom-instance1 '
             '--database-version=POSTGRES_9_6 --memory=1024MiB --cpu=1 '
             '--availability-type=REGIONAL')

  def testCreateV1Exception(self):
    with self.AssertRaisesExceptionRegexp(
        sql_exceptions.ArgumentError,
        r'First Generation instances can no longer be created\.'):
      self.Run('sql instances create create-instance1 --tier=D1')

  def testCreateWithRootPassword(self):
    diff = {
        'name': 'some-instance',
        'rootPassword': 'somepassword'
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetExternalMainInstance(), diff)
    self.Run('sql instances create some-instance --root-password=somepassword')

  def testCreateSqlServerWithoutRootPassword(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException, r'Missing required argument '
        r'\[--root-password\]'):
      self.Run('sql instances create some-instance '
               '--database-version=SQLSERVER_2017_STANDARD')


class InstancesCreateGATest(_BaseInstancesCreateTest, base.SqlMockTestGA):

  # LINT.IfChange(ga_version_test)
  def testCreateUnknownVersion(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('sql instances create instance1 --database-version=UNKNOWN')
    self.AssertErrContains(
        "argument --database-version: Invalid choice: 'UNKNOWN'.")
    self.AssertErrContains(
        'Valid choices are [MYSQL_5_5, MYSQL_5_6, MYSQL_5_7, POSTGRES_10, '
        'POSTGRES_11, POSTGRES_12, POSTGRES_9_6, SQLSERVER_2017_ENTERPRISE, '
        'SQLSERVER_2017_EXPRESS, SQLSERVER_2017_STANDARD, SQLSERVER_2017_WEB].')
  # LINT.ThenChange(:version_tests)


class _BaseInstancesCreateBetaTest(_BaseInstancesCreateTest):

  def testCreateWithLabels(self):
    diff = {
        'name': 'tiered-instance',
        'settings': {
            'userLabels': self.messages.Settings.UserLabelsValue(
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
                        value='bar',),
                ],),
            'tier': 'db-n1-standard-2'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)

    self.Run('sql instances create tiered-instance '
             '--labels bar=value,baz=qux,foo=bar --tier db-n1-standard-2')

  def testCreateWithStorageAutoIncreaseLimitWithIncreaseEnabled(self):
    diff = {
        'name': 'tiered-instance',
        'settings': {
            'storageAutoResize': True,
            'storageAutoResizeLimit': 100,
            'tier': 'db-n1-standard-2'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)

    self.Run('sql instances create tiered-instance '
             '--storage-auto-increase-limit=100 --storage-auto-increase '
             '--tier db-n1-standard-2')

  def testCreateWithStorageAutoIncreaseLimitWithIncreaseNotEnabled(self):
    with self.AssertRaisesExceptionRegexp(exceptions.RequiredArgumentException,
                                          r'Missing required argument '
                                          r'\[--storage-auto-increase\]'):
      self.Run('sql instances create tiered-instance '
               '--storage-auto-increase-limit=100 --tier db-n1-standard-2')

  def testCreateWithDatabaseFlags(self):
    diff = {
        'name': 'create-instance',
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
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create create-instance '
             '--database-flags first=one,second=2')

  def testCreateExternalMainWithDefaultPort(self):
    diff = {
        'name':
            'xm-instance',
        'onPremisesConfiguration':
            self.messages.OnPremisesConfiguration(
                kind='sql#onPremisesConfiguration', hostPort='127.0.0.1:3306')
    }
    self.ExpectInstanceInsert(self.GetExternalMainRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetExternalMainInstance(), diff)
    self.Run('sql instances create xm-instance '
             '--source-ip-address=127.0.0.1')

  def testCreateExternalMainWithCustomPort(self):
    diff = {
        'name':
            'xm-instance',
        'onPremisesConfiguration':
            self.messages.OnPremisesConfiguration(
                kind='sql#onPremisesConfiguration', hostPort='127.0.0.1:8080')
    }
    self.ExpectInstanceInsert(self.GetExternalMainRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetExternalMainInstance(), diff)
    self.Run('sql instances create xm-instance '
             '--source-ip-address=127.0.0.1 --source-port=8080')

  def testCreateExternalMainReplicaWithoutSSL(self):
    main_diff = {
        'name':
            'xm-instance',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
    }
    replica_diff = {
        'name':
            'xm-instance-replica',
        'settings': {
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
        'mainInstanceName':
            'xm-instance',
        'replicaConfiguration':
            self.messages.ReplicaConfiguration(
                kind='sql#demoteMainMysqlReplicaConfiguration',
                mysqlReplicaConfiguration=self.messages
                .MySqlReplicaConfiguration(
                    kind='sql#mysqlReplicaConfiguration',
                    username='root',
                    password='somepword',
                    dumpFilePath='gs://xm-bucket/dumpfile.sql'))
    }
    self.ExpectInstanceGet(self.GetExternalMainInstance(), main_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)
    self.Run('sql instances create xm-instance-replica '
             '--main-username=root --main-password=somepword '
             '--main-dump-file-path=gs://xm-bucket/dumpfile.sql '
             '--main-instance-name=xm-instance')

  def testCreateExternalMainReplicaWithPasswordPrompt(self):
    # The password prompt flag should cause getpass to get called.
    self.StartObjectPatch(getpass, 'getpass', return_value='somepword')
    main_diff = {
        'name':
            'xm-instance',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
    }
    replica_diff = {
        'name':
            'xm-instance-replica',
        'settings': {
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
        'mainInstanceName':
            'xm-instance',
        'replicaConfiguration':
            self.messages.ReplicaConfiguration(
                kind='sql#demoteMainMysqlReplicaConfiguration',
                mysqlReplicaConfiguration=self.messages
                .MySqlReplicaConfiguration(
                    kind='sql#mysqlReplicaConfiguration',
                    username='root',
                    password='somepword',
                    dumpFilePath='gs://xm-bucket/dumpfile.sql'))
    }
    self.ExpectInstanceGet(self.GetExternalMainInstance(), main_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)
    self.Run('sql instances create xm-instance-replica '
             '--main-username=root --prompt-for-main-password '
             '--main-dump-file-path=gs://xm-bucket/dumpfile.sql '
             '--main-instance-name=xm-instance')

  def testCreateExternalMainReplicaWithCACert(self):
    # Need file read mock to get cert file contents.
    read_file_mock = self.StartObjectPatch(
        files, 'ReadFileContents', return_value='file_data')
    main_diff = {
        'name':
            'xm-instance',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
    }
    replica_diff = {
        'name':
            'xm-instance-replica',
        'settings': {
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
        'mainInstanceName':
            'xm-instance',
        'replicaConfiguration':
            self.messages.ReplicaConfiguration(
                kind='sql#demoteMainMysqlReplicaConfiguration',
                mysqlReplicaConfiguration=self.messages
                .MySqlReplicaConfiguration(
                    kind='sql#mysqlReplicaConfiguration',
                    username='root',
                    password='somepword',
                    dumpFilePath='gs://xm-bucket/dumpfile.sql',
                    caCertificate='file_data'))
    }
    self.ExpectInstanceGet(self.GetExternalMainInstance(), main_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)
    self.Run('sql instances create xm-instance-replica '
             '--main-username=root --main-password=somepword '
             '--main-dump-file-path=gs://xm-bucket/dumpfile.sql '
             '--main-instance-name=xm-instance '
             '--main-ca-certificate-path=/path/to/ca_cert.pem')

    # File contents should be read once, for the CA Cert
    # (plus one for the properties framework).
    self.assertEqual(read_file_mock.call_count, 2)

  def testCreateExternalMainWithCAAndClientCerts(self):
    # Need file read mock to get cert file contents.
    read_file_mock = self.StartObjectPatch(
        files, 'ReadFileContents', return_value='file_data')
    main_diff = {
        'name':
            'xm-instance',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
    }
    replica_diff = {
        'name':
            'xm-instance-replica',
        'settings': {
            'replicationType':
                self.messages.Settings.ReplicationTypeValueValuesEnum
                .ASYNCHRONOUS,
        },
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
        'mainInstanceName':
            'xm-instance',
        'replicaConfiguration':
            self.messages.ReplicaConfiguration(
                kind='sql#demoteMainMysqlReplicaConfiguration',
                mysqlReplicaConfiguration=self.messages
                .MySqlReplicaConfiguration(
                    kind='sql#mysqlReplicaConfiguration',
                    username='root',
                    password='somepword',
                    dumpFilePath='gs://xm-bucket/dumpfile.sql',
                    caCertificate='file_data',
                    clientCertificate='file_data',
                    clientKey='file_data'))
    }
    self.ExpectInstanceGet(self.GetExternalMainInstance(), main_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)
    self.Run('sql instances create xm-instance-replica '
             '--main-username=root --main-password=somepword '
             '--main-dump-file-path=gs://xm-bucket/dumpfile.sql '
             '--main-instance-name=xm-instance '
             '--client-certificate-path=/path/to/client_cert.pem '
             '--client-key-path=/path/to/client_key.pem '
             '--main-ca-certificate-path=/path/to/ca_cert.pem')

    # File contents should be read three times, one for each cert
    # (plus one for the properties framework).
    self.assertEqual(read_file_mock.call_count, 4)

  def testCreateExternalMainReplicaWithoutMainId(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'To create a read replica of an external main instance, '
        r'\[--main-instance-name\] must be specified'):
      self.Run('sql instances create xm-instance-replica '
               '--main-username=root --main-password=somepword '
               '--main-dump-file-path=gs://xm-bucket/dumpfile.sql ')

  def testCreateExternalMainReplicaWithoutPassword(self):
    main_diff = {
        'name':
            'xm-instance',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .MYSQL_5_7,
        'region':
            'us-west1',
    }
    self.ExpectInstanceGet(self.GetExternalMainInstance(), main_diff)
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'To create a read replica of an external main instance, '
        r'\[--main-password\] or \[--prompt-for-main-password\] '
        r'must be specified'):
      self.Run('sql instances create xm-instance-replica '
               '--main-username=root --main-instance-name=xm-instance '
               '--main-dump-file-path=gs://xm-bucket/dumpfile.sql ')

  def testCreatePrivateNetwork(self):
    diff = {
        'name': 'create-instance1',
        'settings': {
            'ipConfiguration':
                self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=None,
                    requireSsl=None,
                    privateNetwork=(
                        'https://compute.googleapis.com/compute/v1/projects/'
                        'fake-project/global/networks/somenetwork')),
            'tier':
                'db-n1-standard-1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)

    self.Run('sql instances create create-instance1 '
             '--network=somenetwork --tier=db-n1-standard-1')
    self.AssertOutputContains(
        """\
NAME DATABASE_VERSION LOCATION TIER PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-instance1 MYSQL_5_7 us-central db-n1-standard-1 0.0.0.0 - RUNNABLE
""",
        normalize_space=True)

  def testCreateWithEncryptionKey(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    key = 'projects/example/locations/us-central1/keyRings/somekey/cryptoKeys/a'
    diff = {
        'name':
            'create-instance1',
        'region':
            'us-central1',
        'settings': {
            'tier': 'db-n1-standard-1'
        },
        'diskEncryptionConfiguration':
            self.messages.DiskEncryptionConfiguration(
                kind='sql#diskEncryptionConfiguration', kmsKeyName=key)
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)

    self.Run('sql instances create create-instance1 --region=us-central1 '
             '--disk-encryption-key="{}"'.format(key))
    # Check that the CMEK prompt was displayed.
    self.assertEqual(prompt_mock.call_count, 1)
    self.AssertErrContains(
        'You are creating a Cloud SQL instance encrypted with a '
        'customer-managed key. If anyone destroys a customer-managed key, all '
        'data encrypted with it will be permanently lost.')

  def testCreateWithInvalidEncryptionKey(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('sql instances create custom-instance1 --region=us-central1 '
               '--disk-encryption-key=projects/whatever')


class InstancesCreateBetaTest(_BaseInstancesCreateBetaTest,
                              base.SqlMockTestBeta):
  pass


class InstancesCreateAlphaTest(_BaseInstancesCreateBetaTest,
                               base.SqlMockTestAlpha):

  def testCreatePostgresWithPointInTimeRecovery(self):
    diff = {
        'name':
            'custom-instance1',
        'databaseVersion':
            self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum
            .POSTGRES_9_6,
        'settings': {
            'backupConfiguration':
                self.messages.BackupConfiguration(
                    pointInTimeRecoveryEnabled=True,
                    enabled=True,
                    kind='sql#backupConfiguration',
                    startTime='00:00'),
            'tier':
                'db-custom-1-1024'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)
    self.Run('sql instances create custom-instance1 '
             '--database-version=POSTGRES_9_6 --memory=1024MiB --cpu=1 '
             '--enable-point-in-time-recovery')


if __name__ == '__main__':
  test_case.main()
