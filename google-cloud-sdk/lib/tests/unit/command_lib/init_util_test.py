# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for googlecloudsdk.command_lib.init_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.api_lib.resource_manager import operations
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib import init_util
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case

from mock import call


class PickProjectTestsBase(sdk_test_base.WithLogCapture, test_case.WithInput):
  _PROJECT_IDS = ['foo', 'bar', 'baz']

  def SetUp(self):
    self.messages = apis.GetMessagesModule('cloudresourcemanager', 'v1')
    self.create_projects_mock = self.StartObjectPatch(projects_api, 'Create')
    self.get_operation_mock = self.StartObjectPatch(operations, 'GetOperation')

  def GetCreateProjectOperation(self, project_id):
    operation_name = 'pc.1234'
    proj = self.messages.Project(projectId=project_id)
    return self.messages.Operation(
        name='operations/' + operation_name,
        done=True,
        response=operations.ToOperationResponse(proj))

  def SetProjectToCreate(self, project_id):
    op = self.GetCreateProjectOperation(project_id)
    self.get_operation_mock.return_value = op
    self.create_projects_mock.return_value = op

  def SetupFailedProjectCreate(self, project_id):
    op = self.GetCreateProjectOperation(project_id)
    self.get_operation_mock.return_value = op
    self.create_projects_mock.return_value = op
    status = self.messages.Status(code=7, message='Something Bad Happened')
    op.error = status


