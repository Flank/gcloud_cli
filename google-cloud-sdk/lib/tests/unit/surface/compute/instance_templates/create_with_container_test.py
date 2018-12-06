# -*- coding: utf-8 -*- #
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
"""Tests for the instances create-with-container subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.compute import containers_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InstanceTemplatesCreateWithContainerTestBase(test_base.BaseTest):

  def _SetUp(self):
    m = self.messages
    self.cos_image_name = 'cos-beta-63-8872-76-0'
    self.cos_image_path = ('projects/cos-cloud/global/images/'
                           'cos-beta-63-8872-76-0')
    self.cos_images_list_request = [
        (self.compute.images,
         'List',
         self.messages.ComputeImagesListRequest(
             project='cos-cloud')),
    ]
    self.make_requests.side_effect = iter([
        [m.Image(
            name=self.cos_image_name,
            selfLink=self.cos_image_path,
            creationTimestamp='2016-06-06T18:52:15.455-07:00')],
        [m.InstanceTemplate(
            name='it-1',
            properties=self.messages.InstanceProperties(
                machineType='n1-standard-1'))],
    ])
    self.default_attached_disk = m.AttachedDisk(
        autoDelete=True,
        boot=True,
        initializeParams=m.AttachedDiskInitializeParams(
            sourceImage=self.cos_image_path),
        licenses=[],
        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    self.default_machine_type = 'n1-standard-1'
    self.default_container_manifest = {
        'spec': {
            'containers': [{
                'name': 'it-1',
                'image': 'gcr.io/my-docker/test-image',
                'securityContext': {
                    'privileged': False
                },
                'stdin': False,
                'tty': False,
                'volumeMounts': []
            }],
            'restartPolicy':
                'Always',
            'volumes': []
        }
    }
    self.default_metadata = m.Metadata(items=[
        m.Metadata.ItemsValueListEntry(
            key='gce-container-declaration',
            value=containers_utils.DumpYaml(self.default_container_manifest)),
        m.Metadata.ItemsValueListEntry(
            key='google-logging-enabled',
            value='true')])
    self.default_tags = None
    self.default_labels = m.InstanceProperties.LabelsValue(
        additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key='container-vm', value='cos-beta-63-8872-76-0')]
    )
    self.default_network_interface = m.NetworkInterface(
        accessConfigs=[m.AccessConfig(
            name='external-nat',
            type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)],
        network=('{0}/projects/my-project/global/networks/default'
                 .format(self.compute_uri)))
    self.default_service_account = m.ServiceAccount(
        email='default',
        scopes=[
            'https://www.googleapis.com/auth/devstorage.read_only',
            'https://www.googleapis.com/auth/logging.write',
            'https://www.googleapis.com/auth/monitoring.write',
            'https://www.googleapis.com/auth/pubsub',
            'https://www.googleapis.com/auth/service.management.readonly',
            'https://www.googleapis.com/auth/servicecontrol',
            'https://www.googleapis.com/auth/trace.append'])


class InstanceTemplatesCreateFromContainerTest(
    InstanceTemplatesCreateWithContainerTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self._SetUp()

  def testSimple(self):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],)
    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME  MACHINE_TYPE   PREEMPTIBLE  CREATION_TIMESTAMP
        it-1  n1-standard-1
        """))

  def testAllDockerOptions(self):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          --container-command='echo -a "Hello world!"'
          --container-privileged
          --container-image=gcr.io/my-docker/test-image
        """)
    expected_manifest = {
        'spec': {
            'containers': [{
                'name': 'it-1',
                'image': 'gcr.io/my-docker/test-image',
                'command': ['echo -a "Hello world!"'],
                'securityContext': {
                    'privileged': True
                },
                'stdin': False,
                'tty': False,
                'volumeMounts': []
            }],
            'restartPolicy':
                'Always',
            'volumes': []
        }
    }
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=m.Metadata(items=[
                          m.Metadata.ItemsValueListEntry(
                              key='gce-container-declaration',
                              value=containers_utils.DumpYaml(
                                  expected_manifest)),
                          m.Metadata.ItemsValueListEntry(
                              key='google-logging-enabled', value='true')
                      ]),
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',))],)

  def testCreateBootDiskOptions(self):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          --boot-disk-size 199GB
          --boot-disk-type pd-ssd
          --boot-disk-device-name boot-disk
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[m.AttachedDisk(
                          autoDelete=True,
                          deviceName='boot-disk',
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              diskSizeGb=199,
                              diskType='pd-ssd',
                              sourceImage=self.cos_image_path,
                          ),
                          licenses=[],
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT
                      )],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],)

  def testCreateMetadataOptions(self):
    m = self.messages
    metadata_file = self.Touch(directory=self.temp_path,
                               name='metadata.txt',
                               contents='foo')
    self.Run("""
        compute instance-templates create-with-container it-1
          --metadata x=abc
          --metadata-from-file y={0}
          --container-image=gcr.io/my-docker/test-image
        """.format(metadata_file))
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=m.Metadata(items=[
                          m.Metadata.ItemsValueListEntry(
                              key='gce-container-declaration',
                              value=containers_utils.DumpYaml(
                                  self.default_container_manifest)),
                          m.Metadata.ItemsValueListEntry(
                              key='google-logging-enabled', value='true'),
                          m.Metadata.ItemsValueListEntry(key='x', value='abc'),
                          m.Metadata.ItemsValueListEntry(key='y', value='foo'),
                      ]),
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',))],)

  def testTagsOptions(self):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          --tags tag-1,tag-2
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=m.Tags(items=['tag-1', 'tag-2']))),
              project='my-project',
          ))],)

  def testCreateNetworkingOptions(self):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          --can-ip-forward
          --network some-other-network
          --address 74.125.28.139
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=True,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[m.NetworkInterface(
                          accessConfigs=[m.AccessConfig(
                              name='external-nat',
                              natIP='74.125.28.139',
                              type=(m.AccessConfig.TypeValueValuesEnum
                                    .ONE_TO_ONE_NAT))],
                          network=('{0}/projects/my-project/global/networks/'
                                   'some-other-network'
                                   .format(self.compute_uri)))],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],)

  def testCreateScopeOptions(self):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          --scopes compute-rw
          --service-account 1234@project.gserviceaccount.com
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[m.ServiceAccount(
                          email='1234@project.gserviceaccount.com',
                          scopes=['https://www.googleapis.com/auth/'
                                  'compute'])],
                      tags=self.default_tags)),
              project='my-project',
          ))],)

  def testCreateSchedulingPolicyOptions(self):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          --preemptible
          --no-restart-on-failure
          --maintenance-policy=terminate
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(
                          automaticRestart=False,
                          onHostMaintenance=(
                              m.Scheduling.OnHostMaintenanceValueValuesEnum
                              .TERMINATE),
                          preemptible=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],)

  def testCreateMachineTypeOptions(self):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          --machine-type=n1-standard-1
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],)

  def testCreateCustomMachineTypeOptions(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [m.Image(
            name=self.cos_image_name,
            selfLink=self.cos_image_path,
            creationTimestamp='2016-06-06T18:52:15.455-07:00')],
        [m.MachineType(
            creationTimestamp='2013-09-06T17:54:10.636-07:00',
            guestCpus=int(10),
            memoryMb=int(1000))],
        [],
    ])
    self.Run("""
        compute instance-templates create-with-container it-1
          --custom-cpu 10
          --custom-memory 1000MiB
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType='custom-10-1000',
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],)

  def testCreateExtendedCustomMachineTypeOptions(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [m.Image(
            name=self.cos_image_name,
            selfLink=self.cos_image_path,
            creationTimestamp='2016-06-06T18:52:15.455-07:00')],
        [m.MachineType(
            creationTimestamp='2013-09-06T17:54:10.636-07:00',
            guestCpus=int(10),
            memoryMb=int(1000))],
        [],
    ])
    self.Run("""
        compute instance-templates create-with-container it-1
          --custom-cpu 10
          --custom-memory 1000MiB
          --custom-extensions
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType='custom-10-1000-ext',
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],)

  def testCreateRequireDockerImageOrSpec(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Missing required argument \[--container-image\]: '
        'You must provide container image'):
      self.Run("""
          compute instance-templates create-with-container it-1
          """)

  def testCreateExistingBootDisk(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Boot disk specified for containerized VM.'):
      self.Run("""
          compute instance-templates create-with-container it-1
            --disk name=disk-1,boot=yes
            --container-image=gcr.io/my-docker/test-image
          """)

  def testCreateMetadataKeyConflict(self):
    with self.AssertRaisesExceptionMatches(
        containers_utils.InvalidMetadataKeyException,
        'Metadata key "user-data" is not allowed when '
        'running containerized VM'):
      self.Run("""
          compute instance-templates create-with-container it-1
            --metadata user-data=somedata
            --container-image=gcr.io/my-docker/test-image
          """)

  # Deprecation of --scopes flag tests

  def testScopesLegacyFormatDeprecationNotice(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--scopes]: Flag format --scopes [ACCOUNT=]SCOPE,'
        '[[ACCOUNT=]SCOPE, ...] is removed. Use --scopes [SCOPE,...] '
        '--service-account ACCOUNT instead.'):
      self.Run('compute instance-templates create-with-container instance-1 '
               '--scopes=acc1=scope1,acc1=scope2 '
               '--container-image=gcr.io/my-docker/test-image')

  def testScopesNewFormatNoDeprecationNotice(self):
    self.Run('compute instance-templates create-with-container asdf '
             '--scopes=scope1,scope2 --service-account acc1@example.com '
             '--container-image=gcr.io/my-docker/test-image')
    self.AssertErrEquals('')

  def testNoServiceAccount(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instance-templates create-with-container asdf '
               '--no-service-account '
               '--container-image=gcr.io/my-docker/test-image')

  def testScopesWithNoServiceAccount(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instance-templates create-with-container asdf '
               '--scopes=scope1 --no-service-account '
               '--container-image=gcr.io/my-docker/test-image')

  def testWithMinCpuPlatform(self):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
          --min-cpu-platform cpu-platform
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      minCpuPlatform='cpu-platform',
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],)
    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME  MACHINE_TYPE   PREEMPTIBLE  CREATION_TIMESTAMP
        it-1  n1-standard-1
        """))

  def testWithCustomImage(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.InstanceTemplate(
                name='it-1',
                properties=self.messages.InstanceProperties(
                    machineType='n1-standard-1'))
        ],
    ])

    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
          --image my-image
          --image-project my-image-project
        """)
    self.CheckRequests(
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[
                          m.AttachedDisk(
                              autoDelete=True,
                              boot=True,
                              initializeParams=m.AttachedDiskInitializeParams(
                                  sourceImage='{}/projects/my-image-project/'
                                  'global/images/my-image'.format(
                                      self.compute_uri)),
                              licenses=[],
                              mode=m.AttachedDisk.ModeValueValuesEnum.
                              READ_WRITE,
                              type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT
                          )
                      ],
                      labels=m.InstanceProperties.LabelsValue(
                          additionalProperties=[
                              (m.InstanceProperties.LabelsValue.
                               AdditionalProperty)(
                                   key='container-vm', value='my-image')]
                      ),
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',))],)
    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME  MACHINE_TYPE   PREEMPTIBLE  CREATION_TIMESTAMP
        it-1  n1-standard-1
        """))

    self.AssertErrEquals('WARNING: This container deployment mechanism '
                         'requires a Container-Optimized OS image in order to '
                         'work. Select an image from a cos-cloud project '
                         '(cost-stable, cos-beta, cos-dev image families).\n')

  def testWithCustomImageFamily(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.InstanceTemplate(
                name='it-1',
                properties=self.messages.InstanceProperties(
                    machineType='n1-standard-1'))
        ],
    ])

    self.Run("""
        compute instance-templates create-with-container it-1
        --container-image=gcr.io/my-docker/test-image
        --image-project bct-staging-images
        --image-family cos-beta
        """)
    self.CheckRequests(
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[
                          m.AttachedDisk(
                              autoDelete=True,
                              boot=True,
                              initializeParams=m.AttachedDiskInitializeParams(
                                  sourceImage=(
                                      '{}/projects/bct-staging-images/global/'
                                      'images/family/cos-beta'.format(
                                          self.compute_uri)),
                              ),
                              licenses=[],
                              mode=m.AttachedDisk.ModeValueValuesEnum.
                              READ_WRITE,
                              type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT
                          )
                      ],
                      labels=m.InstanceProperties.LabelsValue(
                          additionalProperties=[
                              (m.InstanceProperties.LabelsValue.
                               AdditionalProperty)(
                                   key='container-vm', value='family-cos-beta')]
                      ),
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',))],)
    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME  MACHINE_TYPE   PREEMPTIBLE  CREATION_TIMESTAMP
        it-1  n1-standard-1
        """))

    self.AssertErrEquals('WARNING: This container deployment mechanism '
                         'requires a Container-Optimized OS image in order to '
                         'work. Select an image from a cos-cloud project '
                         '(cost-stable, cos-beta, cos-dev image families).\n')


class InstanceTemplatesCreateWithContainerTestAlpha(
    InstanceTemplatesCreateWithContainerTestBase):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._SetUp()

  def createWithOnHostMaintenanceTest(self, flag):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          {}=terminate
          --container-image=gcr.io/my-docker/test-image
        """.format(flag))
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(
                          automaticRestart=True,
                          onHostMaintenance=(
                              m.Scheduling.OnHostMaintenanceValueValuesEnum
                              .TERMINATE)),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],)

  def testAdditionalAttachedDisks(self):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          --local-nvdimm ''
          --local-nvdimm size=3TB
          --disk name=disk-1,mode=rw,device-name=x,boot=no
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[
                          self.default_attached_disk,
                          m.AttachedDisk(
                              autoDelete=False,
                              boot=False,
                              deviceName='x',
                              licenses=[],
                              mode=(m.AttachedDisk.ModeValueValuesEnum
                                    .READ_WRITE),
                              source='disk-1',
                              type=(m.AttachedDisk.TypeValueValuesEnum
                                    .PERSISTENT)),
                          m.AttachedDisk(
                              autoDelete=True,
                              initializeParams=m.AttachedDiskInitializeParams(
                                  diskType='aep-nvdimm'),
                              interface=(m.AttachedDisk.InterfaceValueValuesEnum
                                         .NVDIMM),
                              licenses=[],
                              mode=(m.AttachedDisk.ModeValueValuesEnum
                                    .READ_WRITE),
                              type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
                          m.AttachedDisk(
                              autoDelete=True,
                              diskSizeGb=3072,
                              initializeParams=m.AttachedDiskInitializeParams(
                                  diskType='aep-nvdimm'),
                              interface=(m.AttachedDisk.InterfaceValueValuesEnum
                                         .NVDIMM),
                              licenses=[],
                              mode=(m.AttachedDisk.ModeValueValuesEnum
                                    .READ_WRITE),
                              type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
                      ],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],
    )

  def testWithOnHostMaintenance(self):
    self.createWithOnHostMaintenanceTest('--on-host-maintenance')

  def testMaintenancePolicyDeprecation(self):
    self.createWithOnHostMaintenanceTest('--maintenance-policy')
    self.AssertErrContains(
        'WARNING: The --maintenance-policy flag is now deprecated. '
        'Please use `--on-host-maintenance` instead')


