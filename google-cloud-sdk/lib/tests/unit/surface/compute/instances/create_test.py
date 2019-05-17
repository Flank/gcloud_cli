# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests for the instances create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random
import re
import textwrap

from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.sole_tenancy import util as sole_tenancy_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.cli_test_base import MockArgumentError
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
from tests.lib.surface.compute import utils


import mock
from six.moves import range


_DEFAULT_SCOPES = sorted([
    'https://www.googleapis.com/auth/devstorage.read_only',
    'https://www.googleapis.com/auth/logging.write',
    'https://www.googleapis.com/auth/monitoring.write',
    'https://www.googleapis.com/auth/servicecontrol',
    'https://www.googleapis.com/auth/service.management.readonly',
    'https://www.googleapis.com/auth/pubsub',
    'https://www.googleapis.com/auth/trace.append',
])


def _DefaultMachineTypeOf(api_version):
  return ('https://www.googleapis.com/compute/{ver}/projects/my-project/zones/'
          'central2-a/machineTypes/n1-standard-1').format(ver=api_version)


def _DefaultPreemptibleMachineTypeOf(api_version):
  return ('https://www.googleapis.com/compute/{ver}/projects/my-project/zones/'
          'us-central1-b/machineTypes/n1-standard-1').format(ver=api_version)


def _DefaultNetworkOf(api_version):
  return ('https://www.googleapis.com/compute/{ver}/projects/my-project/'
          'global/networks/default').format(ver=api_version)


def _DefaultImageOf(api_version):
  return ('https://www.googleapis.com/compute/{ver}/projects/debian-cloud/'
          'global/images/family/debian-9').format(ver=api_version)


def _NvdimmDiskTypeOf(api_version):
  return ('https://www.googleapis.com/compute/{ver}/projects/my-project/'
          'zones/central2-a/diskTypes/aep-nvdimm').format(ver=api_version)


def _SsdDiskTypeOf(api_version):
  return ('https://www.googleapis.com/compute/{ver}/projects/my-project/'
          'zones/central2-a/diskTypes/local-ssd').format(ver=api_version)


def _OtherImageOf(api_version):
  return ('https://www.googleapis.com/compute/{ver}/projects/'
          'some-other-project/global/images/other-image'.format(
              ver=api_version))


def _AcceleratorTypeOf(api_version, name):
  return ('https://www.googleapis.com/compute/{ver}/projects/my-project/'
          'zones/central2-a/acceleratorTypes/{name}'.format(
              ver=api_version, name=name))


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)

  test_obj._default_image = _DefaultImageOf(api_version)
  test_obj._default_machine_type = _DefaultMachineTypeOf(api_version)
  test_obj._default_network = _DefaultNetworkOf(api_version)
  test_obj._one_to_one_nat = (
      test_obj.messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)
  test_obj._other_image = _OtherImageOf(api_version)
  test_obj._nvdimm_disk_type = _NvdimmDiskTypeOf(api_version)
  test_obj._ssd_disk_type = _SsdDiskTypeOf(api_version)
  test_obj._default_network_tier = None

  if api_version == 'v1':
    test_obj._instances = test_resources.INSTANCES_V1
  elif api_version == 'alpha':
    test_obj._instances = test_resources.INSTANCES_ALPHA
  elif api_version == 'beta':
    test_obj._instances = test_resources.INSTANCES_BETA
  else:
    raise ValueError('api_version must be \'v1\', \'beta\', or \'alpha\'. '
                     'Got [{0}].'.format(api_version))

  random.seed(1)
  system_random_patcher = mock.patch(
      'random.SystemRandom', new=lambda: random)
  test_obj.addCleanup(system_random_patcher.stop)
  system_random_patcher.start()

  test_obj.make_requests.side_effect = iter([
      [
          test_obj.messages.Zone(name='central2-a'),
      ],
      [
          test_obj.messages.Project(
              defaultServiceAccount='default@service.account'),
      ],
      [],
  ])


class InstancesCreateTestsMixin(test_base.BaseTest):

  def SetUp(self):
    self.project_get_request_v1 = [
        (self.compute_v1.projects,
         'Get',
         self.v1_messages.ComputeProjectsGetRequest(
             project=self.Project()))
    ]

    self.project_get_request_alpha = [
        (self.compute_alpha.projects,
         'Get',
         self.alpha_messages.ComputeProjectsGetRequest(
             project=self.Project()))
    ]

    self.project_get_request_beta = [
        (self.compute_beta.projects,
         'Get',
         self.beta_messages.ComputeProjectsGetRequest(
             project=self.Project()))
    ]

  def SelectApi(self, api, resource_api=None):
    super(InstancesCreateTestsMixin, self).SelectApi(api, resource_api)
    self.project_get_request = getattr(self, 'project_get_request_' + api, None)

  def Project(self):
    project = super(InstancesCreateTestsMixin, self).Project()
    if project:
      return project
    return 'my-project'


class InstancesCreateTestBase(InstancesCreateTestsMixin,
                              sdk_test_base.WithFakeAuth,
                              waiter_test_base.Base):
  API_VERSION = 'v1'

  def SetUp(self):
    self.SelectApi(self.API_VERSION)
    self.api_mock = utils.ComputeApiMock(
        self.API_VERSION, project=self.Project(), zone='central2-a').Start()
    self.addCleanup(self.api_mock.Stop)

    self.status_enum = self.api_mock.messages.Operation.StatusValueValuesEnum

  def TearDown(self):
    self.api_mock.batch_responder.AssertDone()

  def GetInstanceRef(self, name, zone=None):
    return self.api_mock.resources.Parse(
        name,
        params={'project': self.Project(), 'zone': zone or self.api_mock.zone},
        collection='compute.instances')

  def GetImageRef(self, name, project=None):
    return self.api_mock.resources.Create(
        'compute.images', image=name, project=project or self.Project())

  def GetNetworkRef(self, name, project=None):
    return self.api_mock.resources.Parse(
        name,
        params={'project': self.Project()},
        collection='compute.networks')

  def GetMachineTypeRef(self, name, zone=None, project=None):
    return self.api_mock.resources.Parse(
        name,
        params={'project': project or self.Project(),
                'zone': zone or self.api_mock.zone},
        collection='compute.machineTypes')

  def GetOperationRef(self, name, zone=None, region=None):
    params = {'project': self.Project()}
    if region:
      collection = 'compute.regionOperations'
      params['region'] = region
    elif zone:
      collection = 'compute.zoneOperations'
      params['zone'] = zone
    else:
      collection = 'compute.zoneOperations'
      params['zone'] = self.api_mock.zone

    return self.api_mock.resources.Parse(
        name, params, collection=collection)

  def GetOperationMessage(self, operation_ref, status, errors=None):
    operation_cls = self.api_mock.messages.Operation
    operation = operation_cls(
        name=operation_ref.Name(),
        status=status,
        selfLink=operation_ref.SelfLink())
    if errors:
      operations_errors = []
      for e in errors:
        operations_errors.append(
            operation_cls.ErrorValue.ErrorsValueListEntry(
                code=e['code'], message=e['message']))
      operation.error = operation_cls.ErrorValue(errors=operations_errors)
    return operation

  def GetCreateInstanceRequest(self, instance_ref,
                               image_ref=None,
                               machine_type_ref=None,
                               network_ref=None):
    image_ref = (image_ref or self.GetImageRef('family/debian-9',
                                               project='debian-cloud'))
    machine_type_ref = (machine_type_ref or
                        self.GetMachineTypeRef('n1-standard-1'))
    network_ref = self.GetNetworkRef('default')
    m = self.api_mock.messages
    payload = m.ComputeInstancesInsertRequest(
        instance=m.Instance(
            canIpForward=False,
            deletionProtection=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=image_ref.SelfLink(),
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=machine_type_ref.SelfLink(),
            metadata=m.Metadata(),
            name=instance_ref.instance,
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[m.AccessConfig(
                    name='external-nat',
                    type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)],
                network=network_ref.SelfLink())],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(
                automaticRestart=True),
        ),
        project=instance_ref.project,
        zone=instance_ref.zone,
    )
    return (self.api_mock.adapter.apitools_client.instances,
            'Insert',
            payload)


class InstancesCreateGaTest(InstancesCreateTestBase):

  def testDefaultOptions_Async(self):
    instance_ref1 = self.GetInstanceRef('instance-1')
    instance_ref2 = self.GetInstanceRef('instance-2')
    operation_ref1 = self.GetOperationRef('operation-1')
    operation_ref2 = self.GetOperationRef('operation-2')
    self.api_mock.batch_responder.ExpectBatch([
        (self.GetCreateInstanceRequest(instance_ref1),
         self.GetOperationMessage(operation_ref1, self.status_enum.PENDING)),
        (self.GetCreateInstanceRequest(instance_ref2),
         self.GetOperationMessage(operation_ref2, self.status_enum.PENDING)),
    ])
    self.Run('compute instances create {} {} --zone {} --async'.format(
        instance_ref1.instance, instance_ref2.instance, instance_ref1.zone))

    self.CheckRequests(self.zone_get_request)

    self.assertMultiLineEqual(
        'Instance creation in progress for [{}]: {}\n'
        'Instance creation in progress for [{}]: {}\n'
        'Use [gcloud compute operations describe URI] command '
        'to check the status of the operation(s).\n'.format(
            instance_ref1.instance, operation_ref1.SelfLink(),
            instance_ref2.instance, operation_ref2.SelfLink()),
        self.GetErr())
    self.AssertOutputEquals('')


