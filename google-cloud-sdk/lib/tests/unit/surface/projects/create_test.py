# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Tests for projects create."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.resource_manager import operations
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util


class ProjectsCreateTest(base.ProjectsUnitTestBase):

  def SetUp(self):
    self.sm_messages = core_apis.GetMessagesModule('servicemanagement', 'v1')
    self.mocked_sm_client = mock.Client(
        core_apis.GetClientClass('servicemanagement', 'v1'),
        real_client=core_apis.GetClientInstance('servicemanagement',
                                                'v1',
                                                no_http=True))
    self.mocked_sm_client.Mock()
    self.addCleanup(self.mocked_sm_client.Unmock)

  def _expectCreationCall(self, test_project, labels=None, exception=None):
    operation_name = 'pc.1234'
    labels_message = labels_util.Diff(additions=labels).Apply(
        self.messages.Project.LabelsValue).GetOrNone()
    if exception:
      response = None
    else:
      response = self.messages.Operation(name='operations/' + operation_name)
    self.mock_client.projects.Create.Expect(
        self.messages.Project(
            projectId=test_project.projectId,
            name=test_project.name,
            parent=test_project.parent,
            labels=labels_message),
        exception=exception,
        response=response)
    if not exception:
      self.mock_client.operations.Get.Expect(
          request=self.messages.CloudresourcemanagerOperationsGetRequest(
              operationsId=operation_name),
          response=self.messages.Operation(
              name='operations/' + operation_name,
              done=True,
              response=operations.ToOperationResponse(test_project)))

  def _expectServiceEnableCall(self, project_id):
    operation_name = 'operation-12345'
    self.mocked_sm_client.services.Enable.Expect(
        request=self.sm_messages.ServicemanagementServicesEnableRequest(
            serviceName='cloudapis.googleapis.com',
            enableServiceRequest=self.sm_messages.EnableServiceRequest(
                consumerId='project:' + project_id
            )
        ),
        response=self.sm_messages.Operation(
            name=operation_name,
            done=False,
        )
    )

    self.mocked_sm_client.operations.Get.Expect(
        request=self.sm_messages.ServicemanagementOperationsGetRequest(
            operationsId=operation_name,
        ),
        response=self.sm_messages.Operation(
            name=operation_name,
            done=True,
            response=None,
        )
    )

  _CREATE_STDERR_FMT = (
      """Create in progress for """
      """[https://cloudresourcemanager.googleapis.com/v1/projects/{}].
<START PROGRESS TRACKER>Waiting for [operations/pc.1234] to finish
<END PROGRESS TRACKER>SUCCESS
""")

  _MISSING_ID_STDERR = ("""ERROR: (gcloud.projects.create) """
                        """Missing required argument [PROJECT_ID]: """
                        """an id must be provided for the new project
""")

  def createValidProjectHelper(self, run):
    test_project = util.GetTestActiveProjectWithSameNameAndId()
    self._expectCreationCall(test_project)
    self._expectServiceEnableCall(test_project.projectId)
    response = run('create', test_project.projectId, '--format=disable')
    self.assertEqual(response, test_project)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        ProjectsCreateTest._CREATE_STDERR_FMT.format(test_project.projectId))

  def testCreateValidProject(self):
    self.createValidProjectHelper(self.RunProjects)

  def testCreateValidProjectAlpha(self):
    self.createValidProjectHelper(self.RunProjectsAlpha)

  def testCreateValidProjectOutput(self):
    test_project = util.GetTestActiveProjectWithSameNameAndId()
    self._expectCreationCall(test_project)
    self._expectServiceEnableCall(test_project.projectId)
    self.RunProjects('create', test_project.projectId)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        ProjectsCreateTest._CREATE_STDERR_FMT.format(test_project.projectId))

  def testCreateValidProjectWithName(self):
    test_project = util.GetTestActiveProject()
    self._expectCreationCall(test_project)
    self._expectServiceEnableCall(test_project.projectId)
    response = self.RunProjects('create', test_project.projectId, '--name',
                                test_project.name, '--format=disable')
    self.assertEqual(response, test_project)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        ProjectsCreateTest._CREATE_STDERR_FMT.format('feisty-catcher-644'))

  def testCreateValidProjectWithNameOutput(self):
    test_project = util.GetTestActiveProject()
    self._expectCreationCall(test_project)
    self._expectServiceEnableCall(test_project.projectId)
    self.RunProjects('create', test_project.projectId, '--name',
                     test_project.name)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        ProjectsCreateTest._CREATE_STDERR_FMT.format('feisty-catcher-644'))

  def testCreateProjectWithoutId(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [PROJECT_ID]: an id must be provided for '
        'the new project'):
      self.RunProjects('create')
    self.AssertOutputEquals('')

  def testCreateProjectWithIdPromptFromName(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [PROJECT_ID]: an id must be provided for '
        'the new project'):
      self.RunProjects('create', '--name', 'foobar')
    self.AssertOutputEquals('')
    self.AssertErrContains('as project id (Y/n)?')
    # we don't know the exact project id prompted, since this changes by date

  def testCreateProjectWithRejectedIdPromptFromLongName(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [PROJECT_ID]: an id must be provided for '
        'the new project'):
      self.RunProjects('create', '--name', 'foo1234567890123456789012345')
    self.AssertOutputEquals('')
    self.AssertErrContains("""No project id provided.

Use [foo1234567890123456789012345] as project id (Y/n)?""")
    # the very long name means we do know the exact project id prompted

  def testCreateProjectWithAcceptedIdPromptFromLongName(self):
    test_project = util.GetTestProjectWithLongNameAndMatchingId()
    self.WriteInput('y\n')
    self._expectCreationCall(test_project)
    self._expectServiceEnableCall(test_project.projectId)
    self.RunProjects('create', '--name', test_project.name)
    self.AssertOutputEquals('')
    self.AssertErrEquals("""No project id provided.

Use [{}] as project id (Y/n)?  """
                         """
Create in progress for [https://cloudresourcemanager.googleapis.com"""
                         """/v1/projects/abcdefghijklmnopqrstuvwxyz].
<START PROGRESS TRACKER>Waiting for [operations/pc.1234] to finish
<END PROGRESS TRACKER>SUCCESS
""".format(test_project.projectId))

  def createProjectWithBothFolderAndOrganizationSpecifiedHelper(
      self, run, name):
    test_project = util.GetTestActiveProject()
    with self.AssertRaisesExceptionMatches(
        exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: --folder, --organization'):
      run('create', test_project.projectId, '--folder', '12345',
          '--organization', '2048')
    self.AssertOutputEquals('')

  def testCreateProjectWithBothFolderAndOrganizationSpecified(self):
    self.createProjectWithBothFolderAndOrganizationSpecifiedHelper(
        self.RunProjects, 'gcloud.projects.create')

  def testCreateProjectWithBothFolderAndOrganizationSpecifiedAlpha(self):
    self.createProjectWithBothFolderAndOrganizationSpecifiedHelper(
        self.RunProjectsAlpha, 'gcloud.alpha.projects.create')

  def createValidProjectWithFolderParentHelper(self, run):
    test_project = util.GetTestActiveProjectWithFolderParent()
    self._expectCreationCall(test_project)
    self._expectServiceEnableCall(test_project.projectId)
    response = run('create', test_project.projectId, '--folder', '12345',
                   '--format=disable')
    self.assertEqual(response, test_project)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        ProjectsCreateTest._CREATE_STDERR_FMT.format(test_project.projectId))

  def testCreateValidProjectWithFolderParent(self):
    self.createValidProjectWithFolderParentHelper(self.RunProjects)

  def testCreateValidProjectWithFolderParentAlpha(self):
    self.createValidProjectWithFolderParentHelper(self.RunProjectsAlpha)

  def testCreateValidProjectWithFolderParentOutput(self):
    test_project = util.GetTestActiveProjectWithFolderParent()
    self._expectCreationCall(test_project)
    self._expectServiceEnableCall(test_project.projectId)
    self.RunProjectsAlpha('create', test_project.projectId, '--folder', '12345')
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        ProjectsCreateTest._CREATE_STDERR_FMT.format(test_project.projectId))

  def testCreateValidProjectWithOrganizationParent(self):
    test_project = util.GetTestActiveProjectWithOrganizationParent()
    self._expectCreationCall(test_project)
    self._expectServiceEnableCall(test_project.projectId)
    response = self.RunProjects('create', test_project.projectId,
                                '--organization', '2048', '--format=disable')
    self.assertEqual(response, test_project)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        ProjectsCreateTest._CREATE_STDERR_FMT.format(test_project.projectId))

  def testCreateValidProjectWithOrganizationParentOutput(self):
    test_project = util.GetTestActiveProjectWithOrganizationParent()
    self._expectCreationCall(test_project)
    self._expectServiceEnableCall(test_project.projectId)
    self.RunProjects('create', test_project.projectId, '--organization', '2048')
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        ProjectsCreateTest._CREATE_STDERR_FMT.format(test_project.projectId))

  def testCreateValidProjectWithLabels(self):
    labels = {'key1': 'value1', 'key2': 'value2'}
    test_project = util.GetTestActiveProjectWithLabels(labels)
    self._expectCreationCall(test_project, labels=labels)
    self._expectServiceEnableCall(test_project.projectId)
    response = self.RunProjects('create', test_project.projectId, '--labels',
                                util.GetLabelsFlagValue(labels),
                                '--format=disable')
    self.assertProjectsEqual(response, test_project)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        ProjectsCreateTest._CREATE_STDERR_FMT.format(test_project.projectId))

  def createValidProjectWithLabelsOutputHelper(self, run):
    labels = {'key1': 'value1', 'key2': 'value2'}
    test_project = util.GetTestActiveProjectWithLabels(labels)
    self._expectCreationCall(test_project, labels)
    self._expectServiceEnableCall(test_project.projectId)
    run('create', test_project.projectId, '--labels',
        util.GetLabelsFlagValue(labels))
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        ProjectsCreateTest._CREATE_STDERR_FMT.format(test_project.projectId))

  def testCreateValidProjectWithLabelsOutput(self):
    self.createValidProjectWithLabelsOutputHelper(self.RunProjects)

  def testCreateValidProjectWithLabelsOutputAlpha(self):
    self.createValidProjectWithLabelsOutputHelper(self.RunProjectsAlpha)

  def testCreateProjectAlreadyExists(self):
    exception = http_error.MakeHttpError(code=409)
    test_project = util.GetTestActiveProjectWithSameNameAndId()
    self._expectCreationCall(test_project, exception=exception)
    regexp = (r'Project creation failed. The project ID you specified is '
              'already in use by another project. Please try an alternative '
              'ID.')
    with self.assertRaisesRegex(exceptions.HttpException, regexp):
      self.RunProjects('create', test_project.projectId)
    self.AssertOutputEquals('')

  def testCreateProjectFails(self):
    exception = http_error.MakeHttpError(code=403)
    test_project = util.GetTestActiveProjectWithSameNameAndId()
    self._expectCreationCall(test_project, exception=exception)
    with self.assertRaises(exceptions.HttpException):
      self.RunProjects('create', test_project.projectId)
    self.AssertOutputEquals('')

  def assertProjectsEqual(self, expected, actual):
    # Labels have no ordering guarantee.
    expected_labels = {}
    for prop in expected.labels.additionalProperties:
      expected_labels[prop.key] = prop.value
    expected_labels_ref = expected.labels
    expected.labels = None

    actual_labels = {}
    for prop in actual.labels.additionalProperties:
      actual_labels[prop.key] = prop.value
    actual_labels_ref = actual.labels
    actual.labels = None

    self.assertEqual(expected_labels, actual_labels)
    self.assertEqual(expected, actual)

    expected.labels = expected_labels_ref
    actual.labels = actual_labels_ref

  def _prepareEmptyConfigAndExpectProjectCreation(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root',
                            return_value=self.temp_path)
    prop = properties.FromString('core/project')
    self.assertEqual(prop.Get(), None)
    test_project = util.GetTestActiveProjectWithSameNameAndId()
    self._expectCreationCall(test_project)
    self._expectServiceEnableCall(test_project.projectId)
    return prop, test_project.projectId

  def testNoProjectChangeWithoutSetDefault(self):
    prop, project_id = self._prepareEmptyConfigAndExpectProjectCreation()
    self.RunProjects('create', project_id)
    self.assertEqual(prop.Get(), None)
    self.AssertOutputEquals('')

  def testProjectChangedWithSetDefault(self):
    prop, project_id = self._prepareEmptyConfigAndExpectProjectCreation()
    self.RunProjects('create', project_id, '--set-as-default')
    self.assertEqual(prop.Get(), project_id)
    self.AssertOutputEquals('')

  def testProjectChangedWithNoSetDefault(self):
    prop, project_id = self._prepareEmptyConfigAndExpectProjectCreation()
    self.RunProjects('create', project_id, '--no-set-as-default')
    self.assertEqual(prop.Get(), None)
    self.AssertOutputEquals('')


if __name__ == '__main__':
  test_case.main()
