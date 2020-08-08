# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the images list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.resource_manager import org_policies
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.images import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class ImagesListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.IMAGES +
                                            test_resources.CENTOS_IMAGES)
    ]
    self.all_project_requests = [
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='centos-cloud')),
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='cos-cloud')),
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='debian-cloud')),
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='fedora-coreos-cloud')),
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='my-project')),
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='rhel-cloud')),
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='rhel-sap-cloud')),
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='suse-cloud')),
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='suse-sap-cloud')),
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='ubuntu-os-cloud')),
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='windows-cloud')),
        (self.compute_v1.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='windows-sql-cloud')),
    ]

  def testSimpleCase(self):
    self.Run("""
        compute images list
        """)

    self.list_json.assert_called_once_with(
        requests=self.all_project_requests,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME               PROJECT      FAMILY   DEPRECATED STATUS
            image-1            my-project                       READY
            image-2            my-project                       READY
            image-4            my-project                       READY
            centos-6-v20140408 centos-cloud centos-6            READY
            """), normalize_space=True)

  def testWithNoStandardImages(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.IMAGES)
    ]
    self.Run("""
        compute images list --uri --no-standard-images
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-1
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-2
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-4
            """))

  def testWithShowPreviewImages(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.IMAGES)
    ]
    self.Run("""
        compute images list --uri --no-standard-images --show-preview-images
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-1
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-2
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-4
            """))

  def testWithShowDeprecated(self):
    self.Run("""
        compute images list --show-deprecated
        """)

    self.list_json.assert_called_once_with(
        requests=self.all_project_requests,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME               PROJECT      FAMILY   DEPRECATED STATUS
            image-1            my-project                       READY
            image-2            my-project                       READY
            image-3            my-project            DEPRECATED READY
            image-4            my-project                       READY
            centos-6-v20140408 centos-cloud centos-6            READY
            centos-6-v20140318 centos-cloud centos-6 DEPRECATED READY
            """), normalize_space=True)

  def testWithNameRegexes(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.IMAGES +
                                            test_resources.CENTOS_IMAGES)
    ]
    self.Run("""
        compute images list
          --regexp "image-.*|centos-.*" --uri
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='centos-cloud')),
                  (self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='cos-cloud')),
                  (self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='debian-cloud')),
                  (self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='fedora-coreos-cloud')),
                  (self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='my-project')),
                  (self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='rhel-cloud')),
                  (self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='rhel-sap-cloud')),
                  (self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='suse-cloud')),
                  (self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='suse-sap-cloud')),
                  (self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='ubuntu-os-cloud')),
                  (self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='windows-cloud')),
                  (self.compute_v1.images, 'List',
                   self.messages.ComputeImagesListRequest(
                       filter=r'name eq ".*(^image-.*|centos-.*$).*"',
                       project='windows-sql-cloud'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-1
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-2
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-4
            https://compute.googleapis.com/compute/v1/projects/centos-cloud/global/images/centos-6-v20140408
            """))

  def testPositionalArgsWithSimpleNames(self):
    self.Run("""
        compute images list
          image-1 image-2
          --uri
        """)

    self.list_json.assert_called_once_with(
        requests=self.all_project_requests,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-1
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-2
            """))

  def testPositionalArgsWithUri(self):
    self.Run("""
        compute images list
          https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-1
          --uri
        """)

    self.list_json.assert_called_once_with(
        requests=self.all_project_requests,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-1
            """))

  def testPositionalArgsWithUriAndSimpleName(self):
    self.Run("""
        compute images list
          https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-1
          image-2
          --uri
        """)

    self.list_json.assert_called_once_with(
        requests=self.all_project_requests,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-1
            https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-2
            """))

  def testWithRequestError(self):
    def MakeRequests(*_, **kwargs):
      for image in test_resources.IMAGES:
        yield resource_projector.MakeSerializable(image)
      kwargs['errors'].append((500, 'Internal Error'))
    self.list_json.side_effect = MakeRequests

    self.Run("""
        compute images list
        """)
    self.AssertErrContains(
        textwrap.dedent("""\
        WARNING: Some requests did not succeed.
         - Internal Error

        """))

    self.list_json.assert_called_once_with(
        requests=self.all_project_requests,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[(500, 'Internal Error')])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    PROJECT    FAMILY DEPRECATED STATUS
            image-1 my-project                   READY
            image-2 my-project                   READY
            image-4 my-project                   READY
            """), normalize_space=True)

  def testImagesCompleter(self):
    self.RunCompleter(
        flags.ImagesCompleter,
        expected_command=[
            'compute',
            'images',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'image-1',
            'image-2',
            'image-4',
        ],
        cli=self.cli,
    )


class ImagesListBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.IMAGES +
                                            test_resources.CENTOS_IMAGES)
    ]
    self.all_project_requests = [
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='centos-cloud')),
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='cos-cloud')),
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='debian-cloud')),
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='fedora-coreos-cloud')),
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='my-project')),
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='rhel-cloud')),
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='rhel-sap-cloud')),
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='suse-cloud')),
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='suse-sap-cloud')),
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='ubuntu-os-cloud')),
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='windows-cloud')),
        (self.compute.images, 'List',
         self.messages.ComputeImagesListRequest(
             project='windows-sql-cloud')),
    ]

    self.mocked_org_policies_client = apitools_mock.Client(
        apis.GetClientClass('cloudresourcemanager',
                            org_policies.ORG_POLICIES_API_VERSION))
    self.mocked_org_policies_client.Mock()
    self.addCleanup(self.mocked_org_policies_client.Unmock)

    self.org_policies_messages = org_policies.OrgPoliciesMessages()

  def testNoFlagsOrgPolicySuccess(self):
    list_policy = self.org_policies_messages.ListPolicy(
        allowedValues=['projects/centos-cloud'])
    self.mocked_org_policies_client.projects.GetEffectiveOrgPolicy.Expect(
        request=self.org_policies_messages.
        CloudresourcemanagerProjectsGetEffectiveOrgPolicyRequest(
            projectsId='my-project',
            getEffectiveOrgPolicyRequest=self.
            org_policies_messages.GetEffectiveOrgPolicyRequest(
                constraint=org_policies.FormatConstraint(
                    'compute.trustedImageProjects'))),
        response=self.org_policies_messages.OrgPolicy(listPolicy=list_policy))

    self.Run("""
        compute images list
        """)

    self.list_json.assert_called_once_with(
        requests=self.all_project_requests,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        """\
        NAME               PROJECT      FAMILY   DEPRECATED STATUS
        image-1            my-project                       BLOCKED_BY_POLICY
        image-2            my-project                       BLOCKED_BY_POLICY
        image-4            my-project                       BLOCKED_BY_POLICY
        centos-6-v20140408 centos-cloud centos-6            READY
        """,
        normalize_space=True)

  def testNoFlagsOrgPolicyFailure(self):

    list_policy = self.org_policies_messages.ListPolicy(
        allowedValues=['THIS RECORD IS MALFORMED'])
    self.mocked_org_policies_client.projects.GetEffectiveOrgPolicy.Expect(
        request=self.org_policies_messages.
        CloudresourcemanagerProjectsGetEffectiveOrgPolicyRequest(
            projectsId='my-project',
            getEffectiveOrgPolicyRequest=self.
            org_policies_messages.GetEffectiveOrgPolicyRequest(
                constraint=org_policies.FormatConstraint(
                    'compute.trustedImageProjects'))),
        response=self.org_policies_messages.OrgPolicy(listPolicy=list_policy))

    self.Run('compute images list --verbosity=info')

    self.list_json.assert_called_once_with(
        requests=self.all_project_requests,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        """\
        NAME               PROJECT      FAMILY   DEPRECATED STATUS
        image-1            my-project                       READY
        image-2            my-project                       READY
        image-4            my-project                       READY
        centos-6-v20140408 centos-cloud centos-6            READY
        """,
        normalize_space=True)
    # pylint:disable=line-too-long
    self.AssertErrContains(
        """\
        INFO: could not parse resource [THIS RECORD IS MALFORMED]: It is not in compute.projects collection as it does not match path template projects/(.*)$
        INFO: could not parse resource [THIS RECORD IS MALFORMED]: It is not in compute.projects collection as it does not match path template projects/(.*)$
        INFO: could not parse resource [THIS RECORD IS MALFORMED]: It is not in compute.projects collection as it does not match path template projects/(.*)$
        """,
        normalize_space=True)
    # pylint:enable=line-too-long


if __name__ == '__main__':
  test_case.main()
