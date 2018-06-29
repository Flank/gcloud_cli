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

"""Tests for the instance-templates create subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
import random
import textwrap

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.sole_tenancy import util as sole_tenancy_util
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


_DEFAULT_IMAGE = (
    '{compute_uri}/projects/debian-cloud/global/images/family/debian-9')
_DEFAULT_MACHINE_TYPE = 'n1-standard-1'
_DEFAULT_NETWORK = (
    '{compute_uri}/projects/my-project/'
    'global/networks/default')
_DEFAULT_SCOPES = sorted([
    'https://www.googleapis.com/auth/devstorage.read_only',
    'https://www.googleapis.com/auth/logging.write',
    'https://www.googleapis.com/auth/monitoring.write',
    'https://www.googleapis.com/auth/servicecontrol',
    'https://www.googleapis.com/auth/service.management.readonly',
    'https://www.googleapis.com/auth/pubsub',
    'https://www.googleapis.com/auth/trace.append',
])


_INSTANCE_TEMPLATES = {
    'v1': test_resources.INSTANCE_TEMPLATES_V1,
    'beta': test_resources.INSTANCE_TEMPLATES_BETA,
    'alpha': test_resources.INSTANCE_TEMPLATES_ALPHA,
}


def SetUp(test, api):
  test.SelectApi(api)

  test._instance_templates = _INSTANCE_TEMPLATES[api]

  test._default_image = _DEFAULT_IMAGE.format(compute_uri=test.compute_uri)
  test._default_network = _DEFAULT_NETWORK.format(compute_uri=test.compute_uri)
  test._one_to_one_nat = (test.messages.AccessConfig
                          .TypeValueValuesEnum.ONE_TO_ONE_NAT)

  test._default_access_config = test.messages.AccessConfig(
      name='external-nat', type=test._one_to_one_nat)

  random.seed(1)
  system_random_patcher = mock.patch(
      'random.SystemRandom', new=lambda: random)
  test.addCleanup(system_random_patcher.stop)
  system_random_patcher.start()

  test.make_requests.side_effect = iter([
      [
          test.messages.Image(
              name='debian-9-stretch-v20170619',
              selfLink=test._default_image),
      ],

      [],
  ])

  test.get_default_image_requests = [(
      test.compute.images,
      'GetFromFamily',
      test.messages.ComputeImagesGetFromFamilyRequest(
          family='debian-9',
          project='debian-cloud'))]


class InstanceTemplatesCreateTest(test_base.BaseTest):

  def SetUp(self):
    SetUp(self, 'v1')

  def testDefaultOptions(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testAttachmentOfExistingBootDisk(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Disk(name='disk-1'),
        ],
        [],
    ])

    # Ensures that the boot disk is placed at index 0 of the disks
    # list.
    self.Run("""
        compute instance-templates create template-1
          --disk name=disk-2
          --disk name=disk-1,boot=yes
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=False,
                    boot=True,
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    source=('disk-1'),
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                m.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    source=('disk-2'),
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testLocalSSDsAndBootDisk(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Disk(name='disk-1'),
        ],
        [],
    ])

    # Ensures that the boot disk is placed at index 0 of the disks
    # list.
    self.Run("""
        compute instance-templates create template-1
          --disk name=disk-2
          --disk name=disk-1,boot=yes
          --local-ssd ''
          --local-ssd interface=NVME
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=False,
                    boot=True,
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    source=('disk-1'),
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                m.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    source=('disk-2'),
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                m.AttachedDisk(
                    autoDelete=True,
                    initializeParams=(
                        m.AttachedDiskInitializeParams(
                            diskType='local-ssd')),
                    mode=(m.AttachedDisk
                          .ModeValueValuesEnum.READ_WRITE),
                    type=(m.AttachedDisk
                          .TypeValueValuesEnum.SCRATCH)),
                m.AttachedDisk(
                    autoDelete=True,
                    initializeParams=(
                        m.AttachedDiskInitializeParams(
                            diskType='local-ssd')),
                    interface=(m.AttachedDisk
                               .InterfaceValueValuesEnum.NVME),
                    mode=(m.AttachedDisk
                          .ModeValueValuesEnum.READ_WRITE),
                    type=(m.AttachedDisk
                          .TypeValueValuesEnum.SCRATCH)),
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithNonExistentImage(self):
    m = self.messages
    def MakeRequests(*_, **kwargs):
      yield None
      kwargs['errors'].append((404, 'Not Found'))
    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not fetch image resource:
         - Not Found
        """)):
      self.Run("""
          compute instance-templates create template-1
            --image non-existent-image --image-project non-existent-project
          """)

    self.CheckRequests(
        [(self.compute.images,
          'Get',
          m.ComputeImagesGetRequest(
              image='non-existent-image',
              project='non-existent-project'
          ))],
    )

  def testWithNonExistentImageNoImageProject(self):
    m = self.messages
    def MakeRequests(*_, **kwargs):
      if False:  # pylint: disable=using-constant-test
        yield
      kwargs['errors'].append((404, 'Not Found'))
    self.make_requests.side_effect = MakeRequests

    with self.assertRaisesRegex(
        utils.ImageNotFoundError,
        (r'The resource \[(.*)projects/my-project/global/images/non-existent-'
         r'image\] was not found. Is the image located in another project\? '
         r'Use the --image-project flag to specify the project where the image '
         r'is located.')):
      self.Run("""
          compute instance-templates create template-1
            --image non-existent-image
          """)

    self.CheckRequests(
        [(self.compute.images,
          'Get',
          m.ComputeImagesGetRequest(
              image='non-existent-image',
              project='my-project'
          ))],
    )

  def testPerformanceWarningWithStandardPd(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --boot-disk-size 199GB
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    diskSizeGb=199,
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )
    self.AssertErrContains(
        'WARNING: You have selected a disk size of under [200GB]. This may '
        'result in poor I/O performance. For more information, see: '
        'https://developers.google.com/compute/docs/disks#performance.')

  def testCanIpForward(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --can-ip-forward
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=True,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithDescription(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --description "Hakuna Matata"
        """)

    template = m.InstanceTemplate(
        name='template-1',
        description=('Hakuna Matata'),
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithSingleScope(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --scopes compute-rw
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=[
                        'https://www.googleapis.com/auth/compute',
                    ]),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testExplicitDefaultScopes(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --scopes compute-rw,default
        """)

    expected_scopes = sorted(_DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/compute'])
    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=expected_scopes),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithNoScopes(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --no-scopes
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],

            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[],
            scheduling=m.Scheduling(automaticRestart=True)
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithManyScopes(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --scopes compute-rw,https://www.googleapis.com/auth/devstorage.full_control
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=[
                        'https://www.googleapis.com/auth/compute',
                        ('https://www.googleapis.com/auth/devstorage'
                         '.full_control'),
                    ]),
            ],
            scheduling=m.Scheduling(automaticRestart=True)
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithManyScopesAndServiceAccount(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --scopes compute-rw,https://www.googleapis.com/auth/devstorage.full_control
          --service-account 1234@project.gserviceaccount.com
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
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
            scheduling=m.Scheduling(automaticRestart=True)
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithIllegalScopeValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[default=sql=https://www.googleapis.com/auth/devstorage.'
        r'full_control\] is an illegal value for \[--scopes\]. Values must be '
        r'of the form \[SCOPE\].'):
      self.Run("""
          compute instance-templates create template-1
            --scopes default=sql=https://www.googleapis.com/auth/devstorage.full_control,compute-rw
          """)

    self.CheckRequests()

  def testWithNoAddress(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --no-address
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithAddress(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --address 74.125.28.139
        """)

    access_config = m.AccessConfig(
        name='external-nat',
        type=self._one_to_one_nat,
        natIP='74.125.28.139')

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testAddressAndNoAddressMutualExclusion(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --address: At most one of --address | --no-address '
        'may be specified.'):
      self.Run("""
          compute instance-templates create template-1
            --address 74.125.28.139
            --no-address
          """)

    self.CheckRequests()

  def testWithImageInSameProject(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='my-image',
                selfLink=('{compute}/projects/'
                          'my-project/global/images/my-image'.format(
                              compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image my-image
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=(
                        '{compute}/projects/'
                        'my-project/global/images/my-image'.format(
                            compute=self.compute_uri)),
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        [(self.compute.images,
          'Get',
          m.ComputeImagesGetRequest(
              image='my-image',
              project='my-project'))],

        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithImageInDifferentProject(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='other-image',
                selfLink=('{compute}/projects/some-other-project/global/images'
                          '/other-image'.format(compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image other-image
          --image-project some-other-project
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=(
                        '{compute}/projects/some-other-project/global/images'
                        '/other-image'.format(compute=self.compute_uri)),
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        [(self.compute.images,
          'Get',
          m.ComputeImagesGetRequest(
              image='other-image',
              project='some-other-project'))],

        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithImageInDifferentProjectWithUri(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='other-image',
                selfLink=('{compute}/projects/some-other-project/global'
                          '/images/other-image'.format(
                              compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image other-image
          --image-project {compute}/projects/some-other-project
          """.format(compute=self.compute_uri))

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=(
                        '{compute}/projects/some-other-project/global/images'
                        '/other-image'.format(compute=self.compute_uri)),
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        [(self.compute.images,
          'Get',
          m.ComputeImagesGetRequest(
              image='other-image',
              project='some-other-project'))],

        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithNoImageAndBootDiskDeviceNameOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-device-name\] can only be used when creating a new '
        r'boot disk.'):
      self.Run("""
          compute instance-templates create template-1
            --disk boot=yes,name=my-disk
            --boot-disk-device-name x
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskSizeOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-size\] can only be used when creating a new boot '
        r'disk.'):
      self.Run("""
          compute instance-templates create template-1
            --disk boot=yes,name=my-disk
            --boot-disk-size 10GB
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskTypeOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-type\] can only be used when creating a new boot '
        r'disk.'):
      self.Run("""
          compute instance-templates create template-1
            --disk boot=yes,name=my-disk
            --boot-disk-type pd-ssd
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskAutoDeleteOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--no-boot-disk-auto-delete\] can only be used when creating a new '
        'boot disk.'):
      self.Run("""
          compute instance-templates create template-1
            --disk boot=yes,name=my-disk
            --no-boot-disk-auto-delete
          """)

    self.CheckRequests()

  def testIllegalAutoDeleteValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[auto-delete\] in \[--disk\] must be \[yes\] or \[no\], '
        r'not \[true\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk boot=yes,name=my-disk,auto-delete=true
          """)

    self.CheckRequests()

  def testWithMetadata(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --metadata x=y,z=1,a=b,c=d
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(
                items=[
                    m.Metadata.ItemsValueListEntry(key='a', value='b'),
                    m.Metadata.ItemsValueListEntry(key='c', value='d'),
                    m.Metadata.ItemsValueListEntry(key='x', value='y'),
                    m.Metadata.ItemsValueListEntry(key='z', value='1'),
                ]),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithMetadataFromFile(self):
    m = self.messages

    metadata_file1 = self.Touch(
        self.temp_path, 'file-1', contents='hello')
    metadata_file2 = self.Touch(
        self.temp_path, 'file-2', contents='hello\nand\ngoodbye')

    self.Run("""
        compute instance-templates create template-1
          --metadata-from-file x={},y={}
        """.format(metadata_file1, metadata_file2))

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(
                items=[
                    m.Metadata.ItemsValueListEntry(
                        key='x', value='hello'),
                    m.Metadata.ItemsValueListEntry(
                        key='y', value='hello\nand\ngoodbye'),
                ]),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithMetadataAndMetadataFromFile(self):
    m = self.messages

    metadata_file1 = self.Touch(
        self.temp_path, 'file-1', contents='hello')
    metadata_file2 = self.Touch(
        self.temp_path, 'file-2', contents='hello\nand\ngoodbye')

    self.Run("""
        compute instance-templates create template-1
          --metadata a=x,b=y,z=d
          --metadata-from-file x={},y={}
        """.format(metadata_file1, metadata_file2))

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
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
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithMetadataContainingDuplicateKeys(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Encountered duplicate metadata key \[x\].'):
      self.Run("""
          compute instance-templates create template-1
            --metadata x=y,z=1
            --metadata-from-file x=file-1
          """)

    self.CheckRequests()

  def testWithMetadataFromNonExistentFile(self):
    metadata_file = self.Touch(
        self.temp_path, 'file-1', contents='hello')
    with self.assertRaisesRegex(
        files.Error,
        r'Unable to read file \[garbage\]: .*No such file or directory'):
      self.Run("""
          compute instance-templates create template-1
            --metadata-from-file x={},y=garbage
          """.format(metadata_file))

    self.CheckRequests()

  def testWithNetwork(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --network some-other-network
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=(
                    '{compute}/projects/my-project/global/networks/'
                    'some-other-network'.format(compute=self.compute_uri)))],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithNoRestartOnFailure(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --no-restart-on-failure
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=False),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithMaintenancePolicy(self):
    self.templateTestWithMaintenancePolicy("""
        compute instance-templates create template-1
          --maintenance-policy TERMINATE
        """)

  def testWithMaintenancePolicyLowerCase(self):
    self.templateTestWithMaintenancePolicy("""
        compute instance-templates create template-1
          --maintenance-policy terminate
        """)

  def templateTestWithMaintenancePolicy(self, cmd):
    m = self.messages
    self.Run(cmd)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(
                automaticRestart=True,
                onHostMaintenance=(
                    m.Scheduling.OnHostMaintenanceValueValuesEnum
                    .TERMINATE)),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithTags(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --tags a,b,c,d
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
            tags=m.Tags(items=['a', 'b', 'c', 'd'])
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testDefaultOutput(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='debian-9-stretch-v20170619',
                selfLink=self._default_image),
        ],
        [self._instance_templates[0]]
    ])

    self.Run("""
        compute instance-templates create instance-template-1
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                MACHINE_TYPE  PREEMPTIBLE CREATION_TIMESTAMP
            instance-template-1 n1-standard-1             2013-09-06T17:54:10.636-07:00
            """), normalize_space=True)

  def testJsonOutput(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='debian-9-stretch-v20170619',
                selfLink=self._default_image),
        ],
        [self._instance_templates[0]]
    ])

    self.Run("""
        compute instance-templates create template-1
          --format json
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            [
              {{
                "creationTimestamp": "2013-09-06T17:54:10.636-07:00",
                "name": "instance-template-1",
                "properties": {{
                  "disks": [
                    {{
                      "autoDelete": true,
                      "boot": true,
                      "deviceName": "device-1",
                      "mode": "READ_WRITE",
                      "source": "disk-1",
                      "type": "PERSISTENT"
                    }}
                  ],
                  "machineType": "n1-standard-1",
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
                  }}
                }},
                "selfLink": "{compute}/projects/my-project/global/instanceTemplates/instance-template-1"
               }}
            ]
            """.format(compute=self.compute_uri)), normalize_space=True)

  def testTextOutput(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='debian-9-stretch-v20170619',
                selfLink=self._default_image),
        ],
        [self._instance_templates[0]]
    ])

    self.Run("""
        compute instance-templates create template-1
          --format text
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            ---
            creationTimestamp:                                      2013-09-06T17:54:10.636-07:00
            name:                                                   instance-template-1
            properties.disks[0].autoDelete:                         True
            properties.disks[0].boot:                               True
            properties.disks[0].deviceName:                         device-1
            properties.disks[0].mode:                               READ_WRITE
            properties.disks[0].source:                             disk-1
            properties.disks[0].type:                               PERSISTENT
            properties.machineType:                                 n1-standard-1
            properties.networkInterfaces[0].accessConfigs[0].natIP: 23.251.133.75
            properties.networkInterfaces[0].networkIP:              10.0.0.1
            properties.scheduling.automaticRestart:                 False
            properties.scheduling.onHostMaintenance:                TERMINATE
            properties.scheduling.preemptible:                      False
            selfLink:                                               {compute}/projects/my-project/global/instanceTemplates/instance-template-1
            """.format(compute=self.compute_uri)))

  def testYamlOutput(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='debian-9-stretch-v20170619',
                selfLink=self._default_image),
        ],
        [self._instance_templates[0]]
    ])

    self.Run("""
        compute instance-templates create template-1
          --format yaml
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            ---
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            name: instance-template-1
            properties:
              disks:
              - autoDelete: true
                boot: true
                deviceName: device-1
                mode: READ_WRITE
                source: disk-1
                type: PERSISTENT
              machineType: n1-standard-1
              networkInterfaces:
              - accessConfigs:
                - natIP: 23.251.133.75
                networkIP: 10.0.0.1
              scheduling:
                automaticRestart: false
                onHostMaintenance: TERMINATE
                preemptible: false
            selfLink: {compute}/projects/my-project/global/instanceTemplates/instance-template-1
            """.format(compute=self.compute_uri)))

  def testSimpleDiskOptionWithSingleDiskAndSingleInstance(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --disk name=disk-1
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
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
                    source='disk-1'),
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testComplexDiskOptionWithSingleDiskAndSingleInstance(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --disk name=disk-1,mode=rw,device-name=x,boot=no
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
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
                    source='disk-1'),
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        ),
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testComplexDiskOptionsWithManyDisksAndSingleInstance(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --disk name=disk-1,mode=rw,device-name=x,boot=no
          --disk name=disk-2,mode=ro,device-name=y,auto-delete=yes
          --disk boot=no,device-name=z,name=disk-3,mode=rw
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
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
                    source='disk-1'),
                m.AttachedDisk(
                    autoDelete=True,
                    boot=False,
                    deviceName='y',
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                    source='disk-2'),
                m.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='z',
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                    source='disk-3'),
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testDiskOptionWithNoName(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[name\] is missing in \[--disk\]. \[--disk\] value must be of the '
        r'form \[name=NAME \[mode={ro,rw}\] \[boot={yes,no}\] '
        r'\[device-name=DEVICE_NAME\] \[auto-delete={yes,no}\]\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk mode=rw,device-name=x,boot=no
          """)

    self.CheckRequests()

  def testDiskOptionWithBadMode(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[mode\] in \[--disk\] must be \[rw\] or \[ro\], not '
        r'\[READ_WRITE\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk name=disk-1,mode=READ_WRITE,device-name=x
          """)

    self.CheckRequests()

  def testDiskOptionWithBadBoot(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[boot\] in \[--disk\] must be \[yes\] or \[no\], not '
        r'\[No\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk name=disk-1,device-name=x,boot=No
          """)

    self.CheckRequests()

  def testDiskOptionWithBootDiskAndImageOption(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Each instance can have exactly one boot disk. One boot disk was '
        r'specified through \[--disk\] and another through \[--image\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk name=disk-1,mode=rw,boot=yes
            --image image-1
          """)

    self.CheckRequests()

  def testDiskOptionWithManyBootDisks(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Each instance can have exactly one boot disk. At least two boot disks '
        r'were specified through \[--disk\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk name=disk-1,mode=rw,boot=yes
            --disk name=disk-2,mode=ro,boot=no
            --disk name=disk-3,mode=rw,boot=yes
          """)

    self.CheckRequests()

  def testComplexDiskOptionsWithManyDisks(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='image-1',
                selfLink=('{compute}/projects/my-project/global/images/'
                          'image-1'.format(compute=self.compute_uri))),
        ],

        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --boot-disk-device-name boot-disk
          --boot-disk-size 100GB
          --boot-disk-type pd-ssd
          --no-boot-disk-auto-delete
          --disk name=disk-1,mode=ro,device-name=x,boot=no
          --disk name=disk-2,mode=ro,device-name=y
          --disk boot=no,device-name=z,name=disk-3,mode=ro
          --image image-1
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=False,
                    boot=True,
                    deviceName='boot-disk',
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=(
                            '{compute}/projects/my-project/global/images'
                            '/image-1'.format(compute=self.compute_uri)),
                        diskSizeGb=100,
                        diskType='pd-ssd'),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                m.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='x',
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                    source='disk-1'),
                m.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='y',
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                    source='disk-2'),
                m.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='z',
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                    source='disk-3'),
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        [(self.compute.images,
          'Get',
          m.ComputeImagesGetRequest(
              image='image-1',
              project='my-project'))],

        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],)

  def testFlagsWithUri(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='my-image',
                selfLink=('{compute}/projects/my-project/global/images/'
                          'my-image'.format(compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --boot-disk-type {compute}/projects/my-project/zones/central1-a/diskTypes/pd-ssd
          --disk name={compute}/projects/my-project/zones/central1-a/disks/disk-1
          --machine-type {compute}/projects/my-project/zones/central1-a/machineTypes/n2-standard-1
          --network {compute}/projects/my-project/global/networks/some-other-network
          --image {compute}/projects/my-project/global/images/my-image
        """.format(compute=self.compute_uri))

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=(
                            '{compute}/'
                            'projects/my-project/global/images/'
                            'my-image'.format(compute=self.compute_uri)),
                        diskType=(
                            '{compute}/'
                            'projects/my-project/zones/central1-a/diskTypes/'
                            'pd-ssd'.format(compute=self.compute_uri)),
                    ),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                m.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                    source=(
                        '{compute}/'
                        'projects/my-project/zones/central1-a/disks/'
                        'disk-1'.format(compute=self.compute_uri))),
            ],
            machineType=('{compute}/projects/'
                         'my-project/zones/central1-a/machineTypes/'
                         'n2-standard-1'.format(compute=self.compute_uri)),
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=('{compute}/projects/my-project/global/networks/'
                         'some-other-network'.format(
                             compute=self.compute_uri)))],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),

        )
    )

    self.CheckRequests(
        [(self.compute.images,
          'Get',
          m.ComputeImagesGetRequest(
              image='my-image',
              project='my-project'))],

        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testPreemptible(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1 --preemptible
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(
                automaticRestart=False,
                preemptible=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testAcceleratorWithDefaultCount(self):
    self.Run("""
          compute instance-templates create template-1
            --accelerator type=nvidia-tesla-k80
          """)
    m = self.messages
    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            guestAccelerators=[
                m.AcceleratorConfig(
                    acceleratorType='nvidia-tesla-k80',
                    acceleratorCount=1)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testAcceleratorWithSpecifiedCount(self):
    self.Run("""
          compute instance-templates create template-1
            --accelerator type=nvidia-tesla-k80,count=4
          """)
    m = self.messages
    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            guestAccelerators=[
                m.AcceleratorConfig(
                    acceleratorType='nvidia-tesla-k80',
                    acceleratorCount=4)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testAcceleratorWithInvalidDictArg(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'Bad syntax for dict arg: \[invalid_value]'):
      self.Run("""
            compute instance-templates create template-1
              --accelerator invalid_value
            """)

  def testAcceleratorWithNoAcceleratorType(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--accelerator]: '
        r'accelerator type must be specified\.'):
      self.Run("""
            compute instance-templates create template-1
              --accelerator count=4
            """)

  def testMultipleNetworkInterfaceCards(self):
    msg = self.messages

    self.Run("""
        compute instance-templates create hamlet
          --network-interface network=default,address=
          --network-interface network=some-net,address=8.8.8.8
          --network-interface subnet=some-subnet
          --region central1
        """)

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          msg.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=msg.InstanceTemplate(
                  name='hamlet',
                  properties=msg.InstanceProperties(
                      canIpForward=False,
                      disks=[
                          msg.AttachedDisk(
                              autoDelete=True,
                              boot=True,
                              initializeParams=msg.AttachedDiskInitializeParams(
                                  sourceImage=(
                                      self.compute_uri +
                                      '/projects/debian-cloud/global/images/'
                                      'family/debian-9'),),
                              mode=msg.AttachedDisk.ModeValueValuesEnum.
                              READ_WRITE,
                              type=msg.AttachedDisk.TypeValueValuesEnum.
                              PERSISTENT,)
                      ],
                      machineType=_DEFAULT_MACHINE_TYPE,
                      metadata=msg.Metadata(),
                      networkInterfaces=[
                          msg.NetworkInterface(
                              accessConfigs=[
                                  msg.AccessConfig(
                                      name='external-nat',
                                      type=self._one_to_one_nat)
                              ],
                              network=self._default_network),
                          msg.NetworkInterface(
                              accessConfigs=[
                                  msg.AccessConfig(
                                      name='external-nat',
                                      natIP='8.8.8.8',
                                      type=self._one_to_one_nat)
                              ],
                              network=(self.compute_uri +
                                       '/projects/my-project/global/networks/'
                                       'some-net')),
                          msg.NetworkInterface(subnetwork=(
                              self.compute_uri +
                              '/projects/my-project/regions/central1/'
                              'subnetworks/some-subnet')),
                      ],
                      scheduling=msg.Scheduling(automaticRestart=True),
                      serviceAccounts=[
                          msg.ServiceAccount(
                              email='default', scopes=_DEFAULT_SCOPES),
                      ],),),
              project='my-project',))],)

  def testNetworkInterfaceWithSubnetAndNetwork(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --network-interface subnet=my-subnetwork,network=my-network
          --region my-region
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[],
                    network=('{compute}/projects/my-project/global/'
                             'networks/my-network'.format(
                                 compute=self.compute_uri)),
                    subnetwork=(
                        '{compute}/projects/my-project/regions/my-region/'
                        'subnetworks/my-subnetwork'.format(
                            compute=self.compute_uri)))
            ],
            serviceAccounts=[
                m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',))],)

  def testMultiNicFlagAndOneNicFlag(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'^arguments not allowed simultaneously: --network-interface, all of '
        r'the following: --address, --network$'):
      self.Run("""
          compute instance-templates create instance-1
            --network-interface ''
            --address 8.8.8.8
            --network net
          """)

  def testAliasIpRanges(self):
    msg = self.messages

    self.Run("""
        compute instance-templates create hamlet
          --network-interface network=default,address=,aliases=range1:/24;/24
          --network-interface network=some-net,address=,aliases=/24
          --network-interface subnet=some-subnet
          --region central1
        """)

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          msg.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=msg.InstanceTemplate(
                  name='hamlet',
                  properties=msg.InstanceProperties(
                      canIpForward=False,
                      disks=[
                          msg.AttachedDisk(
                              autoDelete=True,
                              boot=True,
                              initializeParams=msg.AttachedDiskInitializeParams(
                                  sourceImage=(
                                      self.compute_uri +
                                      '/projects/debian-cloud/global/images/'
                                      'family/debian-9'),),
                              mode=msg.AttachedDisk.ModeValueValuesEnum.
                              READ_WRITE,
                              type=msg.AttachedDisk.TypeValueValuesEnum.
                              PERSISTENT,)
                      ],
                      machineType=_DEFAULT_MACHINE_TYPE,
                      metadata=msg.Metadata(),
                      networkInterfaces=[
                          msg.NetworkInterface(
                              accessConfigs=[self._default_access_config],
                              network=self._default_network,
                              aliasIpRanges=[
                                  msg.AliasIpRange(
                                      subnetworkRangeName='range1',
                                      ipCidrRange='/24'),
                                  msg.AliasIpRange(ipCidrRange='/24')
                              ]),
                          msg.NetworkInterface(
                              accessConfigs=[self._default_access_config],
                              network=(self.compute_uri +
                                       '/projects/my-project/global/networks/'
                                       'some-net'),
                              aliasIpRanges=[
                                  msg.AliasIpRange(ipCidrRange='/24')
                              ]),
                          msg.NetworkInterface(subnetwork=(
                              self.compute_uri +
                              '/projects/my-project/regions/central1/'
                              'subnetworks/some-subnet'))
                      ],
                      scheduling=msg.Scheduling(automaticRestart=True),
                      serviceAccounts=[
                          msg.ServiceAccount(
                              email='default', scopes=_DEFAULT_SCOPES),
                      ],),),
              project='my-project',))],)

  def testInvalidAliasIpRangeFormat(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'An alias IP range must contain range name and IP '
        r'CIDR net mask'):
      self.Run("""
          compute instance-templates create instance-1
            --network-interface network=default,aliases=range1:abc:def;
          """)

  def testWithMinCpuPlatform(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --min-cpu-platform cpu-platform
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            minCpuPlatform='cpu-platform',
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[self._default_access_config],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project'))])

    self.AssertOutputEquals('')
    self.AssertErrEquals('')


class InstanceTemplatesCreateTestAlpha(InstanceTemplatesCreateTest):

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testRegionPromptAttemptedWithSubnet(self):

    # This is very dirty, but at least verifies an attempt to prompt.
    with self.assertRaisesRegex(
        flags.UnderSpecifiedResourceError,
        r'Underspecified resource \[my-subnetwork\]. Specify the \[--region\] '
        r'flag.'):
      self.Run("""
          compute instance-templates create template-1
            --subnet my-subnetwork
          """)

  def testWithoutCustomMemorySpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-cpu: --custom-memory must be specified.'):

      self.Run("""
          compute instance-templates create instance-template-1
               --custom-cpu 4
          """)

  def testWithoutCustomCpuSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-memory: --custom-cpu must be specified.'):

      self.Run("""
          compute instance-templates create instance-template-1
               --custom-memory 4000
          """)

  def testWithMachineTypeAndCustomCpuSpecified(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Cannot set both \[--machine-type\] and \[--custom-cpu\]'):

      self.Run("""
          compute instance-templates create instance-template-1
               --custom-cpu 4
               --custom-memory 4000
               --machine-type n1-standard-1
          """)

  def testWithCustomMachineType(self):
    m = self.messages

    self.Run("""
        compute instance-templates create template-custom-mt
          --custom-cpu 4
          --custom-memory 4096MiB
        """)

    template = m.InstanceTemplate(
        name='template-custom-mt',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType='custom-4-4096',
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithExtendedCustomMachineType(self):
    m = self.messages

    self.Run("""
        compute instance-templates create template-custom-mt
          --custom-cpu 4
          --custom-memory 4096MiB
          --custom-extensions
        """)

    template = m.InstanceTemplate(
        name='template-custom-mt',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType='custom-4-4096-ext',
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testSubnetAndNetwork(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --subnet my-subnetwork
          --network my-network
          --region my-region
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=(
                    '{compute}/projects/my-project/global/'
                    'networks/my-network'.format(
                        compute=self.compute_uri)),
                subnetwork=(
                    '{compute}/projects/my-project/regions/my-region/'
                    'subnetworks/my-subnetwork'.format(
                        compute=self.compute_uri)))],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithSubnetwork(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --subnet my-subnetwork
          --region my-region
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                subnetwork=(
                    '{compute}/projects/my-project/regions/my-region/'
                    'subnetworks/my-subnetwork'.format(
                        compute=self.compute_uri)))],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithImageFamilyInSameProject(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='family/my-family',
                selfLink=('{compute}/projects/'
                          'my-project/global/images/family/my-family'.format(
                              compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image-family my-family
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=(
                        '{compute}/projects/'
                        'my-project/global/images/family/my-family'.format(
                            compute=self.compute_uri)),
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        [(self.compute.images,
          'GetFromFamily',
          m.ComputeImagesGetFromFamilyRequest(
              family='my-family',
              project='my-project'))],

        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithImageFamilyInDifferentProject(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='other-image',
                selfLink=('{compute}/projects/some-other-project/global/images'
                          '/family/other-family'
                          .format(compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image-family other-family
          --image-project some-other-project
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=(
                        '{compute}/projects/some-other-project/global/images'
                        '/family/other-family'
                        .format(compute=self.compute_uri)),
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        [(self.compute.images,
          'GetFromFamily',
          self.messages.ComputeImagesGetFromFamilyRequest(
              family='other-family',
              project='some-other-project'))],

        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithImageFamilyInDifferentProjectWithUri(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='family/other-family',
                selfLink=('{compute}/projects/some-other-project/global'
                          '/images/family/other-family'.format(
                              compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image-family other-family
          --image-project {compute}/projects/some-other-project
          """.format(compute=self.compute_uri))

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=(
                        '{compute}/projects/some-other-project/global/images'
                        '/family/other-family'
                        .format(compute=self.compute_uri)),
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        [(self.compute.images,
          'GetFromFamily',
          m.ComputeImagesGetFromFamilyRequest(
              family='other-family',
              project='some-other-project'))],

        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithCreateDisks(self):
    m = self.messages

    self.Run(
        'compute instance-templates create template-create-disk '
        '  --create-disk name=disk-1,size=10GB,mode=ro,type=SSD,image=debian-8,'
        'image-project=debian-cloud')

    template = m.InstanceTemplate(
        name='template-create-disk',
        properties=m.InstanceProperties(
            canIpForward=False,
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
                    initializeParams=m.AttachedDiskInitializeParams(
                        diskName='disk-1',
                        diskSizeGb=10,
                        sourceImage=(self.compute_uri +
                                     '/projects/debian-cloud/global/images'
                                     '/debian-8'),
                        diskType='SSD'),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithMultipleCreateDisks(self):
    m = self.messages

    self.Run('compute instance-templates create template-create-disk '
             '  --create-disk type=SSD'
             '  --create-disk image=debian-8,image-project=debian-cloud')

    template = m.InstanceTemplate(
        name='template-create-disk',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                m.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    initializeParams=m.AttachedDiskInitializeParams(
                        diskType='SSD'),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                m.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=(self.compute_uri +
                                     '/projects/debian-cloud/global/images'
                                     '/debian-8')),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[self._default_access_config],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        ))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testMultipleNetworkInterfaceCards(self):
    msg = self.messages

    self.Run("""
        compute instance-templates create hamlet
          --network-interface network=default,address=1.2.3.4
          --network-interface network=default,address=,network-tier=premium
          --network-interface network=some-net,address=8.8.8.8,network-tier=SELECT
          --network-interface subnet=some-subnet
          --region central1
        """)

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          msg.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=msg.InstanceTemplate(
                  name='hamlet',
                  properties=msg.InstanceProperties(
                      canIpForward=False,
                      disks=[
                          msg.AttachedDisk(
                              autoDelete=True,
                              boot=True,
                              initializeParams=msg.AttachedDiskInitializeParams(
                                  sourceImage=(
                                      self.compute_uri +
                                      '/projects/debian-cloud/global/images/'
                                      'family/debian-9'),),
                              mode=msg.AttachedDisk.ModeValueValuesEnum.
                              READ_WRITE,
                              type=msg.AttachedDisk.TypeValueValuesEnum.
                              PERSISTENT,)
                      ],
                      machineType=_DEFAULT_MACHINE_TYPE,
                      metadata=msg.Metadata(),
                      networkInterfaces=[
                          msg.NetworkInterface(
                              accessConfigs=[
                                  msg.AccessConfig(
                                      name='external-nat',
                                      natIP='1.2.3.4',
                                      type=self._one_to_one_nat)
                              ],
                              network=self._default_network),
                          msg.NetworkInterface(
                              accessConfigs=[
                                  msg.AccessConfig(
                                      name='external-nat',
                                      networkTier=(
                                          self.messages.AccessConfig.
                                          NetworkTierValueValuesEnum.PREMIUM),
                                      type=self._one_to_one_nat)
                              ],
                              network=self._default_network),
                          msg.NetworkInterface(
                              accessConfigs=[
                                  msg.AccessConfig(
                                      name='external-nat',
                                      networkTier=(
                                          self.messages.AccessConfig.
                                          NetworkTierValueValuesEnum.SELECT),
                                      natIP='8.8.8.8',
                                      type=self._one_to_one_nat)
                              ],
                              network=(
                                  'https://www.googleapis.com/compute/alpha/'
                                  'projects/my-project/global/networks/'
                                  'some-net')),
                          msg.NetworkInterface(subnetwork=(
                              'https://www.googleapis.com/compute/alpha/'
                              'projects/my-project/regions/central1/'
                              'subnetworks/some-subnet')),
                      ],
                      scheduling=msg.Scheduling(automaticRestart=True),
                      serviceAccounts=[
                          msg.ServiceAccount(
                              email='default', scopes=_DEFAULT_SCOPES),
                      ],),),
              project='my-project',))],)

  def testNetworkInterfaceWithSubnetAndNetwork(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --network-interface subnet=my-subnetwork,network=my-network
          --region my-region
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[],
                network=(
                    '{compute}/projects/my-project/global/'
                    'networks/my-network'.format(
                        compute=self.compute_uri)),
                subnetwork=(
                    '{compute}/projects/my-project/regions/my-region/'
                    'subnetworks/my-subnetwork'.format(
                        compute=self.compute_uri)))],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testMultiNicFlagAndOneNicFlag(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'^arguments not allowed simultaneously: --network-interface, all of '
        r'the following: --address, --network$'):
      self.Run("""
          compute instance-templates create instance-1
            --network-interface ''
            --address 8.8.8.8
            --network net
          """)

  def testWithManyScopesAndServiceAccount(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --scopes compute-rw,https://www.googleapis.com/auth/devstorage.full_control,bigquery,https://www.googleapis.com/auth/userinfo.email,sql,https://www.googleapis.com/auth/taskqueue
          --service-account 1234@project.gserviceaccount.com
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='1234@project.gserviceaccount.com',
                    scopes=[
                        'https://www.googleapis.com/auth/bigquery',
                        'https://www.googleapis.com/auth/compute',
                        ('https://www.googleapis.com/auth/devstorage'
                         '.full_control'),
                        'https://www.googleapis.com/auth/sqlservice',
                        'https://www.googleapis.com/auth/taskqueue',
                        'https://www.googleapis.com/auth/userinfo.email',
                    ]),
            ],
            scheduling=m.Scheduling(automaticRestart=True)
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testLocalSSDRequestWithSize(self):
    self.Run("""
        compute instance-templates create template-1
          --local-ssd ''
          --local-ssd interface=NVME,size=750
        """)

    m = self.messages
    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,
                    ),
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                m.AttachedDisk(
                    autoDelete=True,
                    initializeParams=(
                        m.AttachedDiskInitializeParams(
                            diskType='local-ssd')),
                    mode=(m.AttachedDisk
                          .ModeValueValuesEnum.READ_WRITE),
                    type=(m.AttachedDisk
                          .TypeValueValuesEnum.SCRATCH)),
                m.AttachedDisk(
                    autoDelete=True,
                    diskSizeGb=750,
                    initializeParams=(
                        m.AttachedDiskInitializeParams(
                            diskType='local-ssd')),
                    interface=(m.AttachedDisk
                               .InterfaceValueValuesEnum.NVME),
                    mode=(m.AttachedDisk
                          .ModeValueValuesEnum.READ_WRITE),
                    type=(m.AttachedDisk
                          .TypeValueValuesEnum.SCRATCH)),
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testLocalSSDRequestWithBadSize(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Unexpected local SSD size: \[536870912000\]. '
        r'Legal values are positive multiples of 375GB.'):
      self.Run("""
          compute instance-templates create template-1
            --local-ssd size=500
          """)

  def testWithMinCpuPlatform(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --min-cpu-platform cpu-platform
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            minCpuPlatform='cpu-platform',
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[self._default_access_config],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',))],)

  def testWithPremiumNetworkTier(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --network-tier PREMIUM
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[
                        m.AccessConfig(
                            name='external-nat',
                            networkTier=(self.messages.AccessConfig.
                                         NetworkTierValueValuesEnum.PREMIUM),
                            type=self._one_to_one_nat)
                    ],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithSelectNetworkTier(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --network-tier select
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[m.AccessConfig(
                    name='external-nat',
                    networkTier=(self.messages.AccessConfig
                                 .NetworkTierValueValuesEnum.SELECT),
                    type=self._one_to_one_nat)],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithStandardNetworkTier(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --network-tier standard
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[m.NetworkInterface(
                accessConfigs=[m.AccessConfig(
                    name='external-nat',
                    networkTier=(self.messages.AccessConfig
                                 .NetworkTierValueValuesEnum.STANDARD),
                    type=self._one_to_one_nat)],
                network=self._default_network)],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        )
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[RANDOM-NETWORK-TIER\]'
    ):
      self.Run("""
          compute instance-templates create template-1
          --network-tier random-network-tier
          """)

  def testWithOnHostMaintenance(self):
    self.templateTestWithMaintenancePolicy("""
        compute instance-templates create template-1
          --on-host-maintenance TERMINATE
        """)

  def testWithOnHostMaintenanceLowerCase(self):
    self.templateTestWithMaintenancePolicy("""
        compute instance-templates create template-1
          --on-host-maintenance terminate
        """)

  def testMaintenancePolicyDeprecation(self):
    self.templateTestWithMaintenancePolicy("""
        compute instance-templates create template-1
          --maintenance-policy TERMINATE
        """)
    self.AssertErrContains(
        'WARNING: The --maintenance-policy flag is now deprecated. '
        'Please use `--on-host-maintenance` instead')


class InstanceTemplatesCreateTestBeta(InstanceTemplatesCreateTest,
                                      parameterized.TestCase):

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testMultipleNetworkInterfaceCards(self):
    msg = self.messages

    self.Run("""
        compute instance-templates create hamlet
          --network-interface network=default,address=
          --network-interface network=some-net,address=8.8.8.8
          --network-interface subnet=some-subnet
          --region central1
        """)

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          msg.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=msg.InstanceTemplate(
                  name='hamlet',
                  properties=msg.InstanceProperties(
                      canIpForward=False,
                      disks=[
                          msg.AttachedDisk(
                              autoDelete=True,
                              boot=True,
                              initializeParams=msg.AttachedDiskInitializeParams(
                                  sourceImage=(
                                      self.compute_uri +
                                      '/projects/debian-cloud/global/images/'
                                      'family/debian-9'),),
                              mode=msg.AttachedDisk.ModeValueValuesEnum.
                              READ_WRITE,
                              type=msg.AttachedDisk.TypeValueValuesEnum.
                              PERSISTENT,)
                      ],
                      machineType=_DEFAULT_MACHINE_TYPE,
                      metadata=msg.Metadata(),
                      networkInterfaces=[
                          msg.NetworkInterface(
                              accessConfigs=[self._default_access_config],
                              network=self._default_network),
                          msg.NetworkInterface(
                              accessConfigs=[
                                  msg.AccessConfig(
                                      name='external-nat',
                                      natIP='8.8.8.8',
                                      type=self._one_to_one_nat)
                              ],
                              network=(self.compute_uri +
                                       '/projects/my-project/global/networks/'
                                       'some-net')),
                          msg.NetworkInterface(subnetwork=(
                              self.compute_uri +
                              '/projects/my-project/regions/central1/'
                              'subnetworks/some-subnet')),
                      ],
                      scheduling=msg.Scheduling(automaticRestart=True),
                      serviceAccounts=[
                          msg.ServiceAccount(
                              email='default', scopes=_DEFAULT_SCOPES),
                      ],),),
              project='my-project',))],)

  def testNetworkInterfaceWithSubnetAndNetwork(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --network-interface subnet=my-subnetwork,network=my-network
          --region my-region
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[],
                    network=('{compute}/projects/my-project/global/'
                             'networks/my-network'.format(
                                 compute=self.compute_uri)),
                    subnetwork=(
                        '{compute}/projects/my-project/regions/my-region/'
                        'subnetworks/my-subnetwork'.format(
                            compute=self.compute_uri)))
            ],
            serviceAccounts=[
                m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',))],)

  def testMultiNicFlagAndOneNicFlag(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'^arguments not allowed simultaneously: --network-interface, all of '
        r'the following: --address, --network$'):
      self.Run("""
          compute instance-templates create instance-1
            --network-interface ''
            --address 8.8.8.8
            --network net
          """)

  def testWithMinCpuPlatform(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --min-cpu-platform cpu-platform
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            minCpuPlatform='cpu-platform',
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[self._default_access_config],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',))],)

  @parameterized.named_parameters(
      ('Alpha', 'alpha', calliope_base.ReleaseTrack.ALPHA),
      ('Beta', 'beta', calliope_base.ReleaseTrack.BETA),
  )
  def testCreateWithSourceInstance(self, api_version, track):
    SetUp(self, api_version)
    self.track = track
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --source-instance tkul-konnn-test --source-instance-zone asia-east1-a
        """)

    template = m.InstanceTemplate(
        name='template-1',
        sourceInstance=(
            self.compute_uri +
            '/projects/my-project/zones/asia-east1-a/'
            'instances/tkul-konnn-test'),
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',))],)

  @parameterized.named_parameters(
      ('Alpha', 'alpha', calliope_base.ReleaseTrack.ALPHA),
      ('Beta', 'beta', calliope_base.ReleaseTrack.BETA),
  )
  def testCreateWithSourceInstanceAndConfigureDisk(self, api_version, track):
    SetUp(self, api_version)
    self.track = track
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --source-instance tkul-konnn-test --source-instance-zone asia-east1-a
          --configure-disk auto-delete=true,device-name=foo,instantiate-from=source-image
        """)

    disk_config = m.DiskInstantiationConfig(
        autoDelete=True,
        deviceName='foo',
        instantiateFrom=(
            m.DiskInstantiationConfig.InstantiateFromValueValuesEnum)(
                'SOURCE_IMAGE'),
    )
    template = m.InstanceTemplate(
        name='template-1',
        sourceInstance=(
            self.compute_uri +
            '/projects/my-project/zones/asia-east1-a/'
            'instances/tkul-konnn-test'),
        sourceInstanceParams=m.SourceInstanceParams(
            diskConfigs=[
                disk_config,
            ],
        ),
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',))],)

  @parameterized.named_parameters(
      ('Alpha', 'alpha', calliope_base.ReleaseTrack.ALPHA),
      ('Beta', 'beta', calliope_base.ReleaseTrack.BETA),
  )
  def testCreateWithSourceInstanceAndConfigureBlankDisk(
      self, api_version, track):
    SetUp(self, api_version)
    self.track = track
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --source-instance tkul-konnn-test --source-instance-zone asia-east1-a
          --configure-disk auto-delete=true,device-name=foo,instantiate-from=blank
        """)

    disk_config = m.DiskInstantiationConfig(
        autoDelete=True,
        deviceName='foo',
        instantiateFrom=(
            m.DiskInstantiationConfig.InstantiateFromValueValuesEnum)(
                'BLANK'),
    )
    template = m.InstanceTemplate(
        name='template-1',
        sourceInstance=(
            self.compute_uri +
            '/projects/my-project/zones/asia-east1-a/'
            'instances/tkul-konnn-test'),
        sourceInstanceParams=m.SourceInstanceParams(
            diskConfigs=[
                disk_config,
            ],
        ),
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',))],)

  @parameterized.named_parameters(
      ('Alpha', 'alpha', calliope_base.ReleaseTrack.ALPHA),
      ('Beta', 'beta', calliope_base.ReleaseTrack.BETA),
  )
  def testCreateWithSourceInstanceAndConfigureDiskNoAutoDelete(
      self, api_version, track):
    SetUp(self, api_version)
    self.track = track
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --source-instance tkul-konnn-test --source-instance-zone asia-east1-a
          --configure-disk auto-delete=false,device-name=foo,instantiate-from=source-image
        """)

    disk_config = m.DiskInstantiationConfig(
        autoDelete=False,
        deviceName='foo',
        instantiateFrom=(
            m.DiskInstantiationConfig.InstantiateFromValueValuesEnum)(
                'SOURCE_IMAGE'),
    )
    template = m.InstanceTemplate(
        name='template-1',
        sourceInstance=(
            self.compute_uri +
            '/projects/my-project/zones/asia-east1-a/'
            'instances/tkul-konnn-test'),
        sourceInstanceParams=m.SourceInstanceParams(
            diskConfigs=[
                disk_config,
            ],
        ),
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',))],)

  @parameterized.named_parameters(
      ('Alpha', 'alpha', calliope_base.ReleaseTrack.ALPHA),
      ('Beta', 'beta', calliope_base.ReleaseTrack.BETA),
  )
  def testCreateWithSourceInstanceAndConfigureDiskCustomImage(
      self, api_version, track):
    SetUp(self, api_version)
    self.track = track
    m = self.messages
    self.Run('compute instance-templates create template-1 '
             '--source-instance tkul-konnn-test '
             '--source-instance-zone asia-east1-a '
             '--configure-disk auto-delete=true,device-name=foo,'
             'instantiate-from=custom-image,'
             'custom-image=projects/image-project/global/images/my-image')

    disk_config = m.DiskInstantiationConfig(
        autoDelete=True,
        deviceName='foo',
        instantiateFrom=(
            m.DiskInstantiationConfig.InstantiateFromValueValuesEnum)(
                'CUSTOM_IMAGE'),
        customImage='projects/image-project/global/images/my-image'
    )
    template = m.InstanceTemplate(
        name='template-1',
        sourceInstance=(
            self.compute_uri +
            '/projects/my-project/zones/asia-east1-a/'
            'instances/tkul-konnn-test'),
        sourceInstanceParams=m.SourceInstanceParams(
            diskConfigs=[
                disk_config,
            ],
        ),
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',))],)

  @parameterized.named_parameters(
      ('Alpha', 'alpha', calliope_base.ReleaseTrack.ALPHA),
      ('Beta', 'beta', calliope_base.ReleaseTrack.BETA),
  )
  def testCreateWithConfigureDiskBadCustomImageArg(
      self, api_version, track):
    SetUp(self, api_version)
    self.track = track
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Value for `instaniate-from` must be \'custom-image\' if the key '
        '`custom-image` is specified.'):
      self.Run('compute instance-templates create template-1 '
               '--source-instance tkul-konnn-test '
               '--source-instance-zone asia-east1-a '
               '--configure-disk auto-delete=true,device-name=foo,'
               'instantiate-from=source-image,'
               'custom-image=projects/image-project/global/images/my-image')

  def testWithPremiumNetworkTier(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --network-tier PREMIUM
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[
                        m.AccessConfig(
                            name='external-nat',
                            networkTier=(self.messages.AccessConfig.
                                         NetworkTierValueValuesEnum.PREMIUM),
                            type=self._one_to_one_nat)
                    ],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        ))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithStandardNetworkTier(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --network-tier standard
        """)

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[
                        m.AccessConfig(
                            name='external-nat',
                            networkTier=(self.messages.AccessConfig.
                                         NetworkTierValueValuesEnum.STANDARD),
                            type=self._one_to_one_nat)
                    ],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(email='default', scopes=_DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        ))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[RANDOM-NETWORK-TIER\]'):
      self.Run("""
          compute instance-templates create template-1
          --network-tier random-network-tier
          """)


@parameterized.parameters(
    ('alpha', calliope_base.ReleaseTrack.ALPHA),
    ('beta', calliope_base.ReleaseTrack.BETA),
    ('v1', calliope_base.ReleaseTrack.GA))
class ScopesDeprecationTests(test_base.BaseTest, parameterized.TestCase):
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
      self.Run('compute instance-templates create asdf '
               '--scopes=acc1=scope1,acc1=scope2')

  def testScopesNewFormatNoDeprecationNotice(self, api, release_track):
    SetUp(self, api)
    self.track = release_track

    self.Run('compute instance-templates create asdf '
             '--scopes=scope1,scope2 --service-account acc1@example.com ')
    self.AssertErrEquals('')

  def testNoServiceAccount(self, api, release_track):
    SetUp(self, api)
    self.track = release_track

    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instance-templates create asdf '
               '--no-service-account ')

  def testScopesWithNoServiceAccount(self, api, release_track):
    SetUp(self, api)
    self.track = release_track

    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instance-templates create asdf '
               '--scopes=scope1 --no-service-account ')

  def testNoServiceAccountNoScopes(self, api, release_track):
    SetUp(self, api)
    self.track = release_track

    m = self.messages
    self.Run('compute instance-templates create asdf '
             '--no-service-account --no-scopes')
    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=m.InstanceTemplate(
                  name='asdf',
                  properties=m.InstanceProperties(
                      canIpForward=False,
                      disks=[m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,
                          ),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                      machineType=_DEFAULT_MACHINE_TYPE,
                      metadata=m.Metadata(),
                      networkInterfaces=[m.NetworkInterface(
                          accessConfigs=[self._default_access_config],
                          network=self._default_network)],
                      serviceAccounts=[],
                      scheduling=m.Scheduling(automaticRestart=True)
                  )
              ),
              project='my-project',
          ))],
    )


class LabelsTest(test_base.BaseTest):
  """Test for instance templates with labels."""

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testCreateWithLabels(self):
    msg = self.messages
    self.Run("""
        compute instance-templates create hamlet
            --disk name=boot-disk,boot=yes
            --labels k-0=v-0,k-1=v-1
        """)

    labels_in_request = (('k-0', 'v-0'), ('k-1', 'v-1'))
    template = msg.InstanceTemplate(
        name='hamlet',
        properties=msg.InstanceProperties(
            canIpForward=False,
            disks=[
                msg.AttachedDisk(
                    autoDelete=False,
                    boot=True,
                    mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    source=('boot-disk'),
                    type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
            ],
            labels=msg.InstanceProperties.LabelsValue(
                additionalProperties=[
                    msg.InstanceProperties.LabelsValue.AdditionalProperty(
                        key=pair[0], value=pair[1])
                    for pair in labels_in_request]),
            machineType=_DEFAULT_MACHINE_TYPE,
            metadata=msg.Metadata(),
            networkInterfaces=[msg.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)],
            serviceAccounts=[
                msg.ServiceAccount(
                    email='default',
                    scopes=_DEFAULT_SCOPES
                ),
            ],
            scheduling=msg.Scheduling(automaticRestart=True),
        )
    )
    self.CheckRequests(
        [(self.compute.instanceTemplates, 'Insert',
          msg.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project'))])

  def testCreateWithInvalidLabels(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run("""
          compute instance-templates create hamlet
            --disk name=boot-disk,boot=yes
            --labels=inv@lid-key=inv@l!d-value
          """)


class InstanceTemplatesCreateShieldedVMConfigAlphaTest(
    InstanceTemplatesCreateTest, parameterized.TestCase):
  """Test creation of VM instances with shielded VM config."""

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateSVMCkWithNoProperties(self):
    m = self.messages
    self.Run(
        'compute instance-templates create template-1 ')
    prop = m.InstanceProperties(
        canIpForward=False,
        disks=[m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,
            ),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
        machineType=_DEFAULT_MACHINE_TYPE,
        metadata=m.Metadata(),
        networkInterfaces=[m.NetworkInterface(
            accessConfigs=[self._default_access_config],
            network=self._default_network)],
        serviceAccounts=[
            m.ServiceAccount(
                email='default',
                scopes=_DEFAULT_SCOPES
            ),
        ],
        scheduling=m.Scheduling(automaticRestart=True),
    )
    template = m.InstanceTemplate(
        name='template-1',
        properties=prop
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  @parameterized.named_parameters(
      ('EnableSecureBoot', '--shielded-vm-secure-boot', True, None, None),
      ('EnableVtpm', '--shielded-vm-vtpm', None, True, None),
      ('EnableIntegrity', '--shielded-vm-integrity-monitoring', None, None,
       True),
      ('DisableSecureBoot', '--no-shielded-vm-secure-boot', False, None, None),
      ('DisableVtpm', '--no-shielded-vm-vtpm', None, False, None),
      ('DisableIntegrity', '--no-shielded-vm-integrity-monitoring', None, None,
       False),
      ('ESecureBootEvtpm', '--shielded-vm-secure-boot --shielded-vm-vtpm', True,
       True, None),
      ('DSecureBootDvtpm', '--no-shielded-vm-secure-boot --no-shielded-vm-vtpm',
       False, False, None),
      ('ESecureBootDvtpm', '--shielded-vm-secure-boot --no-shielded-vm-vtpm',
       True, False, None),
      ('DSecureBootEvtpm', '--no-shielded-vm-secure-boot --shielded-vm-vtpm',
       False, True, None),
      ('DSecureBootEvtpmEIntegrity',
       ('--no-shielded-vm-secure-boot --shielded-vm-vtpm'
        ' --shielded-vm-integrity-monitoring'), False, True, True),
  )
  def testCreateSVMCkWithAllProperties(self, cmd_flag, enable_secure_boot,
                                       enable_vtpm,
                                       enable_integrity_monitoring):
    m = self.messages
    self.Run('compute instance-templates create template-1 '
             '{}'.format(cmd_flag))

    prop = m.InstanceProperties(
        canIpForward=False,
        disks=[m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,
            ),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
        machineType=_DEFAULT_MACHINE_TYPE,
        metadata=m.Metadata(),
        networkInterfaces=[m.NetworkInterface(
            accessConfigs=[self._default_access_config],
            network=self._default_network)],
        serviceAccounts=[
            m.ServiceAccount(
                email='default',
                scopes=_DEFAULT_SCOPES
            ),
        ],
        scheduling=m.Scheduling(automaticRestart=True),
    )

    # Add shielded vm config info.
    prop.shieldedVmConfig = m.ShieldedVmConfig(
        enableSecureBoot=enable_secure_boot,
        enableVtpm=enable_vtpm,
        enableIntegrityMonitoring=enable_integrity_monitoring)

    template = m.InstanceTemplate(
        name='template-1',
        properties=prop
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )


class InstanceTemplatesCreateShieldedVMConfigBetaTest(
    InstanceTemplatesCreateShieldedVMConfigAlphaTest):
  """Test creation of VM instances with shielded VM config."""

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA


class InstanceTemplatesCreateWithNodeAffinity(test_base.BaseTest,
                                              parameterized.TestCase):
  """Test creation of VM instances on sole tenant host."""

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.node_affinity = self.messages.SchedulingNodeAffinity
    self.operator_enum = self.node_affinity.OperatorValueValuesEnum

  def _CheckCreateRequests(self, node_affinities):
    m = self.messages
    prop = m.InstanceProperties(
        canIpForward=False,
        disks=[m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,
            ),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
        machineType=_DEFAULT_MACHINE_TYPE,
        metadata=m.Metadata(),
        networkInterfaces=[m.NetworkInterface(
            accessConfigs=[self._default_access_config],
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
    )
    template = m.InstanceTemplate(
        name='template-1',
        properties=prop
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],)

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
        compute instance-templates create template-1
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
        compute instance-templates create template-1
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
        compute instance-templates create template-1
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
          compute instance-templates create template-1
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
          compute instance-templates create template-1
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
    with self.AssertRaisesExceptionRegexp(
        sole_tenancy_util.NodeAffinityFileParseError,
        r"Expected type <(class|type) '(str|unicode)'> for field values, found "
        r"3 \(type <(class|type) 'int'>\)"):
      self.Run("""
          compute instance-templates create template-1
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
          compute instance-templates create template-1
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
          compute instance-templates create template-1
            --node-affinity-file {}
          """.format(node_affinity_file))

  def testCreate_NodeGroup(self):
    node_affinities = [
        self.node_affinity(
            key='compute.googleapis.com/node-group-name',
            operator=self.operator_enum.IN,
            values=['my-node-group'])]
    self.Run("""
        compute instance-templates create template-1
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
        compute instance-templates create template-1
          --node my-node
        """)

    self._CheckCreateRequests(node_affinities)


if __name__ == '__main__':
  test_case.main()