class InstancesCreateTest(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'v1')

  def testDefaultOptions(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

    self.AssertOutputNotContains('Please use --image-family')

  def testAliasWithReplacement(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        [
            self.messages.Image(
                name='debian-8-jessie-v20151130',
                selfLink=('https://www.googleapis.com/compute/v1/'
                          'projects/debian-cloud/global/'
                          'images/debian-8-jessie-v20151130'),
            )
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1
          --zone central2-a --image debian-8
        """)

    self.AssertErrContains('Please use --image-family=debian-8 and'
                           ' --image-project=debian-cloud instead.')

  def testAliasWithoutReplacement(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        [
            self.messages.Image(
                name='debian-8-jessie-v20151130',
                selfLink=('https://www.googleapis.com/compute/v1/'
                          'projects/debian-cloud/global/'
                          'images/debian-8-jessie-v20151130'),
            )
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1
          --zone central2-a --image opensuse-13
        """)

    self.AssertErrContains('Please use --image-family and'
                           ' --image-project instead.')

  def testUserOutputDisabled(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a --no-user-output-enabled
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

    self.AssertErrNotContains('instance-1')
    self.AssertOutputNotContains('instance-1')

  def testAttachmentOfExistingBootDisk(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    # Ensures that the boot disk is placed at index 0 of the disks
    # list.
    self.Run("""
        compute instances create instance-1
          --disk name=disk-2
          --disk name=disk-1,boot=yes
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=True,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/'
                                  'disks/disk-1'),
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/'
                                  'disks/disk-2'),
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testAttachmentOfExistingBootDiskWithNonExistentBootDisk(self):
    m = self.messages

    def MakeRequests(*_, **kwargs):
      if kwargs['requests'][0][0] == self.compute.zones:
        # This is the zonal get for deprecation warning.
        yield m.Zone(name='central2-a')
      else:
        # This is where the boot disk is fetched.
        kwargs['errors'].append((404, 'Not Found'))
    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not fetch resource:
         - Not Found
        """)):
      self.Run("""
          compute instances create instance-1
            --disk name=disk-2
            --disk name=disk-1,boot=yes
            --zone central2-a
          """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=True,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/'
                                  'disks/disk-1'),
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/'
                                  'disks/disk-2'),
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES,
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithNonExistentImage(self):
    m = self.messages

    def MakeRequests(*_, **kwargs):
      print(kwargs)
      if kwargs['requests'][0][0] == self.compute.zones:
        yield m.Zone(name='central2-a')
      else:
        kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not fetch resource:
         - Not Found
        """)):
      self.Run("""
          compute instances create instance-1
            --image non-existent-image
            --zone central2-a
          """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=(self.compute_uri +
                                       '/projects/my-project/global/images/'
                                       'non-existent-image'),
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES,
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testPerformanceWarningWithStandardPd(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --boot-disk-size 199GB
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          diskSizeGb=199,
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )
    self.AssertErrContains(
        'WARNING: You have selected a disk size of under [200GB]. This may '
        'result in poor I/O performance. For more information, see: '
        'https://developers.google.com/compute/docs/disks#performance.')

  def testCanIpForward(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --can-ip-forward
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=True,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithDescription(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --description "My Very Excellent Mother Just Served Us Nine Pizzas"
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  description=(
                      'My Very Excellent Mother Just Served Us Nine Pizzas'),
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithSingleScope(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --scopes compute-rw
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],

                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=[
                              'https://www.googleapis.com/auth/compute',
                          ]),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithInvalidServiceAccount(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--service-account]: Invalid format: expected '
        r'default or user@domain\.com, received user@google.com='
        r'https://www\.googleapis\.com/auth/trace\.append'
    ):
      self.Run("""
          compute instances create instance-1
            --service-account user@google.com=https://www.googleapis.com/auth/trace.append
            --zone central2-a
          """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request)

  def testWithNoScopes(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --no-scopes
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],

                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithManyScopes(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --scopes compute-rw,https://www.googleapis.com/auth/devstorage.full_control
          --service-account=1234@project.gserviceaccount.com
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],

                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='1234@project.gserviceaccount.com',
                          scopes=[
                              'https://www.googleapis.com/auth/compute',
                              ('https://www.googleapis.com/auth/devstorage'
                               '.full_control'),
                          ]),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testExplicitDefaultScopes(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --scopes compute-rw,default
          --zone central2-a
        """)

    expected_scopes = (_DEFAULT_SCOPES +
                       ['https://www.googleapis.com/auth/compute'])
    expected_scopes.sort()
    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],

                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=expected_scopes),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithIllegalScopeValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[default=sql=https://www.googleapis.com/auth/devstorage.'
        r'full_control\] is an illegal value for \[--scopes\]. Values must be '
        r'of the form \[SCOPE\].'):
      self.Run("""
          compute instances create instance-1
            --scopes default=sql=https://www.googleapis.com/auth/devstorage.full_control,compute-rw
            --zone central2-a
          """)

    self.CheckRequests(
        self.zone_get_request,)

  def testWithEmptyScopeValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Scope cannot be an empty string.'):
      self.Run("""
          compute instances create instance-1
            --scopes compute-rw,,sql
            --zone central2-a
          """)

    self.CheckRequests()

  def testWithNoAddress(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --no-address
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithIPv4Address(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --address 74.125.28.139
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat,
                          natIP='74.125.28.139')],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithIPv6Address(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --address 2620:0:1009:3:3d84:93bf:5c74:cd14
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat,
                          natIP='2620:0:1009:3:3d84:93bf:5c74:cd14')],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithNamedAddress(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a')
        ],
        [
            m.Address(
                name='address-1',
                address='74.125.28.139'),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --address address-1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.addresses,
          'Get',
          m.ComputeAddressesGetRequest(
              address='address-1',
              project='my-project',
              region='central2'))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat,
                          natIP='74.125.28.139')],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testAddressAndNoAddressMutualExclusion(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --address: At most one of --address | --no-address '
        'may be specified.'):
      self.Run("""
          compute instances create instance-1
            --address 74.125.28.139
            --no-address
            --zone central2-a
          """)

    self.CheckRequests()

  def testWithImageInSameProject(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --image my-image
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=(
                              'https://www.googleapis.com/compute/{0}/projects/'
                              'my-project/global/images/my-image'.format(
                                  self.api)),
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithImageInDifferentProject(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1 --zone central2-a
          --image other-image
          --image-project some-other-project
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._other_image),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithImageInDifferentProjectWithUri(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1 --zone central2-a
          --image other-image
          --image-project https://www.googleapis.com/compute/{0}/projects/some-other-project
        """.format(self.api))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._other_image),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithImageProjectButNoImage(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Must specify either \[--image\] or \[--image-family\] when '
        r'specifying \[--image-project\] flag.'):
      self.Run("""
          compute instances create instance-1
            --image-project some-other-project
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskDeviceNameOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-device-name\] can only be used when creating a new '
        r'boot disk.'):
      self.Run("""
          compute instances create instance-1
            --disk boot=yes,name=my-disk
            --boot-disk-device-name x
            --zone central2-a
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskSizeOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-size\] can only be used when creating a new boot '
        r'disk.'):
      self.Run("""
          compute instances create instance-1
            --disk boot=yes,name=my-disk
            --boot-disk-size 10GB
            --zone central2-a
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskTypeOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-type\] can only be used when creating a new boot '
        r'disk.'):
      self.Run("""
          compute instances create instance-1
            --disk boot=yes,name=my-disk
            --boot-disk-type pd-ssd
            --zone central2-a
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskAutoDeleteOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--no-boot-disk-auto-delete\] can only be used when creating a new '
        'boot disk.'):
      self.Run("""
          compute instances create instance-1
            --disk boot=yes,name=my-disk
            --no-boot-disk-auto-delete
            --zone central2-a
          """)

    self.CheckRequests()

  def testIllegalAutoDeleteValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[auto-delete\] in \[--disk\] must be \[yes\] or \[no\], '
        r'not \[true\].'):
      self.Run("""
          compute instances create instance-1
            --disk boot=yes,name=my-disk,auto-delete=true
            --zone central2-a
          """)

    self.CheckRequests()

  def testWithMetadata(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --metadata x=y,z=1,a=b,c=d
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(
                      items=[
                          m.Metadata.ItemsValueListEntry(key='a', value='b'),
                          m.Metadata.ItemsValueListEntry(key='c', value='d'),
                          m.Metadata.ItemsValueListEntry(key='x', value='y'),
                          m.Metadata.ItemsValueListEntry(key='z', value='1'),
                      ]),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithMetadataFromFile(self):
    m = self.messages

    metadata_file1 = self.Touch(
        self.temp_path, 'file-1', contents='hello')
    metadata_file2 = self.Touch(
        self.temp_path, 'file-2', contents='hello\nand\ngoodbye')

    self.Run("""
        compute instances create instance-1
          --metadata-from-file x={},y={}
          --zone central2-a
        """.format(metadata_file1, metadata_file2))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(
                      items=[
                          m.Metadata.ItemsValueListEntry(
                              key='x', value='hello'),
                          m.Metadata.ItemsValueListEntry(
                              key='y', value='hello\nand\ngoodbye'),
                      ]),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithMetadataAndMetadataFromFile(self):
    m = self.messages

    metadata_file1 = self.Touch(
        self.temp_path, 'file-1', contents='hello')
    metadata_file2 = self.Touch(
        self.temp_path, 'file-2', contents='hello\nand\ngoodbye')

    self.Run("""
        compute instances create instance-1
          --metadata a=x,b=y,z=d
          --metadata-from-file x={},y={}
          --zone central2-a
        """.format(metadata_file1, metadata_file2))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(
                      items=[
                          m.Metadata.ItemsValueListEntry(
                              key='a', value='x'),
                          m.Metadata.ItemsValueListEntry(
                              key='b', value='y'),
                          m.Metadata.ItemsValueListEntry(
                              key='x', value='hello'),
                          m.Metadata.ItemsValueListEntry(
                              key='y', value='hello\nand\ngoodbye'),
                          m.Metadata.ItemsValueListEntry(
                              key='z', value='d'),
                      ]),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithMetadataContainingDuplicateKeys(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Encountered duplicate metadata key \[x\].'):
      self.Run("""
          compute instances create instance-1
            --metadata x=y,z=1
            --metadata-from-file x=file-1
            --zone central2-a
          """)

    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          self.messages.ComputeZonesGetRequest(
              project='my-project',
              zone='central2-a'))])

  def testWithMetadataFromNonExistentFile(self):
    metdata_file = self.Touch(self.temp_path, 'file-1', contents='hello')

    with self.assertRaisesRegex(
        files.Error,
        r'Unable to read file \[garbage\]: .*No such file or directory'):
      self.Run("""
          compute instances create instance-1
            --metadata-from-file x={},y=garbage
            --zone central2-a
          """.format(metdata_file))

    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          self.messages.ComputeZonesGetRequest(
              project='my-project',
              zone='central2-a'))])

  def testWithNetwork(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --network some-other-network
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=(
                          self.compute_uri + '/projects/'
                          'my-project/global/networks/some-other-network'))],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithNoRestartOnFailure(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --no-restart-on-failure
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=False),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithTags(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --tags a,b,c,d
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
                  tags=m.Tags(
                      items=['a', 'b', 'c', 'd'])),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def _MakeInsertRequest(self, instance_ref):
    m = self.messages
    return m.ComputeInstancesInsertRequest(
        instance=m.Instance(
            canIpForward=False,
            deletionProtection=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=self._default_machine_type,
            metadata=m.Metadata(),
            name=instance_ref.instance,
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[m.AccessConfig(
                    name='external-nat',
                    type=self._one_to_one_nat)],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(
                automaticRestart=True),
        ),
        project=instance_ref.project,
        zone=instance_ref.zone,
    )

  def testManyInstances(self):
    instance_refs = [
        resources.REGISTRY.Create('compute.instances',
                                  instance='instance-{}'.format(i),
                                  zone='central2-a',
                                  project=self.Project())
        for i in range(3)]

    self.Run('compute instances create {} --zone central2-a'.format(
        ' '.join(i.instance for i in instance_refs)
    ))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self._MakeInsertRequest(instance_refs[i])) for i in range(3)],
    )

  def testManyInstances_ViaUri(self):
    properties.VALUES.core.project.Set('should-not-be-used')
    instance_refs = [
        resources.REGISTRY.Create('compute.instances',
                                  instance='instance-{}'.format(i),
                                  zone='central2-a',
                                  project=self.Project())
        for i in range(3)]

    self.Run('compute instances create {}'.format(
        ' '.join(i.SelfLink() for i in instance_refs)
    ))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self._MakeInsertRequest(instance_refs[i])) for i in range(3)],
    )

  def testDefaultOutput(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='zone-1')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        self._instances
    ])

    self.Run("""
        compute instances create instance-1 instance-2 instance-3 --zone zone-1
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   MACHINE_TYPE  PREEMPTIBLE INTERNAL_IP EXTERNAL_IP   STATUS
            instance-1 zone-1 n1-standard-1             10.0.0.1    23.251.133.75 RUNNING
            instance-2 zone-1 n1-standard-1             10.0.0.2    23.251.133.74 RUNNING
            instance-3 zone-1 n1-standard-2             10.0.0.3    23.251.133.76 RUNNING
            """), normalize_space=True)

  def testOutput(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='zone-1')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        self._instances
    ])

    self.Run("""
        compute instances create instance-1 instance-2 instance-3
          --format json
          --zone zone-1
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            [
              {{
                "machineType": "https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-1",
                "name": "instance-1",
                "networkInterfaces": [
                  {{
                    "accessConfigs": [
                      {{
                        "natIP": "23.251.133.75"
                      }}
                    ],
                    "networkIP": "10.0.0.1"
                  }}
                ],
                "scheduling": {{
                  "automaticRestart": false,
                  "onHostMaintenance": "TERMINATE",
                  "preemptible": false
                }},
                "selfLink": "{compute_uri}/projects/my-project/zones/zone-1/instances/instance-1",
                "status": "RUNNING",
                "zone": "https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1"
              }},
              {{
                "machineType": "https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-1",
                "name": "instance-2",
                "networkInterfaces": [
                  {{
                    "accessConfigs": [
                      {{
                        "natIP": "23.251.133.74"
                      }}
                    ],
                    "networkIP": "10.0.0.2"
                  }}
                ],
                "scheduling": {{
                  "automaticRestart": false,
                  "onHostMaintenance": "TERMINATE",
                  "preemptible": false
                }},
                "selfLink": "{compute_uri}/projects/my-project/zones/zone-1/instances/instance-2",
                "status": "RUNNING",
                "zone": "https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1"
              }},
              {{
                "machineType": "https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-2",
                "name": "instance-3",
                "networkInterfaces": [
                  {{
                    "accessConfigs": [
                      {{
                        "natIP": "23.251.133.76"
                      }}
                    ],
                    "networkIP": "10.0.0.3"
                  }}
                ],
                "scheduling": {{
                  "automaticRestart": false,
                  "onHostMaintenance": "TERMINATE",
                  "preemptible": false
                }},
                "selfLink": "{compute_uri}/projects/my-project/zones/zone-1/instances/instance-3",
                "status": "RUNNING",
                "zone": "https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1"
              }}
            ]
            """.format(compute_uri=self.compute_uri)))

  def testSimpleDiskOptionWithSingleDiskAndSingleInstance(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --disk name=disk-1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,
                          ),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-1')),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testComplexDiskOptionWithSingleDiskAndSingleInstance(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --disk name=disk-1,mode=rw,device-name=x,boot=no
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,
                          ),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-1')),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testComplexDiskOptionsWithManyDisksAndSingleInstance(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --disk name=disk-1,mode=rw,device-name=x,boot=no
          --disk name=disk-2,mode=ro,device-name=y,auto-delete=yes
          --disk boot=no,device-name=z,name=disk-3,mode=rw
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,
                          ),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-1')),
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=False,
                          deviceName='y',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-2')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='z',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-3')),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testDiskOptionWithNoName(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[name\] is missing in \[--disk\]. \[--disk\] value must be of the '
        r'form \[name=NAME \[mode={ro,rw}\] \[boot={yes,no}\] '
        r'\[device-name=DEVICE_NAME\] \[auto-delete={yes,no}\]\].'):
      self.Run("""
          compute instances create instance-1
            --disk mode=rw,device-name=x,boot=no
            --zone central2-a
          """)

    self.CheckRequests()

  def testDiskOptionWithBadMode(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[mode\] in \[--disk\] must be \[rw\] or \[ro\], not '
        r'\[READ_WRITE\].'):
      self.Run("""
          compute instances create instance-1
            --disk name=disk-1,mode=READ_WRITE,device-name=x
            --zone central2-a
          """)

    self.CheckRequests()

  def testDiskOptionWithBadBoot(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[boot\] in \[--disk\] must be \[yes\] or \[no\], not '
        r'\[No\].'):
      self.Run("""
          compute instances create instance-1
            --disk name=disk-1,device-name=x,boot=No
            --zone central2-a
          """)

    self.CheckRequests()

  def testDiskOptionWithReadWriteDisksAndMultipleInstances(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Cannot attach disk \[disk-1\] in read-write mode to more than one '
        'instance.'):
      self.Run("""
          compute instances create instance-1 instance-2
            --disk name=disk-1,mode=rw
            --zone central2-a
          """)

    self.CheckRequests()

  def testDiskOptionWithBootDiskAndImageOption(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Each instance can have exactly one boot disk. One boot disk was '
        r'specified through \[--disk\] and another through \[--image\].'):
      self.Run("""
          compute instances create instance-1
            --disk name=disk-1,mode=rw,boot=yes
            --image image-1
            --zone central2-a
          """)

    self.CheckRequests()

  def testDiskOptionWithManyBootDisks(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Each instance can have exactly one boot disk. At least two boot disks '
        r'were specified through \[--disk\].'):
      self.Run("""
          compute instances create instance-1
            --disk name=disk-1,mode=rw,boot=yes
            --disk name=disk-2,mode=ro,boot=no
            --disk name=disk-3,mode=rw,boot=yes
            --zone central2-a
          """)

    self.CheckRequests()

  def testComplexDiskOptionsWithManyDisksAndManyInstances(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1 instance-2 instance-3
          --boot-disk-device-name boot-disk
          --boot-disk-size 100GB
          --boot-disk-type pd-ssd
          --no-boot-disk-auto-delete
          --disk name=disk-1,mode=ro,device-name=x,boot=no
          --disk name=disk-2,mode=ro,device-name=y
          --disk boot=no,device-name=z,name=disk-3,mode=ro
          --image image-1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=True,
                          deviceName='boot-disk',
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=(
                                  self.compute_uri +
                                  '/projects/my-project/global/images/image-1'),
                              diskSizeGb=100,
                              diskType=(
                                  self.compute_uri +
                                  '/projects/my-project/zones/central2-a/'
                                  'diskTypes/pd-ssd')),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-1')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='y',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-2')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='z',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-3')),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          )),

         (self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=True,
                          deviceName='boot-disk',
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=(
                                  self.compute_uri +
                                  '/projects/my-project/global/images/image-1'),
                              diskSizeGb=100,
                              diskType=(
                                  self.compute_uri +
                                  '/projects/my-project/zones/central2-a/'
                                  'diskTypes/pd-ssd')),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-1')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='y',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-2')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='z',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-3')),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-2',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          )),

         (self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=True,
                          deviceName='boot-disk',
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=(
                                  self.compute_uri +
                                  '/projects/my-project/global/images/image-1'),
                              diskSizeGb=100,
                              diskType=(
                                  self.compute_uri +
                                  '/projects/my-project/zones/central2-a/'
                                  'diskTypes/pd-ssd')),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-1')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='y',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-2')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='z',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central2-a/disks/'
                              'disk-3')),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-3',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testPromptingWithOneInstance(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    m = self.messages

    self.WriteInput('4\n')
    self.make_requests.side_effect = iter([
        test_resources.ZONES,
        [
            m.Zone(name='us-central1-b')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
        """)

    self.CheckRequests(
        self.zones_list_request,

        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='us-central1-b'))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=(self.compute_uri + '/projects/'
                               'my-project/zones/us-central1-b/machineTypes/'
                               'n1-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='us-central1-b',
          ))],
    )

    # This tool should not sort the zones as returned from the
    # server. Zone orderings are different on a per-project basis to
    # ensure equal load on all zones.
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains(
        '"choices": ["europe-west1-a", "europe-west1-b (DELETED)", '
        '"us-central1-a (DEPRECATED)", "us-central1-b"]')

  def testPromptingWithSimpleNamesAndUris(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    m = self.messages

    self.WriteInput('4\n')
    self.make_requests.side_effect = iter([
        test_resources.ZONES,
        [
            m.Zone(name='us-central1-b'),
            m.Zone(name='central3-a'),
            m.Zone(name='central3-b')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        []  # For the MakeRequests call in Run
    ])

    self.Run("""
        compute instances create
          instance-1
          {compute_uri}/projects/my-project/zones/central3-a/instances/instance-2
          instance-3
          {compute_uri}/projects/my-project/zones/central3-b/instances/instance-4
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        self.zones_list_request,

        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='us-central1-b')),
         (self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='central3-a')),
         (self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='central3-b'))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=(self.compute_uri + '/projects/'
                               'my-project/zones/us-central1-b/machineTypes/'
                               'n1-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='us-central1-b',
          )),

         (self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=(self.compute_uri + '/projects/'
                               'my-project/zones/central3-a/machineTypes/'
                               'n1-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-2',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central3-a',
          )),

         (self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=(self.compute_uri + '/projects/'
                               'my-project/zones/us-central1-b/machineTypes/'
                               'n1-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-3',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='us-central1-b',
          )),

         (self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=(self.compute_uri + '/projects/'
                               'my-project/zones/central3-b/machineTypes/'
                               'n1-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-4',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central3-b',
          ))],
    )
    self.AssertErrContains('For the following instances:')
    self.AssertErrContains('instance-1')
    self.AssertErrContains('instance-3')
    self.AssertErrContains('choose a zone:')
    self.AssertErrContains('us-central1-a (DEPRECATED)')
    self.AssertErrContains('us-central1-b')
    self.AssertErrContains('europe-west1-a')
    self.AssertErrContains('europe-west1-b (DELETED)')

  def testPromptingError(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    m = self.messages

    def MakeRequests(*_, **kwargs):
      yield m.Zone(name='central2-a')
      kwargs['errors'].append((500, 'Server Error'))
    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        r'Could not fetch resource:'):
      self.Run("""
         compute instances create instance-1
         """)

    self.CheckRequests(
        self.zones_list_request,
    )
    self.AssertErrContains('Server Error')
    self.AssertErrNotContains('choose a zone:')
    self.AssertErrNotContains('central2-a')

  def testPromptingWithQuiet(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=False)
    self.make_requests.side_effect = iter([
        test_resources.ZONES,
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
    ])

    with self.assertRaisesRegex(
        compute_flags.UnderSpecifiedResourceError,
        r'Underspecified resource \[instance-1\]. Specify the \[--zone\] '
        r'flag\.'):
      self.Run("""
         compute instances create instance-1 --quiet
         """)

    self.CheckRequests()

  def testInvalidUri(self):
    with self.assertRaisesRegex(
        resources.InvalidResourceException, r'could not parse resource '
        r'\[https://www.googleapis.com/compute/zones/central3-a/instances/'
        r'instance-2\]: unknown api www'):
      self.Run("""
         compute instances create https://www.googleapis.com/compute/zones/central3-a/instances/instance-2
         """)

    self.CheckRequests()

  def testFlagsWithUri(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central1-a')
        ],
        [
            m.Address(
                name='address-1',
                address='74.125.28.139'),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --zone {uri}/projects/my-project/zones/central1-a
          --boot-disk-type {uri}/projects/my-project/zones/central1-a/diskTypes/pd-ssd
          --disk name={uri}/projects/my-project/zones/central1-a/disks/disk-1
          --machine-type {uri}/projects/my-project/zones/central1-a/machineTypes/n2-standard-1
          --network {uri}/projects/my-project/global/networks/some-other-network
          --image {uri}/projects/my-project/global/images/my-image
          --address {uri}/projects/my-project/regions/central1/addresses/address-1
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone=('central1-a')))],
        [(self.compute.addresses,
          'Get',
          m.ComputeAddressesGetRequest(
              address='address-1',
              project='my-project',
              region='central1'))],
        self.project_get_request,

        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=(
                                  self.compute_uri +
                                  '/projects/my-project/global/images/'
                                  'my-image'),
                              diskType=(
                                  self.compute_uri +
                                  '/projects/my-project/zones/central1-a/'
                                  'diskTypes/pd-ssd'),
                          ),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central1-a/disks/'
                              'disk-1')),
                  ],
                  machineType=(self.compute_uri + '/projects/'
                               'my-project/zones/central1-a/machineTypes/'
                               'n2-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat,
                          natIP='74.125.28.139')],
                      network=(self.compute_uri + '/projects/'
                               'my-project/global/networks/'
                               'some-other-network'))],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone=('central1-a'),
          ))],
    )

  def testDefaultZone(self):
    m = self.messages

    properties.VALUES.compute.zone.Set('central2-a')
    self.Run("""
        compute instances create instance-1
        """)

    self.AssertErrNotContains('choose a zone')
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testZoneAndDeprecationWithYes(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    m = self.messages

    self.WriteInput('1\ny\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
            m.Zone(name='central2-b'),
        ],
        [
            m.Zone(
                name='central2-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus
                    .StateValueValuesEnum
                    .DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'),
            ),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1
        """)

    self.CheckRequests(
        self.zones_list_request,
        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='central2-a'))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

    self.AssertErrContains('instance-1')
    self.AssertErrContains('central2-a')
    self.AssertErrContains('central2-b')
    self.AssertErrContains(
        r'WARNING: The following selected zone is deprecated. All resources in '
        r'this zone will be deleted after the turndown date.\n'
        r' - [central2-a] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeprecationWithOneZoneWorksWithYes(self):
    m = self.messages

    self.WriteInput('Y\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central2-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus
                    .StateValueValuesEnum
                    .DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00')
            ),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )
    self.AssertErrContains(
        r'WARNING: The following selected zone is deprecated. All resources in '
        r'this zone will be deleted after the turndown date.\n'
        r' - [central2-a] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeprecationWorkWithOneZoneWithYes(self):
    m = self.messages

    self.WriteInput('y\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central2-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus
                    .StateValueValuesEnum
                    .DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'),
            ),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1 --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='central2-a'))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

    self.AssertErrContains(
        r'WARNING: The following selected zone is deprecated. All resources in '
        r'this zone will be deleted after the turndown date.\n'
        r' - [central2-a] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeprecationWorkWithOneZoneWithNo(self):
    m = self.messages

    self.WriteInput('n\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central2-b',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus
                    .StateValueValuesEnum
                    .DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'))
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    with self.AssertRaisesToolExceptionRegexp('Creation aborted by user.'):
      self.Run("""
          compute instances create instance-1 --zone central2-b
          """)

    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='central2-b'))],
    )

    self.AssertErrContains(
        r'WARNING: The following selected zone is deprecated. All resources in '
        r'this zone will be deleted after the turndown date.\n'
        r' - [central2-b] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeprecationWorkWithManyZonesWithYes(self):
    m = self.messages

    self.WriteInput('y\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central1-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus
                    .StateValueValuesEnum
                    .DEPRECATED,
                    deleted='2015-05-07T00:00.000-07:00'),
            ),
            m.Zone(
                name='central1-b',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus
                    .StateValueValuesEnum
                    .DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'),
            ),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        []  # For the MakeRequests call in run
    ])

    self.Run("""
        compute instances create
          https://www.googleapis.com/compute/{api}/projects/my-project/zones/central1-a/instances/instance-1
          https://www.googleapis.com/compute/{api}/projects/my-project/zones/central1-b/instances/instance-2
        """.format(api=self.api))

    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='central1-a')),
         (self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='central1-b'))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=(self.compute_uri + '/projects/'
                               'my-project/zones/central1-a/machineTypes/'
                               'n1-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central1-a',
          )),

         (self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=(self.compute_uri + '/projects/'
                               'my-project/zones/central1-b/machineTypes/'
                               'n1-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-2',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central1-b',
          ))],
    )

    self.AssertErrContains(
        r'WARNING: The following selected zones are deprecated. All resources '
        r'in these zones will be deleted after their turndown date.\n'
        r' - [central1-a] 2015-05-07T00:00.000-07:00\n'
        r' - [central1-b] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeprecationWorkWithZonalFetchError(self):
    m = self.messages

    def MakeRequests(*_, **kwargs):
      if kwargs['requests'][0][0] == self.compute.zones:
        yield m.Zone(name='central2-a')
        kwargs['errors'].append((500, 'Server Error'))
      elif kwargs['requests'][0][0] == self.compute.images:
        yield m.Image(
            name='debian-8-jessie-v20151130',
            selfLink=self._default_image)
      elif kwargs['requests'][0][0] == self.compute.projects:
        yield m.Project(
            defaultServiceAccount='default@service.account')
      else:
        yield

    self.make_requests.side_effect = MakeRequests

    self.Run("""
          compute instances create instance-1 --zone central2-a --quiet
          """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testDeprecationWorkWithQuietFlag(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central2-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus
                    .StateValueValuesEnum
                    .DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'),
            ),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1 --zone central2-a --quiet
        """)

    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='central2-a'))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )
    self.AssertErrNotContains('PROMPT_CONTINUE')

  def testZoneDeprecatedWarningNo(self):
    m = self.messages

    self.WriteInput('n\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central2-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus
                    .StateValueValuesEnum
                    .DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00')
            ),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    with self.AssertRaisesToolExceptionRegexp('Creation aborted by user.'):
      self.Run("""
          compute instances create instance-1
            --zone central2-a
          """)

    self.CheckRequests(
        self.zone_get_request,
    )
    self.AssertErrContains(
        r'WARNING: The following selected zone is deprecated. All resources in '
        r'this zone will be deleted after the turndown date.\n'
        r' - [central2-a] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testLocalSSDRequestNoDeviceNames(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --local-ssd ''
          --local-ssd interface=NVME
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=(
                              m.AttachedDiskInitializeParams(
                                  sourceImage=self._default_image)
                          ),
                          mode=(m.AttachedDisk
                                .ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.PERSISTENT)),
                      m.AttachedDisk(
                          autoDelete=True,
                          initializeParams=(
                              m.AttachedDiskInitializeParams(
                                  diskType=self._ssd_disk_type)),
                          mode=(m.AttachedDisk
                                .ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.SCRATCH)),
                      m.AttachedDisk(
                          autoDelete=True,
                          initializeParams=(
                              m.AttachedDiskInitializeParams(
                                  diskType=self._ssd_disk_type)),
                          interface=(m.AttachedDisk
                                     .InterfaceValueValuesEnum.NVME),
                          mode=(m.AttachedDisk
                                .ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.SCRATCH)),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=(m.AccessConfig.TypeValueValuesEnum
                                .ONE_TO_ONE_NAT))],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))]
    )

  def testLocalSSDRequestBadInterface(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Unexpected local SSD interface: \[SATA\]. '
        r'Legal values are \[NVME, SCSI\].'):
      self.Run("""
          compute instances create instance
            --zone central2-a
            --local-ssd device-name=foo,interface=SATA
          """)

  def testLocalSSDRequest(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --local-ssd device-name=foo
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=(
                              m.AttachedDiskInitializeParams(
                                  sourceImage=self._default_image)
                          ),
                          mode=(m.AttachedDisk
                                .ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.PERSISTENT)),
                      m.AttachedDisk(
                          autoDelete=True,
                          deviceName='foo',
                          initializeParams=(
                              m.AttachedDiskInitializeParams(
                                  diskType=self._ssd_disk_type)),
                          mode=(m.AttachedDisk
                                .ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.SCRATCH)),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=(m.AccessConfig.TypeValueValuesEnum
                                .ONE_TO_ONE_NAT))],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))]
    )

  def templateTestLocalSSDRequestTwoSSDs(self, cmd):
    m = self.messages

    self.Run(cmd)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=(
                              m.AttachedDiskInitializeParams(
                                  sourceImage=self._default_image)
                          ),
                          mode=(m.AttachedDisk
                                .ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.PERSISTENT)),
                      m.AttachedDisk(
                          autoDelete=True,
                          deviceName='foo',
                          initializeParams=(
                              m.AttachedDiskInitializeParams(
                                  diskType=self._ssd_disk_type)),
                          mode=(m.AttachedDisk
                                .ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.SCRATCH)),
                      m.AttachedDisk(
                          autoDelete=True,
                          deviceName='bar',
                          initializeParams=(
                              m.AttachedDiskInitializeParams(
                                  diskType=self._ssd_disk_type)),
                          interface=(m.AttachedDisk
                                     .InterfaceValueValuesEnum.NVME),
                          mode=(m.AttachedDisk
                                .ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.SCRATCH)),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=(m.AccessConfig.TypeValueValuesEnum
                                .ONE_TO_ONE_NAT))],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))]
    )

  def testLocalSSDRequestTwoSSDs(self):
    self.templateTestLocalSSDRequestTwoSSDs("""
        compute instances create instance
          --zone central2-a
          --local-ssd device-name=foo
          --local-ssd device-name=bar,interface=NVME
        """)

  def testLowerCaseNvme(self):
    self.templateTestLocalSSDRequestTwoSSDs("""
        compute instances create instance
          --zone central2-a
          --local-ssd device-name=foo
          --local-ssd device-name=bar,interface=nvme
        """)

  def testCustomVMCreate(self):
    m = self.messages

    instance_name = 'vmtest'
    custom_cpu = '2'
    custom_ram_mib = '3500'
    project_name = 'my-project'
    zone_name = 'central2-a'

    self.make_requests.side_effect = iter([
        [
            m.Zone(name=zone_name),
        ],
        [
            m.MachineType(
                creationTimestamp='2013-09-06T17:54:10.636-07:00',
                guestCpus=int(custom_cpu),
                memoryMb=int(custom_ram_mib)),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        []
    ])

    self.Run("""
        compute instances create {0}
        --custom-cpu {1}
        --custom-memory {2}MiB
        --zone {3}
        """.format(instance_name, custom_cpu, custom_ram_mib, zone_name))

    custom_type_string = instance_utils.GetNameForCustom(custom_cpu,
                                                         custom_ram_mib)
    custom_machine_type = ('https://www.googleapis.com/compute/v1/projects/{0}/'
                           'zones/{1}/machineTypes/'
                           '{2}'.format(project_name, zone_name,
                                        custom_type_string))

    custom_machine_type_name = 'custom-{0}-{1}'.format(custom_cpu,
                                                       custom_ram_mib)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.machineTypes,
          'Get',
          m.ComputeMachineTypesGetRequest(
              machineType=custom_machine_type_name,
              project=project_name,
              zone=zone_name))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=custom_machine_type,
                  metadata=m.Metadata(),
                  name=instance_name,
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project=project_name,
              zone=zone_name,
          ))],
        )

  def testCustomVMNoUnitsCreate(self):
    m = self.messages

    instance_name = 'vmtest'
    custom_cpu = '2'
    custom_ram_gib = '3'
    custom_ram_mib = int(custom_ram_gib) * 1024
    project_name = 'my-project'
    zone_name = 'central2-a'

    self.make_requests.side_effect = iter([
        [
            m.Zone(name=zone_name),
        ],
        [
            m.MachineType(
                creationTimestamp='2013-09-06T17:54:10.636-07:00',
                guestCpus=int(custom_cpu),
                memoryMb=int(custom_ram_mib)),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        []
    ])

    self.Run("""
        compute instances create {0}
        --custom-cpu {1}
        --custom-memory {2}
        --zone {3}
        """.format(instance_name, custom_cpu, custom_ram_gib, zone_name))

    custom_type_string = instance_utils.GetNameForCustom(custom_cpu,
                                                         custom_ram_mib)
    custom_machine_type = ('https://www.googleapis.com/compute/v1/projects/{0}/'
                           'zones/{1}/machineTypes/'
                           '{2}'.format(project_name, zone_name,
                                        custom_type_string))

    custom_machine_type_name = 'custom-{0}-{1}'.format(custom_cpu,
                                                       custom_ram_mib)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.machineTypes,
          'Get',
          m.ComputeMachineTypesGetRequest(
              machineType=custom_machine_type_name,
              project=project_name,
              zone=zone_name))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=custom_machine_type,
                  metadata=m.Metadata(),
                  name=instance_name,
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project=project_name,
              zone=zone_name,
          ))],
        )

  def testExtendedCustomVMCreate(self):
    m = self.messages

    instance_name = 'vmtest'
    custom_cpu = '2'
    custom_ram_mib = '3500'
    project_name = 'my-project'
    zone_name = 'central2-a'

    self.make_requests.side_effect = iter([
        [
            m.Zone(name=zone_name),
        ],
        [
            m.MachineType(
                creationTimestamp='2013-09-06T17:54:10.636-07:00',
                guestCpus=int(custom_cpu),
                memoryMb=int(custom_ram_mib)),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        []
    ])

    self.Run("""
        compute instances create {instance_name}
          --custom-cpu {custom_cpu}
          --custom-memory {custom_ram_mib}MiB
          --custom-extensions
          --zone {zone_name}
        """.format(instance_name=instance_name,
                   custom_cpu=custom_cpu,
                   custom_ram_mib=custom_ram_mib,
                   zone_name=zone_name))

    custom_type_string = instance_utils.GetNameForCustom(custom_cpu,
                                                         custom_ram_mib,
                                                         True)
    custom_machine_type = ('https://www.googleapis.com/compute/v1/projects/'
                           '{0}/zones/{1}/machineTypes/'
                           '{2}'.format(project_name, zone_name,
                                        custom_type_string))

    custom_machine_type_name = 'custom-{0}-{1}-ext'.format(custom_cpu,
                                                           custom_ram_mib)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.machineTypes,
          'Get',
          m.ComputeMachineTypesGetRequest(
              machineType=custom_machine_type_name,
              project=project_name,
              zone=zone_name))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=custom_machine_type,
                  metadata=m.Metadata(),
                  name=instance_name,
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=m.AccessConfig.TypeValueValuesEnum.
                          ONE_TO_ONE_NAT)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project=project_name,
              zone=zone_name,
          ))],
        )

  def testCustomAndMachineTypeCreateError(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Cannot set both \[--machine-type\] and \[--custom-cpu\]/'
        r'\[--custom-memory\] for the same instance.'):
      self.Run("""
        compute instances create vmtest
          --custom-cpu 2
          --custom-memory 8
          --machine-type n1-standard-1
          --zone central2-a
        """)

  def testCustomFlagMissingCreateError(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-cpu: --custom-memory must be specified.'):
      self.Run("""
        compute instances create vmtest
          --custom-cpu 2
          --zone central2-a
        """)

  def testCustomZonePrompt(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    m = self.messages

    instance_name = 'vmtest'
    custom_cpu = '2'
    custom_ram_mib = '3500'
    project_name = 'my-project'
    zone_name = test_resources.ZONES[1].name

    self.WriteInput('4\n')

    self.make_requests.side_effect = iter([
        test_resources.ZONES,
        [
            m.Zone(name=zone_name),
        ],
        [
            m.MachineType(
                creationTimestamp='2013-09-06T17:54:10.636-07:00',
                guestCpus=int(custom_cpu),
                memoryMb=int(custom_ram_mib)),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        []
    ])

    self.Run("""
        compute instances create {0}
        --custom-cpu {1}
        --custom-memory {2}MiB
        """.format(instance_name, custom_cpu, custom_ram_mib))

    custom_type_string = instance_utils.GetNameForCustom(custom_cpu,
                                                         custom_ram_mib)
    custom_machine_type = ('https://www.googleapis.com/compute/v1/projects/{0}/'
                           'zones/{1}/machineTypes/'
                           '{2}'.format(project_name, zone_name,
                                        custom_type_string))

    custom_machine_type_name = 'custom-{0}-{1}'.format(custom_cpu,
                                                       custom_ram_mib)

    self.CheckRequests(
        self.zones_list_request,

        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project=project_name,
              zone=zone_name))],

        [(self.compute.machineTypes,
          'Get',
          m.ComputeMachineTypesGetRequest(
              machineType=custom_machine_type_name,
              project=project_name,
              zone=zone_name))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=custom_machine_type,
                  metadata=m.Metadata(),
                  name=instance_name,
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project=project_name,
              zone=zone_name,
          ))],
        )

  def testWithNetworkWithNetworkIp(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --network some-other-network
          --private-network-ip 10.240.0.5
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=(
                          self.compute_uri + '/projects/'
                          'my-project/global/networks/some-other-network'),
                      networkIP='10.240.0.5')],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithSubnetsWithNetworkIp(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --subnet some-subnetwork
          --private-network-ip 10.240.0.5
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      networkIP='10.240.0.5',
                      subnetwork=(
                          self.compute_uri + '/projects/my-project/' +
                          'regions/central2/subnetworks/some-subnetwork'))],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithAddressResourceNetworkIp(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --private-network-ip static-ip
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='instance-1',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=self._default_network,
                        networkIP=(
                            self.compute_uri + '/projects/'
                            'my-project/regions/central2/addresses/static-ip'))
                ],
                serviceAccounts=[
                    m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testWithMalformedNetworkIp(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --private-network-ip 192161.1.1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='instance-1',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=self._default_network,
                        networkIP=(
                            self.compute_uri + '/projects/'
                            'my-project/regions/central2/addresses/192161.1.1'))
                ],
                serviceAccounts=[
                    m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testMultipleNetworkInterfaceCards(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface network=default,address=
          --network-interface network=some-net,private-network-ip=10.0.0.1,address=8.8.8.8
          --network-interface subnet=some-subnet
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', msg.ComputeInstancesInsertRequest(
            instance=msg.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceImage=(self.compute_uri +
                                         '/projects/my-project/global/images/'
                                         'family/yorik'),),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=_DefaultMachineTypeOf(self.api),
                metadata=msg.Metadata(),
                name='hamlet',
                networkInterfaces=[
                    msg.NetworkInterface(
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=_DefaultNetworkOf(self.api)),
                    msg.NetworkInterface(
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat',
                                natIP='8.8.8.8',
                                type=self._one_to_one_nat)
                        ],
                        network=(self.compute_uri +
                                 '/projects/my-project/global/networks/'
                                 'some-net'),
                        networkIP='10.0.0.1'),
                    msg.NetworkInterface(
                        subnetwork=(
                            self.compute_uri + '/projects/my-project/regions/'
                            'central2/subnetworks/some-subnet'),
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],),
                ],
                serviceAccounts=[
                    msg.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=msg.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testNetworkAndSubnetOnOneInterface(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-interface network=some-network,subnet=some-subnetwork
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='instance-1',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=(
                            self.compute_uri + '/projects/my-project/global/'
                            'networks/some-network'),
                        subnetwork=(
                            self.compute_uri + '/projects/my-project/'
                            'regions/central2/subnetworks/some-subnetwork'))
                ],
                serviceAccounts=[
                    m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testNoAddress(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface no-address
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', msg.ComputeInstancesInsertRequest(
            instance=msg.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceImage=(self.compute_uri +
                                         '/projects/my-project/global/images/'
                                         'family/yorik'),),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=_DefaultMachineTypeOf(self.api),
                metadata=msg.Metadata(),
                name='hamlet',
                networkInterfaces=[
                    msg.NetworkInterface(
                        network=(self.compute_uri +
                                 '/projects/my-project/global/networks/'
                                 'default')),
                ],
                serviceAccounts=[
                    msg.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=msg.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testHostnameArg(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a --hostname my-new-hostname
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  hostname='my-new-hostname',
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testNoAddreassAndAddressOnOneInterface(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-interface\]: specifies both address '
        r'and no-address for one interface'):
      self.Run("""
          compute instances create hamlet
            --zone central2-a
            --image {0}/projects/my-project/global/images/family/yorik
            --network-interface address=192.168.1.1,no-address
          """.format(self.compute_uri))

  def testMultiNicFlagAndOneNicFlag(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'^arguments not allowed simultaneously: --network-interface, all of '
        r'the following: --address, --network, --private-network-ip$'):
      self.Run("""
          compute instances create instance-1
            --zone central2-a
            --network-interface ''
            --address 8.8.8.8
            --network net
            --private-network-ip 10.0.0.2
          """)

  def testMultipleMetadataArgumentsShouldFail(self):
    with self.AssertRaisesArgumentError():
      self.Run("""
      compute instances create nvme-template-vm
        --zone central2-a
        --metadata block-project-ssh-keys=TRUE
        --metadata sshKeys=''
        --metadata ssh-keys=''
      """)


class InstancesCreateDiskTest(InstancesCreateTestsMixin):
  """Test creation of VM instances with create disk(s)."""

  def SetUp(self):
    SetUp(self, 'v1')

  def testCreateDiskWithAllProperties(self):
    m = self.messages

    self.Run(
        'compute instances create hamlet '
        '  --zone central2-a '
        '  --create-disk name=disk-1,size=10GB,mode=ro,type=SSD,image=debian-8,'
        'image-project=debian-cloud,device-name=data,auto-delete=yes')

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=False,
                        deviceName='data',
                        initializeParams=m.AttachedDiskInitializeParams(
                            diskName='disk-1',
                            diskSizeGb=10,
                            sourceImage=(self.compute_uri +
                                         '/projects/debian-cloud/global/images'
                                         '/debian-8'),
                            diskType=(self.compute_uri +
                                      '/projects/my-project/zones/central2-a/'
                                      'diskTypes/SSD')),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='hamlet',
                networkInterfaces=[m.NetworkInterface(
                    accessConfigs=[m.AccessConfig(
                        name='external-nat',
                        type=self._one_to_one_nat)],
                    network=self._default_network)],
                serviceAccounts=[
                    m.ServiceAccount(
                        email='default',
                        scopes=_DEFAULT_SCOPES,),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testCreateDisksWithDefaultProperties(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1 instance-2
          --zone central2-a
          --create-disk size=10GB
          --create-disk image=foo
          --create-disk image-family=bar
          --create-disk description='This is a test disk'
        """)

    self.CheckRequests(self.zone_get_request, self.project_get_request, [
        (self.compute.instances, 'Insert',
         m.ComputeInstancesInsertRequest(
             instance=m.Instance(
                 canIpForward=False,
                 deletionProtection=False,
                 disks=[
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=True,
                         initializeParams=m.AttachedDiskInitializeParams(
                             sourceImage=self._default_image,),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             diskSizeGb=10,),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             sourceImage=(self.compute_uri +
                                          '/projects/my-project/global/images/'
                                          'foo'),),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             sourceImage=(self.compute_uri +
                                          '/projects/my-project/global/images/'
                                          'family/bar'),),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             description='This is a test disk'),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                 ],
                 machineType=self._default_machine_type,
                 metadata=m.Metadata(),
                 name='instance-1',
                 networkInterfaces=[
                     m.NetworkInterface(
                         accessConfigs=[
                             m.AccessConfig(
                                 name='external-nat', type=self._one_to_one_nat)
                         ],
                         network=self._default_network)
                 ],
                 serviceAccounts=[
                     m.ServiceAccount(
                         email='default',
                         scopes=_DEFAULT_SCOPES,
                     ),
                 ],
                 scheduling=m.Scheduling(automaticRestart=True),
             ),
             project='my-project',
             zone='central2-a',
         )),
        (self.compute.instances, 'Insert',
         m.ComputeInstancesInsertRequest(
             instance=m.Instance(
                 canIpForward=False,
                 deletionProtection=False,
                 disks=[
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=True,
                         initializeParams=m.AttachedDiskInitializeParams(
                             sourceImage=self._default_image,),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             diskSizeGb=10,),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             sourceImage=(self.compute_uri +
                                          '/projects/my-project/global/images/'
                                          'foo'),),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             sourceImage=(self.compute_uri +
                                          '/projects/my-project/global/images/'
                                          'family/bar'),),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             description='This is a test disk'),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                 ],
                 machineType=self._default_machine_type,
                 metadata=m.Metadata(),
                 name='instance-2',
                 networkInterfaces=[
                     m.NetworkInterface(
                         accessConfigs=[
                             m.AccessConfig(
                                 name='external-nat', type=self._one_to_one_nat)
                         ],
                         network=self._default_network)
                 ],
                 serviceAccounts=[
                     m.ServiceAccount(
                         email='default',
                         scopes=_DEFAULT_SCOPES,
                     ),
                 ],
                 scheduling=m.Scheduling(automaticRestart=True),
             ),
             project='my-project',
             zone='central2-a',
         ))
    ])

  def testImageFamilyFlagCreateDisk(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --create-disk image-family=yorik
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', msg.ComputeInstancesInsertRequest(
            instance=msg.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=False,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceImage=(self.compute_uri +
                                         '/projects/my-project/global/images/'
                                         'family/yorik'),),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=_DefaultMachineTypeOf(self.api),
                metadata=msg.Metadata(),
                name='hamlet',
                networkInterfaces=[msg.NetworkInterface(
                    accessConfigs=[msg.AccessConfig(
                        name='external-nat',
                        type=self._one_to_one_nat)],
                    network=_DefaultNetworkOf(self.api))],
                serviceAccounts=[
                    msg.ServiceAccount(
                        email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=msg.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testImageFamilyURICreateDisk(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --create-disk
              image-family='{0}/projects/my-project/global/images/family/yorik'
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', msg.ComputeInstancesInsertRequest(
            instance=msg.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=False,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceImage=(self.compute_uri +
                                         '/projects/my-project/global/images/'
                                         'family/yorik'),),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=_DefaultMachineTypeOf(self.api),
                metadata=msg.Metadata(),
                name='hamlet',
                networkInterfaces=[msg.NetworkInterface(
                    accessConfigs=[msg.AccessConfig(
                        name='external-nat',
                        type=self._one_to_one_nat)],
                    network=_DefaultNetworkOf(self.api))],
                serviceAccounts=[
                    msg.ServiceAccount(
                        email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=msg.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)


class InstancesCreateDiskTestBeta(InstancesCreateTestsMixin):
  """Test creation of VM instances with create disk(s)."""

  def SetUp(self):
    SetUp(self, 'beta')

  def testCreateDiskWithAllProperties(self):

    m = self.messages
    self.track = calliope_base.ReleaseTrack.BETA

    self.Run(
        'compute instances create testrp '
        '  --zone central2-a '
        '  --create-disk name=disk-1,size=10GB,mode=ro,type=SSD,image=debian-8,'
        'image-project=debian-cloud,device-name=data,auto-delete=yes,'
        'disk-resource-policy='
        'https://www.googleapis.com/compute/projects/'
        'cloudsdktest/regions/central2-a/resourcePolicies/testpolicy',
        self.track)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=False,
                        deviceName='data',
                        initializeParams=m.AttachedDiskInitializeParams(
                            diskName='disk-1',
                            diskSizeGb=10,
                            sourceImage=(self.compute_uri +
                                         '/projects/debian-cloud/global/images'
                                         '/debian-8'),
                            diskType=(self.compute_uri +
                                      '/projects/my-project/zones/central2-a/'
                                      'diskTypes/SSD'),
                            resourcePolicies=['https://www.googleapis.com/'
                                              'compute/projects/'
                                              'cloudsdktest/regions/central2-a/'
                                              'resourcePolicies/testpolicy']),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='testrp',
                networkInterfaces=[m.NetworkInterface(
                    accessConfigs=[m.AccessConfig(
                        name='external-nat',
                        type=self._one_to_one_nat)],
                    network=self._default_network)],
                serviceAccounts=[
                    m.ServiceAccount(
                        email='default',
                        scopes=_DEFAULT_SCOPES,),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)


class PreemptibleInstancesCreateTest(InstancesCreateTestsMixin):
  """Test creation of preemptible VM instances."""

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testPreemptible(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='us-central2-b'),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --machine-type=n1-standard-1
          --zone=us-central1-b
          --preemptible
          --no-restart-on-failure
          --maintenance-policy=terminate
        """)
    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='us-central1-b'))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=_DefaultImageOf('beta'),
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=_DefaultPreemptibleMachineTypeOf('beta'),
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=m.AccessConfig.TypeValueValuesEnum.
                          ONE_TO_ONE_NAT)],
                      network=_DefaultNetworkOf('beta'))],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=False,
                      onHostMaintenance=m.Scheduling.
                      OnHostMaintenanceValueValuesEnum.TERMINATE,
                      preemptible=True)),
              project='my-project',
              zone='us-central1-b',
          ))],
    )

  def testPreemptibleWithoutRestartOrMaintenance(self):
    """Creates a preemptible VM with just the --preemptible flag.

    Unlike the previous test, doesn't supply the restart-on-failure or
    on-host-maintenance flags.
    """
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='us-central2-b'),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --machine-type=n1-standard-1
          --zone=us-central1-b
          --preemptible
        """)
    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='us-central1-b'))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=_DefaultImageOf('beta'),
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=_DefaultPreemptibleMachineTypeOf('beta'),
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=m.AccessConfig.TypeValueValuesEnum.
                          ONE_TO_ONE_NAT)],
                      network=_DefaultNetworkOf('beta'))],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=False,
                      preemptible=True)),
              project='my-project',
              zone='us-central1-b',
          ))],
    )


