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

"""Testing resources for Projects."""

from googlecloudsdk.api_lib.cloudresourcemanager import projects_util


def GetTestActiveProjectsList():
  messages = projects_util.GetMessages()
  return [
      messages.Project(
          lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
          projectId=u'feisty-catcher-644',
          projectNumber=925276746377,
          name=u'My Project 5'),
      messages.Project(
          lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
          projectId=u'test-project-2',
          projectNumber=123002,
          name=u'test-project-2'),
      messages.Project(
          lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
          projectId=u'test-project-3',
          projectNumber=123003,
          name=u'Test Project 3')
  ]


def GetTestProjectWithLongNameAndMatchingId():
  messages = projects_util.GetMessages()
  return messages.Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId=u'abcdefghijklmnopqrstuvwxyz',
      projectNumber=925276746377,
      name=u'AbcdefghijkLMNOpqrstuvwxyz ')  # needs to be at least 24 characters


def GetTestActiveProject(prefix=False):
  messages = projects_util.GetMessages()
  return messages.Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId=(
          u'projects/feisty-catcher-644' if prefix else u'feisty-catcher-644'),
      projectNumber=925276746377,
      name=u'My Project 5')


def GetTestActiveProjectWithSameNameAndId():
  messages = projects_util.GetMessages()
  return messages.Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId=u'test-project-2',
      projectNumber=123002,
      name=u'test-project-2')


def GetTestActiveProjectWithFolderParent():
  messages = projects_util.GetMessages()
  return messages.Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId=u'test-project-2',
      projectNumber=123002,
      name=u'test-project-2',
      parent=messages.ResourceId(
          id='12345', type='folder'))


def GetTestActiveProjectWithOrganizationParent():
  messages = projects_util.GetMessages()
  return messages.Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId=u'test-project-2',
      projectNumber=123002,
      name=u'test-project-2',
      parent=messages.ResourceId(
          id='2048', type='organization'),)


def GetTestActiveProjectWithLabels(labels):
  messages = projects_util.GetMessages()
  labels_message = messages.Project.LabelsValue(
      additionalProperties=[
          messages.Project.LabelsValue.AdditionalProperty(key=key, value=value)
          for key, value in sorted(labels.items())
      ])
  return projects_util.GetMessages().Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId=u'test-project-2',
      projectNumber=123002,
      name=u'test-project-2',
      labels=labels_message)


def GetTestIamPolicy(clear_fields=None):
  """Creates a test IAM policy.

  Args:
      clear_fields: list of policy fields to clear.
  Returns:
      IAM policy.
  """
  if clear_fields is None:
    clear_fields = []

  messages = projects_util.GetMessages()
  policy = projects_util.GetMessages().Policy(
      auditConfigs=[
          messages.AuditConfig(
              auditLogConfigs=[
                  messages.AuditLogConfig(logType=messages.AuditLogConfig.
                                          LogTypeValueValuesEnum.ADMIN_READ)
              ],
              service=u'allServices')
      ],
      bindings=[
          messages.Binding(
              members=[u'serviceAccount:123hash@developer.gserviceaccount.com'],
              role=u'roles/editor'),
          messages.Binding(
              members=[u'user:tester@gmail.com', u'user:slick@gmail.com'],
              role=u'roles/owner')
      ],
      etag=b'<< Unique versioning etag bytefield >>',
      version=0)

  for field in clear_fields:
    policy.reset(field)

  return policy


def GetLabelsFlagValue(labels):
  return ','.join(
      ['{0}={1}'.format(k, v) for k, v in sorted(labels.iteritems())])