class InstanceTemplatesCreateFromContainerWithNetworkTierTest(
    InstanceTemplatesCreateWithContainerTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self._SetUp()

  def CreateRequestWithNetworkTier(self, network_tier):
    m = self.messages

    if network_tier:
      network_tier_enum = m.AccessConfig.NetworkTierValueValuesEnum(
          network_tier)
    else:
      network_tier_enum = None
    return m.ComputeInstanceTemplatesInsertRequest(
        instanceTemplate=m.InstanceTemplate(
            name='it-1',
            properties=m.InstanceProperties(
                canIpForward=False,
                disks=[self.default_attached_disk],
                labels=self.default_labels,
                machineType=self.default_machine_type,
                metadata=self.default_metadata,
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat',
                                networkTier=network_tier_enum,
                                type=(m.AccessConfig.TypeValueValuesEnum.
                                      ONE_TO_ONE_NAT))
                        ],
                        network=(
                            '{0}/projects/my-project/global/networks/default'
                            .format(self.compute_uri)))
                ],
                scheduling=m.Scheduling(automaticRestart=True),
                serviceAccounts=[self.default_service_account],
                tags=self.default_tags)),
        project='my-project')

  def testWithDefaultNetworkTier(self):
    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates, 'Insert',
          self.CreateRequestWithNetworkTier(None))],
    )

  def testWithPremiumNetworkTier(self):
    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
          --network-tier PREMIUM
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates, 'Insert',
          self.CreateRequestWithNetworkTier('PREMIUM'))],
    )

  def testWithStandardNetworkTier(self):
    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
          --network-tier standard
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates, 'Insert',
          self.CreateRequestWithNetworkTier('STANDARD'))],
    )

  def testNetworkTierNotSupported(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[RANDOM-NETWORK-TIER\]'):
      self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
          --network-tier random-network-tier
          """)

  def testWithLabels(self):
    m = self.messages
    expected_labels = m.InstanceProperties.LabelsValue(additionalProperties=[
        m.InstanceProperties.LabelsValue.AdditionalProperty(
            key='container-vm', value='cos-beta-63-8872-76-0'),
        m.InstanceProperties.LabelsValue.AdditionalProperty(key='a', value='1'),
        m.InstanceProperties.LabelsValue.AdditionalProperty(key='b', value='2')
    ])

    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
          --labels=a=1,b=2
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[self.default_attached_disk],
                      labels=expected_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME  MACHINE_TYPE   PREEMPTIBLE  CREATION_TIMESTAMP
        it-1  n1-standard-1
        """))


