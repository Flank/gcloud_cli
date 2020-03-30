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

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class LabelsTest(create_test_base.InstanceTemplatesCreateTestBase):
  """Test for instance templates with labels."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testCreateWithLabels(self):
    msg = self.messages
    self.Run("""
        compute instance-templates create template-1
            --disk name=boot-disk,boot=yes
            --labels k-0=v-0,k-1=v-1
        """)

    labels_in_request = (('k-0', 'v-0'), ('k-1', 'v-1'))
    template = self._MakeInstanceTemplate(
        disks=[
            msg.AttachedDisk(
                autoDelete=False,
                boot=True,
                mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                source=('boot-disk'),
                type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        ],
        labels=msg.InstanceProperties.LabelsValue(additionalProperties=[
            msg.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1]) for pair in labels_in_request
        ]))
    self.CheckRequests([(self.compute.instanceTemplates, 'Insert',
                         msg.ComputeInstanceTemplatesInsertRequest(
                             instanceTemplate=template, project='my-project'))])

  def testCreateWithInvalidLabels(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run("""
          compute instance-templates create template-1
            --disk name=boot-disk,boot=yes
            --labels=inv@lid-key=inv@l!d-value
          """)


if __name__ == '__main__':
  test_case.main()
