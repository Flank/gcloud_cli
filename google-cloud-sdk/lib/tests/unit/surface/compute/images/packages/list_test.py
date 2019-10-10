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
"""Tests for images packages list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
import mock


class ListTest(
    sdk_test_base.WithFakeAuth,
    cli_test_base.CliTestBase,
    sdk_test_base.WithOutputCapture):
  """Test `image packages list` command."""

  def _MakeOccurrence(self, image, name, note_id, package_name,
                      package_versions, package_path, image_project=None):
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
        'https://compute.googleapis.com/compute/v1'
        '/projects/{}/global/images/{}').format(image_project, image)

    return self.messages.Occurrence(
        resourceUrl=resource_url,
        noteName='providers/goog-vulnz/notes/{}'.format(note_id),
        name=name,
        kind=kind.PACKAGE_MANAGER,
        installation=installation)

  def _MakeOccurences(self, filter_):
    return [
        self._MakeOccurrence(image='my-image', name='foo',
                             note_id='CVE-2018-1111',
                             package_name='package_foo',
                             package_versions=[
                                 ('2.7.6.1', '2'),
                                 ('2.7.6.2', '3'),
                                 ('2.7.6.2', '4')
                             ],
                             package_path='/var/lib/dpkg/status',
                             image_project='other-project'),
        self._MakeOccurrence(image='my-image', name='foo2',
                             note_id='CVE-2018-1112',
                             package_name='package_bar',
                             package_versions=[
                                 ('1.15', '1+deb9u1'),
                                 ('1.16', '1+deb9u1')
                             ],
                             package_path='/var/lib/dpkg/status',
                             image_project='other-project'),
    ]

  def _MockYieldFromList(self, filter_string):
    old_yield = list_pager.YieldFromList
    def _FakeYield(service, request, **kwargs):
      self.mock_client.projects_occurrences.List.Expect(
          self.messages.ContaineranalysisProjectsOccurrencesListRequest(
              filter=filter_string,
              pageSize=1000,
              parent='projects/fake-project'
          ),
          self.messages.ListOccurrencesResponse(
              occurrences=self._MakeOccurences(filter_=request.filter)
          )
      )
      return old_yield(service, request, **kwargs)
    self.StartObjectPatch(list_pager, 'YieldFromList', _FakeYield)

  def _MakeImage(self, image_name, image_id):
    return self.compute_messages.Image(name=image_name, id=image_id)

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass('containeranalysis', 'v1alpha1'),
        real_client=core_apis.GetClientInstance(
            'containeranalysis', 'v1alpha1', no_http=True),
    )
    self.mock_compute_client = apitools_mock.Client(
        core_apis.GetClientClass('compute', 'v1'),
        real_client=core_apis.GetClientInstance(
            'compute', 'v1', no_http=True),
    )
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = core_apis.GetMessagesModule('containeranalysis', 'v1alpha1')
    self.compute_messages = core_apis.GetMessagesModule('compute', 'v1')

  def testListPackages(self):
    self._MockYieldFromList(
        'kind = "PACKAGE_MANAGER" AND '
        'has_prefix(resource_url,"https://compute.googleapis.com/compute/") AND '
        'has_prefix(resource_url,"https://compute.googleapis.com/compute/v1/'
        'projects/fake-project/global/images/my-image/id/123")'
        )

    make_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_requests_patcher.stop)
    self.make_requests = make_requests_patcher.start()
    self.make_requests.side_effect = iter([[self._MakeImage('my-image', 123)]])
    self.Run('compute images packages list --image my-image')

    self.AssertOutputEquals("""\
PACKAGE VERSION REVISION
package_bar 1.15 1+deb9u1
package_bar 1.16 1+deb9u1
package_foo 2.7.6.1 2
package_foo 2.7.6.2 3
package_foo 2.7.6.2 4
""", normalize_space=True)
