# Copyright 2017 Google Inc. All Rights Reserved.
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
from __future__ import unicode_literals
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib import init_util
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case

from mock import call


class PickProjectTests(sdk_test_base.WithLogCapture, test_case.WithInput):

  _PROJECT_IDS = ['foo', 'bar', 'baz']

  def SetUp(self):
    self.messages = apis.GetMessagesModule('cloudresourcemanager', 'v1')
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
    self.AssertErrEquals(
        '[qux] is not one of your projects [bar,baz,foo].\n\n'
        'Would you like to create it? (Y/n)?\n', normalize_space=True)

  def testPickProject_PreselectedListingProjectsFails(self):
    """Should take preselected value (without validating it)."""
    self.list_projects_mock.side_effect = RuntimeError('blah')
    self.WriteInput('qux')

    self.assertEqual(init_util.PickProject(), 'qux')
    self.AssertErrEquals(
        'WARNING: Listing available projects failed: blah\n'
        'Enter project id you would like to use:',
        normalize_space=True)

  def testPickProject(self):
    """Should pick the corresponding project."""
    self.WriteInput('2')

    self.assertEqual(init_util.PickProject(), 'baz')
    # Output is sorted lexicographically
    self.AssertErrEquals("""\
        Pick cloud project to use:
         [1] bar
         [2] baz
         [3] foo
         [4] Create a new project
        Please enter numeric choice or text value (must exactly match list item):
        """, normalize_space=True)

  def testPickProject_FreeformInput(self):
    """Should accept free-form input, since it's in the list."""
    self.WriteInput('bar')

    self.assertEqual(init_util.PickProject(), 'bar')
    self.AssertErrEquals("""\
        Pick cloud project to use:
         [1] bar
         [2] baz
         [3] foo
         [4] Create a new project
        Please enter numeric choice or text value (must exactly match list item):
        """, normalize_space=True)

  def testPickProject_BadInput(self):
    """Should return None and show another prompt."""
    self.WriteInput('5')

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals("""\
        Pick cloud project to use:
         [1] bar
         [2] baz
         [3] foo
         [4] Create a new project
        Please enter numeric choice or text value (must exactly match list item): \
        Please enter a value between 1 and 4, or a value present in the list:
        """, normalize_space=True)

  def testPickProject_BadFreeformInput(self):
    """Should return None and show another prompt."""
    self.WriteInput('qux')

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals("""\
        Pick cloud project to use:
         [1] bar
         [2] baz
         [3] foo
         [4] Create a new project
        Please enter numeric choice or text value (must exactly match list item): \
        Please enter a value between 1 and 4, or a value present in the list:
        """, normalize_space=True)

  def testPickProject_NoInput(self):
    """Should pick the corresponding project."""
    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals("""\
        Pick cloud project to use:
         [1] bar
         [2] baz
         [3] foo
         [4] Create a new project
        Please enter numeric choice or text value (must exactly match list item):
        """, normalize_space=True)

  def testPickProject_CreateProject(self):
    """Should pick the corresponding project."""
    create_projects_mock = self.StartObjectPatch(projects_api, 'Create')
    self.WriteInput('4\nnew-project')

    self.assertEqual(init_util.PickProject(), 'new-project')
    self.AssertErrEquals(
        """\
        Pick cloud project to use:
         [1] bar
         [2] baz
         [3] foo
         [4] Create a new project
        Please enter numeric choice or text value (must exactly match list \
        item):
        Enter a Project ID. Note that a Project ID CANNOT be changed later.
        Project IDs must be 6-30 characters (lowercase ASCII, digits, or
        hyphens) in length and start with a lowercase letter.""",
        normalize_space=True)
    create_projects_mock.assert_called_once_with(
        resources.REGISTRY.Create('cloudresourcemanager.projects',
                                  projectId='new-project'))

  def testPickProject_CreateProjectNoInput(self):
    """Should pick the corresponding project."""
    create_projects_mock = self.StartObjectPatch(projects_api, 'Create')
    self.WriteInput('4')

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        """\
        Pick cloud project to use:
         [1] bar
         [2] baz
         [3] foo
         [4] Create a new project
        Please enter numeric choice or text value (must exactly match list \
        item):
        Enter a Project ID. Note that a Project ID CANNOT be changed later.
        Project IDs must be 6-30 characters (lowercase ASCII, digits, or
        hyphens) in length and start with a lowercase letter.""",
        normalize_space=True)
    create_projects_mock.assert_not_called()

  def testPickProject_CreateProjectFails(self):
    """Should pick the corresponding project."""
    create_projects_mock = self.StartObjectPatch(
        projects_api, 'Create', side_effect=RuntimeError('blah'))
    self.WriteInput('4\nnew-project')

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        """\
        Pick cloud project to use:
         [1] bar
         [2] baz
         [3] foo
         [4] Create a new project
        Please enter numeric choice or text value (must exactly match list \
        item):
        Enter a Project ID. Note that a Project ID CANNOT be changed later.
        Project IDs must be 6-30 characters (lowercase ASCII, digits, or
        hyphens) in length and start with a lowercase letter. \
        WARNING: Project creation failed: blah
        Please make sure to create the project [new-project] using
            $ gcloud projects create new-project
        or change to another project using
            $ gcloud config set project <PROJECT ID>
        """,
        normalize_space=True)
    create_projects_mock.assert_called_once_with(
        resources.REGISTRY.Create('cloudresourcemanager.projects',
                                  projectId='new-project'))

  def testPickProject_OneProject(self):
    projects = [self.messages.Project(projectId='spam')]
    self.list_projects_mock.return_value = iter(projects)
    self.WriteInput('1')

    self.assertEqual(init_util.PickProject(), 'spam')
    self.AssertErrEquals(
        'Pick cloud project to use:\n'
        ' [1] spam\n'
        ' [2] Create a new project\n'
        'Please enter numeric choice or text value (must exactly match list '
        'item):\n',
        normalize_space=True)

  def testPickProject_NoProjects(self):
    """Should return None because an empty project ID was given."""
    self.list_projects_mock.return_value = iter([])

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        'This account has no projects.\n\n'
        'Would you like to create one? (Y/n)?\n'
        'Enter a Project ID. Note that a Project ID CANNOT be changed later. \n'
        'Project IDs must be 6-30 characters (lowercase ASCII, digits, or \n'
        'hyphens) in length and start with a lowercase letter.',
        normalize_space=True)

  def testPickProject_NoProjectsDoNotCreate(self):
    self.WriteInput('n')
    self.list_projects_mock.return_value = iter([])

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        'This account has no projects.\n\n'
        'Would you like to create one? (Y/n)?\n',
        normalize_space=True)

  def testPickProject_NoProjectsCreateAProject(self):
    create_projects_mock = self.StartObjectPatch(projects_api, 'Create')
    self.WriteInput('y\nqux')
    self.list_projects_mock.return_value = iter([])

    self.assertEqual(init_util.PickProject(), 'qux')
    self.AssertErrEquals(
        'This account has no projects.\n\n'
        'Would you like to create one? (Y/n)?\n'
        'Enter a Project ID. Note that a Project ID CANNOT be changed later. \n'
        'Project IDs must be 6-30 characters (lowercase ASCII, digits, or \n'
        'hyphens) in length and start with a lowercase letter.',
        normalize_space=True)
    create_projects_mock.assert_called_once_with(
        resources.REGISTRY.Create('cloudresourcemanager.projects',
                                  projectId='qux'))

  def testPickProject_ListingProjectsFails(self):
    """Should take free-form input (without validating it)."""
    self.list_projects_mock.side_effect = RuntimeError('blah')
    self.WriteInput('qux')

    self.assertEqual(init_util.PickProject(), 'qux')
    self.AssertErrEquals(
        'WARNING: Listing available projects failed: blah\n'
        'Enter project id you would like to use:',
        normalize_space=True)

  def testPickProject_ListingProjectsFailsNoInput(self):
    """Should return None."""
    self.list_projects_mock.side_effect = RuntimeError('blah')

    self.assertEqual(init_util.PickProject(), None)
    self.AssertErrEquals(
        'WARNING: Listing available projects failed: blah\n'
        'Enter project id you would like to use:',
        normalize_space=True)


