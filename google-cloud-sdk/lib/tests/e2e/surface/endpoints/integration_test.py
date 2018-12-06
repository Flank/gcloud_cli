# -*- coding: utf-8 -*- #
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

"""Integration tests for Service Manager V1."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import re
import shutil

from googlecloudsdk.api_lib.endpoints import exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from tests.lib import e2e_base
from tests.lib import test_case
import six


# This bucket is associated with the cloud-sdk-integration-testing-app project.
# As such, the credentials of the user running the test will be sufficient to
# access this bucket.
BUCKET = 'gs://cloud-sdk-integration-testing-app-staging'


class GcloudOperationError(Exception):

  def __init__(self, output):
    super(GcloudOperationError, self).__init__(output)
    self.output = output

  def __str__(self):
    return repr(self.output)


def _get_docker_config(*unused_args, **kwargs):
  force_new = kwargs.get('force_new', False)
  home = files.GetHomeDir()
  new_path = os.path.join(home, '.docker', 'config.json')
  old_path = os.path.join(home, '.dockercfg')
  if os.path.exists(new_path) or force_new:
    return new_path, True
  return old_path, False


class EndpointsIntegrationTest(e2e_base.WithServiceAuth):
  """Tests basic functionality of the ServiceManagement V1 client."""

  def SetUp(self):
    self.test_subdirectory = os.path.join(self.temp_path,
                                          'gcloud_integration_tests')
    self.RmTree(self.test_subdirectory)
    try:
      os.mkdir(self.test_subdirectory)
    except OSError:
      # If directory already exists, we can just keep going.
      pass

    self.service = 'my-bookstore-api.{0}.appspot.com'.format(self.Project())

    # Set gsutil env variable
    self.old_boto_path = os.getenv('BOTO_CONFIG', None)
    os.environ['BOTO_CONFIG'] = (config.Paths()
                                 .LegacyCredentialsGSUtilPath(self.Account()))

    # Mock GetDockerConfigPath to write configs to files.GetHomeDir(),
    # which is the Docker code will be looking for it.
    (self.StartPatch(
        'googlecloudsdk.core.docker.client_lib.GetDockerConfigPath')
     .side_effect) = _get_docker_config

  def TearDown(self):
    if self.old_boto_path is None and 'BOTO_CONFIG' in os.environ:
      del os.environ['BOTO_CONFIG']
    elif self.old_boto_path is not None:
      os.environ['BOTO_CONFIG'] = self.old_boto_path

  def testAccessDescribe(self):
    # This service has previously been manually created
    service = 'donotdelete-dot-cloud-sdk-integration-testing.appspot.com'
    self.Run('endpoints services get-iam-policy {0}'.format(service))

    # There are no bindings on this service, so only expect etag in output
    self.AssertOutputContains('etag')

  def testAccessCheck(self):
    service = 'donotdelete-dot-cloud-sdk-integration-testing.appspot.com'
    self.Run('endpoints services check-iam-policy {0}'.format(service))
    expected_lines = [
        'permissions:\n',
        '- servicemanagement.services.bind\n',
        '- servicemanagement.services.delete\n',
        '- servicemanagement.services.report\n',
        '- servicemanagement.services.updateProjectSettings\n',
        '- servicemanagement.services.update\n',
        '- servicemanagement.services.getIamPolicy\n',
        '- servicemanagement.services.getProjectSettings\n',
        '- servicemanagement.services.check\n',
        '- servicemanagement.services.get\n',
        '- servicemanagement.services.setIamPolicy\n',
    ]
    for expected_line in expected_lines:
      self.AssertOutputContains(expected_line)

  def testDeployServiceConfig(self):
    orig_swagger_path = self.Resource(
        'tests', 'e2e', 'surface', 'endpoints', 'testdata',
        'bookstore', 'swagger.json')

    with open(orig_swagger_path) as f:
      test_swagger_path = self.Touch(
          self.temp_path,
          name='swagger.json',
          contents=f.read().replace('${SERVICE_NAME}', self.service))

    # Deploy the config to Inception, which also creates the service.
    # TODO(b/66903297) fix service config to not need --force
    cmd = ('endpoints services --project=%s deploy --force %s' %
           (self.Project(), test_swagger_path))

    self.RunDeployCommandAndValidate(cmd)

    # This assertion validates that the CreateServiceConfig (or
    # SubmitSourceConfig) Operation succeeded.
    self.AssertErrContains(
        'operations describe operations/serviceConfigs.' + self.service)

  def testDeployProtoDescriptor(self):
    orig_proto_path = self.Resource(
        'tests', 'e2e', 'surface', 'endpoints', 'testdata',
        'proto_plus_yaml', 'service_proto.pb')
    test_proto_path = os.path.join(self.temp_path, 'service_proto.pb')
    shutil.copyfile(orig_proto_path, test_proto_path)

    orig_config_path = self.Resource(
        'tests', 'e2e', 'surface', 'endpoints', 'testdata',
        'proto_plus_yaml', 'config.yaml')

    with open(orig_config_path) as f:
      test_config_path = self.Touch(
          self.temp_path,
          name='config.yaml',
          contents=f.read().replace('${SERVICE_NAME}', self.service))

    # Deploy the config to Inception, which also creates the service.
    # TODO(b/66903297) fix service config to not need --force
    cmd = 'endpoints services --project={0} deploy --force {1} {2}'.format(
        self.Project(), test_proto_path, test_config_path)

    self.RunDeployCommandAndValidate(cmd)

    # This assertion validates that the CreateServiceConfig (or
    # SubmitSourceConfig) Operation succeeded.
    self.AssertErrContains(
        'operations describe operations/serviceConfigs.' + self.service)

  def RunDeployCommandAndValidate(self, cmd):
    try:
      self.Run(cmd)

      self.AssertErrContains('Service Configuration')
      self.AssertErrContains('uploaded for service')
      self.AssertErrContains('Operation finished successfully')
    except exceptions.OperationErrorException:
      # We know that concurrent CreateRollout Operations result in failures
      # as Inception cancels the ongoing Operations and lets the last one
      # continue. So if a OperationErrorException happens, we can validate
      # whether a concurrent test or a concurrent test run has triggered our
      # Operation to get cancelled.
      #
      # This is sub-optimal from a test correctness perspective. However:
      # 1. the tests will be run continuously and real failures will surface
      #    in test resultsagain.
      #
      # 2. We can still validate that the rest of the "deploy" commands' actions
      #    succeeded using the validations outside of the try-except block.
      log.warning('OperationErrorException occurred in Endpoints e2e test. '
                  'Validating that it is due to a cancelled rollout operation.')
      self.AssertErrContains(
          'The operation with ID rollouts.' + self.service)
      self.AssertErrContains('resulted in a failure')

  def testDeployYamlServiceConfig(self):
    test_swagger_path = self.Resource(
        'tests', 'e2e', 'surface', 'endpoints', 'testdata',
        'bookstore', 'swagger.json')

    with open(test_swagger_path) as f:
      test_swagger_json = json.loads(
          f.read().replace('${SERVICE_NAME}', self.service))

    # Convert this file to YAML and store it in a temporary location
    test_yaml_swagger_path = self.Touch(
        self.temp_path,
        name='swagger.yaml',
        contents=yaml.dump(test_swagger_json))

    # Deploy the config to Inception, which also creates the service.
    self.ClearOutput()
    # TODO(b/66903297) fix service config to not need --force
    cmd = ('endpoints services --project=%s deploy --force %s' %
           (self.Project(), test_yaml_swagger_path))

    self.RunDeployCommandAndValidate(cmd)

    # This assertion validates that the CreateServiceConfig (or
    # SubmitSourceConfig) Operation succeeded.
    self.AssertErrContains(
        'operations describe operations/serviceConfigs.' + self.service)

  def _extractAndCheckOperation(self, output, op_friendly_name=None):
    op_friendly_name = ('%s operation' % op_friendly_name if op_friendly_name
                        else 'Operation')

    # Extract the operation from the output yaml
    output_yaml = yaml.load(output)
    op = output_yaml.get('name').replace('operations/', '')
    self.assertIsNotNone(op)
    self.ClearOutput()
    self.ClearErr()

    # Check the operation for success
    self._waitForOperationDone(op)

    # Clean up output and error buffers
    self.ClearOutput()
    self.ClearErr()

  def _waitForOperationDone(self, op_name):
    error_re = re.compile(r'^error:\s')

    self.Run('endpoints operations wait %s' % (op_name))
    output = self.GetOutput()
    if 'done' in output.lower():
      # Check to see if an error has occurred
      if error_re.search(output):
        raise GcloudOperationError(output)
      else:
        return True

  def _normalizeServiceConfig(self, config_json):
    """Normalize the service config so it can be compared to others easily.

    The output of convert-config is not deterministic. This method will
    normalize a service config dict for easy side-by-side comparison. This is
    done recursively.

    Args:
      config_json: The dict to normalize.

    Returns:
      The normalized object.
    """
    if isinstance(config_json, list):
      new_list = list()
      for item in config_json:
        new_list.append(self._normalizeServiceConfig(item))
      return sorted(new_list)
    elif isinstance(config_json, dict):
      for k, v in six.iteritems(config_json):
        if k == 'number' and isinstance(v, int):
          config_json[k] = 0
        elif k == 'fileName' and isinstance(v, six.string_types):
          config_json[k] = v.replace('json', '').replace('yaml', '')
        else:
          config_json[k] = self._normalizeServiceConfig(v)
      return config_json

    # If config_json is neither a dict nor a list, just return it
    return config_json


if __name__ == '__main__':
  test_case.main()
