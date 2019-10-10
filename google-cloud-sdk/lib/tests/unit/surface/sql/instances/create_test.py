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

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
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

    # TODO(b/122660263): Remove when V1 instances are no longer supported.
    # Check that no V1 warning is logged.
    self.AssertErrNotContains(
        'First Generation instances will be automatically upgraded '
        'to Second Generation')

  def testCreateActivationPolicy(self):
    diff = {
        'name': 'create-instance1',
        'settings': {
            'tier': 'D1',
            'activationPolicy': 'ON_DEMAND'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)
    self.Run('sql instances create create-instance1 --activation-policy '
             'ON_DEMAND --tier=D1')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME              DATABASE_VERSION  LOCATION    TIER  PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-instance1  MYSQL_5_7         us-central  D1    -               -               RUNNABLE
""",
        normalize_space=True)

  def testSimpleAsyncCreate(self):
    diff = {
        'name': 'create-instance1',
        'settings': {
            'tier': 'D1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.Run('sql instances create create-instance1 --async --tier=D1')
    self.AssertOutputContains("""\
endTime: '2014-08-12T19:39:26.601000+00:00'
insertTime: '2014-08-12T19:38:39.415000+00:00'
kind: sql#operation
name: 344acb84-0000-1111-2222-1e71c6077b34
operationType: CREATE
selfLink: https://www.googleapis.com/sql/v1beta4/projects/fake-project/operations/sample
startTime: '2014-08-12T19:38:39.525000+00:00'
status: DONE
targetId: create-instance1
targetLink: https://www.googleapis.com/sql/v1beta4/projects/fake-project
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
                'D1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)
    self.Run('sql instances create clone-instance-7 --enable-bin-log '
             '--backup-start-time=23:00 --tier=D1')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME              DATABASE_VERSION  LOCATION    TIER  PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
clone-instance-7  MYSQL_5_7         us-central  D1    -               -               RUNNABLE
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
                'D1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)
    self.Run('sql instances create clone-instance-7 --enable-bin-log '
             '--backup --tier=D1')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME              DATABASE_VERSION  LOCATION    TIER  PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
clone-instance-7  MYSQL_5_7         us-central  D1    -               -               RUNNABLE
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
                'D1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)

    self.Run('sql instances create backupless-instance1 --no-backup --tier=D1')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME                  DATABASE_VERSION  LOCATION    TIER  PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
backupless-instance1  MYSQL_5_7         us-central  D1    -               -               RUNNABLE
""",
        normalize_space=True)

  def testCreateReadReplica(self):
    # This test ensures that the replica adopts the db version, tier, and
    # region get automatically copied from the master to the replica without
    # specifying.

    master_diff = {
        'name': 'create-instance1',
        'settings': {
            'tier': 'db-n1-standard-2',
            'replicationType': 'ASYNCHRONOUS'
        },
        'databaseVersion': 'MYSQL_5_7',
        'region': 'us-west1',
    }
    replica_diff = {
        'name': 'create-replica1',
        'settings': {
            'tier': 'db-n1-standard-2',
            'replicationType': 'ASYNCHRONOUS',
        },
        'databaseVersion': 'MYSQL_5_7',
        'region': 'us-west1',
        'masterInstanceName': 'create-instance1'
    }
    self.ExpectInstanceGet(self.GetV2Instance(), master_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)

    self.Run('sql instances create create-replica1 --master-instance-name '
             'create-instance1')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION  LOCATION TIER              PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-replica1  MYSQL_5_7         us-west1 db-n1-standard-2  0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)
    # Ensure that the CMEK message doesn't show up by default.
    self.AssertErrNotContains(
        'Your replica will be encrypted with the master instance\'s '
        'customer-managed encryption key. If anyone destroys this key, all '
        'data encrypted with it will be permanently lost.')

  def testCreateReadReplicaOverridingTier(self):
    # This test ensures that the user is able to specify a tier different than
    # the tier of the master.

    master_diff = {
        'name': 'create-instance1',
        'settings': {
            'tier': 'db-n1-standard-2',
            'replicationType': 'ASYNCHRONOUS'
        },
        'databaseVersion': 'MYSQL_5_7',
        'region': 'us-west1',
    }
    replica_diff = {
        'name': 'create-replica1',
        'settings': {
            'tier': 'db-n1-standard-4',
            'replicationType': 'ASYNCHRONOUS',
        },
        'databaseVersion': 'MYSQL_5_7',
        'region': 'us-west1',
        'masterInstanceName': 'create-instance1'
    }
    self.ExpectInstanceGet(self.GetV2Instance(), master_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)

    self.Run('sql instances create create-replica1 --master-instance-name '
             'create-instance1 --tier=db-n1-standard-4')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME             DATABASE_VERSION  LOCATION TIER              PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-replica1  MYSQL_5_7         us-west1 db-n1-standard-4  0.0.0.0         -               RUNNABLE
""",
        normalize_space=True)

  def testCreateReadReplicaWithCmek(self):
    # This test ensures that a warning shows up when a replica of a instance
    # with a customer-managed encryption key is being created.

    master_diff = {
        'name':
            'create-instance1',
        'diskEncryptionConfiguration':
            self.messages.DiskEncryptionConfiguration(kmsKeyName='some-key'),
        'settings': {
            'replicationType': 'ASYNCHRONOUS'
        },
        'databaseVersion':
            'MYSQL_5_7',
    }
    replica_diff = {
        'name': 'create-replica1',
        'settings': {
            'replicationType': 'ASYNCHRONOUS',
        },
        'databaseVersion': 'MYSQL_5_7',
        'masterInstanceName': 'create-instance1'
    }
    self.ExpectInstanceGet(self.GetV2Instance(), master_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)

    self.Run('sql instances create create-replica1 --master-instance-name '
             'create-instance1')
    # Ensure that the CMEK message is showing up.
    self.AssertErrContains(
        'Your replica will be encrypted with the master instance\'s '
        'customer-managed encryption key. If anyone destroys this key, all '
        'data encrypted with it will be permanently lost.')

  def testCreateNoMaster(self):
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='master-name',
            project=self.Project(),),
        exception=http_error.MakeHttpError(
            code=409,
            reason='notAuthorized',))

    with self.AssertRaisesHttpExceptionRegexp(r'You are either not authorized '
                                              'to access the master instance or'
                                              ' it does not exist.'):
      self.Run('sql instances create replica-name --master-instance-name='
               'master-name')

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
                    updateTrack='canary',
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
                'D1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)

    self.Run('sql instances create create-instance1 '
             '--authorized-networks=10.10.10.1/16 --tier=D1')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME              DATABASE_VERSION  LOCATION    TIER  PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-instance1  MYSQL_5_7         us-central  D1    -               -               RUNNABLE
