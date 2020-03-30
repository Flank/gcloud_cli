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
"""Test base for the instances create-with-container subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import containers_utils
from tests.lib.surface.compute import test_base


class InstancesCreateWithContainerTestBase(test_base.BaseTest):
  """Test base for instances create-with-container command."""

  def SetUp(self):
    self.SelectApi(self.api_version)
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

  def AcceleratorTypeOf(self, name):
    return ('https://compute.googleapis.com/compute/{ver}/projects/my-project/'
            'zones/central2-a/acceleratorTypes/{name}'.format(
                ver=self.api_version, name=name))