class InstancesCreateCsekTestBeta(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testFoundInstanceNameKeyFileWrappedRsaKey(self):
    private_key_fname = self.WriteKeyFile(include_rsa_encrypted=True)
    msg = self.messages

    self.Run("""
        compute instances create wrappedkeydisk
          --csek-key-file {0}
          --zone central2-a
        """.format(private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[msg.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      deviceName='wrappedkeydisk',
                      initializeParams=msg.AttachedDiskInitializeParams(
                          sourceImage=_DefaultImageOf(self.api)
                      ),
                      mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                      diskEncryptionKey=msg.CustomerEncryptionKey(
                          rsaEncryptedKey=test_base.SAMPLE_WRAPPED_CSEK_KEY))],
                  machineType=_DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='wrappedkeydisk',
                  networkInterfaces=[msg.NetworkInterface(
                      accessConfigs=[msg.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=_DefaultNetworkOf(self.api))],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=msg.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateCsekTest(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'v1')

  def testFoundInstNameKeyFile(self):
    private_key_fname = self.WriteKeyFile()
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --csek-key-file {0}
          --zone central2-a
        """.format(private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[msg.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      deviceName='hamlet',
                      initializeParams=msg.AttachedDiskInitializeParams(
                          sourceImage=_DefaultImageOf(self.api)
                      ),
                      mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                      diskEncryptionKey=msg.CustomerEncryptionKey(
                          rawKey=('abcdefghijklmnopqrstuv'
                                  'wxyz1234567890AAAAAAA=')),)],
                  machineType=_DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[msg.NetworkInterface(
                      accessConfigs=[msg.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=_DefaultNetworkOf(self.api))],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=msg.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testFoundInstNameKeyFromStdin(self):
    self.WriteInput(self.GetKeyFileContent())
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --csek-key-file -
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[msg.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      deviceName='hamlet',
                      initializeParams=msg.AttachedDiskInitializeParams(
                          sourceImage=_DefaultImageOf(self.api)
                      ),
                      mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                      diskEncryptionKey=msg.CustomerEncryptionKey(
                          rawKey=('abcdefghijklmnopqrstuv'
                                  'wxyz1234567890AAAAAAA=')),)],
                  machineType=_DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[msg.NetworkInterface(
                      accessConfigs=[msg.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=_DefaultNetworkOf(self.api))],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=msg.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testFoundInstNameKeyFileRsaWrappedKey(self):
    private_key_fname = self.WriteKeyFile(include_rsa_encrypted=True)

    with self.assertRaisesRegex(csek_utils.BadKeyTypeException, re.escape(
        'Invalid key type [rsa-encrypted]: this feature is only allowed in the '
        'alpha and beta versions of this command.')):
      self.Run("""
          compute instances create hamlet
            --csek-key-file {0}
            --zone central2-a
          """.format(private_key_fname))

  def testNotFoundInstNameKeyFileFail(self):
    private_key_fname = self.WriteKeyFile()

    with self.AssertRaisesExceptionMatches(csek_utils.MissingCsekException,
                                           'Key required for resource'):
      self.Run("""
          compute instances create instance-1
            --csek-key-file {0}
            --zone central2-a
          """.format(private_key_fname))

  def testNotFoundInstNameKeyFileOk(self):
    private_key_fname = self.WriteKeyFile()
    msg = self.messages

    self.Run("""
        compute instances create instance-1
          --csek-key-file {0}
          --zone central2-a
          --no-require-csek-key-create
        """.format(private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[msg.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      deviceName='instance-1',
                      initializeParams=msg.AttachedDiskInitializeParams(
                          sourceImage=_DefaultImageOf(self.api)
                      ),
                      mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=_DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='instance-1',
                  networkInterfaces=[msg.NetworkInterface(
                      accessConfigs=[msg.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=_DefaultNetworkOf(self.api))],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=msg.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testFoundInstNameImageNameKeyFile(self):
    private_key_fname = self.WriteKeyFile()
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --csek-key-file {0}
          --zone central2-a
          --image yorik
        """.format(private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[msg.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      deviceName='hamlet',
                      initializeParams=msg.AttachedDiskInitializeParams(
                          sourceImage=(
                              self.compute_uri +
                              '/projects/my-project/global/images/'
                              'yorik'),
                          sourceImageEncryptionKey=msg.CustomerEncryptionKey(
                              rawKey=('aFellowOfInfiniteJestOf'
                                      'MostExcellentFancy00='))
                      ),
                      mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                      diskEncryptionKey=msg.CustomerEncryptionKey(
                          rawKey=('abcdefghijklmnopqrstuv'
                                  'wxyz1234567890AAAAAAA=')))],
                  machineType=_DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[msg.NetworkInterface(
                      accessConfigs=[msg.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=_DefaultNetworkOf(self.api))],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=msg.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testTwoDisksFoundKeyFile(self):
    private_key_fname = self.WriteKeyFile()
    msg = self.messages

    self.Run("""
        compute instances create instance-1
          --disk name=hamlet,boot=yes
          --disk name=ophelia
          --csek-key-file {0}
          --zone central2-a
        """.format(private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      msg.AttachedDisk(
                          autoDelete=False,
                          boot=True,
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'hamlet'.format(api=self.api)),
                          diskEncryptionKey=msg.CustomerEncryptionKey(
                              rawKey=('abcdefghijklmnopqrstuv'
                                      'wxyz1234567890AAAAAAA='))),
                      msg.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'ophelia'.format(api=self.api)),
                          diskEncryptionKey=msg.CustomerEncryptionKey(
                              rawKey=('OpheliaOphelia00000000'
                                      '00000000000000000000X=')))],
                  machineType=_DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='instance-1',
                  networkInterfaces=[msg.NetworkInterface(
                      accessConfigs=[msg.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=_DefaultNetworkOf(self.api))],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=msg.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateWithSubnets(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testWithSubnets(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --subnet some-subnetwork
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          networkTier=self._default_network_tier,
                          type=self._one_to_one_nat)],
                      subnetwork=(
                          self.compute_uri + '/projects/my-project/' +
                          'regions/central2/subnetworks/some-subnetwork'))],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testSubnetAndNetwork(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --network some-network
          --subnet some-subnetwork
          --zone central2-a
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          networkTier=self._default_network_tier,
                          type=self._one_to_one_nat)],
                      network=(
                          self.compute_uri + '/projects/my-project/global/'
                          'networks/some-network'),
                      subnetwork=(
                          self.compute_uri + '/projects/my-project/'
                          'regions/central2/subnetworks/some-subnetwork'))],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


