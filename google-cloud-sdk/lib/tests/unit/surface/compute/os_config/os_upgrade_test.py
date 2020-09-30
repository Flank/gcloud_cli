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
"""Tests for the os-config os-upgrade command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import config
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import daisy_test_base

_DEFAULT_TIMEOUT = '7056s'


class OsUpgradeTestBeta(daisy_test_base.DaisyBaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.instance = 'projects/my-project/zones/z/instances/i'
    self.source_os = 'windows-2008r2'
    self.target_os = 'windows-2012r2'
    self.tags = ['gce-os-upgrade']
    self.builder = daisy_utils._DEFAULT_BUILDER_DOCKER_PATTERN.format(
        executable=daisy_utils._OS_UPGRADE_BUILDER_EXECUTABLE,
        docker_image_tag=daisy_utils._DEFAULT_BUILDER_VERSION)

  def PrepareMocks(self, step, async_flag=False, permissions=None,
                   timeout='7200s'):
    self.PrepareDaisyMocks(
        step, async_flag=async_flag, permissions=permissions, timeout=timeout,
        is_import=False)

  def GetOsUpgradeStep(self, additional_arg=None):
    args = [
        '-instance={0}'.format(self.instance),
        '-source-os={0}'.format(self.source_os),
        '-target-os={0}'.format(self.target_os),
        '-timeout={0}'.format(_DEFAULT_TIMEOUT),
        '-client-id=gcloud',
    ]
    if additional_arg:
      args.append(additional_arg)
    args.append('-client-version={0}'.format(config.CLOUD_SDK_VERSION))
    return self.GetOsUpgradeStepForArgs(args)

  def GetOsUpgradeStepForArgs(self, args):
    return self.cloudbuild_v1_messages.BuildStep(
        args=args,
        name=self.builder,
    )

  def testPromptNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp(
        'Upgrade aborted by user.'):
      self.Run("""
               compute os-config os-upgrade {0} --source-os {1} --target-os {2}
               """.format(self.instance, self.source_os, self.target_os))

  def testPromptYes(self):
    build_step = self.GetOsUpgradeStep()
    self.PrepareMocks(build_step)

    self.WriteInput('y\n')
    self.Run("""
             compute os-config os-upgrade {0} --source-os {1} --target-os {2}
             """.format(self.instance, self.source_os, self.target_os))

    self.AssertOutputContains("""\
        [windows-upgrade] output
        """, normalize_space=True)

  def testCommonCase(self):
    build_step = self.GetOsUpgradeStep()
    self.PrepareMocks(build_step)

    self.Run("""
             compute os-config os-upgrade {0} --source-os {1} --target-os {2}
             --quiet
             """.format(self.instance, self.source_os, self.target_os))

    self.AssertOutputContains("""\
        [windows-upgrade] output
        """, normalize_space=True)

  def testMissingInstance(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument INSTANCE_NAME: Must be specified.'):
      self.Run("""
             compute os-config os-upgrade --source-os {0} --target-os {1}
             --quiet
             """.format(self.source_os, self.target_os))

  def testMissingSourceOS(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --source-os: Must be specified.'):
      self.Run("""
             compute os-config os-upgrade {0} --target-os {1}
             --quiet
             """.format(self.instance, self.target_os))

  def testMissingTargetOS(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-os: Must be specified.'):
      self.Run("""
             compute os-config os-upgrade {0} --source-os {1}
             --quiet
             """.format(self.instance, self.source_os))

  def testIncorrectSourceOS(self):
    with self.AssertRaisesArgumentErrorMatches(
        '''\
argument --source-os: Invalid choice: 'bad-os'.

Valid choices are [windows-2008r2].'''):
      self.Run("""
             compute os-config os-upgrade {0} --source-os {1} --target-os {2}
             --quiet
             """.format(self.instance, 'bad-os', self.target_os))

  def testIncorrectTargetOS(self):
    with self.AssertRaisesArgumentErrorMatches(
        '''\
argument --target-os: Invalid choice: 'bad-os'.

Valid choices are [windows-2012r2].'''):
      self.Run("""
             compute os-config os-upgrade {0} --source-os {1} --target-os {2}
             --quiet
             """.format(self.instance, self.source_os, 'bad-os'))

  def testWithNoCreateMachineBackup(self):
    self.runTestWithBoolArg('create-machine-backup', False)

  def testWithRollback(self):
    self.runTestWithBoolArg('auto-rollback')

  def testWithStagingInstallMedia(self):
    self.runTestWithBoolArg('use-staging-install-media')

  def runTestWithBoolArg(self, name, value=True):
    gcloud_arg_name = name if value else 'no-{0}'.format(name)
    cloudbuild_arg_name = name if value else '{0}=false'.format(name)
    build_step = self.GetOsUpgradeStep(
        additional_arg='-{0}'.format(cloudbuild_arg_name))
    self.PrepareMocks(build_step)

    self.Run("""
               compute os-config os-upgrade {0} --source-os {1} --target-os {2}
               --quiet --{3}
               """.format(self.instance, self.source_os, self.target_os,
                          gcloud_arg_name))

    self.AssertOutputContains(
        """\
          [windows-upgrade] output
          """,
        normalize_space=True)

  def testExitOnMissingPermissions(self):
    missing_permissions = self.crm_v1_messages.Policy(
        bindings=[],
    )
    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self._ExpectServiceUsage()
    self._ExpectIamRolesGet(
        is_import=False, permissions=missing_permissions, skip_compute=True)

    get_request = self.crm_v1_messages \
      .CloudresourcemanagerProjectsGetIamPolicyRequest(
          getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(
              options=self.crm_v1_messages.GetPolicyOptions(
                  requestedPolicyVersion=
                  iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
          resource='my-project')
    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        request=get_request,
        response=missing_permissions,
    )

    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run("""
             compute os-config os-upgrade {0} --source-os {1} --target-os {2}
             """.format(self.instance, self.source_os, self.target_os))

  def testAllowFailedServiceAccountPermissionModification(self):
    actual_permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_USER),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
    ])
    self.PrepareDaisyMocks(
        self.GetOsUpgradeStep(),
        permissions=actual_permissions,
        is_import=False,
    )

    # mock for 2 service accounts.
    for _ in range(2):
      self.mocked_crm_v1.projects.GetIamPolicy.Expect(
          request=(
              self.crm_v1_messages
              .CloudresourcemanagerProjectsGetIamPolicyRequest(
                  getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(
                      options=self.crm_v1_messages.GetPolicyOptions(
                          requestedPolicyVersion=iam_util
                          .MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
                  resource='my-project')),
          response=self.permissions,
      )
      self.mocked_crm_v1.projects.SetIamPolicy.Expect(
          self.crm_v1_messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
              resource='my-project',
              setIamPolicyRequest=self.crm_v1_messages.SetIamPolicyRequest(
                  policy=self.permissions,),
          ),
          exception=api_exceptions.HttpForbiddenError('response', 'content',
                                                      'url'))
    self.Run("""
             compute os-config os-upgrade {0} --source-os {1} --target-os {2}
             --quiet
             """.format(self.instance, self.source_os, self.target_os))

    self.AssertOutputContains("""\
        [windows-upgrade] output
        """, normalize_space=True)

  def testAllowFailedIamGetRoles(self):
    self._ExpectServiceUsage()

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    get_request = self.crm_v1_messages \
      .CloudresourcemanagerProjectsGetIamPolicyRequest(
          getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(
              options=self.crm_v1_messages.GetPolicyOptions(
                  requestedPolicyVersion=
                  iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
          resource='my-project')
    actual_permissions = self.crm_v1_messages.Policy(bindings=[])
    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        request=get_request,
        response=actual_permissions,
    )

    self.mocked_iam_v1.roles.Get.Expect(
        self.iam_v1_messages.IamRolesGetRequest(
            name=daisy_utils.ROLE_COMPUTE_ADMIN),
        exception=api_exceptions.HttpForbiddenError('response', 'content',
                                                    'url'))
    self.mocked_iam_v1.roles.Get.Expect(
        self.iam_v1_messages.IamRolesGetRequest(
            name=daisy_utils.ROLE_COMPUTE_STORAGE_ADMIN),
        exception=api_exceptions.HttpForbiddenError('response', 'content',
                                                    'url'))

    # Called once for each missed service account role.
    self._ExpectAddIamPolicyBinding(5)

    self._ExpectCloudBuild(self.GetOsUpgradeStep())

    self.Run("""
             compute os-config os-upgrade {0} --source-os {1} --target-os {2}
             --quiet
             """.format(self.instance, self.source_os, self.target_os))

    self.AssertOutputContains("""\
        [windows-upgrade] output
        """, normalize_space=True)

  def testEditorPermissionIsSufficientForComputeAccount(self):
    actual_permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_COMPUTE_ADMIN),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_USER),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
        self.crm_v1_messages.Binding(
            members=[
                'serviceAccount:123456-compute@developer.gserviceaccount.com'
            ],
            role=daisy_utils.ROLE_EDITOR),
    ])
    self.PrepareDaisyMocks(
        self.GetOsUpgradeStep(),
        permissions=actual_permissions,
        is_import=False,
    )

    self.Run("""
             compute os-config os-upgrade {0} --source-os {1} --target-os {2}
             --quiet
             """.format(self.instance, self.source_os, self.target_os))

    self.AssertOutputContains("""\
        [windows-upgrade] output
        """, normalize_space=True)

  def testCustomRolePermissionIsSufficientForComputeAccount(self):
    actual_permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_COMPUTE_ADMIN),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_USER),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
        self.crm_v1_messages.Binding(
            members=[
                'serviceAccount:123456-compute@developer.gserviceaccount.com'
            ],
            role='roles/custom'),
    ])
    self.PrepareDaisyMocks(
        self.GetOsUpgradeStep(),
        permissions=actual_permissions,
        is_import=False,
    )

    self.Run("""
             compute os-config os-upgrade {0} --source-os {1} --target-os {2}
             --quiet
             """.format(self.instance, self.source_os, self.target_os))

    self.AssertOutputContains("""\
        [windows-upgrade] output
        """, normalize_space=True)

  def testAddMissingPermissions(self):
    actual_permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_COMPUTE_ADMIN),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
        self.crm_v1_messages.Binding(
            members=[
                'serviceAccount:123456-compute@developer.gserviceaccount.com'
            ],
            role=daisy_utils.ROLE_COMPUTE_STORAGE_ADMIN),
    ])
    self.PrepareDaisyMocks(
        self.GetOsUpgradeStep(),
        permissions=actual_permissions,
        is_import=False,
    )

    # Called once for each missed service account role.
    self._ExpectAddIamPolicyBinding(2)

    self.Run("""
             compute os-config os-upgrade {0} --source-os {1} --target-os {2}
             --quiet
             """.format(self.instance, self.source_os, self.target_os))

    self.AssertOutputContains("""\
        [windows-upgrade] output
        """, normalize_space=True)


class OsUpgradeTestAlpha(OsUpgradeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
