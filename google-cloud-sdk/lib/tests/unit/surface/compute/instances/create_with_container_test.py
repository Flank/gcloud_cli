# -*- coding: utf-8 -*- #
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
"""Tests for the instances create-with-container subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import containers_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InstancesCreateWithContainerTestBase(test_base.BaseTest):

  def _SetUp(self):
    m = self.messages
    self.cos_image_name = 'cos-dev-63-8872-76-0'
    self.cos_image_path = ('projects/cos-cloud/global/images/'
                           'cos-dev-63-8872-76-0')
    self.make_requests.side_effect = iter([
        [m.Zone(name='central2-a'),
         m.Zone(name='central2-b'),
         m.Zone(name='central2-c')],
        [m.Image(
            name=self.cos_image_name,
            selfLink=self.cos_image_path,
            creationTimestamp='2016-06-06T18:52:15.455-07:00')],
        []
    ])
    self.cos_images_list_request = [
        (self.compute.images,
         'List',
         self.messages.ComputeImagesListRequest(
             project='cos-cloud')),
    ]
    self.default_attached_disk = m.AttachedDisk(
        autoDelete=True,
        boot=True,
        initializeParams=m.AttachedDiskInitializeParams(
            sourceImage=self.cos_image_path),
        licenses=[],
        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    self.default_machine_type = ('{0}/projects/my-project/zones/central2-a/'
                                 'machineTypes/n1-standard-1'
                                 .format(self.compute_uri))
    self.default_container_manifest = {
        'spec': {
            'containers': [{
                'name': 'instance-1',
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
    self.default_labels = m.Instance.LabelsValue(
        additionalProperties=[
            m.Instance.LabelsValue.AdditionalProperty(
                key='container-vm', value='cos-dev-63-8872-76-0')]
    )
    self.default_metadata = m.Metadata(items=[
        m.Metadata.ItemsValueListEntry(
            key='gce-container-declaration',
            value=containers_utils.DumpYaml(self.default_container_manifest)),
        m.Metadata.ItemsValueListEntry(
            key='google-logging-enabled', value='true')])
    self.default_tags = None
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


class InstancesCreateWithContainerTest(InstancesCreateWithContainerTestBase,
                                       parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self._SetUp()

  def testSimple(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testMinCpuPlatform(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --min-cpu-platform asdf
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                disks=[self.default_attached_disk],
                labels=self.default_labels,
                machineType=self.default_machine_type,
                metadata=self.default_metadata,
                minCpuPlatform='asdf',
                name='instance-1',
                networkInterfaces=[self.default_network_interface],
                scheduling=m.Scheduling(automaticRestart=True),
                serviceAccounts=[self.default_service_account],
                tags=self.default_tags),
            project='my-project',
            zone='central2-a',))],)

  @parameterized.parameters(('ON-FAILURE',), ('on-failure',))
  def testAllDockerOptions(self, restart_policy):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-command='echo -a "Hello world!"'
          --container-privileged
          --container-image=gcr.io/my-docker/test-image
          --container-arg=arg1
          --container-arg=arg2
          --container-env=key1=val1
          --container-mount-host-path=host-path=host-path,mount-path=mount-path,mode=ro
          --container-mount-tmpfs=mount-path=tmpfs
          --container-stdin
          --container-tty
          --container-restart-policy={restart_policy}
        """.format(restart_policy=restart_policy))
    expected_manifest = {
        'spec': {
            'containers': [{
                'name':
                    'instance-1',
                'image':
                    'gcr.io/my-docker/test-image',
                'command': ['echo -a "Hello world!"'],
                'args': ['arg1', 'arg2'],
                'stdin':
                    True,
                'tty':
                    True,
                'securityContext': {
                    'privileged': True
                },
                'env': [{
                    'name': 'key1',
                    'value': 'val1'
                }],
                'volumeMounts': [{
                    'mountPath': 'mount-path',
                    'name': 'host-path-0',
                    'readOnly': True
                }, {
                    'mountPath': 'tmpfs',
                    'name': 'tmpfs-0'
                }]
            }],
            'restartPolicy':
                'OnFailure',
            'volumes': [{
                'name': 'host-path-0',
                'hostPath': {
                    'path': 'host-path'
                }
            }, {
                'name': 'tmpfs-0',
                'emptyDir': {
                    'medium': 'Memory'
                }
            }]
        }
    }
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=m.Metadata(items=[
                      m.Metadata.ItemsValueListEntry(
                          key='gce-container-declaration',
                          value=containers_utils.DumpYaml(expected_manifest)),
                      m.Metadata.ItemsValueListEntry(
                          key='google-logging-enabled', value='true')]),
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testCreateBootDiskOptions(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --boot-disk-size 199GB
          --boot-disk-type pd-ssd
          --boot-disk-device-name boot-disk
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      deviceName='boot-disk',
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          diskSizeGb=199,
                          diskType=('{0}/projects/my-project/zones/central2-a/'
                                    'diskTypes/pd-ssd'
                                    .format(self.compute_uri)),
                          sourceImage=self.cos_image_path,
                      ),
                      licenses=[],
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT
                  )],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testCreateMetadataOptions(self):
    m = self.messages
    metadata_file = self.Touch(directory=self.temp_path,
                               name='metadata-key.txt',
                               contents='foo')
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --metadata x=abc
          --metadata-from-file y='{0}'
          --container-image=gcr.io/my-docker/test-image
        """.format(metadata_file))
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
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
                name='instance-1',
                networkInterfaces=[self.default_network_interface],
                scheduling=m.Scheduling(automaticRestart=True),
                serviceAccounts=[self.default_service_account],
                tags=self.default_tags),
            project='my-project',
            zone='central2-a',))],)

  def testAdditionalAttachedDisksNoSSD(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --disk name=disk-1,mode=rw,device-name=x,boot=no
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[
                      self.default_attached_disk,
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          licenses=[],
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          source=('{0}/projects/my-project/zones/central2-a/'
                                  'disks/disk-1'.format(self.compute_uri)),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.PERSISTENT))],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testTagsOptions(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --tags tag-1,tag-2
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=m.Tags(items=['tag-1', 'tag-2'])),
              project='my-project',
              zone='central2-a',
          ))],)

  def testCreateNetworkingOptions(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [m.Zone(name='central2-a'),
         m.Zone(name='central2-b'),
         m.Zone(name='central2-c')],
        [m.Address(name='address-1', address='74.125.28.139')],
        [m.Image(
            name=self.cos_image_name,
            selfLink=self.cos_image_path,
            creationTimestamp='2016-06-06T18:52:15.455-07:00')],
        [],
    ])
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --can-ip-forward
          --network some-other-network
          --private-network-ip 10.240.0.5
          --address address-1
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.addresses,
          'Get',
          m.ComputeAddressesGetRequest(
              address='address-1',
              project='my-project',
              region='central2'))],
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=True,
                  disks=[self.default_attached_disk],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          natIP='74.125.28.139',
                          type=(m.AccessConfig.TypeValueValuesEnum
                                .ONE_TO_ONE_NAT))],
                      network=('{0}/projects/my-project/global/networks/'
                               'some-other-network'.format(self.compute_uri)),
                      networkIP='10.240.0.5')],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testExplicitDefaultScopes(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --scopes compute-rw,default
          --container-image=gcr.io/my-docker/test-image
        """)
    expected_scopes = sorted([
        'https://www.googleapis.com/auth/compute',
        'https://www.googleapis.com/auth/devstorage.read_only',
        'https://www.googleapis.com/auth/logging.write',
        'https://www.googleapis.com/auth/monitoring.write',
        'https://www.googleapis.com/auth/pubsub',
        'https://www.googleapis.com/auth/service.management.readonly',
        'https://www.googleapis.com/auth/servicecontrol',
        'https://www.googleapis.com/auth/trace.append'])
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[m.ServiceAccount(
                      email='default',
                      scopes=expected_scopes)],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testCreateScopeOptions(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --scopes compute-rw
          --service-account 1234@project.gserviceaccount.com
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[m.ServiceAccount(
                      email='1234@project.gserviceaccount.com',
                      scopes=['https://www.googleapis.com/auth/compute'])],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testCreateSchedulingPolicyOptions(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --preemptible
          --no-restart-on-failure
          --maintenance-policy=terminate
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(
                      automaticRestart=False,
                      onHostMaintenance=(
                          m.Scheduling.OnHostMaintenanceValueValuesEnum
                          .TERMINATE),
                      preemptible=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testCreateMachineTypeOptions(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --machine-type=n1-standard-1
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testCreateCustomMachineTypeOptions(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [m.Zone(name='central2-a'),
         m.Zone(name='central2-b'),
         m.Zone(name='central2-c')],
        [m.MachineType(
            creationTimestamp='2013-09-06T17:54:10.636-07:00',
            guestCpus=int(10),
            memoryMb=int(1000))],
        [m.Image(
            name=self.cos_image_name,
            selfLink=self.cos_image_path,
            creationTimestamp='2016-06-06T18:52:15.455-07:00')],
        [],
    ])
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --custom-cpu 10
          --custom-memory 1000MiB
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.machineTypes,
          'Get',
          m.ComputeMachineTypesGetRequest(
              machineType='custom-10-1000',
              project='my-project',
              zone='central2-a'))],
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk],
                  labels=self.default_labels,
                  machineType=('{0}/projects/my-project/zones/central2-a/'
                               'machineTypes/custom-10-1000'
                               .format(self.compute_uri)),
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testCreateExtendedCustomMachineTypeOptions(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [m.Zone(name='central2-a'),
         m.Zone(name='central2-b'),
         m.Zone(name='central2-c')],
        [m.MachineType(
            creationTimestamp='2013-09-06T17:54:10.636-07:00',
            guestCpus=int(10),
            memoryMb=int(1000))],
        [m.Image(
            name=self.cos_image_name,
            selfLink=self.cos_image_path,
            creationTimestamp='2016-06-06T18:52:15.455-07:00')],
        [],
    ])
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --custom-cpu 10
          --custom-memory 1000MiB
          --custom-extensions
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.machineTypes,
          'Get',
          m.ComputeMachineTypesGetRequest(
              machineType='custom-10-1000-ext',
              project='my-project',
              zone='central2-a'))],
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk],
                  labels=self.default_labels,
                  machineType=('{0}/projects/my-project/zones/central2-a/'
                               'machineTypes/custom-10-1000-ext'
                               .format(self.compute_uri)),
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testCreateRequireDockerImageOrSpec(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Missing required argument \[--container-image\]: '
        'You must provide container image'):
      self.Run("""
          compute instances create-with-container instance-1
            --zone central2-a
          """)

  def testCreateExistingBootDisk(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--disk\]: '
        r'Boot disk specified for containerized VM.'):
      self.Run("""
          compute instances create-with-container instance-1
            --zone central2-a
            --disk name=disk-1,boot=yes
            --container-image=gcr.io/my-docker/test-image
          """)

  def testCreateMetadataKeyConflict(self):
    with self.AssertRaisesExceptionMatches(
        containers_utils.InvalidMetadataKeyException,
        'Metadata key "user-data" is not allowed when '
        'running containerized VM'):
      self.Run("""
          compute instances create-with-container instance-1
            --zone central2-a
            --metadata user-data=somedata
            --container-image=gcr.io/my-docker/test-image
          """)

  # Deprecation of --scopes flag tests

  def testScopesLegacyFormatDeprecationNotice(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'Invalid value for [--scopes]: Flag format --scopes [ACCOUNT=]SCOPE,'
        '[[ACCOUNT=]SCOPE, ...] is removed. Use --scopes [SCOPE,...] '
        '--service-account ACCOUNT instead.'):
      self.Run('compute instances create-with-container instance-1 '
               '--scopes=acc1=scope1,acc1=scope2 '
               '--zone zone-1 '
               '--container-image=gcr.io/my-docker/test-image')

  def testScopesNewFormatNoDeprecationNotice(self):
    self.Run('compute instances create-with-container asdf '
             '--scopes=scope1,scope2 --service-account acc1@example.com '
             '--zone zone-1 '
             '--container-image=gcr.io/my-docker/test-image')
    self.AssertErrEquals('')

  def testNoServiceAccount(self):
    with self.AssertRaisesExceptionRegexp(
        calliope_exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instances create-with-container asdf '
               '--no-service-account '
               '--zone zone-1 '
               '--container-image=gcr.io/my-docker/test-image')

  def testScopesWithNoServiceAccount(self):
    with self.AssertRaisesExceptionRegexp(
        calliope_exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instances create-with-container asdf '
               '--scopes=scope1 --no-service-account '
               '--zone zone-1 '
               '--container-image=gcr.io/my-docker/test-image')

  def testCreateWithLabels(self):
    m = self.messages
    self.Run("""
       compute instances create-with-container instance-1
         --zone=central2-a
         --machine-type=n1-standard-1
         --container-image=gcr.io/my-docker/test-image
         --labels=k0=v0,k-1=v-1
         --labels=foo=bar
       """)

    labels_in_request = (
        ('container-vm', 'cos-dev-63-8872-76-0'),
        ('foo', 'bar'),
        ('k-1', 'v-1'),
        ('k0', 'v0')
    )
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk],
                  labels=m.Instance.LabelsValue(
                      additionalProperties=[
                          m.Instance.LabelsValue.AdditionalProperty(
                              key=pair[0], value=pair[1])
                          for pair in labels_in_request]),
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testCreateWithInvalidLabels(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run("""
          compute instances create-with-container instance-with-labels
            --zone=central2-a
            --machine-type=n1-standard-1
            --container-image=gcr.io/my-docker/test-image
            --labels=inv@lid-key=inv@l!d-value
          """)

  def testWithCustomImage(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --image my-image
          --image-project my-image-project
        """)
    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage='{}/projects/my-image-project/'
                            'global/images/my-image'.format(self.compute_uri)),
                        licenses=[],
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                labels=m.Instance.LabelsValue(
                    additionalProperties=[
                        m.Instance.LabelsValue.AdditionalProperty(
                            key='container-vm', value='my-image')]
                ),
                machineType=self.default_machine_type,
                metadata=self.default_metadata,
                name='instance-1',
                networkInterfaces=[self.default_network_interface],
                scheduling=m.Scheduling(automaticRestart=True),
                serviceAccounts=[self.default_service_account],
                tags=self.default_tags),
            project='my-project',
            zone='central2-a'))])

    self.AssertErrEquals('WARNING: This container deployment mechanism '
                         'requires a Container-Optimized OS image in order to '
                         'work. Select an image from a cos-cloud project '
                         '(cost-stable, cos-beta, cos-dev image families).\n')


class InstancesCreateFromContainerWithPublicDnsTest(
    InstancesCreateWithContainerTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self._SetUp()

  def CreateRequestWithPublicDns(self,
                                 set_ptr=None,
                                 ptr_domain_name=None):
    m = self.messages

    access_config = m.AccessConfig(
        name='external-nat',
        type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)

    if set_ptr is not None:
      access_config.setPublicPtr = bool(set_ptr)
    if ptr_domain_name is not None:
      access_config.publicPtrDomainName = ptr_domain_name

    return m.ComputeInstancesInsertRequest(
        instance=m.Instance(
            canIpForward=False,
            disks=[self.default_attached_disk],
            labels=self.default_labels,
            machineType=self.default_machine_type,
            metadata=self.default_metadata,
            name='instance-1',
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[access_config],
                network=('{0}/projects/my-project/global/networks/default'
                         .format(self.compute_uri)))],
            scheduling=m.Scheduling(automaticRestart=True),
            serviceAccounts=[self.default_service_account],
            tags=self.default_tags),
        project='my-project',
        zone='central2-a',)

  def testPublicDnsDisabledByDefault(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          self.CreateRequestWithPublicDns())],)

  def testEnablePtr(self):
    self.Run("""
        compute instances create-with-container instance-1 --public-ptr
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          self.CreateRequestWithPublicDns(set_ptr=True))],)

  def testDisablePtr(self):
    self.Run("""
        compute instances create-with-container instance-1 --no-public-ptr
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          self.CreateRequestWithPublicDns(set_ptr=False))],)

  def testSetPtrDomainName(self):
    self.Run("""
        compute instances create-with-container instance-1
          --public-ptr --public-ptr-domain example.com
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert', self.CreateRequestWithPublicDns(
            set_ptr=True, ptr_domain_name='example.com'))],)

  def testDisablePtrDomainName(self):
    self.Run("""
        compute instances create-with-container instance-1
          --no-public-ptr-domain
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          self.CreateRequestWithPublicDns())],)

  def testInvalidPublicDnsSettings(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-dns: At most one of --public-dns | '
        '--no-public-dns may be specified.'):
      self.Run("""
          compute instances create-with-container instance-1 --no-public-dns
            --public-dns
            --zone central2-a
            --container-image=gcr.io/my-docker/test-image
          """)

    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-ptr: At most one of --public-ptr | --no-public-ptr '
        'may be specified.'):
      self.Run("""
          compute instances create-with-container instance-1 --no-public-ptr
            --public-ptr
            --zone central2-a
            --container-image=gcr.io/my-docker/test-image
          """)

    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-ptr-domain: At most one of --public-ptr-domain | '
        '--no-public-ptr-domain may be specified.'):
      self.Run("""
          compute instances create-with-container instance-1
            --no-public-ptr-domain
            --public-ptr-domain example.com
            --zone central2-a
            --container-image=gcr.io/my-docker/test-image
          """)


class InstancesCreateFromContainerWithNetworkTierTest(
    InstancesCreateWithContainerTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self._SetUp()

  def CreateRequestWithNetworkTier(self, network_tier):
    m = self.messages
    if network_tier:
      network_tier_enum = m.AccessConfig.NetworkTierValueValuesEnum(
          network_tier)
    else:
      network_tier_enum = None
    return m.ComputeInstancesInsertRequest(
        instance=m.Instance(
            canIpForward=False,
            disks=[self.default_attached_disk],
            labels=self.default_labels,
            machineType=self.default_machine_type,
            metadata=self.default_metadata,
            name='instance-1',
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[
                        m.AccessConfig(
                            name='external-nat',
                            type=m.AccessConfig.TypeValueValuesEnum.
                            ONE_TO_ONE_NAT,
                            networkTier=network_tier_enum)
                    ],
                    network=('{0}/projects/my-project/global/networks/default'
                             .format(self.compute_uri)))
            ],
            scheduling=m.Scheduling(automaticRestart=True),
            serviceAccounts=[self.default_service_account],
            tags=self.default_tags),
        project='my-project',
        zone='central2-a',
    )

  def testWithDefaultNetworkTier(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier(None))],
    )

  def testWithPremiumNetworkTier(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --network-tier PREMIUM
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier('PREMIUM'))],
    )

  def testWithStandardNetworkTier(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --network-tier standard
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier('STANDARD'))],
    )

  def testNetworkTierNotSupported(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[RANDOM-NETWORK-TIER\]'):
      self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --network-tier random-network-tier
          """)