class ImageFamilies(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'v1')

  def testImageFamilyFlag(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image-family yorik
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[msg.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=msg.AttachedDiskInitializeParams(
                          sourceImage=(
                              self.compute_uri +
                              '/projects/my-project/global/images/'
                              'family/yorik'),
                      ),
                      mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=_DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[msg.NetworkInterface(
                      accessConfigs=[msg.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=_DefaultNetworkOf(self.api))],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=msg.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testImageFamilyURI(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image-family '{0}/projects/my-project/global/images/family/yorik'
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[msg.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=msg.AttachedDiskInitializeParams(
                          sourceImage=(
                              self.compute_uri +
                              '/projects/my-project/global/images/'
                              'family/yorik'),
                      ),
                      mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=_DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[msg.NetworkInterface(
                      accessConfigs=[msg.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=_DefaultNetworkOf(self.api))],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=msg.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testImageFamilyURIImageFlag(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[msg.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=msg.AttachedDiskInitializeParams(
                          sourceImage=(
                              self.compute_uri +
                              '/projects/my-project/global/images/'
                              'family/yorik'),
                      ),
                      mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=_DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[msg.NetworkInterface(
                      accessConfigs=[msg.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=_DefaultNetworkOf(self.api))],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=msg.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesWithMultipleNetworkInterfaceCardsTest(
    InstancesCreateTestsMixin):
  """Test creation of preemptible VM instances."""

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testMultipleNetworkInterfaceCards(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface network=default,address=
          --network-interface network=some-net,private-network-ip=10.0.0.1,address=8.8.8.8
          --network-interface subnet=some-subnet
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[msg.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=msg.AttachedDiskInitializeParams(
                          sourceImage=(
                              self.compute_uri +
                              '/projects/my-project/global/images/'
                              'family/yorik'),
                      ),
                      mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=_DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          accessConfigs=[msg.AccessConfig(
                              name='external-nat',
                              networkTier=self._default_network_tier,
                              type=self._one_to_one_nat)],
                          network=_DefaultNetworkOf(self.api)),
                      msg.NetworkInterface(
                          accessConfigs=[msg.AccessConfig(
                              name='external-nat',
                              networkTier=self._default_network_tier,
                              natIP='8.8.8.8',
                              type=self._one_to_one_nat)],
                          network=('https://www.googleapis.com/compute/alpha/'
                                   'projects/my-project/global/networks/'
                                   'some-net'),
                          networkIP='10.0.0.1'),
                      msg.NetworkInterface(
                          subnetwork=('https://www.googleapis.com/compute/'
                                      'alpha/projects/my-project/regions/'
                                      'central2/subnetworks/some-subnet'),
                          accessConfigs=[msg.AccessConfig(
                              name='external-nat',
                              networkTier=self._default_network_tier,
                              type=self._one_to_one_nat)],
                      ),
                  ],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=msg.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testNetworkAndSubnetOnOneInterface(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-interface network=some-network,subnet=some-subnetwork
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          networkTier=self._default_network_tier,
                          type=self._one_to_one_nat)],
                      network=(
                          self.compute_uri + '/projects/my-project/global/'
                          'networks/some-network'),
                      subnetwork=(
                          self.compute_uri + '/projects/my-project/'
                          'regions/central2/subnetworks/some-subnetwork'))],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testNoAddress(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface no-address
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[msg.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=msg.AttachedDiskInitializeParams(
                          sourceImage=(
                              self.compute_uri +
                              '/projects/my-project/global/images/'
                              'family/yorik'),
                      ),
                      mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=_DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          network=('https://www.googleapis.com/compute/alpha/'
                                   'projects/my-project/global/networks/'
                                   'default')),
                  ],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=msg.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testNetworkTier(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface network=default
          --network-interface network=some-net,address=8.8.8.8,network-tier=SELECT
          --network-interface subnet=some-subnet,network-tier=premium
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', msg.ComputeInstancesInsertRequest(
            instance=msg.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceImage=(self.compute_uri +
                                         '/projects/my-project/global/images/'
                                         'family/yorik'),),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=_DefaultMachineTypeOf(self.api),
                metadata=msg.Metadata(),
                name='hamlet',
                networkInterfaces=[
                    msg.NetworkInterface(
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat',
                                type=self._one_to_one_nat,
                                networkTier=self._default_network_tier)
                        ],
                        network=_DefaultNetworkOf(self.api)),
                    msg.NetworkInterface(
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat',
                                natIP='8.8.8.8',
                                type=self._one_to_one_nat,
                                networkTier=(msg.AccessConfig.
                                             NetworkTierValueValuesEnum.SELECT))
                        ],
                        network=('https://www.googleapis.com/compute/alpha/'
                                 'projects/my-project/global/networks/'
                                 'some-net')),
                    msg.NetworkInterface(
                        subnetwork=('https://www.googleapis.com/compute/'
                                    'alpha/projects/my-project/regions/'
                                    'central2/subnetworks/some-subnet'),
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat',
                                type=self._one_to_one_nat,
                                networkTier=msg.AccessConfig.
                                NetworkTierValueValuesEnum.PREMIUM)
                        ],),
                ],
                serviceAccounts=[
                    msg.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=msg.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testNoAddreassAndAddressOnOneInterface(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-interface\]: specifies both address '
        r'and no-address for one interface'):
      self.Run("""
          compute instances create hamlet
            --zone central2-a
            --image {0}/projects/my-project/global/images/family/yorik
            --network-interface address=192.168.1.1,no-address
          """.format(self.compute_uri))

  def testMultiNicFlagAndOneNicFlag(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'^arguments not allowed simultaneously: --network-interface, all of '
        r'the following: --address, --network, --private-network-ip$'):
      self.Run("""
          compute instances create instance-1
            compute instances create hamlet
            --network-interface ''
            --address 8.8.8.8
            --network net
            --private-network-ip 10.0.0.2
          """)

  def testMultipleMetadataArgumentsShouldFail(self):
    with self.AssertRaisesArgumentError():
      self.Run('''
      compute instances create nvme-template-vm
        --zone central2-a
        --metadata block-project-ssh-keys=TRUE
        --metadata sshKeys=''
        --metadata ssh-keys=''
      ''')

  def testInvalidNetworkTier(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--network-interface]: '
        'Invalid value for network-tier'):
      self.Run("""
          compute instances create hamlet
            --zone central2-a
            --network-interface network=default
            --network-interface subnet=some-subnet,network-tier=RANDOM-TIER
          """)