class PickProjectTests(PickProjectTestsBase):

  def SetUp(self):
    PickProjectTestsBase.SetUp(self)
    projects = [self.messages.Project(projectId=i) for i in self._PROJECT_IDS]
    self.list_projects_mock = self.StartObjectPatch(projects_api, 'List',
                                                    return_value=iter(projects))

  def testPickProject_Preselected(self):
    """Should accept preselected value, since it's in the list."""
    self.assertEqual(init_util.PickProject('foo'), 'foo')

  def testPickProject_PreselectedButNotAvailable(self):
    """Should return None, since preselected value is not in the list."""
    self.WriteInput('n')
    self.assertEqual(init_util.PickProject('qux'), None)
    self.AssertErrContains(
        '{"ux": "PROMPT_CONTINUE", "message": "[qux] is not one of your '
        'projects [bar,baz,foo]. ", "prompt_string": "Would you like to create '
        'it?"}')

  def testPickProject_PreselectedListingProjectsFails(self):
    """Should take preselected value (without validating it)."""
    self.list_projects_mock.side_effect = RuntimeError('blah')
    self.WriteInput('qux')

    self.assertEqual(init_util.PickProject(), 'qux')
    self.AssertErrEquals(
        'WARNING: Listing available projects failed: blah\n'
        '{"ux": "PROMPT_RESPONSE", "message": "Enter project id you would like '
        'to use: "}',
        normalize_space=True)

  def testPickProject(self):
    """Should pick the corresponding project."""
    self.WriteInput('2')

    self.assertEqual(init_util.PickProject(), 'baz')
    # Output is sorted lexicographically
    self.AssertErrEquals(
        '{"ux": "PROMPT_CHOICE", "message": "Pick cloud project to use: ", '
        '"choices": ["bar", "baz", "foo", "Create a new project"]}\n')

  def testPickProject_FreeformInput(self):
    """Should accept free-form input, since it's in the list."""
    self.WriteInput('bar')

    self.assertEqual(init_util.PickProject(), 'bar')
    self.AssertErrEquals(
        '{"ux": "PROMPT_CHOICE", "message": "Pick cloud project to use: ", '
        '"choices": ["bar", "baz", "foo", "Create a new project"]}\n')

  def testPickProject_BadInput(self):
    """Should return None and show another prompt."""
    self.WriteInput('5')

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        '{"ux": "PROMPT_CHOICE", "message": "Pick cloud project to use: ", '
        '"choices": ["bar", "baz", "foo", "Create a new project"]}\n')

  def testPickProject_BadFreeformInput(self):
    """Should return None and show another prompt."""
    self.WriteInput('qux')

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        '{"ux": "PROMPT_CHOICE", "message": "Pick cloud project to use: ", '
        '"choices": ["bar", "baz", "foo", "Create a new project"]}\n')

  def testPickProject_NoInput(self):
    """Should pick the corresponding project."""
    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        '{"ux": "PROMPT_CHOICE", "message": "Pick cloud project to use: ", '
        '"choices": ["bar", "baz", "foo", "Create a new project"]}\n')

  def testPickProject_CreateProject(self):
    """Should pick the corresponding project."""
    self.SetProjectToCreate('new-project')
    self.WriteInput('4\nnew-project')

    self.assertEqual(init_util.PickProject(), 'new-project')
    self.AssertErrContains(
        '{"ux": "PROMPT_CHOICE", "message": "Pick cloud project to use: ", '
        '"choices": ["bar", "baz", "foo", "Create a new project"]}\n'
        '{"ux": "PROMPT_RESPONSE", "message": "Enter a Project ID. Note that a '
        'Project ID CANNOT be changed later.\\nProject IDs must be 6-30 '
        'characters (lowercase ASCII, digits, or\\nhyphens) in length and '
        'start with a lowercase letter. "}',
        normalize_space=True)
    self.create_projects_mock.assert_called_once_with(
        resources.REGISTRY.Create(
            'cloudresourcemanager.projects', projectId='new-project'))

  def testPickProject_CreateProjectNoInput(self):
    """Should pick the corresponding project."""
    self.WriteInput('4')

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        '{"ux": "PROMPT_CHOICE", "message": "Pick cloud project to use: ", '
        '"choices": ["bar", "baz", "foo", "Create a new project"]}\n'
        '{"ux": "PROMPT_RESPONSE", "message": "Enter a Project ID. Note that a '
        'Project ID CANNOT be changed later.\\nProject IDs must be 6-30 '
        'characters (lowercase ASCII, digits, or\\nhyphens) in length and '
        'start with a lowercase letter. "}',
        normalize_space=True)
    self.create_projects_mock.assert_not_called()

  def testPickProject_CreateProjectFails(self):
    """Should return None because project creation fails."""
    self.create_projects_mock.side_effect = RuntimeError('blah')
    self.WriteInput('4\nnew-project')

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        """\
        {"ux": "PROMPT_CHOICE", "message": "Pick cloud project to use: ", \
        "choices": ["bar", "baz", "foo", "Create a new project"]}
        {"ux": "PROMPT_RESPONSE", "message": "Enter a Project ID. Note that a \
        Project ID CANNOT be changed later.\\nProject IDs must be 6-30 \
        characters (lowercase ASCII, digits, or\\nhyphens) in length and start \
        with a lowercase letter. "}WARNING: Project creation failed: blah
        Please make sure to create the project [new-project] using
            $ gcloud projects create new-project
        or change to another project using
            $ gcloud config set project <PROJECT ID>
        """,
        normalize_space=True)
    self.create_projects_mock.assert_called_once_with(
        resources.REGISTRY.Create('cloudresourcemanager.projects',
                                  projectId='new-project'))

  def testPickProject_CreateProjectFailsAsynchronously(self):
    """Should pick the corresponding project."""
    self.SetupFailedProjectCreate('new-project')
    self.WriteInput('4\nnew-project')

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrContains(
        'Operation [pc.1234] failed: 7: Something Bad Happened',
        normalize_space=True)
    self.create_projects_mock.assert_called_once_with(
        resources.REGISTRY.Create(
            'cloudresourcemanager.projects', projectId='new-project'))

  def testPickProject_OneProject(self):
    projects = [self.messages.Project(projectId='spam')]
    self.list_projects_mock.return_value = iter(projects)
    self.WriteInput('1')

    self.assertEqual(init_util.PickProject(), 'spam')
    self.AssertErrEquals(
        '{"ux": "PROMPT_CHOICE", "message": "Pick cloud project to use: ", '
        '"choices": ["spam", "Create a new project"]}\n')

  def testPickProject_NoProjects(self):
    """Should return None because an empty project ID was given."""
    self.list_projects_mock.return_value = iter([])

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        '{"ux": "PROMPT_CONTINUE", "message": "This account has no projects.", '
        '"prompt_string": "Would you like to create one?"}\n'
        '{"ux": "PROMPT_RESPONSE", "message": "Enter a Project ID. Note that a '
        'Project ID CANNOT be changed later.\\nProject IDs must be 6-30 '
        'characters (lowercase ASCII, digits, or\\nhyphens) in length and '
        'start with a lowercase letter. "}',
        normalize_space=True)

  def testPickProject_NoProjectsDoNotCreate(self):
    self.WriteInput('n')
    self.list_projects_mock.return_value = iter([])

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        '{"ux": "PROMPT_CONTINUE", "message": "This account has no projects.", '
        '"prompt_string": "Would you like to create one?"}\n')

  def testPickProject_NoProjectsCreateAProject(self):
    self.SetProjectToCreate('qux')
    self.WriteInput('y\nqux')
    self.list_projects_mock.return_value = iter([])

    self.assertEqual(init_util.PickProject(), 'qux')
    self.AssertErrContains(
        '{"ux": "PROMPT_CONTINUE", "message": "This account has no projects.", '
        '"prompt_string": "Would you like to create one?"}\n'
        '{"ux": "PROMPT_RESPONSE", "message": "Enter a Project ID. Note that a '
        'Project ID CANNOT be changed later.\\nProject IDs must be 6-30 '
        'characters (lowercase ASCII, digits, or\\nhyphens) in length and '
        'start with a lowercase letter. "}',
        normalize_space=True)
    self.create_projects_mock.assert_called_once_with(
        resources.REGISTRY.Create('cloudresourcemanager.projects',
                                  projectId='qux'))

  def testPickProject_ListingProjectsFails(self):
    """Should take free-form input (without validating it)."""
    self.list_projects_mock.side_effect = RuntimeError('blah')
    self.WriteInput('qux')

    self.assertEqual(init_util.PickProject(), 'qux')
    self.AssertErrEquals(
        'WARNING: Listing available projects failed: blah\n'
        '{"ux": "PROMPT_RESPONSE", "message": "Enter project id you would '
        'like to use: "}',
        normalize_space=True)

  def testPickProject_ListingProjectsFailsNoInput(self):
    """Should return None."""
    self.list_projects_mock.side_effect = RuntimeError('blah')

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        'WARNING: Listing available projects failed: blah\n'
        '{"ux": "PROMPT_RESPONSE", "message": "Enter project id you would like '
        'to use: "}',
        normalize_space=True)


