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
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateSourceInstanceTemplate(
    create_test_base.InstancesCreateTestBase, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testCreateFromTemplate(self):
    m = self.messages

    self.Run('compute instances create instance-1 '
             '--zone central2-a '
             '--source-instance-template template')

    self.CheckRequests(
        self.zone_get_request, self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(deletionProtection=False, name='instance-1'),
              project='my-project',
              sourceInstanceTemplate=(
                  self.compute_uri +
                  '/projects/my-project/global/instanceTemplates/template'),
              zone='central2-a'))])


class InstancesCreateSourceInstanceTemplateBeta(
    InstancesCreateSourceInstanceTemplate):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstancesCreateSourceInstanceTemplateAlpha(
    InstancesCreateSourceInstanceTemplateBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
