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

"""Integration tests for Deployment Manager V2 examples."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import io
import os
import re

from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case

ZONE = 'us-central1-f'
REGION = 'us-central1'
LABELS = 'key1=val1,key2=val2'
UPDATE_LABELS = 'key1=updated'
REMOVE_LABELS = 'key2'
EXPECTED_LABELS = '- key: key1\n  value: val1\n- key: key2\n  value: val2\n'
EXPECTED_UPDATED_LABELS = '- key: key1\n  value: updated'
PREVIEW_LABELS = 'key1=preview'
EXPECTED_LABELS_AFTER_UPDATE_PREVIEW = '- key: key1\n  value: preview\n'


class IntegrationTest(e2e_base.WithServiceAuth):
  """Tests basic functionality of the DeploymentManager V2 client."""

  def testSingleVm(self):
    self.deployExample(['single_vm', 'vm.yaml'], 2)

  def testContainerVm(self):
    self.deployExample(['container_vm', 'container_vm.yaml'], 1)

  def testSaltstack(self):
    self.deployExample(['saltstack', 'salt_cluster.yaml'], 6)

  def testSingleVmWithLabels(self):
    self.deploymentCreateAndUpdateWithLabels('alpha', ['single_vm', 'vm.yaml'],
                                             2)
    self.deploymentCreateAndUpdateWithLabels('beta', ['single_vm', 'vm.yaml'],
                                             2)
    self.deploymentCreateAndUpdateWithLabels('', ['single_vm', 'vm.yaml'],
                                             2)

  def deployExample(self, file_path, resource_count):
    """Helper method to deploy an example template.

    Checks that the template can be created and deleted without errors.

    Args:
       file_path: list of filename pieces that point to the config file under
           //cloud/sdk/deployment_manager/tests/resources/ to deploy.
       resource_count: number of resources expected in this deployment
    """
    # Generate deployment name with a random suffix to allow for multiple
    # simultaneous runs of the integration tests
    self.deployment_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='dm'))
    deployed = False
    try:
      # Call deployments create, should return only after operation completion.
      # We still need to wait for create to finish because otherwise delete
      # will hit a 409 (conflicting operation). If that changes in the service,
      # then this test can be updated to issue only async calls.
      self.Run('deployment-manager deployments create '
               + self.deployment_name + ' --config '
               + self.getConfigFile(file_path))
      # Check that an operation was returned.
      self.AssertErrContains('operation-')
      self.ClearOutput()
      self.ClearErr()
      deployed = True

      # Deployments get on deployment
      self.Run('deployment-manager deployments describe '
               + self.deployment_name)
      self.AssertOutputContains(self.deployment_name)
      self.ClearOutput()
    finally:
      # This block should run before any AssertionErrors, HttpErrors,
      # ToolErrors, or DeploymentManagerExceptions are raised in the try block.
      # Call deployments delete (async) if a deployment was actually created.
      # Don't wait for this to finish, move on to the next test while the
      # delete is processed, since delete is a slow operation.
      if not deployed:
        print(('Deployment %s was not deployed.', self.deployment_name))
      else:
        self.ClearOutput()
        self.Run('deployment-manager deployments delete -q --async '
                 + self.deployment_name + ' --format=default')
        delete_output = self.GetOutput()
        self.ClearOutput()

        # Check that a delete operation was returned.
        delete_operation = re.search(
            r'operation-[\d\w\-]+', delete_output).group()
        self.Run('deployment-manager operations describe '
                 + delete_operation)
        self.AssertOutputContains('delete')
        self.AssertOutputContains(self.deployment_name)
        self.ClearOutput()

  def deploymentCreateAndUpdateWithLabels(self, version, file_path,
                                          resource_count):
    """Helper method to test deployment with labels create and update in alpha.

    Checks that the labels are created and updated as expected.

    Args:
       version: the gcloud version.
       file_path: list of filename pieces that point to the config file under
           //cloud/sdk/deployment_manager/tests/resources/ to deploy.
       resource_count: number of resources expected in this deployment
    """
    # Generate deployment name with a random suffix to allow for multiple
    # simultaneous runs of the integration tests
    self.deployment_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='dm'))

    deployed = False
    updated = False

    try:
      # Call deployments create, should return only after operation completion.
      # We still need to wait for create to finish because otherwise delete
      # will hit a 409 (conflicting operation). If that changes in the service,
      # then this test can be upated to issue only async calls.
      self.Run(version + ' deployment-manager deployments create '
               + self.deployment_name + ' --config '
               + self.getConfigFile(file_path)
               + ' --labels ' + LABELS)
      # Check that an operation was returned.
      self.AssertErrContains('operation-')
      self.ClearOutput()
      self.ClearErr()
      deployed = True

      # Describe the deployment and the labels are as expected.
      self.Run('deployment-manager deployments describe '
               + self.deployment_name)
      self.AssertOutputContains(self.deployment_name)
      self.AssertOutputContains(EXPECTED_LABELS)
      self.ClearOutput()

      # Update deployment labels.
      self.Run(version + ' deployment-manager deployments update '
               + self.deployment_name +' --update-labels '
               + UPDATE_LABELS + ' --remove-labels ' + REMOVE_LABELS)
      self.AssertErrContains(
          'Update deployment metadata completed successfully.')
      self.AssertOutputContains(EXPECTED_UPDATED_LABELS)
      self.ClearOutput()
      self.ClearErr()
      updated = True

      # Describe the deployment and the labels has been updated.
      self.Run('deployment-manager deployments describe '
               + self.deployment_name)
      self.AssertOutputContains(self.deployment_name)
      self.AssertOutputContains(EXPECTED_UPDATED_LABELS)
      self.ClearOutput()

      # Preview the deployment without a new config will get error.
      with self.AssertRaisesHttpExceptionMatches(
          'ResponseError: code=412, message=Cannot preview a deployment '
          'metadata change with a PATCH request.'):
        self.Run(
            '%s deployment-manager deployments update %s --update-labels %s '
            '--preview' % (version, self.deployment_name, UPDATE_LABELS))
      self.ClearOutput()
      self.ClearErr()

      # Preview the deployment with updated labels and the same config file.
      self.Run(version + ' deployment-manager deployments update '
               + self.deployment_name + ' --config '
               + self.getConfigFile(file_path) + ' --update-labels '
               + PREVIEW_LABELS + ' --preview')
      self.AssertErrContains('operation-')
      self.AssertErrContains('completed successfully')
      self.ClearOutput()
      self.ClearErr()

      # Update labels when deployment is in preview will throw error.
      with self.AssertRaisesHttpExceptionMatches(
          'Cannot do a deployment metadata PATCH for a deployment in states '
          'PREVIEWING, UPDATING, or CANCELING. This deployment is in state '
          'PREVIEWING.'):
        self.Run(version + ' deployment-manager deployments update ' +
                 self.deployment_name + ' --update-labels ' + UPDATE_LABELS)
      self.ClearOutput()
      self.ClearErr()

      # Update deployment without flags.
      self.Run(version + ' deployment-manager deployments update '
               + self.deployment_name)
      self.AssertErrContains('operation-')
      self.AssertErrContains('completed successfully')
      self.ClearOutput()
      self.ClearErr()

      # Describe the deployment and the labels are expected.
      self.Run('deployment-manager deployments describe '
               + self.deployment_name)
      self.AssertOutputContains(self.deployment_name)
      self.AssertOutputContains(EXPECTED_LABELS_AFTER_UPDATE_PREVIEW)
      self.ClearOutput()

    finally:
      # This block should run before any AssertionErrors, HttpErrors,
      # ToolErrors, or DeploymentManagerExceptions are raised in the try block.
      # Call deployments delete (async) if a deployment was actually created.
      # Don't wait for this to finish, move on to the next test while the
      # delete is processed, since delete is a slow operation.
      if not deployed or not updated:
        print(('Deployment %s was not %s', self.deployment_name,
               'deployed' if not deployed else 'updated'))
      else:
        self.ClearOutput()
        self.Run('deployment-manager deployments delete -q --async '
                 + self.deployment_name + ' --format=default')
        delete_output = self.GetOutput()
        self.ClearOutput()

        # Check that a delete operation was returned.
        delete_operation = re.search(
            r'operation-[\d\w\-]+', delete_output).group()
        self.Run('deployment-manager operations describe '
                 + delete_operation)
        self.AssertOutputContains('delete')
        self.AssertOutputContains(self.deployment_name)
        self.ClearOutput()

  def replaceParams(self, filename):
    file_contents = io.open(filename, 'rt').read()
    return (file_contents
            .replace('SECOND_ZONE_TO_RUN', ZONE)
            .replace('ZONE_TO_RUN', ZONE)
            .replace('REGION_TO_RUN', REGION)
            .replace('YOUR_PROJECT_NAME', self.Project())
            .replace('YOUR_DEPLOYMENT_NAME', self.deployment_name))

  def getConfigFile(self, file_path):
    # Get all files from the end directory and replace placeholder strings
    # with zone, project, and deployment names.
    example_dir = self.Resource('tests', 'lib', 'surface', 'deployment_manager',
                                'test_data', *(file_path[:-1]))
    deployment_files = [
        f for f in os.listdir(example_dir)
        if os.path.isfile(os.path.join(example_dir, f))
        and not f.endswith('.pyc')]
    file_contents = dict(
        (filename, self.replaceParams(os.path.join(example_dir, filename)))
        for filename in deployment_files
    )
    tempdir = self.CreateTempDir()
    for filename in file_contents:
      self.Touch(directory=tempdir, name=filename,
                 contents=file_contents[filename])
    config_file = os.path.join(tempdir, file_path[-1])
    return os.path.join(tempdir, config_file)

if __name__ == '__main__':
  test_case.main()
