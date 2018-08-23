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
"""Tests for the images deprecate subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

import mock

messages = core_apis.GetMessagesModule('compute', 'v1')

DEPRECATED = messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED


class ImagesDeprecateTest(test_base.BaseTest):

  def SetUp(self):
    datetime_patcher = mock.patch('datetime.datetime', test_base.FakeDateTime)
    self.addCleanup(datetime_patcher.stop)
    datetime_patcher.start()

  def testActiveFlag(self):
    self.templateTestActiveFlag("""
        compute images deprecate my-image
          --state ACTIVE
        """)

  def testActiveFlagLowerCase(self):
    self.templateTestActiveFlag("""
        compute images deprecate my-image
          --state active
        """)

  def templateTestActiveFlag(self, cmd):
    self.Run(cmd)

    self.CheckRequests(
        [(self.compute_v1.images,
          'Deprecate',
          messages.ComputeImagesDeprecateRequest(
              deprecationStatus=messages.DeprecationStatus(),
              image='my-image',
              project='my-project'))],
    )

  def testActiveFlagMustBeOnlyFlag(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'If the state is set to \[ACTIVE\] then none of \[--delete-on\], '
        r'\[--delete-in\], \[--obsolete-on\], \[--obsolete-in\], or '
        r'\[--replacement\] may be provided.'):
      self.Run("""
          compute images deprecate my-image
            --state ACTIVE
             --replacement other-image
        """)

    self.CheckRequests()

  def testDeleteIn(self):
    self.Run("""
        compute images deprecate my-image
          --state DEPRECATED
          --replacement other-image
          --delete-in 1d
        """)

    self.CheckRequests([
        (self.compute_v1.images, 'Deprecate',
         messages.ComputeImagesDeprecateRequest(
             deprecationStatus=messages.DeprecationStatus(
                 state=DEPRECATED,
                 deleted='2014-01-03T03:04:05',
                 replacement=(
                     'https://www.googleapis.com/compute/v1/projects/'
                     'my-project/global/images/other-image')),
             image='my-image',
             project='my-project'))],)

  def testDeleteOn(self):
    self.Run("""
        compute images deprecate my-image
          --state DEPRECATED
          --replacement other-image
          --delete-on 2014-01-02T03:04:05
        """)

    self.CheckRequests([
        (self.compute_v1.images, 'Deprecate',
         messages.ComputeImagesDeprecateRequest(
             deprecationStatus=messages.DeprecationStatus(
                 state=DEPRECATED,
                 deleted='2014-01-02T03:04:05',
                 replacement=(
                     'https://www.googleapis.com/compute/v1/projects/'
                     'my-project/global/images/other-image')),
             image='my-image',
             project='my-project'))],)

  def testObsoleteIn(self):
    self.Run("""
        compute images deprecate my-image
          --state DEPRECATED
          --replacement other-image
          --obsolete-in 1d
        """)

    self.CheckRequests([
        (self.compute_v1.images, 'Deprecate',
         messages.ComputeImagesDeprecateRequest(
             deprecationStatus=messages.DeprecationStatus(
                 state=DEPRECATED,
                 obsolete='2014-01-03T03:04:05',
                 replacement=(
                     'https://www.googleapis.com/compute/v1/projects/'
                     'my-project/global/images/other-image')),
             image='my-image',
             project='my-project'))],)

  def testObsoleteOn(self):
    self.Run("""
        compute images deprecate my-image
          --state DEPRECATED
          --replacement other-image
          --obsolete-on 2014-01-02T03:04:05
        """)

    self.CheckRequests([
        (self.compute_v1.images, 'Deprecate',
         messages.ComputeImagesDeprecateRequest(
             deprecationStatus=messages.DeprecationStatus(
                 state=DEPRECATED,
                 obsolete='2014-01-02T03:04:05',
                 replacement=(
                     'https://www.googleapis.com/compute/v1/projects/'
                     'my-project/global/images/other-image')),
             image='my-image',
             project='my-project'))],)

  def testAllIn(self):
    # In reality, this command would not pass but it should still send this
    # command along to the backend.
    self.Run("""
        compute images deprecate my-image
          --state OBSOLETE
          --replacement other-image
          --obsolete-in 2d
          --delete-in 3d
        """)

    self.CheckRequests([
        (self.compute_v1.images, 'Deprecate',
         messages.ComputeImagesDeprecateRequest(
             deprecationStatus=messages.DeprecationStatus(
                 state=(
                     messages.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
                 obsolete='2014-01-04T03:04:05',
                 deleted='2014-01-05T03:04:05',
                 replacement=(
                     'https://www.googleapis.com/compute/v1/projects/'
                     'my-project/global/images/other-image')),
             image='my-image',
             project='my-project'))],)

  def testUriSupport(self):
    self.Run("""
        compute images deprecate
          https://www.googleapis.com/compute/v1/projects/my-project/global/images/my-image
          --state DEPRECATED
          --replacement https://www.googleapis.com/compute/v1/projects/my-project/global/images/other-image
          --delete-in 1d
        """)

    self.CheckRequests([
        (self.compute_v1.images, 'Deprecate',
         messages.ComputeImagesDeprecateRequest(
             deprecationStatus=messages.DeprecationStatus(
                 state=DEPRECATED,
                 deleted='2014-01-03T03:04:05',
                 replacement=(
                     'https://www.googleapis.com/compute/v1/projects/'
                     'my-project/global/images/other-image')),
             image='my-image',
             project='my-project'))],)

  def testReplacementFlagOptionalForDeprecation(self):
    self.Run('compute images deprecate my-image --state DEPRECATED')

    self.CheckRequests([
        (self.compute_v1.images, 'Deprecate',
         messages.ComputeImagesDeprecateRequest(
             deprecationStatus=messages.DeprecationStatus(
                 state=DEPRECATED,
             ),
             image='my-image',
             project='my-project'))],)

if __name__ == '__main__':
  test_case.main()