class InstancesWithMultipleNetworkInterfaceCardsTestBeta(
    InstancesCreateTestsMixin):
  """Test creation of multinic VM instances for beta."""

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testMultipleNetworkInterfaceCards(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface network=default,address=
          --network-interface network=some-net,private-network-ip=10.0.0.1,address=8.8.8.8
          --network-interface subnet=some-subnet
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', msg.ComputeInstancesInsertRequest(
            instance=msg.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceImage=(self.compute_uri +
                                         '/projects/my-project/global/images/'
                                         'family/yorik'),),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=_DefaultMachineTypeOf(self.api),
                metadata=msg.Metadata(),
                name='hamlet',
                networkInterfaces=[
                    msg.NetworkInterface(
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=_DefaultNetworkOf(self.api)),
                    msg.NetworkInterface(
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat',
                                natIP='8.8.8.8',
                                type=self._one_to_one_nat)
                        ],
                        network=(self.compute_uri +
                                 '/projects/my-project/global/networks/'
                                 'some-net'),
                        networkIP='10.0.0.1'),
                    msg.NetworkInterface(
                        subnetwork=(
                            self.compute_uri + '/projects/my-project/regions/'
                            'central2/subnetworks/some-subnet'),
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],),
                ],
                serviceAccounts=[
                    msg.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=msg.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testNetworkAndSubnetOnOneInterface(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-interface network=some-network,subnet=some-subnetwork
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='instance-1',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=(
                            self.compute_uri + '/projects/my-project/global/'
                            'networks/some-network'),
                        subnetwork=(
                            self.compute_uri + '/projects/my-project/'
                            'regions/central2/subnetworks/some-subnetwork'))
                ],
                serviceAccounts=[
                    m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testNoAddress(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface no-address
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', msg.ComputeInstancesInsertRequest(
            instance=msg.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceImage=(self.compute_uri +
                                         '/projects/my-project/global/images/'
                                         'family/yorik'),),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=_DefaultMachineTypeOf(self.api),
                metadata=msg.Metadata(),
                name='hamlet',
                networkInterfaces=[
                    msg.NetworkInterface(
                        network=(self.compute_uri +
                                 '/projects/my-project/global/networks/'
                                 'default')),
                ],
                serviceAccounts=[
                    msg.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=msg.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testNoAddreassAndAddressOnOneInterface(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-interface\]: specifies both address '
        r'and no-address for one interface'):
      self.Run("""
          compute instances create hamlet
            --zone central2-a
            --image {0}/projects/my-project/global/images/family/yorik
            --network-interface address=192.168.1.1,no-address
          """.format(self.compute_uri))

  def testMultiNicFlagAndOneNicFlag(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'^arguments not allowed simultaneously: --network-interface, all of '
        r'the following: --address, --network, --private-network-ip$'):
      self.Run("""
          compute instances create instance-1
            compute instances create hamlet
            --network-interface ''
            --address 8.8.8.8
            --network net
            --private-network-ip 10.0.0.2
          """)

  def testMultipleMetadataArgumentsShouldFail(self):
    with self.AssertRaisesArgumentError():
      self.Run("""
      compute instances create nvme-template-vm
        --zone central2-a
        --metadata block-project-ssh-keys=TRUE
        --metadata sshKeys=''
        --metadata ssh-keys=''
      """)


class InstanceWithAliasIpRangesTest(
    InstancesCreateTestsMixin):
  """Test creation of instace with alias IP ranges."""

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testAliasIpRanges(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface network=default,address=,aliases=range1:1.2.3.4;range2:/24;/32
          --network-interface network=some-net,private-network-ip=10.0.0.1,address=8.8.8.8,aliases=range1:1.2.3.0/24
          --network-interface subnet=some-subnet
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', msg.ComputeInstancesInsertRequest(
            instance=msg.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceImage=(self.compute_uri +
                                         '/projects/my-project/global/images/'
                                         'family/yorik'),),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=_DefaultMachineTypeOf(self.api),
                metadata=msg.Metadata(),
                name='hamlet',
                networkInterfaces=[
                    msg.NetworkInterface(
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=_DefaultNetworkOf(self.api),
                        aliasIpRanges=[
                            msg.AliasIpRange(
                                subnetworkRangeName='range1',
                                ipCidrRange='1.2.3.4'),
                            msg.AliasIpRange(
                                subnetworkRangeName='range2',
                                ipCidrRange='/24'),
                            msg.AliasIpRange(ipCidrRange='/32')
                        ]),
                    msg.NetworkInterface(
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat',
                                natIP='8.8.8.8',
                                type=self._one_to_one_nat)
                        ],
                        network=('https://www.googleapis.com/compute/v1/'
                                 'projects/my-project/global/networks/'
                                 'some-net'),
                        networkIP='10.0.0.1',
                        aliasIpRanges=[
                            msg.AliasIpRange(
                                subnetworkRangeName='range1',
                                ipCidrRange='1.2.3.0/24')
                        ]),
                    msg.NetworkInterface(
                        subnetwork=('https://www.googleapis.com/compute/v1/'
                                    'projects/my-project/regions/central2/'
                                    'subnetworks/some-subnet'),
                        accessConfigs=[
                            msg.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],),
                ],
                serviceAccounts=[
                    msg.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=msg.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testInvalidAliasIpRangeFormat(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'An alias IP range must contain range name and IP '
        r'range'):
      self.Run("""
          compute instances create instance-1
          --zone central2-a
          --network-interface network=default,aliases=range1:abc:def;
          """)


class InstancesCreateWithNodeAffinity(InstancesCreateTestsMixin,
                                      parameterized.TestCase):
  """Test creation of VM instances on sole tenant host."""

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA
    self.node_affinity = self.messages.SchedulingNodeAffinity
    self.operator_enum = self.node_affinity.OperatorValueValuesEnum

  def _CheckCreateRequests(self, node_affinities):
    m = self.messages
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          networkTier=self._default_network_tier,
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True,
                      nodeAffinities=node_affinities),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testCreate_SimpleNodeAffinityJson(self):
    node_affinities = [
        self.node_affinity(
            key='key1',
            operator=self.operator_enum.IN,
            values=['value1', 'value2'])]
    contents = """\
[{"operator": "IN", "values": ["value1", "value2"], "key": "key1"}]
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    self.Run("""
        compute instances create instance-1 --zone central2-a
          --node-affinity-file {}
        """.format(node_affinity_file))

    self._CheckCreateRequests(node_affinities)

  def testCreate_SimpleNodeAffinityYaml(self):
    node_affinities = [
        self.node_affinity(
            key='key1',
            operator=self.operator_enum.IN,
            values=['value1', 'value2'])]
    contents = """\