class InstanceTemplatesCreateFromContainerWithNetworkTierAlphaTest(
    InstanceTemplatesCreateWithContainerTestBase):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._SetUp()

  def CreateRequestWithNetworkTier(self, network_tier):
    m = self.messages

    if network_tier:
      network_tier_enum = m.AccessConfig.NetworkTierValueValuesEnum(
          network_tier)
    else:
      network_tier_enum = None
    return m.ComputeInstanceTemplatesInsertRequest(
        instanceTemplate=m.InstanceTemplate(
            name='it-1',
            properties=m.InstanceProperties(
                canIpForward=False,
                disks=[self.default_attached_disk],
                labels=self.default_labels,
                machineType=self.default_machine_type,
                metadata=self.default_metadata,
                networkInterfaces=[m.NetworkInterface(
                    accessConfigs=[m.AccessConfig(
                        name='external-nat',
                        networkTier=network_tier_enum,
                        type=(m.AccessConfig
                              .TypeValueValuesEnum.ONE_TO_ONE_NAT))],
                    network=('{0}/projects/my-project/global/networks/default'
                             .format(self.compute_uri)))],
                scheduling=m.Scheduling(automaticRestart=True),
                serviceAccounts=[self.default_service_account],
                tags=self.default_tags)),
        project='my-project')

  def testWithDefaultNetworkTier(self):
    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates, 'Insert',
          self.CreateRequestWithNetworkTier(None))],)

  def testWithPremiumNetworkTier(self):
    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
          --network-tier PREMIUM
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          self.CreateRequestWithNetworkTier('PREMIUM'))],)

  def testWithSelectNetworkTier(self):
    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
          --network-tier select
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          self.CreateRequestWithNetworkTier('SELECT'))],)

  def testWithStandardNetworkTier(self):
    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
          --network-tier standard
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates,
          'Insert',
          self.CreateRequestWithNetworkTier('STANDARD'))],)

  def testNetworkTierNotSupported(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[RANDOM-NETWORK-TIER\]'
    ):
      self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
          --network-tier random-network-tier
          """)

  def testWithLabels(self):
    self.Run("""
        compute instance-templates create-with-container it-1
          --container-image=gcr.io/my-docker/test-image
          --labels=c=3,d=4
        """)
    m = self.messages
    expected_labels = m.InstanceProperties.LabelsValue(additionalProperties=[
        m.InstanceProperties.LabelsValue.AdditionalProperty(
            key='container-vm', value='cos-beta-63-8872-76-0'),
        m.InstanceProperties.LabelsValue.AdditionalProperty(key='c', value='3'),
        m.InstanceProperties.LabelsValue.AdditionalProperty(key='d', value='4')
    ])
    expected_request = self.CreateRequestWithNetworkTier(None)
    expected_request.instanceTemplate.properties.labels = expected_labels
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates, 'Insert', expected_request)],
    )


class InstanceTemplatesCreateFromContainerWithLocalSsdBetaTest(
    InstanceTemplatesCreateWithContainerTestBase):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self._SetUp()

  def testAdditionalAttachedDisks(self):
    m = self.messages
    self.Run("""
        compute instance-templates create-with-container it-1
          --local-ssd device-name=foo
          --local-ssd device-name=bar,interface=NVME
          --disk name=disk-1,mode=rw,device-name=x,boot=no
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.cos_images_list_request,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='it-1',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[
                          self.default_attached_disk,
                          m.AttachedDisk(
                              autoDelete=False,
                              boot=False,
                              deviceName='x',
                              licenses=[],
                              mode=(m.AttachedDisk.ModeValueValuesEnum
                                    .READ_WRITE),
                              source='disk-1',
                              type=(m.AttachedDisk.TypeValueValuesEnum
                                    .PERSISTENT)),
                          m.AttachedDisk(
                              autoDelete=True,
                              deviceName='foo',
                              initializeParams=m.AttachedDiskInitializeParams(
                                  diskType='local-ssd'),
                              licenses=[],
                              mode=(m.AttachedDisk.ModeValueValuesEnum
                                    .READ_WRITE),
                              type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
                          m.AttachedDisk(
                              autoDelete=True,
                              deviceName='bar',
                              initializeParams=m.AttachedDiskInitializeParams(
                                  diskType='local-ssd'),
                              interface=(
                                  m.AttachedDisk.InterfaceValueValuesEnum.NVME),
                              licenses=[],
                              mode=(m.AttachedDisk.ModeValueValuesEnum
                                    .READ_WRITE),
                              type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH)
                      ],
                      labels=self.default_labels,
                      machineType=self.default_machine_type,
                      metadata=self.default_metadata,
                      networkInterfaces=[self.default_network_interface],
                      scheduling=m.Scheduling(automaticRestart=True),
                      serviceAccounts=[self.default_service_account],
                      tags=self.default_tags)),
              project='my-project',
          ))],
    )

if __name__ == '__main__':
  test_case.main()