# BETA versions of above test classes that use GA track.
class InstancesCreateWithContainerTestBeta(InstancesCreateWithContainerTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self._SetUp()

  def testAdditionalAttachedDisks(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --local-ssd ''
          --local-ssd device-name=foo
          --local-ssd device-name=bar,interface=NVME
          --disk name=disk-1,mode=rw,device-name=x,boot=no
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[
                      self.default_attached_disk,
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          licenses=[],
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          source=('{0}/projects/my-project/zones/central2-a/'
                                  'disks/disk-1'.format(self.compute_uri)),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.PERSISTENT)),
                      m.AttachedDisk(
                          autoDelete=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              diskType=('{0}/projects/my-project/zones/'
                                        'central2-a/diskTypes/local-ssd'
                                        .format(self.compute_uri))),
                          licenses=[],
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
                      m.AttachedDisk(
                          autoDelete=True,
                          deviceName='foo',
                          initializeParams=m.AttachedDiskInitializeParams(
                              diskType=('{0}/projects/my-project/zones/'
                                        'central2-a/diskTypes/local-ssd'
                                        .format(self.compute_uri))),
                          licenses=[],
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
                      m.AttachedDisk(
                          autoDelete=True,
                          deviceName='bar',
                          initializeParams=m.AttachedDiskInitializeParams(
                              diskType=('{0}/projects/my-project/zones/'
                                        'central2-a/diskTypes/local-ssd'
                                        .format(self.compute_uri))),
                          interface=(m.AttachedDisk
                                     .InterfaceValueValuesEnum.NVME),
                          licenses=[],
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH)],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)