- key: key1
  operator: IN
  values: [value1, value2]
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    self.Run("""
        compute instances create instance-1 --zone central2-a
          --node-affinity-file {}
        """.format(node_affinity_file))

    self._CheckCreateRequests(node_affinities)

  def testCreate_MultipleNodeAffinityMessages(self):
    node_affinities = [
        self.node_affinity(
            key='key1',
            operator=self.operator_enum.IN,
            values=['value1']),
        self.node_affinity(
            key='key2',
            operator=self.operator_enum.NOT_IN,
            values=['value2', 'value3']),
        self.node_affinity(
            key='key3',
            operator=self.operator_enum.IN,
            values=[])]
    contents = """\
- key: key1
  operator: IN
  values: [value1]
- key: key2
  operator: NOT_IN
  values: [value2, value3]
- key: key3
  operator: IN
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    self.Run("""
        compute instances create instance-1 --zone central2-a
          --node-affinity-file {}
        """.format(node_affinity_file))

    self._CheckCreateRequests(node_affinities)

  def testCreate_InvalidOperator(self):
    contents = """\
- key: key1
  operator: HelloWorld
  values: [value1, value2]
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    with self.AssertRaisesExceptionMatches(
        sole_tenancy_util.NodeAffinityFileParseError,
        "Key [key1] has invalid field formats for: ['operator']"):
      self.Run("""
          compute instances create instance-1 --zone central2-a
            --node-affinity-file {}
          """.format(node_affinity_file))

  def testCreate_NoKey(self):
    contents = """\
- operator: IN
  values: [value1, value2]
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    with self.AssertRaisesExceptionMatches(
        sole_tenancy_util.NodeAffinityFileParseError,
        'A key must be specified for every node affinity label.'):
      self.Run("""
          compute instances create instance-1 --zone central2-a
            --node-affinity-file {}
          """.format(node_affinity_file))

  def testCreate_InvalidYaml(self):
    contents = """\
- key: key1
  operator: IN
  values: 3
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    with self.assertRaisesRegexp(
        sole_tenancy_util.NodeAffinityFileParseError,
        r"Expected type <(type|class) '(str|unicode)'> for field values, "
        r"found 3 \(type <(class|type) 'int'>\)"):
      self.Run("""
          compute instances create instance-1 --zone central2-a
            --node-affinity-file {}
          """.format(node_affinity_file))

  @parameterized.parameters('-', '[{}]')
  def testCreate_EmptyListItem(self, contents):
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    with self.AssertRaisesExceptionMatches(
        sole_tenancy_util.NodeAffinityFileParseError,
        'Empty list item in JSON/YAML file.'):
      self.Run("""
          compute instances create instance-1 --zone central2-a
            --node-affinity-file {}
          """.format(node_affinity_file))

  @parameterized.parameters('', '[]')
  def testCreate_AffinityFileWithLabels(self, contents):
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    with self.AssertRaisesExceptionMatches(
        sole_tenancy_util.NodeAffinityFileParseError,
        'No node affinity labels specified. You must specify at least one '
        'label to create a sole tenancy instance.'):
      self.Run("""
          compute instances create instance-1 --zone central2-a
            --node-affinity-file {}
          """.format(node_affinity_file))

  def testCreate_NodeGroup(self):
    node_affinities = [
        self.node_affinity(
            key='compute.googleapis.com/node-group-name',
            operator=self.operator_enum.IN,
            values=['my-node-group'])]
    self.Run("""
        compute instances create instance-1 --zone central2-a
          --node-group my-node-group
        """)

    self._CheckCreateRequests(node_affinities)

  def testCreate_Node(self):
    node_affinities = [
        self.node_affinity(
            key='compute.googleapis.com/node-name',
            operator=self.operator_enum.IN,
            values=['my-node'])
    ]
    self.Run("""
        compute instances create instance-1 --zone central2-a
          --node my-node
        """)

    self._CheckCreateRequests(node_affinities)


@parameterized.parameters(
    ('alpha', calliope_base.ReleaseTrack.ALPHA),
    ('beta', calliope_base.ReleaseTrack.BETA),
    ('v1', calliope_base.ReleaseTrack.GA))
class InstancesCreateScopesDeprecationTestsGa(InstancesCreateTestsMixin,
                                              parameterized.TestCase):
  # Set of tests of deprecation of old --scopes flag syntax, new --scopes flag
  # syntax and --service-account flag.

  def testScopesLegacyFormatDeprecationNotice(self, api, release_track):
    SetUp(self, api)
    self.track = release_track

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--scopes]: Flag format --scopes [ACCOUNT=]SCOPE,'
        '[[ACCOUNT=]SCOPE, ...] is removed. Use --scopes [SCOPE,...] '
        '--service-account ACCOUNT instead.'):
      self.Run('compute instances create asdf '
               '--scopes=acc1=scope1,acc1=scope2 '
               '--zone zone-1')

  def testScopesNewFormatNoDeprecationNotice(self, api, release_track):
    SetUp(self, api)
    self.track = release_track

    self.Run('compute instances create asdf '
             '--scopes=scope1,scope2 --service-account acc1@example.com '
             '--zone zone-1')
    self.AssertErrEquals('')

  def testNoServiceAccount(self, api, release_track):
    SetUp(self, api)
    self.track = release_track

    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instances create asdf '
               '--no-service-account '
               '--zone zone-1')

  def testScopesWithNoServiceAccount(self, api, release_track):
    SetUp(self, api)
    self.track = release_track

    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instances create asdf '
               '--scopes=acc1=scope1 --no-service-account '
               '--zone zone-1')

  def testWithManyScopes(self, api, release_track):
    SetUp(self, api)
    self.track = release_track

    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --scopes compute-rw,https://www.googleapis.com/auth/devstorage.full_control,bigquery,https://www.googleapis.com/auth/userinfo.email,sql,https://www.googleapis.com/auth/taskqueue,cloud-platform,https://www.googleapis.com/auth/source.read_only
          --service-account 1234@project.gserviceaccount.com
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],

                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='1234@project.gserviceaccount.com',
                          scopes=[
                              'https://www.googleapis.com/auth/bigquery',
                              'https://www.googleapis.com/auth/cloud-platform',
                              'https://www.googleapis.com/auth/compute',
                              ('https://www.googleapis.com/auth/devstorage'
                               '.full_control'),
                              ('https://www.googleapis.com/auth'
                               '/source.read_only'),
                              'https://www.googleapis.com/auth/sqlservice',
                              'https://www.googleapis.com/auth/taskqueue',
                              'https://www.googleapis.com/auth/userinfo.email',
                          ]),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testNoServiceAccountNoScopes(self, api, release_track):
    SetUp(self, api)
    self.track = release_track

    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --no-service-account
          --no-scopes
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],

                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateAttachRegionalDiskGA(InstancesCreateTestsMixin):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    SetUp(self, self.api_version)


class InstancesCreateAttachRegionalDiskBeta(
    InstancesCreateAttachRegionalDiskGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testRegionalDisk(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --disk name=disk1,scope=regional
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                         m.AttachedDisk(
                             autoDelete=False,
                             boot=False,
                             source=(self.compute_uri +
                                     '/projects/my-project/regions/central2/'
                                     'disks/disk1'),
                             mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                             type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT
                         )],

                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          networkTier=self._default_network_tier,
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=[
                              'https://www.googleapis.com/auth/devstorage'
                              '.read_only',
                              'https://www.googleapis.com/auth/logging.write',
                              'https://www.googleapis.com/auth/monitoring'
                              '.write',
                              'https://www.googleapis.com/auth/pubsub',
                              'https://www.googleapis.com/auth/service'
                              '.management.readonly',
                              'https://www.googleapis.com/auth/servicecontrol',
                              'https://www.googleapis.com/auth/trace.append',
                          ]),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True)
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateAttachRegionalDiskAlpha(
    InstancesCreateAttachRegionalDiskBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


class InstancesCreateWithAccelerator(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testCreateInstanceWithAcceleratorNoType(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--accelerator\]: accelerator type must be '
        r'specified\. e\.g\. --accelerator type=nvidia-tesla-k80,count=2'):
      self.Run("""
          compute instances create instance
            --zone central2-a
            --accelerator count=2
          """)

  def testCreateInstanceWithAcceleratorRequest(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --accelerator type=nvidia-tesla-k80,count=2
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=(m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image)),
                        mode=(m.AttachedDisk.ModeValueValuesEnum.READ_WRITE),
                        type=(m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)),
                ],
                guestAccelerators=[
                    m.AcceleratorConfig(
                        acceleratorType=_AcceleratorTypeOf('v1',
                                                           'nvidia-tesla-k80'),
                        acceleratorCount=2,)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='instance',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat',
                                type=(m.AccessConfig.TypeValueValuesEnum.
                                      ONE_TO_ONE_NAT))
                        ],
                        network=self._default_network)
                ],
                serviceAccounts=[
                    m.ServiceAccount(
                        email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))])

  def testCreateInstanceWithAcceleratorCountOmittedRequest(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --accelerator type=nvidia-tesla-k80
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=(m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image)),
                        mode=(m.AttachedDisk.ModeValueValuesEnum.READ_WRITE),
                        type=(m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)),
                ],
                guestAccelerators=[
                    m.AcceleratorConfig(
                        acceleratorType=_AcceleratorTypeOf('v1',
                                                           'nvidia-tesla-k80'),
                        acceleratorCount=1,)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='instance',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat',
                                type=(m.AccessConfig.TypeValueValuesEnum.
                                      ONE_TO_ONE_NAT))
                        ],
                        network=self._default_network)
                ],
                serviceAccounts=[
                    m.ServiceAccount(
                        email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))])


class InstancesCreateWithPublicDns(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def CreateRequestWithPublicDns(self,
                                 set_public_dns=None,
                                 set_ptr=None,
                                 ptr_domain_name=None):
    m = self.messages
    access_config = m.AccessConfig(
        name='external-nat',
        networkTier=self._default_network_tier,
        type=self._one_to_one_nat)

    if set_public_dns is not None:
      access_config.setPublicDns = bool(set_public_dns)
    if set_ptr is not None:
      access_config.setPublicPtr = bool(set_ptr)
    if ptr_domain_name is not None:
      access_config.publicPtrDomainName = ptr_domain_name

    return m.ComputeInstancesInsertRequest(
        instance=m.Instance(
            canIpForward=False,
            deletionProtection=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=self._default_machine_type,
            metadata=m.Metadata(),
            name='instance-1',
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),),
        project='my-project',
        zone='central2-a',)

  def testPublicDnsDisabledByDefault(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns())],)

  def testEnablePublicDns(self):
    self.Run("""
        compute instances create instance-1 --public-dns
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns(set_public_dns=True))],)

  def testDisablePublicDns(self):
    self.Run("""
        compute instances create instance-1 --no-public-dns
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns(set_public_dns=False))],)

  def testInvalidPublicDnsSettings(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-dns: At most one of --public-dns | --no-public-dns '
        'may be specified.'):
      self.Run("""
          compute instances create instance-1 --no-public-dns
            --public-dns
            --zone central2-a
          """)


