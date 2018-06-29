# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Unit tests for environments update."""

from __future__ import absolute_import
from __future__ import unicode_literals
import itertools

from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.command_lib.composer import util as command_util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base
import six


class EnvironmentsUpdateTest(base.EnvironmentsUnitTest):

  def SetUp(self):
    self.running_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=False)
    self.successful_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True)
    self.standard_patch_environment = (
        self._MakePatchEnvironmentWithPyPiPackages({
            'numpy': '==0.1',
            'scikit-learn': '',
            'scipy': '!=0.4',
            'mysql-python': '>0.5.2',
            'path.py': '~=0.9',
            'extras': '[extra1]',
            'more-extras': '[extra1,extra2]',
            'extras-and-version': '[extra-1,extra-2]>=0.1',
        }))

  # Overall update tests
  def testNoUpdateTypeFlagSpecified(self):
    """Tests that updating without an update type flag results in an error."""
    args = [
        'update', '--location', self.TEST_LOCATION, '--project',
        self.TEST_PROJECT, self.TEST_ENVIRONMENT_ID
    ]
    self.AssertRaisesArgumentErrorRegexp(
        r'Exactly one of \(.+\) must be specified.', self.RunEnvironments,
        *args)

  def testMultipleUpdateTypeFlagsSpecified(self):
    """Tests that updating without an update type flag results in an error."""
    # All update flags grouped together by the type of update. Flags from
    # different types of updates should not be allowed together.
    flag_options = [['--node-count=5'], [
        '--clear-airflow-configs', '--remove-airflow-configs=core-a',
        '--update-airflow-configs=core-a=1'
    ], ['--clear-labels', '--remove-labels=a', '--update-labels=a=a'],
                    ['--update-pypi-packages-from-file=some_file']]
    # All pairs of lists in flag_options
    list_pairs = itertools.combinations(flag_options, 2)
    # All pairs of flags that are not both in the same list
    flag_pairs = []
    for list1, list2 in list_pairs:
      flag_pairs.extend(list(itertools.product(list1, list2)))
    # Test all pairs of flags that should not be allowed together
    for flag1, flag2 in flag_pairs:
      args = [
          'update', flag1, flag2, '--location', self.TEST_LOCATION, '--project',
          self.TEST_PROJECT, self.TEST_ENVIRONMENT_ID
      ]
      self.AssertRaisesArgumentErrorRegexp(
          r'Exactly one of \(.+\) must be specified.', self.RunEnvironments,
          *args)

  # Node count update tests
  def _buildNodeCountPatchObject(self, node_count):
    return self.messages.Environment(
        config=self.messages.EnvironmentConfig(nodeCount=node_count))

  def testNodeCountUpdateAsync(self):
    """Tests that update creates a proper node count patch and field mask."""
    expected_patch = self._buildNodeCountPatchObject(5)
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=expected_patch,
        update_mask='config.node_count',
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--node-count',
        '5',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(
        r'^Update in progress for environment \[{}] with operation '
        r'\[{}]'.format(self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testNodeCountUpdateSync(self):
    """Tests the synchronous update of node count."""
    expected_patch = self._buildNodeCountPatchObject(5)
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=expected_patch,
        update_mask='config.node_count',
        response=self.running_op)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=self.successful_op)
    self.RunEnvironments(
        'update',
        '--node-count',
        '5',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(
        r'^{{"ux": "PROGRESS_TRACKER", "message": '
        r'"Waiting for \[{}] to be updated with \[{}]"'.format(
            self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testNodeCountUpdateTooFew(self):
    """Tests that updating the node count to a value < 3 fails."""
    args = [
        'update', '--async', '--node-count', '2', '--location',
        self.TEST_LOCATION, '--project', self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID
    ]
    self.AssertRaisesArgumentErrorMatches('must be greater than or equal to 3',
                                          self.RunEnvironments, *args)

  def _createValidRequirementsFile(self):
    return self.Touch(
        self.root_path,
        contents='numpy==0.1\n'
        'scikit-learn\n'
        'scipy!=0.4\n'
        'mysql-python>0.5.2\n'
        'path.py~=0.9\n'
        'extras[extra1]\n'
        'more-extras[extra1,extra2]\n'
        'extras-and-version[extra-1,extra-2]>=0.1\n')

  def testSetPythonDependenciesSync(self):
    """Tests the successful synchronous update of pypi dependencies from a file.
    """
    mock_file = self._createValidRequirementsFile()
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self.standard_patch_environment,
        update_mask='config.software_config.pypi_packages',
        response=self.running_op)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=self.successful_op)

    self.RunEnvironments(
        'update',
        '--update-pypi-packages-from-file',
        mock_file,
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )

    self.AssertErrMatches(
        r'^{{"ux": "PROGRESS_TRACKER", "message": "Waiting for \[{}] to be '
        r'updated with \[{}]"'.format(self.TEST_ENVIRONMENT_NAME,
                                      self.TEST_OPERATION_NAME))

  def testSetPythonDependenciesSlowFailureSync(self):
    """Tests the failed synchronous update of pypi dependencies from a file."""
    mock_file = self._createValidRequirementsFile()
    error_description = 'ERROR DESCRIPTION'

    failed_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True,
        error=self.messages.Status(message=error_description))

    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self.standard_patch_environment,
        update_mask='config.software_config.pypi_packages',
        response=self.running_op)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=failed_op)

    with self.AssertRaisesExceptionRegexp(
        command_util.Error,
        r'Error updating \[{}]: Operation \[{}] failed: {}'.format(
            self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME,
            error_description)):
      self.RunEnvironments(
          'update',
          '--update-pypi-packages-from-file',
          mock_file,
          '--location',
          self.TEST_LOCATION,
          '--project',
          self.TEST_PROJECT,
          self.TEST_ENVIRONMENT_ID,
      )

  def testSetPythonDependenciesAsync(self):
    """Tests the asynchronous update of pypi dependencies from a file."""
    mock_file = self._createValidRequirementsFile()
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self.standard_patch_environment,
        update_mask='config.software_config.pypi_packages',
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'update',
        '--async',
        '--update-pypi-packages-from-file',
        mock_file,
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.assertEqual(self.running_op, actual_op)
    self.AssertErrMatches(
        r'^Update in progress for environment \[{}] with operation \[{}]'.
        format(self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testSetPythonDependenciesFileNotFound(self):
    """Tests the pypi dependencies file not found error."""
    with self.assertRaises(command_util.Error):
      self.RunEnvironments(
          'update',
          '--update-pypi-packages-from-file',
          './non-existent-file',
          '--location',
          self.TEST_LOCATION,
          '--project',
          self.TEST_PROJECT,
          self.TEST_ENVIRONMENT_ID,
      )

  def testSetPythonDependenciesMissingEnvironment(self):
    """Tests the error when updating a nonexistent environment."""
    mock_file = self._createValidRequirementsFile()
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        'nonexistent-environment',
        patch_environment=self.standard_patch_environment,
        update_mask='config.software_config.pypi_packages',
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))
    with self.AssertRaisesExceptionMatches(
        exceptions.HttpException, 'Resource not found API reason: NOT_FOUND'):
      self.RunEnvironments(
          'update',
          '--update-pypi-packages-from-file',
          mock_file,
          '--location',
          self.TEST_LOCATION,
          '--project',
          self.TEST_PROJECT,
          'nonexistent-environment',
      )

  # Labels update tests
  def _buildLabelsPatchObject(self, patch_entries):
    entry_list = [
        self.messages.Environment.LabelsValue.AdditionalProperty(
            key=key, value=value)
        for key, value in sorted(six.iteritems(patch_entries))
    ]
    return self.messages.Environment(
        labels=self.messages.Environment.LabelsValue(
            additionalProperties=entry_list))

  def testLabelsFieldMaskPrefix(self):
    """Tests that the update labels flag uses the correct field mask prefix.

    Clearing the labels without setting any new values should force the
    field mask to only contain the field mask prefix for labels.
    """
    expected_patch = self._buildLabelsPatchObject({})
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=expected_patch,
        update_mask='labels',
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--clear-labels',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(
        r'^Update in progress for environment \[{}] with operation '
        r'\[{}]'.format(self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testLabelsPatchBuilder(self):
    """Tests that the update labels flag properly constructs a patch object.
    """
    expected_patch = self._buildLabelsPatchObject({'a': '1', 'b': '2'})
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=expected_patch,
        update_mask='labels.a,labels.b,labels.c',
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--update-labels',
        'a=1,b=2',
        '--remove-labels',
        'c',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(
        r'^Update in progress for environment \[{}] with operation '
        r'\[{}]'.format(self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testLabelsSynchronous(self):
    """Tests a successful synchronous update.

    The progress tracker should be activated and terminated, labels to be
    updated and removed should be correctly translated to a patch object and
    field mask.
    """
    expected_patch = self._buildLabelsPatchObject({'a': '1', 'b': '2'})
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=expected_patch,
        update_mask='labels.a,labels.b,labels.c',
        response=self.running_op)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=self.successful_op)
    self.RunEnvironments(
        'update',
        '--update-labels',
        'a=1,b=2',
        '--remove-labels',
        'c',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(
        r'^{{"ux": "PROGRESS_TRACKER", "message": '
        r'"Waiting for \[{}] to be updated with \[{}]", '
        r'"status": "SUCCESS"}}'.format(
            self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testLabelsMultipleUpdateMerge(self):
    """Tests merging when --update-labels is provided multiple times."""
    expected_patch = self._buildLabelsPatchObject({
        'a': '1',
        'b': '2',
        'c': '3',
        'd': '4'
    })
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=expected_patch,
        update_mask='labels.a,labels.b,labels.c,labels.d',
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--update-labels',
        'a=1,b=2',
        '--update-labels',
        'c=3,d=4',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )

  def testLabelsMultipleRemoveMerge(self):
    """Tests merging when --remove-labels is provided multiple times."""
    expected_patch = self._buildLabelsPatchObject({})
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=expected_patch,
        update_mask='labels.a,labels.b,labels.c,labels.d',
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--remove-labels',
        'a,b',
        '--remove-labels',
        'c,d',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )

  # Airflow Config update tests
  def _buildAirflowConfigPatchObject(self, patch_entries):
    # pylint: disable=invalid-name
    AirflowConfigOverridesValue = (
        self.messages.SoftwareConfig.AirflowConfigOverridesValue)
    entry_list = [
        AirflowConfigOverridesValue.AdditionalProperty(key=key, value=value)
        for key, value in sorted(six.iteritems(patch_entries))
    ]
    software_config = self.messages.SoftwareConfig(
        airflowConfigOverrides=AirflowConfigOverridesValue(
            additionalProperties=entry_list))
    return self.messages.Environment(
        config=self.messages.EnvironmentConfig(softwareConfig=software_config))

  def testAirflowConfigFieldMaskPrefix(self):
    """Tests that the update config flag uses the correct field mask prefix.

    Clearing the configs without setting any new values should force the
    field mask to only contain the field mask prefix for configs.
    """
    expected_patch = self._buildAirflowConfigPatchObject({})
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=expected_patch,
        update_mask='config.software_config.airflow_config_overrides',
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--clear-airflow-configs',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(r'^Update in progress for environment \[{}] '
                          r'with operation \[{}]'.format(
                              self.TEST_ENVIRONMENT_NAME,
                              self.TEST_OPERATION_NAME))

  def testAirflowConfigPatchBuilder(self):
    """Tests that the update command can properly construct a patch object."""
    expected_patch = self._buildAirflowConfigPatchObject({
        'core-a': '1',
        'core-b': '2'
    })
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=expected_patch,
        update_mask=('config.software_config.airflow_config_overrides.core-a,'
                     'config.software_config.airflow_config_overrides.core-b'),
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--update-airflow-configs',
        'core-a=1,core-b=2',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(r'^Update in progress for environment \[{}] '
                          r'with operation \[{}]'.format(
                              self.TEST_ENVIRONMENT_NAME,
                              self.TEST_OPERATION_NAME))

  def testAirflowConfigUpdateMultipleFlags(self):
    """Tests that multiple --update-airflow-configs values are merged."""
    expected_patch = self._buildAirflowConfigPatchObject({
        'core-a': '1',
        'core-b': '2',
        'core-c': '3',
        'core-d': '4'
    })
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=expected_patch,
        update_mask=('config.software_config.airflow_config_overrides.core-a,'
                     'config.software_config.airflow_config_overrides.core-b,'
                     'config.software_config.airflow_config_overrides.core-c,'
                     'config.software_config.airflow_config_overrides.core-d'),
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--update-airflow-configs',
        'core-a=1,core-b=2',
        '--update-airflow-configs',
        'core-c=3,core-d=4',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(r'^Update in progress for environment \[{}] '
                          r'with operation \[{}]'.format(
                              self.TEST_ENVIRONMENT_NAME,
                              self.TEST_OPERATION_NAME))

  def testAirflowConfigRemoveMultipleFlags(self):
    """Tests that multiple --remove-airflow-configs values are merged."""
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self._buildAirflowConfigPatchObject({}),
        update_mask=('config.software_config.airflow_config_overrides.core-a,'
                     'config.software_config.airflow_config_overrides.core-b,'
                     'config.software_config.airflow_config_overrides.core-c,'
                     'config.software_config.airflow_config_overrides.core-d'),
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--remove-airflow-configs',
        'core-a,core-b',
        '--remove-airflow-configs',
        'core-c,core-d',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(r'^Update in progress for environment \[{}] '
                          r'with operation \[{}]'.format(
                              self.TEST_ENVIRONMENT_NAME,
                              self.TEST_OPERATION_NAME))

  def testPartialPyPiPackagesFieldMaskPrefix(self):
    """Tests that partial pypi package updates use the right field mask prefix.

    Clearing the configs without setting any new values should force the
    field mask to only contain the field mask prefix for configs.
    """
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self._MakePatchEnvironmentWithPyPiPackages({}),
        update_mask='config.software_config.pypi_packages',
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--clear-pypi-packages',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(r'^Update in progress for environment \[{}] '
                          r'with operation \[{}]'.format(
                              self.TEST_ENVIRONMENT_NAME,
                              self.TEST_OPERATION_NAME))

  def testPartialPyPiPackagesUpdateMultipleFlags(self):
    """Tests that multiple --update-pypi-package values are merged."""
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self._MakePatchEnvironmentWithPyPiPackages({
            'package1': '[extra1]==1',
            'package2': '[extra2,extra3]<2'
        }),
        update_mask=('config.software_config.pypi_packages.package1,'
                     'config.software_config.pypi_packages.package2'),
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--update-pypi-package',
        'package1[extra1]==1',
        '--update-pypi-package',
        'package2[extra2,extra3]<2',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(r'^Update in progress for environment \[{}] '
                          r'with operation \[{}]'.format(
                              self.TEST_ENVIRONMENT_NAME,
                              self.TEST_OPERATION_NAME))

  def testPartialPyPiPackagesRemoveMultipleFlags(self):
    """Tests that multiple --remove-pypi-packages values are merged."""
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self._MakePatchEnvironmentWithPyPiPackages({}),
        update_mask=('config.software_config.pypi_packages.package1,'
                     'config.software_config.pypi_packages.package2,'
                     'config.software_config.pypi_packages.package3,'
                     'config.software_config.pypi_packages.package4'),
        response=self.running_op)
    self.RunEnvironments(
        'update',
        '--async',
        '--remove-pypi-packages',
        'package1',
        '--remove-pypi-packages',
        'package2, package3, package4',
        '--location',
        self.TEST_LOCATION,
        '--project',
        self.TEST_PROJECT,
        self.TEST_ENVIRONMENT_ID,
    )
    self.AssertErrMatches(r'^Update in progress for environment \[{}] '
                          r'with operation \[{}]'.format(
                              self.TEST_ENVIRONMENT_NAME,
                              self.TEST_OPERATION_NAME))

  def _MakePatchEnvironmentWithPyPiPackages(self, expected_package_dict):
    environment_cls = self.messages.Environment
    config_cls = self.messages.EnvironmentConfig
    software_config_cls = self.messages.SoftwareConfig
    pypi_value_cls = software_config_cls.PypiPackagesValue
    deps = [
        pypi_value_cls.AdditionalProperty(key=key, value=value)
        for key, value in sorted(six.iteritems(expected_package_dict))
    ]
    pypi_packages_message = pypi_value_cls(additionalProperties=deps)
    software_config = software_config_cls(pypiPackages=pypi_packages_message)
    config = config_cls(softwareConfig=software_config)
    return environment_cls(config=config)

  def _buildConfigWithEnvVariables(self, env_variables):
    entries = [
        self.messages.SoftwareConfig.EnvVariablesValue.AdditionalProperty(
            key=key, value=value)
        for key, value in sorted(six.iteritems(env_variables))
    ]
    software_config = self.messages.SoftwareConfig(
        envVariables=self.messages.SoftwareConfig.EnvVariablesValue(
            additionalProperties=entries))
    return self.messages.EnvironmentConfig(softwareConfig=software_config)

  def _buildEnvVariablesPatchObject(self, patch_entries):
    return self.messages.Environment(
        config=self._buildConfigWithEnvVariables(patch_entries))

  def _SetExpectEnvironmentGetWithEnvVariables(self, env_variables):
    """Sets ExpectEnvironmentGet, returning environment with env_variables."""
    response = self.MakeEnvironment(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=self._buildConfigWithEnvVariables(env_variables))
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=response)

  def testEnvVariablesWholeFieldMaskPrefix(self):
    """Tests that the correct field mask prefix is used when updating env vars.
    """
    self._SetExpectEnvironmentGetWithEnvVariables({})
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self._buildEnvVariablesPatchObject({}),
        update_mask=('config.software_config.env_variables'),
        response=self.running_op)
    self.RunEnvironments('update', '--async', '--clear-env-variables',
                         '--location', self.TEST_LOCATION, '--project',
                         self.TEST_PROJECT, self.TEST_ENVIRONMENT_ID)
    self.AssertErrMatches(r'^Update in progress for environment \[{}] '
                          r'with operation \[{}]'.format(
                              self.TEST_ENVIRONMENT_NAME,
                              self.TEST_OPERATION_NAME))

  def testEnvVariablesPatchBuilder(self):
    """Tests that the update command can properly construct a patch object."""
    self._SetExpectEnvironmentGetWithEnvVariables({})
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self._buildEnvVariablesPatchObject({
            'name1': 'val1',
            'name2': 'val2'
        }),
        update_mask='config.software_config.env_variables',
        response=self.running_op)
    self.RunEnvironments('update', '--async', '--update-env-variables',
                         'name1=val1,name2=val2', '--location',
                         self.TEST_LOCATION, '--project', self.TEST_PROJECT,
                         self.TEST_ENVIRONMENT_ID)

  def testEnvVariablesUpdateMultipleFlags(self):
    """Tests that multiple --update-env-variables values are merged."""
    self._SetExpectEnvironmentGetWithEnvVariables({
        'name0': 'old_val0',
        'name1': 'old_val1'
    })
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self._buildEnvVariablesPatchObject({
            'name0': 'old_val0',
            'name1': 'val1',
            'name3': 'val3',
            'name2': 'val2',
            'name4': 'val4',
        }),
        update_mask='config.software_config.env_variables',
        response=self.running_op)
    self.RunEnvironments('update', '--async', '--update-env-variables',
                         'name1=val1,name3=val3', '--update-env-variables',
                         'name2=val2,name4=val4', '--location',
                         self.TEST_LOCATION, '--project', self.TEST_PROJECT,
                         self.TEST_ENVIRONMENT_ID)

  def testEnvVariablesRemoveMultipleFlags(self):
    """Tests that multiple --remove-env-variables values are merged."""
    self._SetExpectEnvironmentGetWithEnvVariables({
        'name1': 'val1',
        'name2': 'val2',
        'name3': 'val3',
        'name4': 'val4',
        'name5': 'val5'
    })
    self.ExpectEnvironmentPatch(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        patch_environment=self._buildEnvVariablesPatchObject({
            'name5': 'val5'
        }),
        update_mask='config.software_config.env_variables',
        response=self.running_op)
    self.RunEnvironments('update', '--async', '--remove-env-variables',
                         'name1,name3', '--remove-env-variables', 'name2,name4',
                         '--location', self.TEST_LOCATION, '--project',
                         self.TEST_PROJECT, self.TEST_ENVIRONMENT_ID)


if __name__ == '__main__':
  test_case.main()
