# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for images packages diff subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
import mock


class DiffTest(
    sdk_test_base.WithFakeAuth,
    cli_test_base.CliTestBase,
    sdk_test_base.WithOutputCapture):
  """Test `image packages diff` command."""

  def _MakeOccurrence(self, image, image_id, package_name, package_versions,
                      package_path, image_project=None):
    kind = self.messages.Occurrence.KindValueValuesEnum
    installation = self.messages.Installation(
        name=package_name,
        location=[
            self.messages.Location(  # pylint:disable=g-complex-comprehension
                version=self.messages.Version(
                    name=package_version[0],
                    revision=package_version[1]
                ),
                path=package_path
            ) for package_version in package_versions
        ]
    )

    image_project = image_project or self.Project()
    resource_url = (
        'https://compute.googleapis.com/compute/v1/'
        'projects/{}/global/images/{}/id/{}').format(
            image_project, image, image_id)

    return self.messages.Occurrence(
        resourceUrl=resource_url,
        kind=kind.PACKAGE_MANAGER,
        installation=installation)

  def _MakeOccurences(self, filter_):
    if 'my-image-1' in filter_:
      return [
          self._MakeOccurrence(image='my-image-1',
                               image_id='123',
                               package_name='package_1',
                               package_versions=[
                                   ('1.15', '1+deb9u1'),
                               ],
                               package_path='/var/lib/dpkg/status',
                               image_project='project-1'),
          self._MakeOccurrence(image='my-image-1',
                               image_id='123',
                               package_name='package_2',
                               package_versions=[
                                   ('2.7.6.1', '2'),
                                   ('2.7.6.2', '3')
                               ],
                               package_path='/var/lib/dpkg/status',
                               image_project='project-1'),
          self._MakeOccurrence(image='my-image-1',
                               image_id='123',
                               package_name='package_3',
                               package_versions=[
                                   ('5.24.1', '3+deb9u3'),
                                   ('5.24.2', '3+deb9u3')
                               ],
                               package_path='/var/lib/dpkg/status',
                               image_project='project-1'),
          self._MakeOccurrence(image='my-image-1',
                               image_id='123',
                               package_name='package_same',
                               package_versions=[
                                   ('2.0.28', '2+b1'),
                               ],
                               package_path='/var/lib/dpkg/status',
                               image_project='project-1'),
      ]
    elif 'my-image-2' in filter_:
      return [
          self._MakeOccurrence(image='my-image-2',
                               image_id='456',
                               package_name='package_1',
                               package_versions=[
                                   ('1.17', '1+deb9u3'),
                               ],
                               package_path='/var/lib/dpkg/status',
                               image_project='project-2'),
          self._MakeOccurrence(image='my-image-2',
                               image_id='456',
                               package_name='package_2',
                               package_versions=[
                                   ('2.7.6.1', '1'),
                                   ('2.7.6.3', '3')
                               ],
                               package_path='/var/lib/dpkg/status',
                               image_project='project-2'),
          self._MakeOccurrence(image='my-image-2',
                               image_id='456',
                               package_name='package_4',
                               package_versions=[
                                   ('5.11', '3'),
                                   ('5.12', '4'),
                               ],
                               package_path='/var/lib/dpkg/status',
                               image_project='project-2'),
          self._MakeOccurrence(image='my-image-2',
                               image_id='456',
                               package_name='package_same',
                               package_versions=[
                                   ('2.0.28', '2+b1'),
                               ],
                               package_path='/var/lib/dpkg/status',
                               image_project='project-2'),
      ]

  def _MockYieldFromList(self):
    filter_string = ('kind = "PACKAGE_MANAGER" AND has_prefix(resource_url,'
                     '"https://compute.googleapis.com/compute/") AND has_prefix'
                     '(resource_url,"https://compute.googleapis.com/compute/v1/'
                     'projects/{}/global/images/{}/id/{}")')
    old_yield = list_pager.YieldFromList
    def _FakeYield(service, request, **kwargs):
      if 'my-image-1' in request.filter:
        self.mock_client.projects_occurrences.List.Expect(
            self.messages.ContaineranalysisProjectsOccurrencesListRequest(
                filter=filter_string.format('project-1', 'my-image-1', '123'),
                pageSize=1000,
                parent='projects/project-1'
            ),
            self.messages.ListOccurrencesResponse(
                occurrences=self._MakeOccurences(filter_=request.filter)
            )
        )
      elif 'my-image-2' in request.filter:
        self.mock_client.projects_occurrences.List.Expect(
            self.messages.ContaineranalysisProjectsOccurrencesListRequest(
                filter=filter_string.format('project-2', 'my-image-2', '456'),
                pageSize=1000,
                parent='projects/project-2'
            ),
            self.messages.ListOccurrencesResponse(
                occurrences=self._MakeOccurences(filter_=request.filter)
            )
        )
      return old_yield(service, request, **kwargs)
    self.StartObjectPatch(list_pager, 'YieldFromList', _FakeYield)

  def _MakeImage(self, project, image_name, image_id):
    self_link_string = """https://compute.googleapis.com/compute/v1/projects/{}/
    global/images/{}/id/{}"""
    return self.compute_messages.Image(
        selfLink=self_link_string.format(project, image_name, str(image_id)),
        id=image_id)

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.mock_client = apitools_mock.Client(
        apis.GetClientClass('containeranalysis', 'v1alpha1'),
        real_client=apis.GetClientInstance(
            'containeranalysis', 'v1alpha1', no_http=True),
    )
    self.mock_compute_client = apitools_mock.Client(
        apis.GetClientClass('compute', 'v1'),
        real_client=apis.GetClientInstance(
            'compute', 'v1', no_http=True),
    )
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')
    self.compute_messages = apis.GetMessagesModule('compute', 'v1')

    make_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_requests_patcher.stop)
    self.make_requests = make_requests_patcher.start()

  def testDiffPackages(self):
    self._MockYieldFromList()

    self.make_requests.side_effect = iter(
        [[self._MakeImage('project-1', 'my-image-1', 123)],
         [self._MakeImage('project-2', 'my-image-2', 456)]])

    self.Run('compute images packages diff --base-image my-image-1 '
             '--diff-image my-image-2 --base-project project-1 '
             '--diff-project project-2')

    self.AssertOutputEquals("""\
PACKAGE VERSION_BASE REVISION_BASE VERSION_DIFF REVISION_DIFF
package_1 1.15 1+deb9u1 1.17 1+deb9u3
package_2 2.7.6.1 2 2.7.6.1 1
package_2 2.7.6.2 3 2.7.6.3 3
package_3 5.24.1 3+deb9u3 - -
package_3 5.24.2 3+deb9u3 - -
package_4 - - 5.11 3
package_4 - - 5.12 4
""", normalize_space=True)

  def testShowAddedPackages(self):
    self._MockYieldFromList()

    self.make_requests.side_effect = iter(
        [[self._MakeImage('project-1', 'my-image-1', 123)],
         [self._MakeImage('project-2', 'my-image-2', 456)]])

    self.Run('compute images packages diff --base-image my-image-1 '
             '--diff-image my-image-2 --base-project project-1 '
             '--diff-project project-2 --show-added-packages')

    self.AssertOutputEquals("""\
PACKAGE VERSION_BASE REVISION_BASE VERSION_DIFF REVISION_DIFF
package_4 - - 5.11 3
package_4 - - 5.12 4
""", normalize_space=True)

  def testShowRemovedPackages(self):
    self._MockYieldFromList()

    self.make_requests.side_effect = iter(
        [[self._MakeImage('project-1', 'my-image-1', 123)],
         [self._MakeImage('project-2', 'my-image-2', 456)]])

    self.Run('compute images packages diff --base-image my-image-1 '
             '--diff-image my-image-2 --base-project project-1 '
             '--diff-project project-2 --show-removed-packages')

    self.AssertOutputEquals("""\
PACKAGE VERSION_BASE REVISION_BASE VERSION_DIFF REVISION_DIFF
package_3 5.24.1 3+deb9u3 - -
package_3 5.24.2 3+deb9u3 - -
""", normalize_space=True)

  def testShowUpdatedPackages(self):
    self._MockYieldFromList()

    self.make_requests.side_effect = iter(
        [[self._MakeImage('project-1', 'my-image-1', 123)],
         [self._MakeImage('project-2', 'my-image-2', 456)]])

    self.Run('compute images packages diff --base-image my-image-1 '
             '--diff-image my-image-2 --base-project project-1 '
             '--diff-project project-2 --show-updated-packages')

    self.AssertOutputEquals("""\
PACKAGE VERSION_BASE REVISION_BASE VERSION_DIFF REVISION_DIFF
package_1 1.15 1+deb9u1 1.17 1+deb9u3
package_2 2.7.6.1 2 2.7.6.1 1
package_2 2.7.6.2 3 2.7.6.3 3
""", normalize_space=True)