class InstancesCreateWithPublicPtrTest(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def CreateRequestWithPublicDns(self,
                                 set_ptr=None,
                                 ptr_domain_name=None):
    m = self.messages
    access_config = m.AccessConfig(
        name='external-nat',
        type=self._one_to_one_nat)

    if set_ptr is not None:
      access_config.setPublicPtr = bool(set_ptr)
    if ptr_domain_name is not None:
      access_config.publicPtrDomainName = ptr_domain_name

    return m.ComputeInstancesInsertRequest(
        instance=m.Instance(
            canIpForward=False,
            deletionProtection=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=self._default_machine_type,
            metadata=m.Metadata(),
            name='instance-1',
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),),
        project='my-project',
        zone='central2-a',)

  def testPublicDnsDisabledByDefault(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns())],)

  def testEnablePtr(self):
    self.Run("""
        compute instances create instance-1 --public-ptr
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns(set_ptr=True))],)

  def testDisablePtr(self):
    self.Run("""
        compute instances create instance-1 --no-public-ptr
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns(set_ptr=False))],)

  def testSetPtrDomainName(self):
    self.Run("""
        compute instances create instance-1 --public-ptr
          --public-ptr-domain example.com
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', self.CreateRequestWithPublicDns(
            set_ptr=True, ptr_domain_name='example.com'))],)

  def testDisablePtrDomainName(self):
    self.Run("""
        compute instances create instance-1 --no-public-ptr-domain
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns())],)

  def testInvalidPublicDnsSettings(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-ptr: At most one of --public-ptr | --no-public-ptr '
        'may be specified.'):
      self.Run("""
          compute instances create instance-1 --no-public-ptr
            --public-ptr
            --zone central2-a
          """)

    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-ptr-domain: At most one of --public-ptr-domain | '
        '--no-public-ptr-domain may be specified.'):
      self.Run("""
          compute instances create instance-1
            --no-public-ptr-domain
            --public-ptr-domain example.com
            --zone central2-a
          """)

    with self.assertRaisesRegex(
        exceptions.ConflictingArgumentsException,
        r'arguments not allowed simultaneously: --public-ptr-domain, '
        r'--no-public-ptr'):
      self.Run("""
           compute instances create instance-1 --no-public-ptr
            --public-ptr-domain example.com
            --zone central2-a
          """)


class InstancesCreateWithPublicPtrBetaTest(InstancesCreateWithPublicPtrTest):

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA


class InstancesCreateWithPublicPtrAlphaTest(InstancesCreateWithPublicPtrTest):

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA


class InstancesCreateWithNetworkTierAlpha(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

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
            deletionProtection=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=self._default_machine_type,
            metadata=m.Metadata(),
            name='instance-1',
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[m.AccessConfig(
                    name='external-nat',
                    type=self._one_to_one_nat,
                    networkTier=network_tier_enum)],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),),
        project='my-project',
        zone='central2-a',)

  def testWithDefaultNetworkTier(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier(None))],)

  def testWithPremiumNetworkTier(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-tier PREMIUM
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier('PREMIUM'))],)

  def testWithSelectNetworkTier(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-tier select
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier('SELECT'))],)

  def testWithStandardNetworkTier(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-tier standard
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier('STANDARD'))],
    )

  def testInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionMatches(
        'Invalid value for [--network-tier]: Invalid network tier '
        '[RANDOM-NETWORK-TIER]'):
      self.Run("""
          compute instances create instance-1
            --network-tier random-network-tier
            --zone central2-a
          """)


class InstancesCreateWithNetworkTierBeta(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

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
            deletionProtection=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=self._default_machine_type,
            metadata=m.Metadata(),
            name='instance-1',
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[
                        m.AccessConfig(
                            name='external-nat',
                            type=self._one_to_one_nat,
                            networkTier=network_tier_enum)
                    ],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        ),
        project='my-project',
        zone='central2-a',
    )

  def testWithDefaultNetworkTier(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier(None))],
    )

  def testWithPremiumNetworkTier(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-tier PREMIUM
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier('PREMIUM'))],
    )

  def testWithStandardNetworkTier(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-tier standard
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier('STANDARD'))],
    )

  def testInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionMatches(
        'Invalid value for [--network-tier]: Invalid network tier '
        '[RANDOM-NETWORK-TIER]'):
      self.Run("""
          compute instances create instance-1
            --network-tier random-network-tier
            --zone central2-a
          """)


class InstancesCreateWithNetworkTierGa(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

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
            deletionProtection=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=self._default_machine_type,
            metadata=m.Metadata(),
            name='instance-1',
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[
                        m.AccessConfig(
                            name='external-nat',
                            type=self._one_to_one_nat,
                            networkTier=network_tier_enum)
                    ],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        ),
        project='my-project',
        zone='central2-a',
    )

  def testWithDefaultNetworkTier(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier(None))],
    )

  def testWithPremiumNetworkTier(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-tier PREMIUM
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier('PREMIUM'))],
    )

  def testWithStandardNetworkTier(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-tier standard
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNetworkTier('STANDARD'))],)

  def testInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionMatches(
        'Invalid value for [--network-tier]: Invalid network tier '
        '[RANDOM-NETWORK-TIER]'
    ):
      self.Run("""
          compute instances create instance-1
            --network-tier random-network-tier
            --zone central2-a
          """)


class InstancesCreateMinCpuPlatformAlpha(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testExplicit(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --min-cpu-platform asdf
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                minCpuPlatform='asdf',
                name='instance-1',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat',
                                networkTier=self._default_network_tier,
                                type=self._one_to_one_nat)
                        ],
                        network=self._default_network)
                ],
                serviceAccounts=[
                    m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testDefault(self):
    m = self.messages
    self.Run("""
          compute instances create instance-1
            --zone central2-a
          """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                minCpuPlatform=None,
                name='instance-1',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat',
                                networkTier=self._default_network_tier,
                                type=self._one_to_one_nat)
                        ],
                        network=self._default_network)
                ],
                serviceAccounts=[
                    m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)


class InstancesCreateMinCpuPlatformBeta(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testExplicit(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --min-cpu-platform asdf
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                minCpuPlatform='asdf',
                name='instance-1',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=self._default_network)
                ],
                serviceAccounts=[
                    m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testDefault(self):
    m = self.messages
    self.Run("""
          compute instances create instance-1
            --zone central2-a
          """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                minCpuPlatform=None,
                name='instance-1',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=self._default_network)
                ],
                serviceAccounts=[
                    m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)


class InstancesCreateMinCpuPlatformGA(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testExplicit(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --min-cpu-platform asdf
        """)

    self.CheckRequests(
        self.zone_get_request, self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                minCpuPlatform='asdf',
                name='instance-1',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=self._default_network)
                ],
                serviceAccounts=[
                    m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a'))])

    self.AssertOutputEquals('')
    self.AssertErrEquals('')


class InstancesCreateTestBeta(InstancesCreateTestsMixin,
                              parameterized.TestCase):

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testWithAnyReservationAffinity(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1 --zone central2-a
        --reservation-affinity=any
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  reservationAffinity=m.ReservationAffinity(
                      consumeReservationType=m.ReservationAffinity
                        .ConsumeReservationTypeValueValuesEnum.ANY_RESERVATION,),
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithSpecificReservationAffinity(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1 --zone central2-a
        --reservation-affinity=specific --reservation=my-reservation
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  reservationAffinity=m.ReservationAffinity(
                      consumeReservationType=m.ReservationAffinity
                        .ConsumeReservationTypeValueValuesEnum
                        .SPECIFIC_RESERVATION,
                      key='compute.googleapis.com/reservation-name',
                      values=['my-reservation']),
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithNotSpecifiedReservation(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException,
        'The name the specific reservation must be specified.'):
      self.Run("""
        compute instances create instance-1 --zone central2-a
        --reservation-affinity=specific
        """)

  def testWithNoReservationAffinity(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1 --zone central2-a
        --reservation-affinity=none
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  reservationAffinity=m.ReservationAffinity(
                      consumeReservationType=m.ReservationAffinity
                        .ConsumeReservationTypeValueValuesEnum.NO_RESERVATION,),
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateTestAlpha(InstancesCreateTestBeta):

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testLocalNVDIMMRequest(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --local-nvdimm ''
          --local-nvdimm size=3TB
        """)

    self.CheckRequests(
        self.zone_get_request, self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=(m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image)),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=True,
                          initializeParams=(m.AttachedDiskInitializeParams(
                              diskType=self._nvdimm_disk_type)),
                          interface=(m.AttachedDisk.InterfaceValueValuesEnum
                                     .NVDIMM),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
                      m.AttachedDisk(
                          autoDelete=True,
                          diskSizeGb=3072,
                          initializeParams=(m.AttachedDiskInitializeParams(
                              diskType=self._nvdimm_disk_type)),
                          interface=(m.AttachedDisk.InterfaceValueValuesEnum
                                     .NVDIMM),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=(m.AccessConfig.TypeValueValuesEnum
                                        .ONE_TO_ONE_NAT))
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))])

  def testLocalSSDRequestWithSize(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --local-ssd ''
          --local-ssd interface=NVME,size=750
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=(
                              m.AttachedDiskInitializeParams(
                                  sourceImage=self._default_image)
                          ),
                          mode=(m.AttachedDisk
                                .ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.PERSISTENT)),
                      m.AttachedDisk(
                          autoDelete=True,
                          initializeParams=(
                              m.AttachedDiskInitializeParams(
                                  diskType=self._ssd_disk_type)),
                          mode=(m.AttachedDisk
                                .ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.SCRATCH)),
                      m.AttachedDisk(
                          autoDelete=True,
                          diskSizeGb=750,
                          initializeParams=(
                              m.AttachedDiskInitializeParams(
                                  diskType=self._ssd_disk_type)),
                          interface=(m.AttachedDisk
                                     .InterfaceValueValuesEnum.NVME),
                          mode=(m.AttachedDisk
                                .ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk
                                .TypeValueValuesEnum.SCRATCH)),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=(m.AccessConfig.TypeValueValuesEnum
                                .ONE_TO_ONE_NAT))],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))]
    )

  def testLocalSSDRequestWithBadSize(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Unexpected local SSD size: \[536870912000\]. '
        r'Legal values are positive multiples of 375GB.'):
      self.Run("""
          compute instances create instance
            --zone central2-a
            --local-ssd size=500
          """)

  def createWithOnHostMaintenanceTest(self, flag):
    m = self.messages

    self.Run('compute instances create instance-1 --zone central2-a '
             '{}=TERMINATE'.format(flag))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True,
                      onHostMaintenance=m.Scheduling.
                      OnHostMaintenanceValueValuesEnum.TERMINATE),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithOnHostMaintenance(self):
    self.createWithOnHostMaintenanceTest('--on-host-maintenance')

  def testMaintenancePolicyDeprecation(self):
    self.createWithOnHostMaintenanceTest('--maintenance-policy')
    self.AssertErrContains(
        'WARNING: The --maintenance-policy flag is now deprecated. '
        'Please use `--on-host-maintenance` instead')

  def testWithResourcePolicies(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --resource-policies pol1
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='instance',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=self._default_network)
                ],
                resourcePolicies=[
                    self.compute_uri + '/projects/{}/regions/central2/'
                    'resourcePolicies/pol1'.format(self.Project())],
                serviceAccounts=[
                    m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testWithMultipleResourcePolicies(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --resource-policies pol1,pol2
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='instance',
                networkInterfaces=[
                    m.NetworkInterface(
                        accessConfigs=[
                            m.AccessConfig(
                                name='external-nat', type=self._one_to_one_nat)
                        ],
                        network=self._default_network)
                ],
                resourcePolicies=[
                    self.compute_uri + '/projects/{}/regions/central2/'
                    'resourcePolicies/pol1'.format(self.Project()),
                    self.compute_uri + '/projects/{}/regions/central2/'
                    'resourcePolicies/pol2'.format(self.Project())],
                serviceAccounts=[
                    m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)


class InstancesCreateWithLabelsTest(test_base.BaseTest):
  """Test creation of instances with labels."""

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

    self.project_get_request = [
        (self.compute.projects,
         'Get',
         self.messages.ComputeProjectsGetRequest(
             project='my-project'))
    ]

  def testCreateWithLabels(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [m.Zone(name='central2-a'),],
        [m.Project(defaultServiceAccount='default@service.account'),],
        [],
    ])

    self.Run("""
       compute instances create instance-with-labels
       --zone=central2-a
       --labels=k0=v0,k-1=v-1
       --labels=foo=bar
       """)

    labels_in_request = (('foo', 'bar'), ('k-1', 'v-1'), ('k0', 'v0'))
    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone='central2-a'))],
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=_DefaultImageOf('v1'),
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  labels=m.Instance.LabelsValue(
                      additionalProperties=[
                          m.Instance.LabelsValue.AdditionalProperty(
                              key=pair[0], value=pair[1])
                          for pair in labels_in_request]),
                  metadata=m.Metadata(),
                  machineType=_DefaultMachineTypeOf(self.api),
                  name='instance-with-labels',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=m.AccessConfig.TypeValueValuesEnum.
                          ONE_TO_ONE_NAT)],
                      network=_DefaultNetworkOf('v1'))],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True)),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testCreateWithInvalidLabels(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run("""
          compute instances create instance-with-labels
            --zone=central2-a
            --labels=inv@lid-key=inv@l!d-value
          """)


class InstancesCreateSourceInstanceTemplate(InstancesCreateTestsMixin,
                                            parameterized.TestCase):

  @parameterized.parameters(
      ('alpha', calliope_base.ReleaseTrack.ALPHA),
      ('beta', calliope_base.ReleaseTrack.BETA),
      ('v1', calliope_base.ReleaseTrack.GA))
  def testCreateFromTemplate(self, api_version, track):
    SetUp(self, api_version)
    self.track = track
    m = self.messages

    self.Run('compute instances create instance-1 '
             '--zone central2-a '
             '--source-instance-template template')

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                deletionProtection=False,
                name='instance-1'),
            project='my-project',
            sourceInstanceTemplate=(
                self.compute_uri +
                '/projects/my-project/global/instanceTemplates/template'),
            zone='central2-a'))])