class InstancesCreateFromContainerWithPublicDnsTestBeta(
    InstancesCreateFromContainerWithPublicDnsTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self._SetUp()


class InstancesCreateFromContainerWithNetworkTierTestBeta(
    InstancesCreateFromContainerWithNetworkTierTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self._SetUp()


class InstancesCreateFromContainerAlphaTest(
    InstancesCreateWithContainerTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self._SetUp()

  def CreateRequestWithNetworkTier(self, network_tier):
    m = self.messages
    if network_tier:
      network_tier_enum = m.AccessConfig.NetworkTierValueValuesEnum(
          network_tier)
    else:
      network_tier_enum = None
    return m.ComputeInstancesInsertRequest(
        instance=m.Instance(
            canIpForward=False,
            disks=[self.default_attached_disk],
            labels=self.default_labels,
            machineType=self.default_machine_type,
            metadata=self.default_metadata,
            name='instance-1',
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[m.AccessConfig(
                    name='external-nat',
                    type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT,
                    networkTier=network_tier_enum)],
                network=('{0}/projects/my-project/global/networks/default'
                         .format(self.compute_uri)))],
            scheduling=m.Scheduling(automaticRestart=True),
            serviceAccounts=[self.default_service_account],
            tags=self.default_tags),
        project='my-project',
        zone='central2-a',)

  def testAdditionalAttachedDisks(self):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --local-nvdimm ''
          --local-nvdimm size=3TB
          --disk name=disk-1,mode=rw,device-name=x,boot=no
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[
                      self.default_attached_disk,
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          licenses=[],
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          source=('{0}/projects/my-project/zones/central2-a/'
                                  'disks/disk-1'.format(self.compute_uri)),
                          type=(m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)),
                      m.AttachedDisk(
                          autoDelete=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              diskType=('{0}/projects/my-project/zones/'
                                        'central2-a/diskTypes/aep-nvdimm'
                                        .format(self.compute_uri))),
                          interface=(m.AttachedDisk.InterfaceValueValuesEnum
                                     .NVDIMM),
                          licenses=[],
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
                      m.AttachedDisk(
                          autoDelete=True,
                          diskSizeGb=3072,
                          initializeParams=m.AttachedDiskInitializeParams(
                              diskType=('{0}/projects/my-project/zones/'
                                        'central2-a/diskTypes/aep-nvdimm'
                                        .format(self.compute_uri))),
                          interface=(m.AttachedDisk.InterfaceValueValuesEnum
                                     .NVDIMM),
                          licenses=[],
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH)
                  ],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testEnablePublicDns(self):
    self.Run("""
        compute instances create-with-container instance-1 --public-dns
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          self.CreateRequestWithPublicDns(set_public_dns=True))],)

  def CreateRequestWithPublicDns(self,
                                 set_public_dns=None,
                                 set_ptr=None,
                                 ptr_domain_name=None):
    m = self.messages

    access_config = m.AccessConfig(
        name='external-nat',
        type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)

    if set_public_dns is not None:
      access_config.setPublicDns = bool(set_public_dns)
    if set_ptr is not None:
      access_config.setPublicPtr = bool(set_ptr)
    if ptr_domain_name is not None:
      access_config.publicPtrDomainName = ptr_domain_name

    return m.ComputeInstancesInsertRequest(
        instance=m.Instance(
            canIpForward=False,
            disks=[self.default_attached_disk],
            labels=self.default_labels,
            machineType=self.default_machine_type,
            metadata=self.default_metadata,
            name='instance-1',
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[access_config],
                network=('{0}/projects/my-project/global/networks/default'
                         .format(self.compute_uri)))],
            scheduling=m.Scheduling(automaticRestart=True),
            serviceAccounts=[self.default_service_account],
            tags=self.default_tags),
        project='my-project',
        zone='central2-a',)

  def testDisablePublicDns(self):
    self.Run("""
        compute instances create-with-container instance-1 --no-public-dns
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          self.CreateRequestWithPublicDns(set_public_dns=False))],)

  def testWithDefaultNetworkTier(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier(None))],)

  def testWithPremiumNetworkTier(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --network-tier PREMIUM
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          self.CreateRequestWithNetworkTier('PREMIUM'))],)

  def testWithSelectNetworkTier(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --network-tier select
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          self.CreateRequestWithNetworkTier('SELECT'))],)

  def testWithStandardNetworkTier(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --network-tier standard
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          self.CreateRequestWithNetworkTier('STANDARD'))],)

  def testNetworkTierNotSupported(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[RANDOM-NETWORK-TIER\]'
    ):
      self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --network-tier random-network-tier
          """)

  def createWithOnHostMaintenanceTest(self, flag):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          {}=terminate
          --container-image=gcr.io/my-docker/test-image
        """.format(flag))
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=self.default_metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(
                      automaticRestart=True,
                      onHostMaintenance=(
                          m.Scheduling.OnHostMaintenanceValueValuesEnum
                          .TERMINATE)),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  def testWithOnHostMaintenance(self):
    self.createWithOnHostMaintenanceTest('--on-host-maintenance')

  def testMaintenancePolicyDeprecation(self):
    self.createWithOnHostMaintenanceTest('--maintenance-policy')
    self.AssertErrContains(
        'WARNING: The --maintenance-policy flag is now deprecated. '
        'Please use `--on-host-maintenance` instead')