""",
        normalize_space=True)

  def testCreateCustomMachine(self):
    diff = {
        'name': 'custom-instance1',
        'databaseVersion': 'POSTGRES_9_6',
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
                pricingPlan='PER_USE',
                replicationType='SYNCHRONOUS',
                settingsVersion=None,
                tier='D1',
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
      self.Run('sql instances create create-instance1 --tier=D1')

    self.AssertErrNotContains('already exists')

  def testCreateConfirmsCancel(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql instances create custom-instance --pricing-plan=PACKAGE')

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

  def testCreateWithGaeApps(self):
    diff = {
        'name': 'create-instance',
        'settings': {
            'authorizedGaeApplications': ['00c61b117c180a15eb9c4cb9986']
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.Run('sql instances create create-instance '
             '--authorized-gae-apps 00c61b117c180a15eb9c4cb9986')

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
                self.messages.LocationPreference(zone='europe-west1-b')
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
                self.messages.LocationPreference(zone='europe-west1-b')
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
        'name': 'custom-instance1',
        'databaseVersion': 'POSTGRES_9_6',
        'settings': {
            'availabilityType': 'REGIONAL',
            'tier': 'db-custom-1-1024'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetPostgresInstance(), diff)

    self.Run('sql instances create custom-instance1 '
             '--database-version=POSTGRES_9_6 --memory=1024MiB --cpu=1 '
             '--availability-type=REGIONAL')

  # TODO(b/122660263): Remove when V1 instances are no longer supported.
  def testV1WarningAndPrompt(self):
    # Mock the prompt to continue creating a V1 instance.
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    diff = {'name': 'create-instance1', 'settings': {'tier': 'D1',}}
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)

    # Create V1 instance.
    self.Run('sql instances create create-instance1 --tier=D1')

    # Check that a V1 warning is logged.
    self.AssertErrContains(
        'First Generation instances will be automatically upgraded '
        'to Second Generation')

    # Check that the V1 prompt to continue was called.
    self.assertEqual(prompt_mock.call_count, 1)

  def testCreateWithRootPassword(self):
    diff = {
        'name': 'some-instance',
        'rootPassword': 'somepassword'
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetExternalMasterInstance(), diff)
    self.Run('sql instances create some-instance --root-password=somepassword')


class InstancesCreateGATest(_BaseInstancesCreateTest, base.SqlMockTestGA):
  pass


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

  def testCreateExternalMasterWithDefaultPort(self):
    diff = {
        'name':
            'xm-instance',
        'onPremisesConfiguration':
            self.messages.OnPremisesConfiguration(hostPort='127.0.0.1:3306')
    }
    self.ExpectInstanceInsert(self.GetExternalMasterRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetExternalMasterInstance(), diff)
    self.Run('sql instances create xm-instance '
             '--source-ip-address=127.0.0.1')

  def testCreateExternalMasterWithCustomPort(self):
    diff = {
        'name':
            'xm-instance',
        'onPremisesConfiguration':
            self.messages.OnPremisesConfiguration(hostPort='127.0.0.1:8080')
    }
    self.ExpectInstanceInsert(self.GetExternalMasterRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetExternalMasterInstance(), diff)
    self.Run('sql instances create xm-instance '
             '--source-ip-address=127.0.0.1 --source-port=8080')

  def testCreateExternalMasterReplicaWithoutSSL(self):
    master_diff = {
        'name': 'xm-instance',
        'databaseVersion': 'MYSQL_5_7',
        'region': 'us-west1',
    }
    replica_diff = {
        'name':
            'xm-instance-replica',
        'settings': {
            'replicationType': 'ASYNCHRONOUS',
        },
        'databaseVersion':
            'MYSQL_5_7',
        'region':
            'us-west1',
        'masterInstanceName':
            'xm-instance',
        'replicaConfiguration':
            self.messages.ReplicaConfiguration(
                mysqlReplicaConfiguration=self.messages.
                MySqlReplicaConfiguration(
                    username='root',
                    password='somepword',
                    dumpFilePath='gs://xm-bucket/dumpfile.sql'))
    }
    self.ExpectInstanceGet(self.GetExternalMasterInstance(), master_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)
    self.Run('sql instances create xm-instance-replica '
             '--master-username=root --master-password=somepword '
             '--master-dump-file-path=gs://xm-bucket/dumpfile.sql '
             '--master-instance-name=xm-instance')

  def testCreateExternalMasterReplicaWithPasswordPrompt(self):
    # The password prompt flag should cause getpass to get called.
    self.StartObjectPatch(getpass, 'getpass', return_value='somepword')
    master_diff = {
        'name': 'xm-instance',
        'databaseVersion': 'MYSQL_5_7',
        'region': 'us-west1',
    }
    replica_diff = {
        'name':
            'xm-instance-replica',
        'settings': {
            'replicationType': 'ASYNCHRONOUS',
        },
        'databaseVersion':
            'MYSQL_5_7',
        'region':
            'us-west1',
        'masterInstanceName':
            'xm-instance',
        'replicaConfiguration':
            self.messages.ReplicaConfiguration(
                mysqlReplicaConfiguration=self.messages.
                MySqlReplicaConfiguration(
                    username='root',
                    password='somepword',
                    dumpFilePath='gs://xm-bucket/dumpfile.sql'))
    }
    self.ExpectInstanceGet(self.GetExternalMasterInstance(), master_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)
    self.Run('sql instances create xm-instance-replica '
             '--master-username=root --prompt-for-master-password '
             '--master-dump-file-path=gs://xm-bucket/dumpfile.sql '
             '--master-instance-name=xm-instance')

  def testCreateExternalMasterReplicaWithCACert(self):
    # Need file read mock to get cert file contents.
    read_file_mock = self.StartObjectPatch(
        files, 'ReadFileContents', return_value='file_data')
    master_diff = {
        'name': 'xm-instance',
        'databaseVersion': 'MYSQL_5_7',
        'region': 'us-west1',
    }
    replica_diff = {
        'name':
            'xm-instance-replica',
        'settings': {
            'replicationType': 'ASYNCHRONOUS',
        },
        'databaseVersion':
            'MYSQL_5_7',
        'region':
            'us-west1',
        'masterInstanceName':
            'xm-instance',
        'replicaConfiguration':
            self.messages.ReplicaConfiguration(
                mysqlReplicaConfiguration=self.messages.
                MySqlReplicaConfiguration(
                    username='root',
                    password='somepword',
                    dumpFilePath='gs://xm-bucket/dumpfile.sql',
                    caCertificate='file_data'))
    }
    self.ExpectInstanceGet(self.GetExternalMasterInstance(), master_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)
    self.Run('sql instances create xm-instance-replica '
             '--master-username=root --master-password=somepword '
             '--master-dump-file-path=gs://xm-bucket/dumpfile.sql '
             '--master-instance-name=xm-instance '
             '--master-ca-certificate-path=/path/to/ca_cert.pem')

    # File contents should be read once, for the CA Cert
    # (plus one for the properties framework).
    self.assertEqual(read_file_mock.call_count, 2)

  def testCreateExternalMasterWithCAAndClientCerts(self):
    # Need file read mock to get cert file contents.
    read_file_mock = self.StartObjectPatch(
        files, 'ReadFileContents', return_value='file_data')
    master_diff = {
        'name': 'xm-instance',
        'databaseVersion': 'MYSQL_5_7',
        'region': 'us-west1',
    }
    replica_diff = {
        'name':
            'xm-instance-replica',
        'settings': {
            'replicationType': 'ASYNCHRONOUS',
        },
        'databaseVersion':
            'MYSQL_5_7',
        'region':
            'us-west1',
        'masterInstanceName':
            'xm-instance',
        'replicaConfiguration':
            self.messages.ReplicaConfiguration(
                mysqlReplicaConfiguration=self.messages.
                MySqlReplicaConfiguration(
                    username='root',
                    password='somepword',
                    dumpFilePath='gs://xm-bucket/dumpfile.sql',
                    caCertificate='file_data',
                    clientCertificate='file_data',
                    clientKey='file_data'))
    }
    self.ExpectInstanceGet(self.GetExternalMasterInstance(), master_diff)
    self.ExpectInstanceInsert(self.GetRequestInstance(), replica_diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV2Instance(), replica_diff)
    self.Run('sql instances create xm-instance-replica '
             '--master-username=root --master-password=somepword '
             '--master-dump-file-path=gs://xm-bucket/dumpfile.sql '
             '--master-instance-name=xm-instance '
             '--client-certificate-path=/path/to/client_cert.pem '
             '--client-key-path=/path/to/client_key.pem '
             '--master-ca-certificate-path=/path/to/ca_cert.pem')

    # File contents should be read three times, one for each cert
    # (plus one for the properties framework).
    self.assertEqual(read_file_mock.call_count, 4)

  def testCreateExternalMasterReplicaWithoutMasterId(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'To create a read replica of an external master instance, '
        r'\[--master-instance-name\] must be specified'):
      self.Run('sql instances create xm-instance-replica '
               '--master-username=root --master-password=somepword '
               '--master-dump-file-path=gs://xm-bucket/dumpfile.sql ')

  def testCreateExternalMasterReplicaWithoutPassword(self):
    master_diff = {
        'name': 'xm-instance',
        'databaseVersion': 'MYSQL_5_7',
        'region': 'us-west1',
    }
    self.ExpectInstanceGet(self.GetExternalMasterInstance(), master_diff)
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'To create a read replica of an external master instance, '
        r'\[--master-password\] or \[--prompt-for-master-password\] '
        r'must be specified'):
      self.Run('sql instances create xm-instance-replica '
               '--master-username=root --master-instance-name=xm-instance '
               '--master-dump-file-path=gs://xm-bucket/dumpfile.sql ')

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
                'D1'
        }
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)

    self.Run('sql instances create create-instance1 '
             '--network=somenetwork --tier=D1')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME              DATABASE_VERSION  LOCATION    TIER  PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
create-instance1  MYSQL_5_7         us-central  D1    -               -               RUNNABLE
""",
        normalize_space=True)

  def testCreateSqlServerWithoutRootPassword(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException, r'Missing required argument '
        r'\[--root-password\]'):
      self.Run('sql instances create some-instance '
               '--database-version=SQLSERVER_2017_STANDARD')


class InstancesCreateBetaTest(_BaseInstancesCreateBetaTest,
                              base.SqlMockTestBeta):
  pass


class InstancesCreateAlphaTest(_BaseInstancesCreateBetaTest,
                               base.SqlMockTestAlpha):

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
            self.messages.DiskEncryptionConfiguration(kmsKeyName=key)
    }
    self.ExpectInstanceInsert(self.GetRequestInstance(), diff)
    self.ExpectDoneCreateOperationGet()
    self.ExpectInstanceGet(self.GetV1Instance(), diff)

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

if __name__ == '__main__':
  test_case.main()