class InstancesCreateWithKmsTestGa(InstancesCreateTestsMixin):

  GLOBAL_KMS_KEY = ('projects/key-project/locations/global/keyRings/my-ring/'
                    'cryptoKeys/my-key')
  GLOBAL_KMS_KEY_SAME_PROJECT = ('projects/my-project/locations/global/'
                                 'keyRings/my-ring/cryptoKeys/my-key')

  def SetupApiAndTrack(self):
    SetUp(self, 'v1')
    self._api = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SetupApiAndTrack()
    self.global_kms_key = self.messages.CustomerEncryptionKey(
        kmsKeyName=self.GLOBAL_KMS_KEY)
    self.global_kms_key_in_same_project = self.messages.CustomerEncryptionKey(
        kmsKeyName=self.GLOBAL_KMS_KEY_SAME_PROJECT)

  def assertBootDiskWithKmsKey(self, expected_key=None):
    if not expected_key:
      expected_key = self.global_kms_key
    m = self.messages
    self.assertDefaultRequestWithAttachedDisks(m.AttachedDisk(
        autoDelete=True,
        boot=True,
        diskEncryptionKey=expected_key,
        initializeParams=m.AttachedDiskInitializeParams(
            sourceImage=_DefaultImageOf(self._api),
        ),
        mode=(m.AttachedDisk
              .ModeValueValuesEnum.READ_WRITE),
        type=(m.AttachedDisk
              .TypeValueValuesEnum.PERSISTENT)))

  def testBootDiskWithKmsKey(self):
    self.Run("""
        compute instances create instance
          --zone central2-a
          --boot-disk-kms-key projects/key-project/locations/global/keyRings/my-ring/cryptoKeys/my-key
        """)
    self.assertBootDiskWithKmsKey()

  def testBootDiskWithKmsKeyAsParts(self):
    self.Run("""
        compute instances create instance
          --zone central2-a
          --boot-disk-kms-key my-key
          --boot-disk-kms-project key-project
          --boot-disk-kms-location global
          --boot-disk-kms-keyring my-ring
        """)
    self.assertBootDiskWithKmsKey()

  def testBootDiskWithKmsKeyAsPartsUseDefaultProject(self):
    self.Run("""
        compute instances create instance
          --zone central2-a
          --boot-disk-kms-key my-key
          --boot-disk-kms-location global
          --boot-disk-kms-keyring my-ring
        """)
    self.assertBootDiskWithKmsKey(
        expected_key=self.global_kms_key_in_same_project)

  def testBootDiskWithKmsKeyAsPartsNoKeyRing(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'KMS cryptokey resource was not fully specified.'):
      self.Run("""
          compute instances create instance
            --zone central2-a
            --boot-disk-kms-key my-key
            --boot-disk-kms-location global
          """)

  def testBootDiskWithKmsKeyAsPartsUnqualifiedKey(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'KMS cryptokey resource was not fully specified.'):
      self.Run("""
          compute instances create instance
            --zone central2-a
            --boot-disk-kms-key my-key
          """)

  def testBootDiskWithKmsKeyAsPartsLocationOnly(self):
    with self.AssertRaisesArgumentError():
      self.Run("""
          compute instances create instance
            --zone central2-a
            --boot-disk-kms-location global
          """)

  def testCreateNonBootDiskWithKmsKey(self):
    self.Run("""
        compute instances create instance
          --zone central2-a
          --create-disk name=disk-1,image=foo,size=10GB,kms-key=projects/key-project/locations/global/keyRings/my-ring/cryptoKeys/my-key
        """)
    self.assertNonBootDiskWithKmsKey()

  def testCreateNonBootDiskWithKmsKeyAsParts(self):
    self.Run("""
        compute instances create instance
          --zone central2-a
          --create-disk name=disk-1,image=foo,size=10GB,kms-key=my-key,kms-project=key-project,kms-location=global,kms-keyring=my-ring
        """)
    self.assertNonBootDiskWithKmsKey()

  def testCreateNonBootDiskWithKmsKeyAsPartsUseDefaultProject(self):
    self.Run("""
        compute instances create instance
          --zone central2-a
          --create-disk name=disk-1,image=foo,size=10GB,kms-key=my-key,kms-location=global,kms-keyring=my-ring
        """)
    self.assertNonBootDiskWithKmsKey(
        expected_key=self.global_kms_key_in_same_project)

  def testCreateNonBootDiskWithKmsKeyAsPartsLocationOnly(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'KMS cryptokey resource was not fully specified.'):
      self.Run("""
          compute instances create instance
            --zone central2-a
            --create-disk name=disk-1,image=foo,size=10GB,kms-location=global
          """)

  def testWithNoImageAndBootDiskKmsKeyOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-kms-key\] can only be used when creating a new boot '
        r'disk.'):
      self.Run("""
          compute instances create instance-1
            --disk boot=yes,name=my-disk
            --boot-disk-kms-key projects/key-project/locations/global/keyRings/my-ring/cryptoKeys/my-key
            --zone central2-a
          """)

    self.CheckRequests()

  def assertNonBootDiskWithKmsKey(self, expected_key=None):
    if not expected_key:
      expected_key = self.global_kms_key
    m = self.messages
    self.assertDefaultRequestWithAttachedDisks([
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=True,
            boot=False,
            diskEncryptionKey=expected_key,
            initializeParams=m.AttachedDiskInitializeParams(
                diskName='disk-1',
                diskSizeGb=10,
                sourceImage=(self.compute_uri +
                             '/projects/my-project/global/images/'
                             'foo')),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    ])

  def assertDefaultRequestWithAttachedDisks(self, disks):
    m = self.messages
    if not isinstance(disks, list):
      disks = [disks]
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=disks,
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=(m.AccessConfig.TypeValueValuesEnum
                                .ONE_TO_ONE_NAT))],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))]
    )


class InstancesCreateWithKmsTestBeta(InstancesCreateWithKmsTestGa):

  def SetupApiAndTrack(self):
    SetUp(self, 'beta')
    self._api = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class InstancesCreateWithKmsTestAlpha(InstancesCreateWithKmsTestGa):

  def SetupApiAndTrack(self):
    SetUp(self, 'alpha')
    self._api = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateWithImageAndFamilyFlags(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Must specify exactly one of \[image\], \[image-family\] or '
        r'\[source-snapshot\] for a \[--create-disk\]. '
        r'These fields are mutually exclusive.'):
      self.Run("""
          compute instances create vm
            --create-disk image=foo,image-family=bar
          """)

    self.CheckRequests()


class InstancesCreateDeletionProtection(InstancesCreateTestsMixin,
                                        parameterized.TestCase):
  """Test creation of VM instances using deletion protection flag."""

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def _GetExpectedInstance(self, deletion_protection):
    m = self.messages
    return m.Instance(
        canIpForward=False,
        deletionProtection=deletion_protection,
        disks=[
            m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
        ],
        machineType=self._default_machine_type,
        metadata=m.Metadata(),
        minCpuPlatform=None,
        name='instance-1',
        networkInterfaces=[
            m.NetworkInterface(
                accessConfigs=[
                    m.AccessConfig(
                        name='external-nat',
                        type=self._one_to_one_nat)
                ],
                network=self._default_network)
        ],
        serviceAccounts=[
            m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
        ],
        scheduling=m.Scheduling(automaticRestart=True),)

  @parameterized.named_parameters(
      ('SetTrue', '--deletion-protection', True),
      ('SetFalse', '--no-deletion-protection', False),
      ('Default', '', False))
  def testDeletionProtection(self, flag, deletion_protection):
    m = self.messages

    self.Run('compute instances create instance-1 '
             '--zone central2-a {}'.format(flag))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=self._GetExpectedInstance(
                deletion_protection=deletion_protection),
            project='my-project',
            zone='central2-a',))],)


class InstancesCreateShieldedInstanceConfigGATest(InstancesCreateTestsMixin,
                                                  parameterized.TestCase):
  """Test creation of VM instances with shielded VM config for v1 API."""

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  # TODO(b/120429236): remove tests for shielded-vm flag after migration to
  # shielded-instance flags is complete.
  @parameterized.named_parameters(
      ('-InstanceEnableSecureBoot', '--shielded-secure-boot', True, None, None),
      ('-InstanceEnableVtpm', '--shielded-vtpm', None, True, None),
      ('-InstanceEnableIntegrity', '--shielded-integrity-monitoring', None,
       None, True), ('-InstanceDisableSecureBoot', '--no-shielded-secure-boot',
                     False, None, None),
      ('-InstanceDisableVtpm', '--no-shielded-vtpm', None, False, None),
      ('-InstanceDisableIntegrity', '--no-shielded-integrity-monitoring', None,
       None, False),
      ('-InstanceESecureBootEvtpm', '--shielded-secure-boot --shielded-vtpm',
       True, True, None),
      ('-InstanceDSecureBootDvtpm',
       '--no-shielded-secure-boot --no-shielded-vtpm', False, False, None),
      ('-InstanceESecureBootDvtpm', '--shielded-secure-boot --no-shielded-vtpm',
       True, False, None),
      ('-InstanceDSecureBootEvtpm', '--no-shielded-secure-boot --shielded-vtpm',
       False, True, None),
      ('-InstanceDSecureBootEvtpmEIntegrity',
       ('--no-shielded-secure-boot --shielded-vtpm'
        ' --shielded-integrity-monitoring'), False, True, True))
  def testCreateSVMCkWithAllProperties(self, cmd_flag, enable_secure_boot,
                                       enable_vtpm,
                                       enable_integrity_monitoring):
    m = self.messages

    self.Run(
        'compute instances create instance-1 '
        '  --zone central2-a {}'.format(cmd_flag))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  minCpuPlatform=None,
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
                  shieldedInstanceConfig=m.ShieldedInstanceConfig(
                      enableSecureBoot=enable_secure_boot,
                      enableVtpm=enable_vtpm,
                      enableIntegrityMonitoring=enable_integrity_monitoring)),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateShieldedInstanceConfigBetaTest(
    InstancesCreateShieldedInstanceConfigGATest):
  """Test creation of VM instances with shielded VM config for Beta API."""

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA


class InstancesCreateShieldedInstanceConfigAlphaTest(
    InstancesCreateShieldedInstanceConfigGATest):
  """Test creation of VM instances with shielded VM config for alpha API."""

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA


class InstancesCreateDiskFromSnapshotTestGA(InstancesCreateTestsMixin,
                                            parameterized.TestCase):
  """Test creation of VM instances with create disk(s)."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    SetUp(self, self.api_version)


class InstancesCreateDiskFromSnapshotTestBeta(
    InstancesCreateDiskFromSnapshotTestGA):
  """Test creation of VM instances with create disk(s)."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstancesCreateDiskFromSnapshotTestAlpha(
    InstancesCreateDiskFromSnapshotTestBeta):
  """Test creation of VM instances with create disk(s)."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testCreateDiskWithAllProperties(self):
    m = self.messages

    self.Run(
        'compute instances create hamlet '
        '  --zone central2-a '
        '  --create-disk name=disk-1,size=10GB,mode=ro,type=SSD,'
        'source-snapshot=my-snapshot,device-name=data,auto-delete=yes')

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=False,
                        deviceName='data',
                        initializeParams=m.AttachedDiskInitializeParams(
                            diskName='disk-1',
                            diskSizeGb=10,
                            sourceSnapshot=(self.compute_uri +
                                            '/projects/my-project/global/'
                                            'snapshots/my-snapshot'),
                            diskType=(self.compute_uri +
                                      '/projects/my-project/zones/central2-a/'
                                      'diskTypes/SSD')),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='hamlet',
                networkInterfaces=[m.NetworkInterface(
                    accessConfigs=[m.AccessConfig(
                        name='external-nat',
                        type=self._one_to_one_nat)],
                    network=self._default_network)],
                serviceAccounts=[
                    m.ServiceAccount(
                        email='default',
                        scopes=_DEFAULT_SCOPES,),
                ],
                scheduling=m.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testCreateDiskWithSnapshotProperty(self):
    msg = self.messages
    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --create-disk source-snapshot=my-backup
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', msg.ComputeInstancesInsertRequest(
            instance=msg.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                    msg.AttachedDisk(
                        autoDelete=True,
                        boot=False,
                        initializeParams=msg.AttachedDiskInitializeParams(
                            sourceSnapshot=(self.compute_uri +
                                            '/projects/my-project/global/'
                                            'snapshots/my-backup'),),
                        mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                machineType=_DefaultMachineTypeOf(self.api),
                metadata=msg.Metadata(),
                name='hamlet',
                networkInterfaces=[msg.NetworkInterface(
                    accessConfigs=[msg.AccessConfig(
                        name='external-nat',
                        type=self._one_to_one_nat)],
                    network=_DefaultNetworkOf(self.api))],
                serviceAccounts=[
                    msg.ServiceAccount(
                        email='default', scopes=_DEFAULT_SCOPES),
                ],
                scheduling=msg.Scheduling(automaticRestart=True),),
            project='my-project',
            zone='central2-a',))],)

  def testCreateDiskSnapshotAndImagePropertyFails(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Must specify exactly one of \[image\], \[image-family\] or '
        r'\[source-snapshot\] for a \[--create-disk\]. '
        r'These fields are mutually exclusive.'):
      self.Run("""
          compute instances create vm
            --create-disk image=foo,source-snapshot=my-snapshot
          """)

  @parameterized.parameters([
      ('', 'my-backup'),
      (('https://www.googleapis.com/compute/'
        'alpha/projects/my-project/global/snapshots/'), 'my-backup')])
  def testCreateBootDiskWithSnapshotFlag(
      self,
      snapshot_path,
      snapshot_name):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    snapshot_arg = snapshot_path + snapshot_name
    self.Run("""
        compute instances create instance-1
          --source-snapshot {}
          --zone central2-a
        """.format(snapshot_arg))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceSnapshot=(
                              'https://www.googleapis.com/compute/{0}/projects/'
                              'my-project/global/snapshots/{1}'.format(
                                  self.api, snapshot_name)),
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=_DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testCreateBootDiskWithSnapshotAndImageFlagFails(self):
    with self.assertRaisesRegex(
        MockArgumentError,
        r'argument --image: At most one of --image \| --image-family \| '
        r'--source-snapshot may be specified.'):
      self.Run("""
          compute instances create vm
            --image=foo --source-snapshot=my-snapshot
          """)


class InstancesCreateFromMachineImage(InstancesCreateTestsMixin):

  def testAlpha(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    m = self.messages

    self.Run('compute instances create instance-1 '
             '--zone central2-a '
             '--source-machine-image machine-image-1')

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                name='instance-1',
                deletionProtection=False,
                sourceMachineImage=(
                    'https://www.googleapis.com/compute/alpha/projects/'
                    'my-project/global/machineImages/machine-image-1')),
            project='my-project',
            zone='central2-a'))])


class InstancesCreateWithDisplayDevice(InstancesCreateTestsMixin):

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testCreateWithDisplayDevice(self):
    m = self.messages
    self.Run('compute instances create instance-1 '
             '--zone central2-a '
             '--enable-display-device')

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert', m.ComputeInstancesInsertRequest(
            instance=m.Instance(
                canIpForward=False,
                deletionProtection=False,
                disks=[
                    m.AttachedDisk(
                        autoDelete=True,
                        boot=True,
                        initializeParams=m.AttachedDiskInitializeParams(
                            sourceImage=self._default_image,),
                        mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                        type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                ],
                displayDevice=m.DisplayDevice(enableDisplay=True),
                machineType=self._default_machine_type,
                metadata=m.Metadata(),
                name='instance-1',
                networkInterfaces=[m.NetworkInterface(
                    accessConfigs=[m.AccessConfig(
                        name='external-nat',
                        type=self._one_to_one_nat)],
                    network=self._default_network)],
                serviceAccounts=[
                    m.ServiceAccount(
                        email='default',
                        scopes=_DEFAULT_SCOPES
                    ),
                ],
                scheduling=m.Scheduling(
                    automaticRestart=True),
            ),
            project='my-project',
            zone='central2-a'))])


if __name__ == '__main__':
  test_case.main()
