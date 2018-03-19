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
"""Tests that exercise build cancelation."""

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error


class CancelTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def mockedNow(self, tzinfo=None):
    return times.ParseDateTime('2016-05-26T00:05:00.000000Z', tzinfo=tzinfo)

  def SetUp(self):
    self.mocked_cloudbuild_v1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)

    properties.VALUES.core.project.Set('my-project')

    self.cloudbuild_v1_messages = core_apis.GetMessagesModule(
        'cloudbuild', 'v1')

    self._statuses = self.cloudbuild_v1_messages.Build.StatusValueValuesEnum

    self.times_now = times.Now
    times.Now = self.mockedNow

  def TearDown(self):
    times.Now = self.times_now

  def _Run(self, args):
    self.Run(['alpha']+args)

  def testCancelSuccess(self):
    self.mocked_cloudbuild_v1.projects_builds.Cancel.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCancelRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Build(
            createTime='2016-03-31T19:12:32.838111Z',
            finishTime='2016-03-31T19:13:23.397232Z',
            id='123-456-789',
            images=['image1'],
            projectId='my-project',
            source=self.cloudbuild_v1_messages.Source(
                storageSource=self.cloudbuild_v1_messages.StorageSource(
                    bucket='some-bucket',
                    object='object.tgz',
                )),
            startTime='2016-03-31T19:12:34.971501Z',
            status=self._statuses.CANCELLED,
            steps=[
                self.cloudbuild_v1_messages.BuildStep(
                    name='name1',
                    args=['arg1', 'arg2'],
                    env=['env1', 'env2'],
                ),
                self.cloudbuild_v1_messages.BuildStep(
                    name='name2',
                    args=['arg1', 'arg2'],
                    env=['env1', 'env2'],
                ),
                self.cloudbuild_v1_messages.BuildStep(
                    name='name3',
                    args=['arg1', 'arg2'],
                ),
            ],
            timeout='600.000s'))

    self._Run(['container', 'builds', 'cancel', '123-456-789'])
    self.AssertErrContains("""\
Cancelled [https://cloudbuild.googleapis.com/v1/projects/my-project/builds/123-456-789].
""", normalize_space=True)
    self.AssertOutputContains("""\
status: CANCELLED
""", normalize_space=True)

  def testCancelMultipleSuccess(self):
    self.mocked_cloudbuild_v1.projects_builds.Cancel.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCancelRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Build(
            createTime='2016-03-31T19:12:32.838111Z',
            finishTime='2016-03-31T19:13:23.397232Z',
            id='123-456-789',
            images=['image1'],
            projectId='my-project',
            source=self.cloudbuild_v1_messages.Source(
                storageSource=self.cloudbuild_v1_messages.StorageSource(
                    bucket='some-bucket',
                    object='object.tgz',
                )),
            startTime='2016-03-31T19:12:34.971501Z',
            status=self._statuses.CANCELLED,
            steps=[
                self.cloudbuild_v1_messages.BuildStep(
                    name='name1',
                    args=['arg1', 'arg2'],
                    env=['env1', 'env2'],
                ),
                self.cloudbuild_v1_messages.BuildStep(
                    name='name2',
                    args=['arg1', 'arg2'],
                    env=['env1', 'env2'],
                ),
                self.cloudbuild_v1_messages.BuildStep(
                    name='name3',
                    args=['arg1', 'arg2'],
                ),
            ],
            timeout='600.000s'))
    self.mocked_cloudbuild_v1.projects_builds.Cancel.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCancelRequest(
            id='987-654-321',
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Build(
            createTime='2016-03-31T19:12:32.838111Z',
            finishTime='2016-03-31T19:13:23.397232Z',
            id='987-654-321',
            images=['image1'],
            projectId='my-project',
            source=self.cloudbuild_v1_messages.Source(
                storageSource=self.cloudbuild_v1_messages.StorageSource(
                    bucket='some-bucket',
                    object='object.tgz',
                )),
            startTime='2016-03-31T19:12:34.971501Z',
            status=self._statuses.CANCELLED,
            steps=[
                self.cloudbuild_v1_messages.BuildStep(
                    name='name1',
                    args=['arg1', 'arg2'],
                    env=['env1', 'env2'],
                ),
                self.cloudbuild_v1_messages.BuildStep(
                    name='name2',
                    args=['arg1', 'arg2'],
                    env=['env1', 'env2'],
                ),
                self.cloudbuild_v1_messages.BuildStep(
                    name='name3',
                    args=['arg1', 'arg2'],
                ),
            ],
            timeout='600.000s'))

    self._Run(['container', 'builds', 'cancel', '123-456-789', '987-654-321'])
    self.AssertErrContains("""\
Cancelled [https://cloudbuild.googleapis.com/v1/projects/my-project/builds/123-456-789].
""", normalize_space=True)
    self.AssertErrContains("""\
Cancelled [https://cloudbuild.googleapis.com/v1/projects/my-project/builds/987-654-321].
""", normalize_space=True)

  def testCancelAlreadyFinished(self):
    self.mocked_cloudbuild_v1.projects_builds.Cancel.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCancelRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        exception=http_error.MakeHttpError(code=400, message='Invalid argument')
    )

    with self.assertRaisesRegexp(
        exceptions.HttpException, 'Invalid argument'):
      self._Run(['container', 'builds', 'cancel', '123-456-789'])

  def testCancelNotFound(self):
    self.mocked_cloudbuild_v1.projects_builds.Cancel.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCancelRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        exception=http_error.MakeHttpError(code=404)
    )

    with self.assertRaisesRegexp(
        exceptions.HttpException, 'Resource not found'):
      self._Run(['container', 'builds', 'cancel', '123-456-789'])


if __name__ == '__main__':
  test_case.main()
