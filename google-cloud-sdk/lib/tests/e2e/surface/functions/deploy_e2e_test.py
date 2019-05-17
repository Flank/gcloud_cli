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
"""End to End tests for the 'functions deploy' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import contextlib
import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import retry
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case
import six


FUNCTIONS_STAGING_BUCKET = 'e2e-functions-do-not-delete'
FUNCTION_NAME_PREFIX = 'function_deploy_e2e'
PACKAGE_JSON_FILE = """\
    {
      "name": "test",
      "version": "0.0.1",
      "main": "functions.js"
    }
"""

FUNCTION_JS_FILE = """\
/**
 * HTTP Cloud Function.
 *
 * @param {{Object}} req Cloud Function request context.
 * @param {{Object}} res Cloud Function response context.
 */
exports.{func_name} = function {func_name} (req, res) {{
  console.log('Called function: {func_name} - Hello World!');
  res.send('Hello World!');
}};
"""

UPDATED_FUNCTION_JS_FILE = """\
/**
 * HTTP Cloud Function.
 *
 * @param {{Object}} req Cloud Function request context.
 * @param {{Object}} res Cloud Function response context.
 */
exports.{func_name} = function {func_name} (req, res) {{
  console.log('Called function: {func_name} - Hello Bob!');
  res.send('Hello Bob!');
}};
"""

PUBSUB_JS_FILE = """\
/**
 * Background Cloud Function to be triggered by Pub/Sub.
 *
 * @param {{object}} event The Cloud Functions event.
 * @param {{function}} callback The callback function.
 */
exports.{func_name} = function (event, callback) {{
  const pubsubMessage = event.data;
  const name = pubsubMessage.data ? Buffer.from(pubsubMessage.data, 'base64').toString() : 'World';

  console.log(`Hello, ${{name}}!`);

  callback();
}};
"""

PUBSUB_DATA = base64.b64encode(b'Pubsub!')  # 'UHVic3ViIQ=='


STORAGE_JS_FILE = """\
/**
 * Background Cloud Function to be triggered by GCS Storage Bucket.
 *
 * @param {{object}} event The Cloud Functions event.
 * @param {{function}} callback The callback function.
 */
exports.{func_name} = function (event, callback) {{
  const file = event.data;

  console.log(`Uploaded, ${{file}}!`);

  callback();
}};
"""


# TODO(b/120152563): fix the release tracks.
class DeployE2ETestBase(e2e_base.WithServiceAuth,
                        cli_test_base.CliTestBase):
  """End to End tests for gcloud functions deploy command."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.function_path = self.CreateTempDir()

  def _WriteFunctionSource(self, function_name, file_path,
                           content=FUNCTION_JS_FILE,
                           file_name='functions.js'):
    path = file_path
    self.Touch(path, 'package.json', contents=PACKAGE_JSON_FILE)
    content = content.format(func_name=function_name)
    full_path = self.Touch(path, file_name, contents=content)
    return os.path.dirname(full_path)

  def _GenerateFunctionName(self):
    generator = e2e_utils.GetResourceNameGenerator(
        prefix=FUNCTION_NAME_PREFIX, sequence_start=0, delimiter='_')
    return next(generator)

  @contextlib.contextmanager
  def _DeployFunction(self, *args, **kwargs):
    name = kwargs.pop('name', self._GenerateFunctionName())
    contents = kwargs.pop('function_content', FUNCTION_JS_FILE)
    command_args = []
    source = kwargs.pop('source', '')
    self._WriteFunctionSource(name, source or self.function_path,
                              content=contents)
    if source:
      source = '--source {}'.format(source)

    for no_value_flag in args:
      command_args.append(no_value_flag.replace('_', '-'))

    for flag, flag_value in  six.iteritems(kwargs):
      command_args.append('--{}'.format(flag.replace('_', '-')))
      command_args.append(flag_value)
    command_args.append('--entry-point {}'.format(name))
    try:
      command = 'functions deploy {name} {source} {args}'.format(
          name=name, source=source, args=' '.join(command_args))
      self.Run(command)
      yield name
    finally:
      delete_retryer = retry.Retryer(max_retrials=3,
                                     exponential_sleep_multiplier=2)
      delete_retryer.RetryOnException(
          self.Run, ['functions delete {} --quiet'.format(name)])

  def _CreateOversizedFile(self, parent_dir, file_name, subdir=''):
    if subdir:
      os.makedirs(os.path.join(parent_dir, subdir))
    with open(os.path.join(parent_dir, subdir, file_name), 'w') as f:
      f.write(' ' * (512 * 2**20 + 1))

  def _ParseLabels(self, function_resource):
    if not function_resource or not function_resource.labels:
      return None
    labels = {}
    for label_property in function_resource.labels.additionalProperties:
      labels[label_property.key] = label_property.value

    return labels

  def _ParseEnvVars(self, function_resource):
    if not function_resource or not function_resource.environmentVariables:
      return {}
    env_vars = {}
    for prop in function_resource.environmentVariables.additionalProperties:
      env_vars[prop.key] = prop.value

    return env_vars