class PickProjectTestsLimitExceeded(sdk_test_base.WithLogCapture,
                                    test_case.WithInput):
  """Tests for when a user has more projects than _PROJECT_LIST_LIMIT.

  The project list limit changes how users select their projects in PickProject
  when they have exceeded a certain number of projects, as listing them all can
  be very slow.
  """

  _PROJECT_IDS = ['foo', 'bar', 'baz']

  def SetUp(self):
    self.messages = apis.GetMessagesModule('cloudresourcemanager', 'v1')
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
        """\
        This account has a lot of projects! Listing them all can take a while.
         [1] Enter a project ID
         [2] Create a new project
         [3] List projects
        Please enter your numeric choice:""",
        normalize_space=True)
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
    create_projects_mock = self.StartObjectPatch(projects_api, 'Create')

    self.WriteInput('2\nqux')
    self.assertEqual(init_util.PickProject(), 'qux')
    self.AssertErrContains(
        """\
        This account has a lot of projects! Listing them all can take a while.
         [1] Enter a project ID
         [2] Create a new project
         [3] List projects
        Please enter your numeric choice:""",
        normalize_space=True)
    create_projects_mock.assert_called_once_with(
        resources.REGISTRY.Create('cloudresourcemanager.projects',
                                  projectId='qux'))

  def testPickProject_ListProjects(self):
    self.WriteInput('3\n1')
    self.assertEqual(init_util.PickProject(), 'bar')
    self.AssertErrContains(
        """\
        This account has a lot of projects! Listing them all can take a while.
         [1] Enter a project ID
         [2] Create a new project
         [3] List projects
        Please enter your numeric choice:""",
        normalize_space=True)
    self.AssertErrContains(
        """\
        Pick cloud project to use:
         [1] bar
         [2] baz
         [3] foo
         [4] Create a new project
        Please enter numeric choice or text value (must exactly match list \
        item):""",
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