class PickProjectTestsLimitExceeded(PickProjectTestsBase):
  """Tests for when a user has more projects than _PROJECT_LIST_LIMIT.

  The project list limit changes how users select their projects in PickProject
  when they have exceeded a certain number of projects, as listing them all can
  be very slow.
  """

  def SetUp(self):
    PickProjectTestsBase.SetUp(self)
    projects = [self.messages.Project(projectId=i) for i in self._PROJECT_IDS]
    # List will at most be called twice and since during each call the iterator
    # is exhausted, the return value has to be instantiated twice and set as a
    # side effect.
    self.list_projects_mock = self.StartObjectPatch(
        projects_api, 'List', side_effect=[iter(projects), iter(projects)])
    self.StartPatch('googlecloudsdk.command_lib.init_util._PROJECT_LIST_LIMIT',
                    2)

  def testPickProject_Preselected(self):
    get_projects_mock = self.StartObjectPatch(projects_api, 'Get')
    self.StartObjectPatch(projects_util, 'IsActive', return_value=True)

    self.assertEqual(init_util.PickProject('qux'), 'qux')
    get_projects_mock.assert_called_once_with(
        resources.REGISTRY.Create('cloudresourcemanager.projects',
                                  projectId='qux'))

  def testPickProject_EnterProjectId(self):
    get_projects_mock = self.StartObjectPatch(projects_api, 'Get')
    self.StartObjectPatch(projects_util, 'IsActive', side_effect=[False, True])

    self.WriteInput('1\nxuq\nqux')
    self.assertEqual(init_util.PickProject(), 'qux')
    self.AssertErrContains(
        '{"ux": "PROMPT_CHOICE", "message": "This account has a lot of '
        'projects! Listing them all can take a while.", "choices": '
        '["Enter a project ID", "Create a new project", "List projects"]}')
    self.AssertErrContains('Project ID does not exist or is not active. Please '
                           'enter an existing and active Project ID.')
    self.AssertErrContains('Enter an existing project id you would like to '
                           'use:')
    get_projects_mock.assert_has_calls([
        call(resources.REGISTRY.Create('cloudresourcemanager.projects',
                                       projectId='xuq')),
        call(resources.REGISTRY.Create('cloudresourcemanager.projects',
                                       projectId='qux'))])

  def testPickProject_CreateProject(self):
    self.SetProjectToCreate('qux')

    self.WriteInput('2\nqux')
    self.assertEqual(init_util.PickProject(), 'qux')
    self.AssertErrContains(
        '{"ux": "PROMPT_CHOICE", "message": "This account has a lot of '
        'projects! Listing them all can take a while.", "choices": '
        '["Enter a project ID", "Create a new project", "List projects"]}')
    self.create_projects_mock.assert_called_once_with(
        resources.REGISTRY.Create('cloudresourcemanager.projects',
                                  projectId='qux'))

  def testPickProject_ListProjects(self):
    self.WriteInput('3\n1')
    self.assertEqual(init_util.PickProject(), 'bar')
    self.AssertErrContains(
        '{"ux": "PROMPT_CHOICE", "message": "This account has a lot of '
        'projects! Listing them all can take a while.", "choices": '
        '["Enter a project ID", "Create a new project", "List projects"]}')
    self.AssertErrContains('{"ux": "PROMPT_CHOICE", "message": "Pick cloud '
                           'project to use: ", "choices": ["bar", "baz", '
                           '"foo", "Create a new project"]}')


if __name__ == '__main__':
  test_case.main()