class TriggerTest(DeployE2ETestBase):
  """Deploy Trigger Tests."""
  # General Workflow:
  # Deploy, Describe, Call, Delete
  # Variations: Triggers, staging bucket

  def testHttpTriggerExample(self):
    """Test Simple HTTP Cloud Function Example w/local source."""
    with self._DeployFunction('--trigger-http',
                              source=self.function_path,
                              runtime='nodejs6') as function_name:
      self.Run('functions describe {}'.format(function_name))
      self.AssertOutputContains(function_name)
      self.Run('functions call {}'.format(function_name))
      self.AssertOutputContains('Hello World!')

  def testHttpTriggerNoSource(self):
    """Test Quickstart Example w/local source, no source argument."""
    func_name = self._GenerateFunctionName()
    with files.ChDir(self.function_path):
      with self._DeployFunction('--trigger-http',
                                name=func_name,
                                runtime='nodejs6') as function_name:
        self.Run('functions describe {}'.format(function_name))
        self.AssertOutputContains(function_name)
        self.Run('functions call {}'.format(function_name))
        self.AssertOutputContains('Hello World!')

  def testPubSubTrigger(self):
    """Test PubSub Example."""
    with self._DeployFunction(
        source=self.function_path,
        trigger_event='providers/cloud.pubsub/eventTypes/topic.publish',
        trigger_resource='test-topic',
        runtime='nodejs6',
        function_content=PUBSUB_JS_FILE) as function_name:
      self.Run('functions describe {}'.format(function_name))
      self.AssertOutputContains(function_name)
      data = """'{{"data": "'{}'"}}'""".format(PUBSUB_DATA)
      call_result = self.Run('functions call {} --data {}'.format(
          function_name, data))
      self.assertTrue(call_result)
      self.assertTrue(call_result.executionId)

  def testStorageTrigger(self):
    with self._DeployFunction(
        source=self.function_path,
        trigger_event='google.storage.object.finalize',
        trigger_resource='e2e-input-functions',
        runtime='nodejs6',
        function_content=STORAGE_JS_FILE) as function_name:
      self.Run('functions describe {}'.format(function_name))
      self.AssertOutputContains(function_name)
      call_cmd = """functions call {} --data '{{"name": "test.txt"}}'""".format(
          function_name)
      call_result = self.Run(call_cmd)
      self.assertTrue(call_result)
      self.assertTrue(call_result.executionId)

  def testStagingBucketDeploy(self):
    """Test with --staging-bucket flag."""
    with self._DeployFunction('--trigger-http',
                              source=self.function_path,
                              stage_bucket=FUNCTIONS_STAGING_BUCKET,
                              runtime='nodejs6') as function_name:
      self.Run('functions describe {}'.format(function_name))
      self.AssertOutputContains(function_name)
      self.Run('functions call {}'.format(function_name))
      self.AssertOutputContains('Hello World!')


