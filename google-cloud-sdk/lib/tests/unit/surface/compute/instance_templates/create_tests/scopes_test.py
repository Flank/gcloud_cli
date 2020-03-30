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
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class ScopesDeprecationTests(create_test_base.InstanceTemplatesCreateTestBase):
  # Set of tests of deprecation of old --scopes flag syntax, new --scopes flag
  # syntax and --service-account flag.

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testScopesLegacyFormatDeprecationNotice(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--scopes]: Flag format --scopes [ACCOUNT=]SCOPE,'
        '[[ACCOUNT=]SCOPE, ...] is removed. Use --scopes [SCOPE,...] '
        '--service-account ACCOUNT instead.'):
      self.Run('compute instance-templates create template-1 '
               '--scopes=acc1=scope1,acc1=scope2')

  def testScopesNewFormatNoDeprecationNotice(self):
    self.Run('compute instance-templates create template-1 '
             '--scopes=scope1,scope2 --service-account acc1@example.com ')
    self.AssertErrEquals('')

  def testNoServiceAccount(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instance-templates create template-1 '
               '--no-service-account ')

  def testScopesWithNoServiceAccount(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        r'.*argument \[--no-scopes]: required with argument '
        r'--no-service-account'):
      self.Run('compute instance-templates create template-1 '
               '--scopes=scope1 --no-service-account ')

  def testNoServiceAccountNoScopes(self):
    m = self.messages
    self.Run('compute instance-templates create template-1 '
             '--no-service-account --no-scopes')

    template = self._MakeInstanceTemplate(serviceAccounts=[])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
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

    template = self._MakeInstanceTemplate(serviceAccounts=[
        m.ServiceAccount(
            email='default',
            scopes=[
                'https://www.googleapis.com/auth/compute',
            ]),
    ])

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

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/compute'])
    template = self._MakeInstanceTemplate(serviceAccounts=[
        m.ServiceAccount(email='default', scopes=expected_scopes),
    ])

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

    template = self._MakeInstanceTemplate(serviceAccounts=[])

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

    template = self._MakeInstanceTemplate(serviceAccounts=[
        m.ServiceAccount(
            email='default',
            scopes=[
                'https://www.googleapis.com/auth/compute',
                'https://www.googleapis.com/auth/devstorage.full_control',
            ]),
    ])

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
          --scopes compute-rw,https://www.googleapis.com/auth/devstorage.full_control,bigquery,https://www.googleapis.com/auth/userinfo.email,sql,https://www.googleapis.com/auth/taskqueue
          --service-account 1234@project.gserviceaccount.com
        """)

    template = self._MakeInstanceTemplate(serviceAccounts=[
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
    ])

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


class ScopesDeprecationTestsBeta(ScopesDeprecationTests):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class ScopesDeprecationTestsAlpha(ScopesDeprecationTestsBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