class InstancesCreateFromContainerContainerMountDiskTestBeta(
    InstancesCreateWithContainerTestBase,
    parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.SelectApi('beta')
    self._SetUp()

  def GetDiskMessage(self, initialize_params=None, mode=None, source=None,
                     auto_delete=False, device_name='disk-1'):
    m = self.messages
    return m.AttachedDisk(
        autoDelete=auto_delete,
        boot=False,
        deviceName=device_name,
        licenses=[],
        initializeParams=initialize_params,
        mode=mode or m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
        source=source,
        type=(m.AttachedDisk.TypeValueValuesEnum.PERSISTENT))

  def _CheckCallsForCreateInstanceWithContainer(self, disk, container_manifest):
    m = self.messages
    metadata = m.Metadata(items=[
        m.Metadata.ItemsValueListEntry(
            key='gce-container-declaration',
            value=containers_utils.DumpYaml(container_manifest)),
        m.Metadata.ItemsValueListEntry(
            key='google-logging-enabled', value='true')])
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk, disk],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],)

  @parameterized.named_parameters(
      ('DeviceNameGiven', 'name=disk-1,mode=rw,device-name=disk-1',
       'name=disk-1,mount-path="/mounted"', False),
      ('DeviceNameNotGiven', 'name=disk-1,mode=rw',
       'name=disk-1,mount-path="/mounted"', True),
      ('DeviceNameNotGivenAndDiskNameNotGiven', 'name=disk-1,mode=rw',
       'mount-path="/mounted"', True),
      ('ContainerNameNotGiven', 'name=disk-1,mode=rw,device-name=disk-1',
       'mount-path="/mounted"', False))
  def testContainerMountDiskCreate(self, disk_flag_value, container_flag_value,
                                   expect_warning):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --create-disk {}
          --container-mount-disk {}
        """.format(disk_flag_value, container_flag_value))
    disk = self.GetDiskMessage(
        initialize_params=m.AttachedDiskInitializeParams(
            diskName='disk-1'),
        auto_delete=True)
    container_manifest = {
        'spec': {
            'containers': [{
                'name': 'instance-1',
                'image': 'gcr.io/my-docker/test-image',
                'securityContext': {
                    'privileged': False
                },
                'stdin': False,
                'tty': False,
                'volumeMounts': [{
                    'name': 'pd-0',
                    'mountPath': '/mounted',
                    'readOnly': False
                }]
            }],
            'restartPolicy':
                'Always',
            'volumes': [{
                'name': 'pd-0',
                'gcePersistentDisk': {
                    'pdName': 'disk-1',
                    'fsType': 'ext4'
                }
            }]
        }
    }
    self._CheckCallsForCreateInstanceWithContainer(disk, container_manifest)
    warning_text = (
        'Default device-name for disk name [disk-1] will be [disk-1] because '
        'it is being mounted to a container with [`--container-mount-disk`]')
    if expect_warning:
      self.AssertErrContains(warning_text)
    else:
      self.AssertErrNotContains(warning_text)

  @parameterized.named_parameters(
      ('DeviceNameGiven', 'name=disk-1,mode=rw,device-name=disk-1',
       'name=disk-1,mount-path="/mounted"', False),
      ('DeviceNameNotGiven', 'name=disk-1,mode=rw',
       'name=disk-1,mount-path="/mounted"', True),
      ('DeviceNameNotGivenAndDiskNameNotGiven', 'name=disk-1,mode=rw',
       'mount-path="/mounted"', True),
      ('ContainerNameNotGiven', 'name=disk-1,mode=rw,device-name=disk-1',
       'mount-path="/mounted"', False))
  def testContainerMountDiskAttach(self, disk_flag_value, container_flag_value,
                                   expect_warning):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --disk {}
          --container-mount-disk {}
        """.format(disk_flag_value, container_flag_value))
    disk = self.GetDiskMessage(
        source='{}/projects/my-project/zones/central2-a/disks/disk-1'.format(
            self.compute_uri))
    container_manifest = {
        'spec': {
            'containers': [{
                'name': 'instance-1',
                'image': 'gcr.io/my-docker/test-image',
                'securityContext': {
                    'privileged': False
                },
                'stdin': False,
                'tty': False,
                'volumeMounts': [{
                    'name': 'pd-0',
                    'mountPath': '/mounted',
                    'readOnly': False
                }]
            }],
            'restartPolicy':
                'Always',
            'volumes': [{
                'name': 'pd-0',
                'gcePersistentDisk': {
                    'pdName': 'disk-1',
                    'fsType': 'ext4'
                }
            }]
        }
    }
    self._CheckCallsForCreateInstanceWithContainer(disk, container_manifest)
    warning_text = (
        'Default device-name for disk name [disk-1] will be [disk-1] because '
        'it is being mounted to a container with [`--container-mount-disk`]')
    if expect_warning:
      self.AssertErrContains(warning_text)
    else:
      self.AssertErrNotContains(warning_text)

  def testContainerMountDiskWithOptions(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --disk name=disk-1,mode=rw,device-name=disk-1
          --container-mount-disk
          name=disk-1,mode=ro,mount-path="/mounted",partition=1
          --container-mount-disk
          name=disk-1,mode=ro,mount-path="/mounted-1",partition=2
        """)
    disk = self.GetDiskMessage(
        source=('{0}/projects/my-project/zones/central2-a/'
                'disks/disk-1'.format(self.compute_uri)))
    container_manifest = {
        'spec': {
            'containers': [{
                'name': 'instance-1',
                'image': 'gcr.io/my-docker/test-image',
                'securityContext': {
                    'privileged': False
                },
                'stdin': False,
                'tty': False,
                'volumeMounts': [
                    {'name': 'pd-0',
                     'mountPath': '/mounted',
                     'readOnly': True},
                    {'name': 'pd-1',
                     'mountPath': '/mounted-1',
                     'readOnly': True}]
            }],
            'restartPolicy':
                'Always',
            'volumes': [
                {'name': 'pd-0',
                 'gcePersistentDisk': {
                     'pdName': 'disk-1',
                     'fsType': 'ext4',
                     'partition': 1}},
                {'name': 'pd-1',
                 'gcePersistentDisk': {
                     'pdName': 'disk-1',
                     'fsType': 'ext4',
                     'partition': 2}}
            ]
        }
    }
    self._CheckCallsForCreateInstanceWithContainer(disk, container_manifest)

  @parameterized.named_parameters(
      ('NameGivenWithPartition',
       '--container-mount-disk '
       'name=disk-1,mode=ro,mount-path="/mounted",partition=1 '
       '--container-mount-disk '
       'name=disk-1,mode=ro,mount-path="/mounted-1",partition=1',
       {'pdName': 'disk-1', 'fsType': 'ext4', 'partition': 1}),
      ('NameNotGivenWithPartition',
       '--container-mount-disk mode=ro,mount-path="/mounted",partition=1 '
       '--container-mount-disk mode=ro,mount-path="/mounted-1",partition=1',
       {'pdName': 'disk-1', 'fsType': 'ext4', 'partition': 1}),
      ('NameGivenNoPartition',
       '--container-mount-disk name=disk-1,mode=ro,mount-path="/mounted" '
       '--container-mount-disk name=disk-1,mode=ro,mount-path="/mounted-1"',
       {'pdName': 'disk-1', 'fsType': 'ext4'}),
      ('NameNotGivenNoPartition',
       '--container-mount-disk mode=ro,mount-path="/mounted" '
       '--container-mount-disk mode=ro,mount-path="/mounted-1"',
       {'pdName': 'disk-1', 'fsType': 'ext4'}))
  def testContainerMountDiskWithRepeatedDiskAndPartition(
      self, container_mount_disk_flag, volume_pd_config):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --disk name=disk-1,mode=rw,device-name=disk-1
          {}
        """.format(container_mount_disk_flag))
    disk = self.GetDiskMessage(
        source=('{0}/projects/my-project/zones/central2-a/'
                'disks/disk-1'.format(self.compute_uri)))
    container_manifest = {
        'spec': {
            'containers': [{
                'name': 'instance-1',
                'image': 'gcr.io/my-docker/test-image',
                'securityContext': {
                    'privileged': False
                },
                'stdin': False,
                'tty': False,
                'volumeMounts': [
                    {'name': 'pd-0',
                     'mountPath': '/mounted',
                     'readOnly': True},
                    {'name': 'pd-0',
                     'mountPath': '/mounted-1',
                     'readOnly': True}]
            }],
            'restartPolicy':
                'Always',
            'volumes': [
                {'name': 'pd-0',
                 'gcePersistentDisk': volume_pd_config}
            ]
        }
    }
    self._CheckCallsForCreateInstanceWithContainer(disk, container_manifest)

  @parameterized.named_parameters(
      # device-name, if given, must be the same as name.
      ('AttachMismatched', '--disk name=disk-1,mode=rw,device-name=pd-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)\[disk-1\](.*)\[pd-1\]'),
      ('CreateMismatched',
       '--create-disk name=disk-1,mode=rw,device-name=pd-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)\[disk-1\](.*)\[pd-1\]'),
      # --disk or --create-disk must have a disk whose name matches.
      ('NoDisk', '',
       '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)Must be used with `--disk` or '
       r'`--create-disk`'),
      ('AttachNotFound', '--disk name=disk-2,mode=rw,device-name=disk-2',
       '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)\[disk-1\]'),
      ('CreateNotFound',
       '--create-disk name=disk-2,mode=rw,device-name=disk-2',
       '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)\[disk-1\]'),
      # If no name is given for --container-mount-disk, there can be only one
      # disk specified with --disk or --create-disk.
      ('NoNameSpecified', '--disk name=disk-1,mode=rw,device-name=disk-1 '
       '--disk name=disk-2,mode=rw,device-name=disk-2',
       '--container-mount-disk mount-path="/mounted"',
       r'--container-mount-disk(.*)Must specify the name of the disk to be '
       r'mounted'),
      # If no name is given for --create-disk, should fail.
      ('DiskNameNotGiven', '--create-disk mode=rw',
       '--container-mount-disk mount-path="/mounted"',
       r'--container-mount-disk'),
      # attached disk mode must be rw if --container-mount-disk mode is rw.
      ('MismatchedModeAttach', '--disk name=disk-1,mode=ro,device-name=disk-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted",mode=rw',
       r'--container-mount-disk(.*)\[rw\](.*)\[ro\](.*)disk name \[disk-1\], '
       r'partition \[None\]'),
      ('MismatchedModeCreate',
       '--create-disk name=disk-1,mode=ro,device-name=disk-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted",mode=rw',
       r'--container-mount-disk(.*)\[rw\](.*)\[ro\](.*)disk name \[disk-1\], '
       r'partition \[None\]'),
      ('CreatedInROMode',
       '--create-disk name=disk-1,mode=ro,device-name=disk-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted",mode=ro',
       r'--container-mount-disk(.*)disk named \[disk-1\](.*)disk is created '
       r'in \[ro\] mode'),
      ('PartitionWithCreateDisk',
       '--create-disk name=disk-1,device-name=disk-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted",partition=1',
       r'--container-mount-disk(.*)partition'))
  def testContainerMountDiskInvalid(self, disk_flag, container_mount_flag,
                                    regexp):
    with self.assertRaisesRegexp(
        calliope_exceptions.InvalidArgumentException,
        regexp):
      self.Run("""
          compute instances create-with-container instance-1
            --zone central2-a
            --container-image=gcr.io/my-docker/test-image
            {}
            {}
          """.format(disk_flag, container_mount_flag))


class InstancesCreateFromContainerContainerMountDiskTestAlpha(
    InstancesCreateFromContainerContainerMountDiskTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.SelectApi('alpha')
    self._SetUp()

if __name__ == '__main__':
  test_case.main()
