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
"""Tests for the images export subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import daisy_test_base


class ImagesExportTestGA(daisy_test_base.DaisyBaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.regionalized = False
    self.creates_bucket_if_cloudbuild_disabled = False
    self.image_name = 'my-image'
    self.destination_uri = 'gs://31dd/my-image.tar.gz'
    self.daisy_builder = 'gcr.io/compute-image-tools/daisy:release'
    self.tags = ['gce-daisy', 'gce-daisy-image-export']

  def PrepareDaisyMocks(self, daisy_step, timeout='7200s', log_location=None,
                        permissions=None, async_flag=False, regionalized=True,
                        source_disk='source-image.vmdk'):
    super(ImagesExportTestGA, self).PrepareDaisyMocks(
        daisy_step, timeout=timeout, log_location=log_location,
        permissions=permissions, async_flag=async_flag,
        regionalized=regionalized, source_disk=source_disk, is_import=True)

  def GetNetworkStep(self, network=None, subnet=None,
                     include_zone=True, include_empty_network=False):
    daisy_vars = (
        '-variables=source_image=projects/my-project/global/images/{0},'
        'destination={1}').format(self.image_name, self.destination_uri)
    return super(ImagesExportTestGA, self).GetNetworkStep(
        workflow='../workflows/export/image_export.wf.json',
        daisy_vars=daisy_vars, operation=daisy_utils.ImageOperation.EXPORT,
        network=network, subnet=subnet, include_zone=include_zone,
        include_empty_network=include_empty_network)

  def testCommonCase(self):
    export_workflow = ('../workflows/export/image_export.wf.json')
    daisy_step = self.cloudbuild_v1_messages.BuildStep(
        args=[
            '-gcs_path=gs://{0}/'.format(
                self.GetScratchBucketName(regionalized=self.regionalized)),
            '-default_timeout={0}'.format(daisy_test_base._DEFAULT_TIMEOUT),
            '-variables=source_image=projects/my-project/global/images/{0},'
            'destination={1}'.format(self.image_name, self.destination_uri),
            export_workflow,
        ],
        name=self.daisy_builder,
    )

    self.PrepareDaisyMocks(daisy_step, regionalized=self.regionalized)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1}
             """.format(self.image_name, self.destination_uri))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testExportFormat(self):
    export_workflow = ('../workflows/export/image_export_ext.wf.json')
    daisy_step = self.cloudbuild_v1_messages.BuildStep(
        args=[
            '-gcs_path=gs://{0}/'.format(
                self.GetScratchBucketName(regionalized=self.regionalized)),
            '-default_timeout={0}'.format(daisy_test_base._DEFAULT_TIMEOUT),
            '-variables=source_image=projects/my-project/global/images/{0},'
            'destination={1},format=vmdk'
            .format(self.image_name, self.destination_uri),
            export_workflow,
        ],
        name=self.daisy_builder,
    )

    self.PrepareDaisyMocks(daisy_step, regionalized=self.regionalized)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1} --export-format=vmdk
             """.format(self.image_name, self.destination_uri))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testZoneFlag(self):
    zone = 'us-west1-c'
    export_workflow = ('../workflows/export/image_export.wf.json')
    daisy_step = self.cloudbuild_v1_messages.BuildStep(
        args=['-zone={0}'.format(zone),
              '-gcs_path=gs://{0}/'.format(
                  self.GetScratchBucketName(regionalized=self.regionalized)),
              '-default_timeout={0}'.format(daisy_test_base._DEFAULT_TIMEOUT),
              '-variables=source_image=projects/my-project/global/images/{0},'
              'destination={1}'
              .format(self.image_name, self.destination_uri),
              export_workflow,],
        name=self.daisy_builder,
    )

    self.PrepareDaisyMocks(daisy_step, regionalized=self.regionalized)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1} --zone={2}
             """.format(self.image_name, self.destination_uri, zone))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testServiceNotEnabled(self):
    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.servicemanagement_v1_messages.ListServicesResponse(
            services=[
                # Missing 'cloudbuild.googleapis.com'.
                self.servicemanagement_v1_messages.ManagedService(
                    serviceName='logging.googleapis.com')
            ]
        )
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    if self.creates_bucket_if_cloudbuild_disabled:
      self.PrepareDaisyBucketMocks(regionalized=self.regionalized)

    with self.assertRaisesRegexp(console_io.UnattendedPromptError,
                                 ('This prompt could not be answered because '
                                  'you are not in an interactive session.')):
      self.Run("""
               compute images export --image {0}
               --destination-uri {1}
               """.format(self.image_name, self.destination_uri))

    self.AssertErrContains('cloudbuild.googleapis.com')

  def testImageProject(self):
    export_workflow = ('../workflows/export/image_export.wf.json')
    daisy_step = self.cloudbuild_v1_messages.BuildStep(
        args=[
            '-gcs_path=gs://{0}/'.format(
                self.GetScratchBucketName(regionalized=self.regionalized)),
            '-default_timeout={0}'.format(daisy_test_base._DEFAULT_TIMEOUT),
            '-variables=source_image=projects/debian-cloud/global/images/{0},'
            'destination={1}'
            .format(self.image_name, self.destination_uri),
            export_workflow,
        ],
        name=self.daisy_builder,
    )

    self.PrepareDaisyMocks(daisy_step, regionalized=self.regionalized)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1} --image-project debian-cloud
             """.format(self.image_name, self.destination_uri))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testNetworkFlag(self):
    daisy_step = self.GetNetworkStep(network=self.network, include_zone=False)
    self.PrepareDaisyMocks(daisy_step, regionalized=self.regionalized)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1} --network {2}
             """.format(self.image_name, self.destination_uri, self.network))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testMissingImage(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--image | --image-family) must be specified.'):
      self.Run("""
               compute images export --destination-uri {0}
               """.format(self.destination_uri))

  def testMissingDestination(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --destination-uri: Must be specified'):
      self.Run("""
               compute images export --image {0}
               """.format(self.image_name))


class ImagesExportTestBeta(ImagesExportTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.regionalized = False


class ImagesExportTestAlpha(ImagesExportTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.regionalized = True
    self.creates_bucket_if_cloudbuild_disabled = True

  def testSubnetFlag(self):
    daisy_step = self.GetNetworkStep(network=self.network, subnet=self.subnet)
    self.PrepareDaisyMocks(daisy_step, regionalized=self.regionalized)

    self.Run("""
             compute images export --image {0} --destination-uri {1}
             --network {2} --subnet {3} --zone my-region-c
             """.format(self.image_name, self.destination_uri, self.network,
                        self.subnet))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testSubnetFlagNetworkVariableClearedIfNetworkFlagNotSpecified(self):
    daisy_step = self.GetNetworkStep(
        network='', include_empty_network=True, subnet=self.subnet)
    self.PrepareDaisyMocks(daisy_step, regionalized=self.regionalized)

    self.Run("""
             compute images export --image {0} --destination-uri {1}
             --subnet {2} --zone my-region-c
             """.format(self.image_name, self.destination_uri, self.subnet))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testSubnetFlagZoneAndRegionNotSpecified(self):
    error = r'Region or zone should be specified.'
    with self.AssertRaisesExceptionRegexp(
        daisy_utils.SubnetException, error):
      self.Run("""
             compute images export --image {0} --destination-uri {1}
             --subnet {2}
             """.format(self.image_name, self.destination_uri, self.subnet))

  def testSubnetFlagZoneAsProperty(self):
    daisy_step = self.GetNetworkStep(network=self.network, subnet=self.subnet)
    self.PrepareDaisyMocks(daisy_step, regionalized=self.regionalized)

    properties.VALUES.compute.zone.Set('my-region-c')
    self.Run("""
             compute images export --image {0} --destination-uri {1}
             --network {2} --subnet {3}
             """.format(self.image_name, self.destination_uri, self.network,
                        self.subnet))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testSubnetFlagRegionAsProperty(self):
    daisy_step = self.GetNetworkStep(
        network=self.network, subnet=self.subnet, include_zone=False)
    self.PrepareDaisyMocks(daisy_step, regionalized=self.regionalized)

    properties.VALUES.compute.region.Set('my-region')
    self.Run("""
             compute images export --image {0} --destination-uri {1}
             --network {2} --subnet {3}
             """.format(self.image_name, self.destination_uri, self.network,
                        self.subnet))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