class RedeployTest(DeployE2ETestBase):
  """Redeploy Tests."""
  # General Workflow:
  # Deploy, Describe, Call, [Update Function and/or Metadata], Deploy,->
  # Describe, Call, Delete
  # Variations: Source, metadata (including labels), staging bucket

  def _RunAndCheckErr(self, function_name, output):
    self.ClearOutput()
    self.Run('functions call {}'.format(function_name))
    self.AssertOutputContains(output)

  def testRedeployNewFunction(self):
    """Test redeploy with source code update."""
    with self._DeployFunction('--trigger-http',
                              source=self.function_path,
                              runtime='nodejs6') as function_name:
      self.AssertOutputContains(function_name)
      self.Run('functions call {}'.format(function_name))
      self.AssertOutputContains('Hello World!')
      # Update function file and redeploy
      self.ClearOutput()
      self._WriteFunctionSource(function_name, self.function_path,
                                content=UPDATED_FUNCTION_JS_FILE)
      self.Run(
          'functions deploy {name} --source {source}'.format(
              name=function_name, source=self.function_path))
      call_retryer = retry.Retryer(exponential_sleep_multiplier=2)
      call_retryer.RetryOnException(self._RunAndCheckErr,
                                    [function_name, 'Hello Bob!'],
                                    sleep_ms=1000)

  def testRedeployMetadataUpdate(self):
    """Test redeploy with no source change, just metadata changes."""
    with self._DeployFunction('--trigger-http',
                              source=self.function_path,
                              runtime='nodejs6') as function_name:
      self.AssertOutputContains(function_name)
      self.Run('functions call {}'.format(function_name))
      self.AssertOutputContains('Hello World!')

      # Update metadata and redeploy
      self.ClearOutput()
      newlabels = 'foo=bar,guess=who'
      region = 'us-central1'
      timeout = '540s'
      self.Run(
          'functions deploy {name} --source {source} '
          '--memory 512 '
          '--region {region} --timeout {timeout} --trigger-http '
          '--update-labels {labels} --clear-labels'.format(
              name=function_name, source=self.function_path,
              region=region, timeout=timeout, labels=newlabels))
      describe_result = self.Run('functions describe {}'.format(
          function_name))
      self.assertEqual(512, describe_result.availableMemoryMb)
      updated_labels = self._ParseLabels(describe_result)
      self.assertIn('foo', updated_labels,)
      self.assertIn('guess', updated_labels)
      self.assertIn('deployment-tool', updated_labels)
      self.assertEqual(describe_result.timeout, timeout)
      self.assertIn(region, describe_result.name)

  def testRedeployStagingBucket(self):
    """Test redeploy with staging bucket."""
    with self._DeployFunction(
        '--trigger-http', source=self.function_path, runtime='nodejs6',
        stage_bucket=FUNCTIONS_STAGING_BUCKET) as function_name:
      self.Run('functions describe {}'.format(function_name))
      self.AssertOutputContains(function_name)
      self.Run('functions call {}'.format(function_name))
      self.AssertOutputContains('Hello World!')
      self.ClearOutput()
      self._WriteFunctionSource(function_name, self.function_path,
                                content=UPDATED_FUNCTION_JS_FILE)
      self.Run(
          'functions deploy {name} --source {source} --trigger-http '
          '--stage-bucket e2e-input-functions --entry-point {name}'.format(
              name=function_name, source=self.function_path))
      call_retryer = retry.Retryer(exponential_sleep_multiplier=2)
      call_retryer.RetryOnException(self._RunAndCheckErr,
                                    [function_name, 'Hello Bob!'],
                                    sleep_ms=1000)


class EnvVarRedeployTest(DeployE2ETestBase):
  """Environment Variable Redeploy Tests."""

  def _RunAndCheckErr(self, function_name, output):
    self.ClearOutput()
    self.Run('functions call {}'.format(function_name))
    self.AssertOutputContains(output)

  def testRedeployEnvVarUpdate(self):
    """Test redeploy with no source change, just environment variable changes.
    """
    self.track = calliope_base.ReleaseTrack.GA
    with self._DeployFunction('--trigger-http', source=self.function_path,
                              set_env_vars='FOO=bar',
                              runtime='nodejs6') as function_name:
      self.AssertOutputContains(function_name)
      self.Run('functions call {}'.format(function_name))
      self.AssertOutputContains('Hello World!')

      # Update env vars and redeploy
      self.ClearOutput()
      new_env_vars = 'BAZ=boo'
      self.Run(
          'functions deploy {name} --source {source} '
          '--trigger-http --update-env-vars {env_vars}'.format(
              name=function_name, source=self.function_path,
              env_vars=new_env_vars))
      describe_result = self.Run('functions describe {}'.format(
          function_name))
      updated_env_vars = self._ParseEnvVars(describe_result)
      self.assertEquals('bar', updated_env_vars.get('FOO'))
      self.assertEquals('boo', updated_env_vars.get('BAZ'))


class MiscWorkflowTest(DeployE2ETestBase):
  """Misc Deploy Workflow Tests."""

  def _RunAndCheckLog(self, function_name):
    self.ClearOutput()
    self.Run('functions logs read {}'.format(function_name))
    self.AssertOutputContains(
        'Called function: {} - Hello World!'.format(function_name))
    self.AssertOutputContains(function_name)

  def testLogRead(self):
    """Test deploy and read logs."""
    with self._DeployFunction('--trigger-http',
                              source=self.function_path,
                              runtime='nodejs6') as function_name:
      self.Run('functions call {}'.format(function_name))
      self.AssertOutputContains(function_name)
      log_retryer = retry.Retryer(exponential_sleep_multiplier=2)
      log_retryer.RetryOnException(self._RunAndCheckLog,
                                   [function_name], sleep_ms=10)


if __name__ == '__main__':
  test_case.main()
