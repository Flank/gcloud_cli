# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Basic tests of the argument wiring between gcloud app and appcfg."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import multiprocessing.pool
import os
import shutil
import tempfile
import time

from apitools.base.py import encoding
from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.app import build as app_build
from googlecloudsdk.api_lib.app import cloud_build
from googlecloudsdk.api_lib.app import deploy_app_command_util
from googlecloudsdk.api_lib.app import deploy_command_util
from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import exceptions
from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.api_lib.app import runtime_builders
from googlecloudsdk.api_lib.app import runtime_registry
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.api_lib.cloudbuild import build
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import logs as cloudbuild_logs
from googlecloudsdk.api_lib.datastore import index_api
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import exceptions as sm_exceptions
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import exceptions as api_lib_exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.app import create_util
from googlecloudsdk.command_lib.app import deploy_util
from googlecloudsdk.command_lib.app import exceptions as app_exceptions
from googlecloudsdk.command_lib.app import output_helpers
from googlecloudsdk.command_lib.app import source_files_util
from googlecloudsdk.command_lib.app import staging
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files as file_utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import build_base
from tests.lib.apitools import http_error
from tests.lib.surface.app import api_test_util
from tests.lib.surface.app import cloud_storage_util
from tests.lib.surface.app import util as test_util
from googlecloudsdk.third_party.appengine.admin.tools.conversion import yaml_schema_v1
from googlecloudsdk.third_party.appengine.tools import context_util
import mock


REMOTE_CONTEXT = {
    'labels': {'category': 'remote_repo'},
    'context': {
        'cloudRepo': {
            'repoId': {
                'projectRepoId': {'repoName': 'default',
                                  'projectId': 'fake-project'}},
            'revisionId': 'fake_revision'}}}

SNAPSHOT_CONTEXT = {
    'labels': {'category': 'snapshot'},
    'context': {
        'cloudWorkspace': {
            'workspaceId': {
                'name': 'google/_snapshot/fakesnapshot',
                'repoId': {
                    'projectRepoId': {'repoName': 'google-source-snapshots',
                                      'projectId': 'fake-project'}}}}}}

FAKE_SOURCE_CONTEXTS = [REMOTE_CONTEXT, SNAPSHOT_CONTEXT]


DEFAULT_SERVICE_HINT = (
    'You can stream logs from the command line by running:\n'
    '  $ gcloud app logs tail -s default\n\n'
    'To view your application in the web browser run:\n'
    '  $ gcloud app browse')
SINGLE_SERVICE_HINT = (
    'You can stream logs from the command line by running:\n'
    '  $ gcloud app logs tail -s {0}\n\n'
    'To view your application in the web browser run:\n'
    '  $ gcloud app browse -s {0}')
MULTIPLE_SERVICES_HINT = (
    'You can stream logs from the command line by running:\n'
    '  $ gcloud app logs tail -s <service>\n\n'
    'To view your application in the web browser run:\n'
    '  $ gcloud app browse -s <service>')
CRON_HINT = 'Cron jobs have been updated.'
CRON_WITH_TASKS_HINT = (
    'Cron jobs have been updated.'
    '\n\nVisit the Cloud Platform Console Task Queues '
    'page to view your queues and cron jobs.\n'
    'https://console.cloud.google.com/appengine/taskqueues/cron?project')
DISPATCH_HINT = 'Custom routings have been updated.'
DOS_HINT = ('DoS protection has been updated.'
            '\n\nTo delete all blacklist entries, redeploy the dos.yaml file '
            'with the following content:'
            '\n    blacklist:')
INDEX_HINT = 'Indexes are being rebuilt. This may take a moment.'
QUEUE_HINT = ('Task queues have been updated.'
              '\n\nVisit the Cloud Platform Console Task Queues '
              'page to view your queues and cron jobs.')
STOP_VERSION_MESSAGE = 'Stopping version [{project}/{service}/{version}].\n'
STOP_VERSION_HINT = (
    'Sent request to stop version [{project}/{service}/{version}]. '
    'This operation may take some time to complete. '
    'If you would like to verify that it succeeded, run:\n'
    '  $ gcloud app versions describe -s default {version}\n'
    'until it shows that the version has stopped.')


class InfrastructureException(Exception):
  """Indicator that test infrastructure must be updated."""


class DeployTestBase(api_test_util.ApiTestBase,
                     test_util.WithFakeRPC,
                     test_util.WithAppData):

  TEST_MODULES = {'mod1': '1', 'default': '1'}

  def SetUp(self):
    self.strict = False

    self.generate_mock = self.StartObjectPatch(
        context_util, 'CalculateExtendedSourceContexts', return_value=[])

    self.gdcmock_args = []

    # Override default retry logic so that tests don't do unnecessary sleeps.
    self.StartObjectPatch(time, 'sleep')

    # TODO(b/15948153) The progress tracker interferes with output during its
    # execution, leading to flaky tests.
    self.StartObjectPatch(progress_tracker, 'ProgressTracker')

    # Mocks for VM deployments.
    self.create_temp_dockerfile_mock = self.StartObjectPatch(
        deploy_command_util, '_GetDockerfiles')


class DeployWithApiTestsBase(DeployTestBase, cloud_storage_util.WithGCSCalls):
  """Base class for testing deployments."""

  HANDLER_FILE = 'handlers.py'
  HANDLER_CONTENT = 'def foo(): pass'
  UTIL_FILE = 'utils.py'
  UTIL_CONTENT = 'def bar(): pass'

  def SetUp(self):
    # set up mock clients.
    self.su_services_messages = core_apis.GetMessagesModule(
        'serviceusage', 'v1')
    self.su_mocked_client = apitools_mock.Client(
        core_apis.GetClientClass('serviceusage', 'v1'),
        real_client=core_apis.GetClientInstance(
            'serviceusage', 'v1', no_http=True))
    self.su_mocked_client.Mock()
    self.addCleanup(self.su_mocked_client.Unmock)
    # Mock out copying files to GCS.
    self._storage_client_mock = self.StartObjectPatch(storage_api,
                                                      'StorageClient')
    self.copy_file_mock = self._storage_client_mock.CopyFileToGCS
    self.list_mock = self._storage_client_mock.ListBucket

    # Mock out the multiprocessing--this causes all sorts of complications
    # for unit tests, and will be fully tested in the e2e tests. We can
    # assume that Python's process pool works.
    self.pool_mock = mock.MagicMock(multiprocessing.pool.Pool)
    self.pool_mock.map.side_effect = map
    self.StartPatch('multiprocessing.Pool').return_value = self.pool_mock
    self.temp_path = os.path.realpath(self.temp_path)
    self.mock_index_api_create_indexes = self.StartObjectPatch(
        index_api, 'CreateMissingIndexes')

  def ExpectServiceDeployed(self, service, version, set_default=1,
                            set_default_success=True,
                            default_bucket='gs://default-bucket/',
                            hostname=None,
                            create_attempts=1, create_success=True,
                            stop_version=None,
                            stop_version_suppressed=False,
                            existing_services=None,
                            deployment=None,
                            handlers=None, beta_settings=None,
                            version_call_args=None,
                            operation_metadata=None,
                            project=None):
    """Build expected calls and responses for a single service deployment.

    Args:
      service: str, service to be updated
      version: str, version to be deployed
      set_default: int, number of calls expected to be made to set the
          default version
      set_default_success: bool, True if setting default will succeed
      default_bucket: str, the bucket for GetApplicationRequest
      hostname: str, hostname for the application
      create_attempts: int, number of calls expected to be made to
          create version
      create_success: bool, True if create should succeed
      stop_version: str, version ID that deploy is expected to send a stop
          request for.
      stop_version_suppressed: bool, if user passes --stop-previous-version and
          there is a previous version but stop call will be suppressed.
      existing_services: {str: {}}, dictionary of service IDs to dicts
          that look up information by version ID. Example:
             {'default': {'a': {'traffic_split': 1.0, 'manual_scaling': True}}}
      deployment: deployment manifest for expected create version call
      handlers: [appengine_v1_messages.UrlMap] list of handlers to be
          passed to the version Create method
      beta_settings: appengine_v1_messages.Version.BetaSettingsValue, a
          message containing settings to be passed to version Create method
      version_call_args: dict of additional kwargs to be passed to the version
          Create method (e.g. {'vm': True})
      operation_metadata: Metadata to be returned on the Operation.
      project: str, ID of project (self.Project() will be used by default)
    """
    project = project or self.Project()
    self.ExpectGetApplicationRequest(project, code_bucket=default_bucket,
                                     hostname=hostname)
    self.ExpectListServicesRequest(project, existing_services)
    self.ExpectCreateVersion(project, service, version,
                             num_attempts=create_attempts,
                             success=create_success,
                             deployment=deployment,
                             handlers=handlers,
                             beta_settings=beta_settings,
                             operation_metadata=operation_metadata,
                             version_call_args=version_call_args)

    # A call to list all versions will be made before setting default version
    # only if --stop-previous-version is True.
    if set_default and stop_version:
      # Only update traffic split for deployed version if it is new.
      if service not in existing_services:
        existing_services.update({service: {version: {'traffic_split': 0.0}}})
      elif version not in existing_services[service]:
        existing_services[service].update({version: {'traffic_split': 0.0}})
      else:
        # No stop version call should be made if version ID hasn't changed.
        stop_version = None
      self.ExpectListVersionsRequest(
          project,
          service,
          existing_services)

    if set_default:
      self.ExpectSetDefault(project, service, version,
                            num_tries=set_default,
                            success=set_default_success)

    if stop_version and not stop_version_suppressed:
      self.ExpectStopVersionRequest(project, service, stop_version)

  def ExpectServicesDeployed(self, services, deployment=None):
    """Build expected calls and responses for deployment of multiple services.

    Args:
      services: [(str, str)], sorted list of service ID to version ID
      deployment: appengine_v1_messages.Deployment, deployment
          manifest for files.
    """
    project = self.Project()
    handlers = self.DefaultHandlers()
    self.ExpectGetApplicationRequest(project)
    self.ExpectListServicesRequest(project)
    for service, version in services:
      self.ExpectCreateVersion(project, service, version,
                               handlers=handlers,
                               deployment=deployment)
      self.ExpectSetDefault(project, service, version)

  def AssertConfigDeployed(self, cron=False, dispatch=False, dos=False,
                           queue=False, index=False):
    """Assert expected calls for deploying configs."""
    project = self.Project()

    self.AssertRequested('https://appengine.google.com/api/cron/update',
                         {'app_id': project},
                         requested=cron)
    self.AssertRequested('https://appengine.google.com/api/dispatch/update',
                         {'app_id': project},
                         requested=dispatch)
    self.AssertRequested('https://appengine.google.com/api/dos/update',
                         {'app_id': project},
                         requested=dos)
    self.AssertRequested('https://appengine.google.com/api/queue/update',
                         {'app_id': project},
                         requested=queue)
    if index:
      self.mock_index_api_create_indexes.assert_called_once()

  def AssertPostDeployHints(self, default_service=False, single_service=None,
                            multiple_services=False, cron=False,
                            cron_with_tasks=False, dispatch=False, dos=False,
                            index=False, queue=False, stop_version=None):
    """Assert that hints are correctly displayed after deploying.

    Args:
      default_service: bool, if True then default service hint should be used.
      single_service: str|None, the name of the single service if not 'default.'
      multiple_services: bool, if True then the hint for multiple services
          should be used.
      cron: bool, if True the cron.yaml hint should be displayed.
      cron_with_tasks: bool, if True, the tasks queues page hint should be
          displayed after the cron.yaml hint (if False, means that queue.yaml
          was also deployed.)
      dispatch: bool, if True the dispatch.yaml hint should be displayed.
      dos: bool, if True the dos.yaml hint should be displayed.
      index: bool, if True the index.yaml hint should be displayed.
      queue: bool, if True, the queue.yaml hint should be displayed.
      stop_version: str|None, the name of the previous version that was stopped
          or None if no such version exists

    Raises:
      InfrastructureException: if an invalid combination of arguments is
      given.
    """
    def _AssertHintDisplayedOrNotDisplayed(condition, hint):
      """Checks that hint is displayed if and only if condition is True."""
      if condition:
        self.AssertErrContains(hint, normalize_space=True)
      else:
        self.AssertErrNotContains(hint, normalize_space=True)
    _AssertHintDisplayedOrNotDisplayed(default_service, DEFAULT_SERVICE_HINT)
    _AssertHintDisplayedOrNotDisplayed(single_service,
                                       SINGLE_SERVICE_HINT.format(
                                           single_service))
    _AssertHintDisplayedOrNotDisplayed(multiple_services,
                                       MULTIPLE_SERVICES_HINT)
    _AssertHintDisplayedOrNotDisplayed(cron, CRON_HINT)
    _AssertHintDisplayedOrNotDisplayed(cron_with_tasks, CRON_WITH_TASKS_HINT)
    _AssertHintDisplayedOrNotDisplayed(dispatch, DISPATCH_HINT)
    _AssertHintDisplayedOrNotDisplayed(dos, DOS_HINT)
    _AssertHintDisplayedOrNotDisplayed(index, INDEX_HINT)
    _AssertHintDisplayedOrNotDisplayed(queue, QUEUE_HINT)
    # --stop-previous-version checks
    if stop_version and multiple_services:
      raise InfrastructureException(
          'Need to update test infrastructure to support this check')
    stop_service = single_service or (default_service and 'default')
    _AssertHintDisplayedOrNotDisplayed(
        stop_version, STOP_VERSION_MESSAGE.format(
            project=self.Project(), version=stop_version, service=stop_service))
    _AssertHintDisplayedOrNotDisplayed(stop_version, STOP_VERSION_HINT.format(
        project=self.Project(), version=stop_version, service=stop_service))

  def _RuntimeBuilderExperimentEnabled(self, enabled=True):
    experiment_config = mock.MagicMock()
    self.StartObjectPatch(experiment_config, 'GetExperimentPercentWithDefault',
                          return_value=100 if enabled else 0)
    self.StartObjectPatch(runtime_builders.Experiments, 'LoadFromURI',
                          return_value=experiment_config)


class DeployWithApiTests(DeployWithApiTestsBase):
  """Tests the deploy command."""

  def SetUp(self):
    self.build_and_push_mock = self.StartPatch('googlecloudsdk.api_lib.app.'
                                               'deploy_command_util.'
                                               'BuildAndPushDockerImage')
    fake_image = app_build.BuildArtifact.MakeImageArtifact(
        'appengine.gcr.io/gcloud/1.default')
    self.build_and_push_mock.return_value = fake_image
    properties.VALUES.app.trigger_build_server_side.Set(None)
    self._RuntimeBuilderExperimentEnabled()

  def testNoCodeBucketRepairsApp(self):
    """Test deploy with no default bucket."""
    self.MakeApp()

    # Expect all requests associated with repairing app and deploying.
    self.ExpectGetApplicationRequest(self.Project(), code_bucket='')
    self.ExpectRepairApplicationRequest(self.Project())
    bucket = 'gs://default-bucket/'
    self.ExpectGetApplicationRequest(self.Project(), code_bucket=bucket)
    self.ExpectListServicesRequest(self.Project(), None)
    self.ExpectCreateVersion(self.Project(), 'default', '1',
                             deployment=self.GetDeploymentMessage())
    self.ExpectSetDefault(self.Project(), 'default', '1')
    # Explicitly calling Run so that the bucket is not appended.
    self.Run('app deploy {m} --version 1'.format(m=self.FullPath('app.yaml')))

  def testDontCreateAppIfNonInteractive(self):
    """Tests that no app is created in non-interactive mode.

    This test ensures that `gcloud app deploy` fails with a missing-app error
    message when (1) run non-interactively, and (2) the project has no app.
    """
    self.MakeApp()

    # Expect GetApplication to fail.
    self.ExpectGetApplicationRequest(
        self.Project(), exception=http_error.MakeDetailedHttpError(
            code=404,
            details=http_error.ExampleErrorDetails()))
    create_app_mock = self.StartObjectPatch(create_util,
                                            'CreateAppInteractively')

    with self.assertRaisesRegex(app_exceptions.MissingApplicationError,
                                'does not contain an App Engine application'):
      self.Run('app deploy ' + self.FullPath('app.yaml'))

    create_app_mock.assert_not_called()

  def testOfferCreateAppInteractively(self):
    """Offer to create an app during deploy if an app does not yet exist."""

    # This is required for all interactive tests
    self.StartObjectPatch(console_io, 'CanPrompt', return_value=True)

    # Mock the create app command_lib call (this is tested in create_test)
    self.create_app_mock = self.StartObjectPatch(
        create_util, 'CreateAppInteractively')
    self.MakeApp()

    # Expect GetApplication to fail a 404 the first time.
    # App doesn't exist in this project.
    self.ExpectGetApplicationRequest(
        self.Project(),
        exception=http_error.MakeDetailedHttpError(
            code=404,
            details=http_error.ExampleErrorDetails()))

    # Since CreateAppInteractively is mocked, no app create request is
    # necessary, but when the app is created, a new GetApplication request will
    # be made.
    bucket = 'https://storage.googleapis.com/default-bucket/'
    self.ExpectServiceDeployed('default', '1',
                               deployment=self.GetDeploymentMessage(
                                   source_url_base=bucket))

    self.Run('app deploy --version 1 ' + self.FullPath('app.yaml'))
    self.create_app_mock.assert_called_once_with(mock.ANY, self.Project())

  def testRaisePermissionsErrorForWrongProject(self):
    """Ensure informative error is raised when GetApplication receives a 403."""
    self.MakeApp()
    self.ExpectGetApplicationRequest(
        self.Project(),
        exception=http_error.MakeDetailedHttpError(
            code=403,
            message='Original message.'))
    with self.assertRaisesRegex(
        api_lib_exceptions.HttpException,
        (r'Permissions error fetching application \[{}\]. '
         r'Please make sure you are using the correct project ID and that '
         r'you have permission to view applications on the project.'
         .format('apps/' + self.Project()))):
      self.Run('app deploy ' + self.FullPath('app.yaml'))

  def testRaiseHttpExceptionDuringCreateApp(self):
    """Test generic error during create app."""
    self.MakeApp()
    self.ExpectGetApplicationRequest(
        self.Project(),
        exception=http_error.MakeDetailedHttpError(
            code=402,
            message='Original message.'))
    with self.assertRaisesRegex(
        api_lib_exceptions.HttpException,
        (r'Original message.')):
      self.Run('app deploy ' + self.FullPath('app.yaml'))

  def testRequiresGsStyleBucketUrl(self):
    """Test raises error for invalid --bucket argument."""
    self.MakeApp()

    error_regex = 'argument --bucket: Must be a valid'
    with self.AssertRaisesArgumentErrorRegexp(error_regex):
      self.Run('app deploy --bucket=foobar {m}'.format(
          m=self.FullPath('app.yaml')))

  def testYamlConversionFailed(self):
    """Test raises ConfigError when yaml conversion fails."""
    self.MakeApp()
    self.ExpectGetApplicationRequest(self.Project())
    self.ExpectListServicesRequest(self.Project())

    # A scenario where converting to JSON would fail even though the logic in
    # the yaml_parsing module succeeded should be unlikely, but is still very
    # possible due to the fact that the schemas for validation are distinct
    # between the two.
    # In order to recreate this scenario, patch the underlying method to raise
    # a ValueError (the standard error type returned when the provided YAML
    # is incompatible) and ensure the user gets a reasonable message.
    self.StartObjectPatch(yaml_schema_v1.SCHEMA, 'ConvertValue',
                          side_effect=ValueError('A conversion error.'))

    error_regex = (r'^\[(.*)\] could not be converted to the App Engine '
                   r'configuration format for the following reason: A '
                   r'conversion error.$')
    with self.assertRaisesRegex(exceptions.ConfigError, error_regex):
      self.Run('app deploy --version=1 ' + self.FullPath('app.yaml'))

  def testStaging_MavenNoAppYaml(self):
    """Tests that a deployment of Java11 Maven project functions correctly."""

    # Load a Maven pom.xml project structure without app.yaml.
    app_dir = self.Resource('tests', 'unit', 'surface', 'app', 'test_data',
                            'maven_no_appyaml')
    with file_utils.TemporaryDirectory() as staging_area:
      # Create a stager with an empty staging directory.
      stager = staging.GetStager(staging_area)
      # Call the staging phase:
      staging_dir = stager.Stage(
          os.path.join(app_dir, 'pom.xml'), app_dir, 'java-maven-project',
          env.STANDARD)

      # Staging directory should now contain a pom.xml and a generated
      # app.yaml with a single line: runtime: java11.
      staged_pom_file = os.path.join(staging_dir, 'pom.xml')
      self.AssertFileExists(staged_pom_file)
      staged_yaml_file = os.path.join(staging_dir, 'app.yaml')
      self.AssertFileExistsWithContents('runtime: java11\n', staged_yaml_file)

  def testStaging_MavenWithAppYaml(self):
    """Tests that a deployment of Java11 Maven project functions correctly."""

    # Load a Maven pom.xml project structure with app.yaml.
    app_dir = self.Resource('tests', 'unit', 'surface', 'app', 'test_data',
                            'maven_with_appyaml')
    with file_utils.TemporaryDirectory() as staging_area:
      # Create a stager with an empty staging directory.
      stager = staging.GetStager(staging_area)
      # Call the staging phase:
      staging_dir = stager.Stage(app_dir, app_dir, 'java-maven-project',
                                 env.STANDARD)

      # Staging directory should now contain a pom.xml and the
      # app.yaml from src/main/appengine directory in its root.
      staged_pom_file = os.path.join(staging_dir, 'pom.xml')
      self.AssertFileExists(staged_pom_file)
      staged_yaml_file = os.path.join(staging_dir, 'app.yaml')
      self.AssertFileExistsWithContents(
          'runtime: java11\nenv_variables:\n  SPANNER_INSTANCE: xxx\n',
          staged_yaml_file)
      # Verify that the built target/ area is not staged.
      staged_target_directory = os.path.join(staging_dir, 'target')
      if os.path.isdir(staged_target_directory):
        self.fail(
            'No expected directory [{0}] .'.format(staged_target_directory))

  def testStaging_CannotDeployMavenForJava8(self):
    """Tests deploying a Maven project does not work for GAE Java8."""

    # Load a Maven pom.xml project structure which is a Java8 GAE application.
    app_dir = self.Resource('tests', 'unit', 'surface', 'app', 'test_data',
                            'maven_gae_java8')
    with file_utils.TemporaryDirectory() as staging_area:
      # Create a stager with an empty staging directory.
      stager = staging.GetStager(staging_area)
      with self.assertRaises(staging.MavenPomNotSupported):
        stager.Stage(app_dir, app_dir, 'java-maven-project', env.STANDARD)

  def testStaging_Java11JarWithManifestClassPath(self):
    """Tests that a deployment of Java11 jar with dep jars functions correctly.
    """

    # Add a foo.jar in a temp app directory that we want to deploy as a jar.
    with file_utils.TemporaryDirectory() as app_dir:
      # exploded_jar has a complex MANIFEST.MF entry used for testing.
      dir_name = self.Resource('tests', 'unit', 'surface', 'app', 'test_data',
                               'exploded_jar')
      jar_file = os.path.join(app_dir, 'foo.jar')
      shutil.make_archive(jar_file, 'zip', dir_name)
      # Remove zip extension.
      os.rename(jar_file + '.zip', jar_file)
      # Copy dependent jar file to deploy as well.
      os.mkdir(os.path.join(app_dir, 'lib'))
      shutil.copy2(
          self.Resource('tests', 'unit', 'surface', 'app', 'test_data', 'lib',
                        'dependent.jar'), os.path.join(app_dir, 'lib'))

      with file_utils.TemporaryDirectory() as staging_area:
        # Create a stager with an empty staging directory.
        stager = staging.GetStager(staging_area)
        # Call the staging phase:
        staging_dir = stager.Stage(jar_file, app_dir, 'java-jar', env.STANDARD)

        # Staging directory should now contain a copy of the jar, and a
        # generated app.yaml with a single line: runtime: java11.
        staged_jar_file = os.path.join(staging_dir, 'foo.jar')
        self.AssertFileExists(staged_jar_file)
        staged_dependent_jar_file = os.path.join(staging_dir, 'lib',
                                                 'dependent.jar')
        self.AssertFileExists(staged_dependent_jar_file)
        staged_yaml_file = os.path.join(staging_dir, 'app.yaml')
        self.AssertFileExistsWithContents('runtime: java11\n', staged_yaml_file)

  def testDeploy_StructuredOutput(self):
    """Tests that the output of a single-service deploy matches expected."""
    self.WriteApp('app.yaml')
    self.ExpectServiceDeployed(
        'default', '1',
        deployment=self.GetDeploymentMessage(filenames=['app.yaml']))

    properties.VALUES.core.user_output_enabled.Set(True)
    structured_output = self.Run(
        ('app deploy --bucket=gs://default-bucket/ --version=1 {0}').format(
            self.FullPath('app.yaml')))
    self.assertEqual(structured_output, {
        'configs': [],
        'versions': [
            version_util.Version(self.Project(), 'default', '1')
        ]
    })

    url = 'https://{project}.appspot.com'.format(project=self.Project())
    self.AssertErrContains('Deployed service [default] to [{0}]'.format(url))
    self.AssertPostDeployHints(default_service=True)

  def testDeploy_TiRuntime(self):
    """Tests that a Ti runtime functions correctly."""
    self.WriteApp('app.yaml', data='', runtime='nodejs8')
    self.ExpectServiceDeployed(
        'default', '1',
        deployment=self.GetDeploymentMessage(filenames=['app.yaml']),
        handlers=[],
        version_call_args={'runtime': 'nodejs8', 'threadsafe': None})

    properties.VALUES.core.user_output_enabled.Set(True)
    self.Run('app deploy --bucket=gs://default-bucket/ --version=1 {0}'.format(
        self.FullPath('app.yaml')))

    # Check that if no handlers, we get https
    url = 'https://{project}.appspot.com'.format(project=self.Project())
    self.AssertErrContains('Deployed service [default] to [{0}]'.format(url))

  def testStaging_Java11JarRuntime(self):
    """Tests that a Titanium Java11 fatjar deployment functions correctly."""

    # We are trying to deploy a simple jar with a simple MANIFEST.MF.
    with file_utils.TemporaryDirectory() as app_dir:
      jar_file = self.Resource('tests', 'unit', 'surface', 'app', 'test_data',
                               'lib', 'example.jar')
      with file_utils.TemporaryDirectory() as staging_area:
        # Create a stager with an empty staging directory.
        stager = staging.GetStager(staging_area)
        # Call the staging phase:
        staging_dir = stager.Stage(jar_file, app_dir, 'java-jar', env.STANDARD)

        # Staging directory should now contain a copy of the jar, and a
        # generated app.yaml with a single line: runtime: java11.
        self.AssertFileExists(os.path.join(staging_dir, 'example.jar'))

        staged_yaml_file = os.path.join(staging_dir, 'app.yaml')
        self.AssertFileExistsWithContents('runtime: java11\n', staged_yaml_file)

  def testStaging_ErrorWhenNoMainClass(self):
    """Tests error detection when a jar is incomplete."""

    # We are trying to deploy a simple jar with a simple MANIFEST.MF.
    with file_utils.TemporaryDirectory() as app_dir:
      jar_file = self.Resource('tests', 'unit', 'surface', 'app', 'test_data',
                               'lib', 'dependent.jar')
      with file_utils.TemporaryDirectory() as staging_area:
        # Create a stager with an empty staging directory.
        stager = staging.GetStager(staging_area)

        with self.assertRaises(staging.NoMainClassError):
          stager.Stage(jar_file, app_dir, 'java-jar', env.STANDARD)

  def testDeploy_JavaStandard(self):
    """Tests that a Java standard deployment invokes staging etc."""
    with file_utils.TemporaryDirectory() as stage_dir:
      # Synthesize the staging result without running Java real staging
      self.WriteFile('app.yaml', self.APP_DATA_JAVA_YAML,
                     directory=stage_dir)
      self.StartObjectPatch(staging.Stager, 'Stage', return_value=stage_dir)
      self.WriteJavaApp()
      self.ExpectServiceDeployed(
          'default', '1',
          deployment=self.GetDeploymentMessage(
              filenames=['app.yaml'], directory=stage_dir),
          version_call_args={'runtime': 'java7'})

      properties.VALUES.core.user_output_enabled.Set(True)
      name = os.path.join('WEB-INF', 'appengine-web.xml')
      structured_output = self.Run(
          ('app deploy --bucket=gs://default-bucket/ --version=1 {0}').format(
              self.FullPath(name)))
    self.assertEqual(structured_output, {
        'configs': [],
        'versions': [
            version_util.Version(self.Project(), 'default', '1')
        ]
    })

    url = 'https://{project}.appspot.com'.format(project=self.Project())
    self.AssertErrContains('Deployed service [default] to [{0}]'.format(url))
    self.AssertPostDeployHints(default_service=True)

  def testDeploy_VmTrue(self):
    """Tests basic deploy with vm, asserts no files written to app directory."""
    self.StartObjectPatch(deploy_command_util, 'PossiblyEnableFlex')
    self.WriteVmRuntime('app.yaml', 'python-compat')
    expected_deployment = self.GetDeploymentMessage(
        filenames=['app.yaml'],
        container_image_url='appengine.gcr.io/gcloud/1.default')
    handlers = self.DefaultHandlers(with_static=True)
    beta_settings = self.VmBetaSettings(vm_runtime='python-compat')
    self.ExpectServiceDeployed('default', '1',
                               deployment=expected_deployment,
                               handlers=handlers,
                               beta_settings=beta_settings,
                               version_call_args={'vm': True, 'runtime': 'vm'})

    structured_output = self.Run(
        ('app deploy --bucket=gs://default-bucket/ --version=1 {0}').format(
            self.FullPath('app.yaml')))
    self.assertEqual(structured_output, {
        'configs': [],
        'versions': [
            version_util.Version(self.Project(), 'default', '1')
        ]
    })

    url = 'https://{project}.appspot.com'.format(
        project=self.Project())
    self.AssertErrContains('Deployed service [default] to [{0}]'.format(url))
    self.AssertErrContains('Deployments using `vm: true` have been deprecated.')
    self.AssertPostDeployHints(default_service=True)

    # Make sure no extra files were written.
    self.assertFalse(os.path.exists(self.FullPath('Dockerfile')))
    self.assertFalse(os.path.exists(self.FullPath('.dockerignore')))

  def testDeploy_StagingStep(self):
    """Make sure the staging step is invoked and that tmp dir is utilized.

    Tested here:
      - That the staging step is invoked.
      - That deploy can succeed if staging succeeds.
      - That the staging directory from the staging step is used during:
        - File upload
        - Build and docker push

    Tested in other places:
      - The staging command itself.
      - That the correct files are uploaded.
    """
    properties.VALUES.app.trigger_build_server_side.Set(False)
    self.StartPropertyPatch(config.Paths, 'sdk_root', return_value='sdk_root')
    command = staging._BundledCommand('stage.sh', 'stage.cmd')
    staging_area = '/staging-area'
    registry = runtime_registry.Registry({
        runtime_registry.RegistryEntry('python27', {env.STANDARD}): command
    })
    stager = staging.Stager(registry, staging_area)
    get_stager_mock = self.StartObjectPatch(
        staging, 'GetStager', return_value=stager, autospec=True)

    # Mocking for the staging step
    staging_dir = 'staging-dir'
    self.StartPropertyPatch(
        file_utils.TemporaryDirectory, 'path', return_value=staging_area)
    mkdtemp_mock = self.StartObjectPatch(
        tempfile, 'mkdtemp', autospec=True, return_value=staging_dir)
    self.StartObjectPatch(file_utils, 'RmTree')
    exec_mock = self.StartObjectPatch(execution_utils, 'Exec', return_value=0)

    get_source_files_mock = self.StartObjectPatch(
        source_files_util, 'GetSourceFiles', autospec=True,
        return_value=['f1', 'f2'])

    build_mock = self.StartObjectPatch(
        deploy_util.ServiceDeployer, '_PossiblyBuildAndPush',
        return_value=None)
    upload_files_mock = self.StartObjectPatch(
        deploy_app_command_util, 'CopyFilesToCodeBucket', return_value={},
        autospec=True)

    deployment_message = deployment_message = encoding.PyValueToMessage(
        self.messages.Deployment, {'files': {}})
    self.ExpectServiceDeployed('default', '1', deployment=deployment_message)

    self.WriteApp('app.yaml', runtime='python27')

    properties.VALUES.core.user_output_enabled.Set(True)
    app_yaml_path = self.FullPath('app.yaml')
    unstaged_app_dir = os.path.dirname(app_yaml_path)
    self.Run(
        ('app deploy --bucket=gs://default-bucket/ --version=1 {0}').format(
            app_yaml_path))

    url = 'https://{project}.appspot.com'.format(project=self.Project())
    self.AssertErrContains('Deployed service [default] to [{0}]'.format(url))
    self.AssertPostDeployHints(default_service=True)
    self.assertEqual(get_stager_mock.call_count, 1)
    mkdtemp_mock.assert_called_with(dir=staging_area)
    exec_mock.assert_called_once_with(
        [os.path.join('sdk_root', command.name), mock.ANY, mock.ANY,
         staging_dir], no_exit=True, out_func=mock.ANY, err_func=mock.ANY)

    self.assertNotEqual(unstaged_app_dir, staging_dir)

    get_source_files_mock.assert_called_once_with(
        staging_dir, mock.ANY, mock.ANY, mock.ANY, mock.ANY,
        unstaged_app_dir, None)

    build_mock.assert_called_once_with(
        mock.ANY, mock.ANY, staging_dir, ['f1', 'f2'], mock.ANY, mock.ANY,
        mock.ANY, deploy_util.FlexImageBuildOptions.ON_CLIENT)
    upload_files_mock.assert_called_once_with(staging_dir,
                                              ['f1', 'f2'], mock.ANY,
                                              max_file_size=32 * 1024 * 1024)

  def testDeploy_CustomStaging(self):
    """Tests that an explicit --staging-command gets run."""
    command = self.Touch(self.temp_path, 'my-command')
    self.StartObjectPatch(deploy_app_command_util, 'CopyFilesToCodeBucket',
                          autospec=True, return_value={})
    self.StartObjectPatch(enable_api, 'EnableServiceIfDisabled')
    exec_mock = self.StartObjectPatch(execution_utils, 'Exec', return_value=0)

    deployment_message = encoding.PyValueToMessage(
        self.messages.Deployment, {'files': {}})
    self.ExpectServiceDeployed('default', '1', deployment=deployment_message)
    self.WriteApp('app.yaml', runtime='python27')
    self.Run(
        'app deploy --bucket=gs://default-bucket/ --version=1 {0} '
        '--staging-command={1}'.format(self.FullPath('app.yaml'), command))

    exec_mock.assert_called_once_with(
        [command, mock.ANY, mock.ANY, mock.ANY],
        no_exit=True, out_func=mock.ANY, err_func=mock.ANY)

  def testDeploy_CustomDomain(self):
    """Test correct deployment with a custom domain."""
    project = 'example.com:' + self.Project()
    self.WriteApp('app.yaml')
    # Expect a GetApplication request.
    hostname = self.Project() + '.example.com'
    self.ExpectServiceDeployed('default', '1',
                               deployment=self.GetDeploymentMessage(
                                   filenames=['app.yaml']),
                               hostname=hostname,
                               project=project)

    properties.VALUES.core.user_output_enabled.Set(True)
    self.Run(
        ('app deploy --project={project} --bucket=gs://default-bucket/ '
         '--version=1 {deployable}').format(
             project=project,
             deployable=self.FullPath('app.yaml')))

    url = 'https://{0}'.format(hostname)
    self.AssertErrContains('Deployed service [default] to [{0}]'.format(url))

  def testDeploy_ModuleInAppYaml(self):
    """Test deploy, deprecation warning with non-default module in app.yaml."""
    self.WriteApp('app.yaml', module='cupcake')
    # Simulate SetDefault failing twice so the retry logic kicks in.
    self.ExpectServiceDeployed('cupcake', '1', set_default=3,
                               deployment=self.GetDeploymentMessage(
                                   filenames=['app.yaml']))

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '{0}').format(self.FullPath('app.yaml')))

    self.AssertErrContains(
        'Field module is deprecated; use service instead')
    self.AssertPostDeployHints(single_service='cupcake')

  def testDeploy_ModuleInAppYamlSetDefaultFailure(self):
    """Test successful deploy and warning when deploy fails to set default."""
    self.WriteApp('app.yaml', module='carrot')
    # Simulate SetDefault failing four times so the retry logic kicks in.
    self.ExpectServiceDeployed('carrot', '1', set_default=4,
                               set_default_success=False,
                               deployment=self.GetDeploymentMessage(
                                   filenames=['app.yaml']))

    error_regex = ('Your deployment has succeeded, but promoting the new '
                   'version to default failed. You may not have permissions '
                   'to change traffic splits.')
    with self.assertRaisesRegex(deploy_util.VersionPromotionError,
                                error_regex):
      self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
                '{0}').format(self.FullPath('app.yaml')))

  def testDeploy_ServiceInAppYaml(self):
    """Tests deployment and end hint for non-default service in app.yaml."""
    self.WriteApp('app.yaml', service='fakeservice')
    self.ExpectServiceDeployed('fakeservice', '1',
                               deployment=self.GetDeploymentMessage(
                                   filenames=['app.yaml']))

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '{0}').format(self.FullPath('app.yaml')))

    self.AssertErrNotContains(
        'The "module" parameter in application .yaml files is deprecated.')
    self.AssertErrNotContains('Please use the "service" parameter instead.')
    self.AssertPostDeployHints(single_service='fakeservice')

  def testDeploy_TwoServicesInAppYaml(self):
    """Tests deployment of two different services, and end hint."""
    self.WriteApp('app.yaml')
    self.WriteApp('app2.yaml', service='fakeservice')
    deployment = self.GetDeploymentMessage(filenames=['app.yaml', 'app2.yaml'])
    self.ExpectServicesDeployed([('default', '1'),
                                 ('fakeservice', '1')],
                                deployment=deployment)
    properties.VALUES.core.user_output_enabled.Set(True)
    structured_output = self.Run(
        ('app deploy {0} {1} --bucket=gs://default-bucket/ '
         '--version=1').format(self.FullPath('app.yaml'),
                               self.FullPath('app2.yaml')))
    self.assertEqual(structured_output,
                     {'configs': [],
                      'versions': [
                          version_util.Version(self.Project(),
                                               'default', '1'),
                          version_util.Version(self.Project(),
                                               'fakeservice', '1')]})
    self.AssertPostDeployHints(multiple_services=True)

  def testDeploy_InvalidVersionFlag(self):
    """Test no API calls made and error raised with invalid --version."""
    self.WriteApp('app.yaml')
    with self.AssertRaisesArgumentErrorRegexp(
        'May only contain lowercase letters'):
      self.Run(('app deploy --version=CapitalLettersInHere '
                '{0}').format(self.FullPath('app.yaml')))

  def testStopPreviousVersion_NoPreviousVersion(self):
    """Test deploy with --stop-previous-version if no previous versions."""
    self.MakeApp()
    # No stop call should be made if no previous versions exist.
    self.ExpectServiceDeployed('default', '1',
                               deployment=self.GetDeploymentMessage())

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '--stop-previous-version {0}').format(self.FullPath('app.yaml')))

    self.AssertPostDeployHints(default_service=True)

  def testStopPreviousVersion_PreviousVersions_VmTrue(self):
    """Test deploy with --stop-previous-version and VM."""
    existing_services = {'default': {'a': {'traffic_split': 1.0,
                                           'vm': True}}}
    self.MakeApp()
    self.ExpectServiceDeployed('default', '1', stop_version='a',
                               existing_services=existing_services,
                               deployment=self.GetDeploymentMessage())

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '--stop-previous-version {0}').format(self.FullPath('app.yaml')))
    self.AssertPostDeployHints(default_service=True, stop_version='a')

  def testStopPreviousVersion_PreviousVersions_EnvFlex(self):
    """Test deploy with --stop-previous-version in Flex."""
    existing_services = {'default': {'a': {'traffic_split': 1.0,
                                           'env': 'flex'}}}
    self.MakeApp()
    self.ExpectServiceDeployed('default', '1', stop_version='a',
                               existing_services=existing_services,
                               deployment=self.GetDeploymentMessage())

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '--stop-previous-version {0}').format(self.FullPath('app.yaml')))
    self.AssertPostDeployHints(default_service=True, stop_version='a')

  def testStopPreviousVersion_PreviousVersion_SameId(self):
    """Test deploy with --stop-previous-version if version ID unchanged."""
    existing_services = {'default': {'a': {'traffic_split': 1.0,
                                           'vm': True}}}
    self.MakeApp()
    self.ExpectServiceDeployed('default', 'a',
                               existing_services=existing_services,
                               stop_version='a',
                               deployment=self.GetDeploymentMessage())

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=a '
              '--stop-previous-version {0}').format(self.FullPath('app.yaml')))
    self.AssertPostDeployHints(default_service=True, stop_version=None)

  def testStopPreviousVersion_PreviousVersions_VmFalseBasicScaling(self):
    """Test deploy with --stop-previous-version, no VM, and basic scaling."""
    existing_services = {
        'default': {'a': {'traffic_split': 1.0,
                          'basic_scaling': self.messages.BasicScaling()},
                    'b': {}}}
    self.MakeApp()
    self.ExpectServiceDeployed('default', '1', stop_version='a',
                               existing_services=existing_services,
                               deployment=self.GetDeploymentMessage())

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '--stop-previous-version {0}').format(self.FullPath('app.yaml')))
    self.AssertPostDeployHints(default_service=True, stop_version='a')

  def testStopPreviousVersion_PreviousVersions_VmFalseManualScaling(self):
    """Test deploy with --stop-previous-version, no VM, and manual scaling."""
    existing_services = {
        'default': {
            'a': {'traffic_split': 1.0,
                  'manual_scaling': self.messages.ManualScaling()},
            'b': {'traffic_split': 0.0}}}
    self.MakeApp()
    self.ExpectServiceDeployed('default', '1', stop_version='a',
                               existing_services=existing_services,
                               deployment=self.GetDeploymentMessage())

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '--stop-previous-version {0}').format(self.FullPath('app.yaml')))
    self.AssertPostDeployHints(default_service=True, stop_version='a')

  def testStopPreviousVersion_PreviousVersions_VmFalseAutomaticScaling(self):
    """Test --stop-previous-version with autoscaling standard app."""
    existing_services = {'default': {'a': {'traffic_split': 1.0},
                                     'b': {'traffic_split': 1.0}}}

    self.MakeApp()

    # Autoscaling standard-environment apps cannot be stopped.
    self.ExpectServiceDeployed('default', '1',
                               existing_services=existing_services,
                               stop_version='a',
                               stop_version_suppressed=True,
                               deployment=self.GetDeploymentMessage())

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '--stop-previous-version {0}').format(self.FullPath('app.yaml')))
    self.AssertPostDeployHints(default_service=True, stop_version=None)

  def testStopPreviousVersion_NoDefaultPreviousVersions(self):
    """Test --stop-previous-version with no default version."""
    existing_services = {
        'default': {'a': {'traffic_split': 0.5}, 'b': {'traffic_split': 0.5}}}
    self.MakeApp()

    # No stop version call should be made if there is no default version.
    self.ExpectServiceDeployed('default', '1',
                               existing_services=existing_services,
                               stop_version='a',
                               stop_version_suppressed=True,
                               deployment=self.GetDeploymentMessage())

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '--stop-previous-version {0}').format(self.FullPath('app.yaml')))

  def testPollsOperationNoPromote(self):
    """Test with --no-promote."""
    self.MakeApp()
    self.ExpectServiceDeployed('default', '1', set_default=0,
                               deployment=self.GetDeploymentMessage())

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '--no-promote {m}').format(m=self.FullPath('app.yaml')))

  def testPollsOperation(self):
    """Ensure that we poll the operation until it is complete (2 retries)."""
    self.MakeApp()
    self.ExpectServiceDeployed('default', '1', create_attempts=3,
                               deployment=self.GetDeploymentMessage())

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '{m}').format(m=self.FullPath('app.yaml')))

  def testPollsExhausted(self):
    """Test deploy where the max retries for create version is exceeded."""
    self.MakeApp()
    # Add one attempt for the first CreateService call.
    num_attempts = operations_util.DEFAULT_OPERATION_MAX_TRIES + 1
    self.ExpectServiceDeployed('default', '1', create_attempts=num_attempts,
                               create_success=False,
                               set_default=False,
                               deployment=self.GetDeploymentMessage())

    error_regex = r'Operation \[{0}\] timed out.'.format(
        api_test_util.VersionOperationName(self.Project(), 'default'))
    with self.assertRaisesRegex(operations_util.OperationTimeoutError,
                                error_regex):
      self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
                '{m}').format(m=self.FullPath('app.yaml')))

  def testPollWithErrorAsResult(self):
    """Test OperationError raised when polling errors."""
    self.MakeApp()
    self.ExpectGetApplicationRequest(self.Project())
    self.ExpectListServicesRequest(self.Project())
    deployment = self.GetDeploymentMessage()
    version_call = self.GetCreateVersionCall(self.Project(), 'default',
                                             '1', runtime='python27',
                                             api_version='1',
                                             deployment=deployment)
    self.mock_client.apps_services_versions.Create.Expect(
        version_call,
        response=self.CreateVersionErrorResponse(
            self.Project(),
            'default'
        )
    )

    with self.assertRaisesRegex(operations_util.OperationError,
                                'Error Response:'):
      self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
                '{m}').format(m=self.FullPath('app.yaml')))

  def testPollWithErrorAsResult_NonAscii(self):
    """Test OperationError with non-ascii message."""
    self.MakeApp()
    self.ExpectGetApplicationRequest(self.Project())
    self.ExpectListServicesRequest(self.Project())
    deployment = self.GetDeploymentMessage()
    version_call = self.GetCreateVersionCall(self.Project(), 'default',
                                             '1', runtime='python27',
                                             api_version='1',
                                             deployment=deployment)
    self.mock_client.apps_services_versions.Create.Expect(
        version_call,
        response=self.CreateVersionErrorResponse(
            self.Project(),
            'default',
            message='foo\u3094bar'
        )
    )

    # assertRaisesRegexp does not work with unicode.
    with self.assertRaises(operations_util.OperationError):
      self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
                '{m}').format(m=self.FullPath('app.yaml')))
    self.AssertErrContains(
        'ERROR: (gcloud.app.deploy) Error Response: [UNKNOWN] foo\\u3094bar')

  def testGeneratesDeploymentManifestForAllFiles(self):
    """Test the correct deployment manifest is sent."""
    service_path = self.WriteApp('app.yaml',
                                 data=self.APP_DATA + self.SKIP_FILES_DATA)
    config_dir = os.path.dirname(service_path)
    # Write three files within the same directory as the configuration file.
    # Two of the files should be included, and one shouldn't (due to the
    # skip_files_regex in the YAML).
    self.WriteFile(self.HANDLER_FILE, self.HANDLER_CONTENT,
                   directory=config_dir)
    self.WriteFile(self.UTIL_FILE, self.UTIL_CONTENT, directory=config_dir)
    self.WriteFile('fake.zip', 'Dummy', directory=config_dir)
    # Write a file in a subdirectory.
    os.mkdir(os.path.join(config_dir, 'subdir'))
    self.WriteFile('emptyfile', 'empty',
                   directory=os.path.join(config_dir, 'subdir'))
    expected_deployment = self.GetDeploymentMessage(
        filenames=[self.HANDLER_FILE, self.UTIL_FILE, 'app.yaml',
                   os.path.join('subdir', 'emptyfile')])

    self.ExpectServiceDeployed(
        'default', '1',
        deployment=expected_deployment)

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '{m}').format(m=service_path))

  def testGeneratesDeploymentManifestForNoFilesFlex(self):
    """Test that files are not in manifest with env: 2."""
    properties.VALUES.app.trigger_build_server_side.Set(False)
    self.StartObjectPatch(deploy_command_util, 'PossiblyEnableFlex')
    service_path = self.WriteFlexRuntime('app.yaml', 'python-compat')
    config_dir = os.path.dirname(service_path)
    # Write three files within the same directory as the configuration file.
    # These files would be included without env: 2, but should be left out with
    # it.
    self.WriteFile(self.HANDLER_FILE, self.HANDLER_CONTENT,
                   directory=config_dir)
    self.WriteFile(self.UTIL_FILE, self.UTIL_CONTENT, directory=config_dir)
    self.WriteFile('fake.zip', 'Dummy', directory=config_dir)

    expected_container = 'appengine.gcr.io/gcloud/1.default'

    expected_deployment = self.GetDeploymentMessage(
        filenames=[],
        container_image_url=expected_container)

    self.ExpectServiceDeployed('default', '1',
                               deployment=expected_deployment,
                               handlers=self.DefaultHandlers(with_static=True),
                               version_call_args={
                                   'env': 'flex',
                                   'runtime': 'vm'},
                               beta_settings=self.VmBetaSettings(
                                   vm_runtime='python-compat'))
    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '{m}').format(m=service_path))

  def testUsesDefaultBucketIfNoneProvided(self):
    """Test that deploy uses default bucket if none provided."""
    self.MakeApp()

    code_bucket = '{0}-staging.appspot.com'.format(self.Project())
    expected_deployment = self.GetDeploymentMessage(
        source_url_base=('https://storage.googleapis.com/'
                         '{}-staging.appspot.com/'.format(self.Project())))
    self.ExpectServiceDeployed('default', '1',
                               default_bucket='gs://{0}/'.format(code_bucket),
                               deployment=expected_deployment)

    self.Run('app deploy --version=1 {m}'.format(m=self.FullPath('app.yaml')))

  def testStagingDirectoryBuiltOnWindows(self):
    self.MakeApp()
    self.ExpectServiceDeployed('default', '1',
                               deployment=self.GetDeploymentMessage())

    # Patch so that os.symlink does not exist and is not callable.
    # On Windows environments patching fails because symlink doesn't exist.
    if hasattr(os, 'symlink'):
      self.mock_symlink = self.StartObjectPatch(os, 'symlink',
                                                side_effect=AttributeError())

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '{m}').format(m=self.FullPath('app.yaml')))

  def testDeploy_CronYaml(self):
    """Test deployment and hinting for cron.yaml."""
    self.WriteConfig(self.CRON_DATA)
    self.ExpectGetApplicationRequest(self.Project())
    structured_output = self.Run('app deploy {0}'.format(
        self.FullPath(self.CRON_DATA[0])))

    self.assertEqual(structured_output, {
        'configs': ['cron'],
        'versions': []
    })
    self.AssertConfigDeployed(cron=True)
    self.AssertPostDeployHints(cron=True, cron_with_tasks=True)

  def testDeploy_CronYaml_AuthDisabled(self):
    """Test deployment and hinting for cron.yaml with auth disabled.

    This is the same test as above, just to test that we still make the same
    requests even when auth is disabled.
    """
    properties.VALUES.auth.disable_credentials.Set(True)
    self.WriteConfig(self.CRON_DATA)
    self.ExpectGetApplicationRequest(self.Project())
    structured_output = self.Run('app deploy {0}'.format(
        self.FullPath(self.CRON_DATA[0])))

    self.assertEqual(structured_output, {
        'configs': ['cron'],
        'versions': []
    })
    self.AssertConfigDeployed(cron=True)
    self.AssertPostDeployHints(cron=True, cron_with_tasks=True)

  def testDeploy_DispatchYaml(self):
    """Test deployment and hinting for dispatch.yaml."""
    self.WriteConfig(self.DISPATCH_DATA)
    self.ExpectGetApplicationRequest(self.Project())
    structured_output = self.Run('app deploy {0}'.format(
        self.FullPath(self.DISPATCH_DATA[0])))

    self.assertEqual(structured_output, {
        'configs': ['dispatch'],
        'versions': []
    })
    self.AssertConfigDeployed(dispatch=True)
    self.AssertPostDeployHints(dispatch=True)

  def testDeploy_DosYaml(self):
    """Test deployment and hinting for dos.yaml."""
    self.WriteConfig(self.DOS_DATA)
    self.ExpectGetApplicationRequest(self.Project())
    structured_output = self.Run('app deploy {0}'.format(
        self.FullPath(self.DOS_DATA[0])))

    self.assertEqual(structured_output, {
        'configs': ['dos'],
        'versions': []
    })
    self.AssertConfigDeployed(dos=True)
    self.AssertPostDeployHints(dos=True)

  def testDeploy_IndexYaml(self):
    """Test deployment and hinting for index.yaml."""
    enable_api_mock = self.StartObjectPatch(enable_api, 'IsServiceEnabled',
                                            return_value=True)
    self.WriteConfig(self.INDEX_DATA)
    self.ExpectGetApplicationRequest(self.Project())
    structured_output = self.Run('app deploy {0}'.format(
        self.FullPath(self.INDEX_DATA[0])))

    self.assertEqual(structured_output, {
        'configs': ['index'],
        'versions': []
    })
    self.AssertConfigDeployed(index=True)
    # QUEUE_TASKS_WARNING should only be displayed when deploying queue.yaml
    # even if cloudtasks api is enabled.
    enable_api_mock.assert_not_called()
    self.AssertErrNotContains(output_helpers.QUEUE_TASKS_WARNING,
                              normalize_space=True)
    self.AssertPostDeployHints(index=True)

  def testDeploy_QueueYaml(self):
    """Test deployment and hinting for queue.yaml."""
    enable_api_mock = self.StartObjectPatch(enable_api, 'IsServiceEnabled',
                                            return_value=False)
    self.WriteConfig(self.QUEUE_DATA)
    self.ExpectGetApplicationRequest(self.Project())
    structured_output = self.Run('app deploy {0}'.format(
        self.FullPath(self.QUEUE_DATA[0])))

    self.assertEqual(structured_output, {
        'configs': ['queue'],
        'versions': []
    })
    self.AssertConfigDeployed(queue=True)
    enable_api_mock.assert_called_once_with(self.Project(),
                                            'cloudtasks.googleapis.com')
    self.AssertErrNotContains(output_helpers.QUEUE_TASKS_WARNING,
                              normalize_space=True)
    self.AssertPostDeployHints(queue=True)

  def testDeploy_QueueYamlWithWarning(self):
    """Test deployment and hinting for queue.yaml with task queue warning."""
    enable_api_mock = self.StartObjectPatch(enable_api, 'IsServiceEnabled',
                                            return_value=True)
    self.WriteConfig(self.QUEUE_DATA)
    self.ExpectGetApplicationRequest(self.Project())
    structured_output = self.Run('app deploy {0}'.format(
        self.FullPath(self.QUEUE_DATA[0])))

    self.assertEqual(structured_output, {
        'configs': ['queue'],
        'versions': []
    })
    self.AssertConfigDeployed(queue=True)
    enable_api_mock.assert_called_once_with(self.Project(),
                                            'cloudtasks.googleapis.com')
    self.AssertErrContains(output_helpers.QUEUE_TASKS_WARNING,
                           normalize_space=True)
    self.AssertPostDeployHints(queue=True)

  def testDeploy_QueueYamlServiceApiNotConclusive(self):
    """Test hinting for queue.yaml in case S.M. API is not accessible.

    This occurs when the API responds with 403, 404, and the interpretation is
    that we don't know whether it's enabled. In those cases, we should not fail
    but simply display the warning anyway, with a false positive rate.
    """
    err = sm_exceptions.ListServicesPermissionDeniedException()
    enable_api_mock = self.StartObjectPatch(enable_api, 'IsServiceEnabled',
                                            side_effect=err)
    self.WriteConfig(self.QUEUE_DATA)
    self.ExpectGetApplicationRequest(self.Project())
    structured_output = self.Run('app deploy {0}'.format(
        self.FullPath(self.QUEUE_DATA[0])))

    self.assertEqual(structured_output, {
        'configs': ['queue'],
        'versions': []
    })
    self.AssertConfigDeployed(queue=True)
    enable_api_mock.assert_called_once_with(self.Project(),
                                            'cloudtasks.googleapis.com')
    self.AssertErrContains(output_helpers.QUEUE_TASKS_WARNING,
                           normalize_space=True)
    self.AssertPostDeployHints(queue=True)

  def testDeploy_MultiConfig(self):
    """Test deployment and hinting for multiple .yaml files."""
    enable_api_mock = self.StartObjectPatch(enable_api, 'IsServiceEnabled',
                                            return_value=False)
    self.WriteConfig(self.CRON_DATA)
    self.WriteConfig(self.QUEUE_DATA)
    self.WriteConfig(self.INDEX_DATA)
    self.ExpectGetApplicationRequest(self.Project())
    structured_output = self.Run('app deploy {0} {1} {2}'.format(
        self.FullPath(self.CRON_DATA[0]),
        self.FullPath(self.QUEUE_DATA[0]),
        self.FullPath(self.INDEX_DATA[0])))

    self.assertEqual(set(structured_output['configs']),
                     {'cron', 'index', 'queue'})
    self.assertEqual(structured_output['versions'], [])
    self.AssertConfigDeployed(cron=True, queue=True, index=True)
    enable_api_mock.assert_called_once_with(self.Project(),
                                            'cloudtasks.googleapis.com')
    self.AssertErrNotContains(output_helpers.QUEUE_TASKS_WARNING,
                              normalize_space=True)
    self.AssertPostDeployHints(cron=True, queue=True, index=True)

  def testDeploy_MultiConfigiWithQueueWarning(self):
    """Test deployment and hinting for multiple .yaml files."""
    enable_api_mock = self.StartObjectPatch(enable_api, 'IsServiceEnabled',
                                            return_value=True)
    self.WriteConfig(self.CRON_DATA)
    self.WriteConfig(self.QUEUE_DATA)
    self.WriteConfig(self.INDEX_DATA)
    self.ExpectGetApplicationRequest(self.Project())
    structured_output = self.Run('app deploy {0} {1} {2}'.format(
        self.FullPath(self.CRON_DATA[0]),
        self.FullPath(self.QUEUE_DATA[0]),
        self.FullPath(self.INDEX_DATA[0])))

    self.assertEqual(set(structured_output['configs']),
                     {'cron', 'index', 'queue'})
    self.assertEqual(structured_output['versions'], [])
    self.AssertConfigDeployed(cron=True, queue=True, index=True)
    enable_api_mock.assert_called_once_with(self.Project(),
                                            'cloudtasks.googleapis.com')
    self.AssertErrContains(output_helpers.QUEUE_TASKS_WARNING,
                           normalize_space=True)
    self.AssertPostDeployHints(cron=True, queue=True, index=True)


class DeployWithFlexBase(DeployWithApiTestsBase, build_base.BuildBase):

  def SetUp(self):
    self.execute_build_patch = self.StartObjectPatch(
        build.CloudBuildClient, 'ExecuteCloudBuild', return_value='fake-image')
    self.execute_build_async_patch = self.StartObjectPatch(
        build.CloudBuildClient,
        'ExecuteCloudBuildAsync',
        return_value=self.build_op)
    self.addCleanup(properties.VALUES.app.use_runtime_builders.Set,
                    properties.VALUES.app.use_runtime_builders.Get())
    self.cloudbuild_messages = cloudbuild_util.GetMessagesModule()
    self.mock_cloudbuild_client = apitools_mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mock_cloudbuild_client.Mock()
    self.cloud_client_mock = mock.MagicMock()
    self.StartObjectPatch(
        cloudbuild_logs, 'CloudBuildClient',
        return_value=self.cloud_client_mock)
    self.addCleanup(self.mock_cloudbuild_client.Unmock)
    self.addCleanup(self.cloud_client_mock.Unmock)

    def _GetBuilderRef(self):
      return runtime_builders.BuilderReference(
          self.runtime, 'path', deprecation_message='BUILDER DEPRECATED')
    self.StartObjectPatch(
        runtime_builders.Resolver, 'GetBuilderReference',
        autospec=True, side_effect=_GetBuilderRef)
    self.load_cloud_build_mock = self.StartObjectPatch(
        runtime_builders.BuilderReference, 'LoadCloudBuild',
        return_value=self.cloudbuild_messages.Build())

  def _ExpectServiceDeployed(self, runtime='python-compat'):
    expected_deployment = self.messages.Deployment(
        container=self.messages.ContainerInfo(
            image='us.gcr.io/{}/appengine/default.1:latest'.format(
                self.Project())))
    beta_settings = self.VmBetaSettings(vm_runtime=runtime)
    handlers = self.DefaultHandlers(with_static=True)
    self.ExpectServiceDeployed(
        'default', '1',
        deployment=expected_deployment,
        beta_settings=beta_settings,
        version_call_args={'env': 'flex', 'runtime': 'vm'},
        handlers=handlers)

  def _ExpectServiceDeployedWithBuildId(self, runtime='python-compat'):
    expected_deployment = self.messages.Deployment(
        build=self.messages.BuildInfo(cloudBuildId='build-id'))
    beta_settings = self.VmBetaSettings(vm_runtime=runtime)
    handlers = self.DefaultHandlers(with_static=True)
    self.ExpectServiceDeployed(
        'default',
        '1',
        deployment=expected_deployment,
        beta_settings=beta_settings,
        version_call_args={'env': 'flex',
                           'runtime': 'vm'},
        handlers=handlers)

  def _ExpectServiceDeployedWithBuildOptions(self,
                                             runtime='python-compat',
                                             warning=None,
                                             build_id=None,
                                             timeout=None,
                                             directory=None,
                                             filenames=None):
    expected_deployment = self.GetDeploymentMessage(
        filenames=filenames or ['app.yaml'], directory=directory)
    expected_deployment.cloudBuildOptions = self.messages.CloudBuildOptions(
        appYamlPath='app.yaml', cloudBuildTimeout=timeout)
    create_version_metadata = None
    if build_id:
      create_version_metadata = self.messages.CreateVersionMetadataV1Beta(
          cloudBuildId=build_id)
    operation_metadata = encoding.PyValueToMessage(
        self.messages.Operation.MetadataValue,
        encoding.MessageToPyValue(
            self.messages.OperationMetadataV1Beta(
                warning=[warning] if warning else [],
                createVersionMetadata=create_version_metadata,
            )))
    beta_settings = self.VmBetaSettings(vm_runtime=runtime)
    handlers = self.DefaultHandlers(with_static=True)
    self.ExpectServiceDeployed(
        'default',
        '1',
        deployment=expected_deployment,
        beta_settings=beta_settings,
        version_call_args={
            'env': 'flex',
            'runtime': 'vm'
        },
        operation_metadata=operation_metadata,
        handlers=handlers)


class FlexDeployWithApiTests(DeployWithFlexBase):

  def SetUp(self):
    self.service_path = self.WriteApp('app.yaml', data=self.APP_DATA_ENV_FLEX,
                                      runtime='python-compat')
    self._RuntimeBuilderExperimentEnabled()

  def _ServiceManagementExpectListServicesRequest(self,
                                                  enabled=False,
                                                  error=None):
    state_type = self.su_services_messages.GoogleApiServiceusageV1Service.StateValueValuesEnum
    service = self.su_services_messages.GoogleApiServiceusageV1Service(
        state=state_type.ENABLED if enabled else state_type.DISABLED)
    self.su_mocked_client.services.Get.Expect(
        self.su_services_messages.ServiceusageServicesGetRequest(
            name='projects/%s/services/appengineflex.googleapis.com' %
            self.Project(),),
        response=None if error else service,
        exception=error)

  def _ServiceManagementExpectEnableServicesRequest(self, error=None):
    operation = self.su_services_messages.Operation(
        name='12345',
        done=False,
    )
    complete_operation = self.su_services_messages.Operation(
        name='12345',
        done=True,
    )
    self.su_mocked_client.services.Enable.Expect(
        request=self.su_services_messages.ServiceusageServicesEnableRequest(
            name='projects/%s/services/appengineflex.googleapis.com' %
            self.Project(),),
        response=None if error else operation,
        exception=error,
    )
    if not error:
      self.su_mocked_client.operations.Get.Expect(
          request=self.su_services_messages.ServiceusageOperationsGetRequest(
              name='12345'),
          response=complete_operation)

  def testSkipFilesWithFlex(self):
    """Test that skip files is respected in cloud build."""
    properties.VALUES.app.trigger_build_server_side.Set(False)
    self._ExpectServiceDeployed()
    self._ServiceManagementExpectListServicesRequest(enabled=True)
    service_path = self.WriteApp(
        'app.yaml',
        data=self.APP_DATA_ENV_FLEX + self.SKIP_FILES_DATA,
        runtime='python-compat',
        beta_settings='')
    config_dir = os.path.dirname(service_path)
    # Create some files within the same directory as the configuration file.
    # Two of the files should be included, and one shouldn't (due to the
    # skip_files_regex in the YAML).
    self.WriteFile(self.HANDLER_FILE, self.HANDLER_CONTENT,
                   directory=config_dir)
    self.WriteFile(self.UTIL_FILE, self.UTIL_CONTENT, directory=config_dir)
    self.WriteFile('fake.zip', 'Dummy', directory=config_dir)
    # Make sure subdirectories that aren't skipped are included.
    os.mkdir(os.path.join(config_dir, 'tmp'))
    self.WriteFile('fake2.txt', 'Dummy',
                   directory=os.path.join(config_dir, 'tmp'))
    create_tar_mock = self.StartObjectPatch(cloud_build, '_CreateTar')

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '{m}').format(m=service_path))
    create_tar_mock.assert_called_once_with(
        config_dir,
        mock.ANY,
        set(['app.yaml', self.HANDLER_FILE, self.UTIL_FILE,
             os.path.join('tmp', 'fake2.txt')]),
        mock.ANY)

  def testDefaultSkipFilesWithFlex(self):
    """Test that the default skip files for flexible deployments is correct."""
    self._ServiceManagementExpectListServicesRequest(enabled=True)
    service_path = self.WriteApp(
        'app.yaml',
        data=self.APP_DATA_ENV_FLEX,
        runtime='python-compat',
        beta_settings='')
    config_dir = os.path.dirname(service_path)
    # Create some files within the same directory as the configuration file.
    # The node_modules directory and .git should be skipped when uploading
    # source by default. Other hidden files should not be.
    self.WriteFile(self.HANDLER_FILE, self.HANDLER_CONTENT,
                   directory=config_dir)
    self.WriteFile(self.UTIL_FILE, self.UTIL_CONTENT, directory=config_dir)
    self.WriteFile('.hiddenfile', 'empty', directory=config_dir)
    os.mkdir(os.path.join(config_dir, '.git'))
    self.WriteFile('gitfile', 'empty',
                   directory=os.path.join(config_dir, '.git'))
    os.mkdir(os.path.join(config_dir, 'node_modules'))
    self.WriteFile('badfile', 'empty',
                   directory=os.path.join(config_dir, 'node_modules'))
    os.mkdir(os.path.join(config_dir, 'not_ignored'))
    self.WriteFile('goodfile', 'empty',
                   directory=os.path.join(config_dir, 'not_ignored'))
    self._ExpectServiceDeployedWithBuildOptions(
        directory=config_dir,
        filenames=[
            'app.yaml', self.HANDLER_FILE, self.UTIL_FILE, '.hiddenfile',
            os.path.join('not_ignored', 'goodfile')
        ])

    self.Run(('app deploy --bucket=gs://default-bucket/ --version=1 '
              '{m}').format(m=service_path))

  def testDeploy_GaRespectsRuntimeBuildersConfig(self):
    """Tests that non-beta deployments still respect the config flag.

    python-compat is *not* whitelisted, so it wouldn't get a
    load_cloud_build_mock call unless it the use_runtime_builders property was
    respected.
    """
    properties.VALUES.app.use_runtime_builders.Set(True)
    properties.VALUES.app.trigger_build_server_side.Set(False)
    self._ExpectServiceDeployed('python-compat')
    self._ServiceManagementExpectListServicesRequest(enabled=True)
    service_path = self.WriteApp('app.yaml', data=self.APP_DATA_ENV_FLEX,
                                 runtime='python-compat')

    self.Run('app deploy --bucket=gs://default-bucket/ --version=1 ' +
             service_path)

    self.load_cloud_build_mock.assert_called_once_with(
        {'_OUTPUT_IMAGE': 'us.gcr.io/{}/appengine/default.1:latest'.format(
            self.Project()),
         '_GAE_APPLICATION_YAML_PATH': 'app.yaml'})

  def testDeploy_GaDoesNotUseBetaWhitelistedRuntimeBuilders(self):
    """Tests that non-beta deployments don't use beta whitelisted builders.
    """
    self._ExpectServiceDeployed('test-beta')
    properties.VALUES.app.trigger_build_server_side.Set(False)
    self._ServiceManagementExpectListServicesRequest(enabled=True)
    service_path = self.WriteApp('app.yaml', data=self.APP_DATA_ENV_FLEX,
                                 runtime='test-beta')

    self.Run('app deploy --bucket=gs://default-bucket/ --version=1 ' +
             service_path)

    self.load_cloud_build_mock.assert_not_called()

  def testDeploy_GaUsesWhitelistedRuntimeBuilders(self):
    """Tests that non-beta deployments use GA whitelisted runtime builders.
    """
    self._ServiceManagementExpectListServicesRequest(enabled=True)
    service_path = self.WriteApp('app.yaml', data=self.APP_DATA_ENV_FLEX,
                                 runtime='test-ga')
    self._ExpectServiceDeployedWithBuildOptions(
        'test-ga',
        directory=os.path.dirname(service_path))

    self.Run('app deploy --bucket=gs://default-bucket/ --version=1 ' +
             service_path)

  def testDeploy_EnablesFlexSuccessfully(self):
    """Test that deploy command attempts to enable Flexible API."""
    self._ServiceManagementExpectListServicesRequest(enabled=False)
    self._ServiceManagementExpectEnableServicesRequest()
    self._ExpectServiceDeployedWithBuildOptions()

    self.Run('app deploy {} --version=1 '.format(self.service_path))

  def testDeploy_FlexEnabled(self):
    """Test that deploy command attempts to enable Flexible API."""
    self._ServiceManagementExpectListServicesRequest(enabled=True)
    self._ExpectServiceDeployedWithBuildOptions()
    self.Run('app deploy {} --version=1 '.format(self.service_path))

  def testDeploy_FlexEnabled_runtimeBuilderOptout(self):
    """Test that deploy command attempts to enable Flexible API."""
    properties.VALUES.app.use_runtime_builders.Set(False)
    self._ServiceManagementExpectListServicesRequest(enabled=True)
    self._ExpectServiceDeployed()
    self.Run('app deploy {} --version=1 '.format(self.service_path))

  def testDeploy_FlexEnabled_serverSideBuildOptout(self):
    """Test that deploy command attempts to enable Flexible API."""
    properties.VALUES.app.trigger_build_server_side.Set(False)
    self._ServiceManagementExpectListServicesRequest(enabled=True)
    self._ExpectServiceDeployed()
    self.Run('app deploy {} --version=1 '.format(self.service_path))

  def testDeploy_FlexEnabled_experimentNotEnabled(self):
    """Test that deploy command attempts to enable Flexible API."""
    self._RuntimeBuilderExperimentEnabled(False)
    self._ServiceManagementExpectListServicesRequest(enabled=True)
    self._ExpectServiceDeployed()
    self.Run('app deploy {} --version=1 '.format(self.service_path))

  def testDeploy_EnableFlex_ListFails(self):
    """Test that deploy succeeds if cannot confirm API enabled."""
    self._ServiceManagementExpectListServicesRequest(
        error=http_error.MakeDetailedHttpError(
            code=403, message='Message.'))
    self._ExpectServiceDeployedWithBuildOptions()

    self.Run('app deploy {} --version=1'.format(self.service_path))

    self.AssertErrContains(
        'Unable to verify that the Appengine Flexible API is enabled for '
        'project [fake-project].')

  def testDeploy_EnableFlex_ListFailsGenericError(self):
    """Test that deploy command succeeds if cannot confirm API enabled."""
    self._ServiceManagementExpectListServicesRequest(
        error=http_error.MakeDetailedHttpError(code=400, message='Message.'))
    # Deploy should fail before any other requests to AppEngine.
    self.ExpectGetApplicationRequest(self.Project())

    with self.assertRaises(api_lib_exceptions.HttpException):
      self.Run('app deploy {} --version=1'.format(self.service_path))

  def testDeploy_EnableFlex_EnableFails(self):
    """Test that deploy command raises if enabling API raises permissions error.
    """
    self._ServiceManagementExpectListServicesRequest(enabled=False)
    self._ServiceManagementExpectEnableServicesRequest(
        error=http_error.MakeDetailedHttpError(code=403, message='Message'))
    # Deploy should fail before any other requests to AppEngine.
    self.ExpectGetApplicationRequest(self.Project())
    with self.assertRaisesRegex(
        deploy_command_util.PrepareFailureError,
        r'Enabling the Appengine Flexible API failed on project '
        r'\[fake-project\].'):
      self.Run('app deploy {} --version=1'.format(self.service_path))

  def testDeploy_EnableFlex_EnableFailsGenericError(self):
    """Test that deploy command fails if enabling API fails with any error."""
    self._ServiceManagementExpectListServicesRequest(enabled=False)
    self._ServiceManagementExpectEnableServicesRequest(
        error=http_error.MakeDetailedHttpError(code=400, message='Message'))
    # Deploy should fail before any other requests to AppEngine.
    self.ExpectGetApplicationRequest(self.Project())
    with self.assertRaisesRegex(api_lib_exceptions.HttpException, r'Message'):
      self.Run('app deploy {} --version=1'.format(self.service_path))


class DeployWithApiTestsCWD(DeployWithApiTestsBase, sdk_test_base.WithTempCWD):

  def testDeploy_NoYaml(self):
    """Test deploying with a single python file in a directory."""
    self._RuntimeBuilderExperimentEnabled()
    self.Touch(self.cwd_path, 'start.py')
    properties.VALUES.core.user_output_enabled.Set(True)
    with self.assertRaises(app_exceptions.UnknownSourceError):
      self.Run('app deploy --bucket=gs://default-bucket/ --version=1')
    self.AssertErrContains('Create an app.yaml file')


class BetaDeploy(DeployWithFlexBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.messages = core_apis.GetMessagesModule('appengine', 'v1beta')
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass('appengine', 'v1beta'),
        real_client=core_apis.GetClientInstance(
            'appengine', 'v1beta', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def testStoppedAppRaisesError(self):
    """Test beta command fails if app is stopped."""
    self.MakeApp()
    self.ExpectGetApplicationRequest(self.Project(),
                                     serving_status='USER_DISABLED')
    regex = (
        r'^Unable to deploy to application \[{}\] with status '
        r'\[USER_DISABLED\]: Deploying to stopped apps is not allowed.$'
        .format(self.Project()))
    with self.assertRaisesRegex(deploy_util.StoppedApplicationError,
                                regex):
      self.Run('app deploy ' + self.FullPath('app.yaml'))

  def testDeploy_BuilderWarning(self):
    """Tests that `beta` deployments display builder warnings."""
    properties.VALUES.app.use_runtime_builders.Set(True)
    service_path = self.WriteApp('app.yaml', data=self.APP_DATA_ENV_FLEX,
                                 runtime='python-compat')
    self.StartObjectPatch(enable_api, 'EnableServiceIfDisabled')
    self._ExpectServiceDeployedWithBuildOptions(
        build_id='build-id', warning='BUILDER DEPRECATED')

    self.Run('app deploy --bucket=gs://default-bucket/ --version=1 ' +
             service_path)

    self.AssertErrContains('BUILDER DEPRECATED\n')
    self.cloud_client_mock.Stream.assert_called_once_with(
        resources.REGISTRY.Parse(
            'build-id',
            params={'projectId': self.Project()},
            collection='cloudbuild.projects.builds'), out=log.status)

  def testDeploy_StagingBeta(self):
    """Make sure the beta staging registry is used in beta release track."""
    get_stager_mock = self.StartObjectPatch(
        staging, 'GetBetaStager', return_value=staging.Stager(
            runtime_registry.Registry({}), 'staging-area'))
    self.StartObjectPatch(deploy_app_command_util, 'CopyFilesToCodeBucket',
                          autospec=True, return_value={})
    self.StartObjectPatch(enable_api, 'EnableServiceIfDisabled')

    deployment_message = encoding.PyValueToMessage(
        self.messages.Deployment, {'files': {},})
    self.ExpectServiceDeployed('default', '1', deployment=deployment_message)
    self.WriteApp('app.yaml', runtime='python27')
    self.Run(
        'app deploy --bucket=gs://default-bucket/ --version=1 {0}'.format(
            self.FullPath('app.yaml')))
    self.assertEqual(get_stager_mock.call_count, 1)

  def testDeploy_DoNotUseRuntimeBuildersWhitelist(self):
    """Tests that beta deployments respect explicit property.

    Even though 'aspnetcore' is whitelisted for beta, we should *not* use the
    runtime builder (that is, load_cloud_build_mock is not called).
    """
    properties.VALUES.app.use_runtime_builders.Set(False)
    self.StartObjectPatch(enable_api, 'EnableServiceIfDisabled')
    service_path = self.WriteApp('app.yaml', data=self.APP_DATA_ENV_FLEX,
                                 runtime='aspnetcore')
    self._ExpectServiceDeployedWithBuildOptions('aspnetcore')

    self.Run('app deploy --bucket=gs://default-bucket/ --version=1 ' +
             service_path)

  def testDeploy_CloudBuildTimeout(self):
    """Make sure the beta staging registry is used in beta release track."""
    service_path = self.WriteApp('app.yaml', data=self.APP_DATA_ENV_FLEX,
                                 runtime='python-compat')
    self.StartObjectPatch(enable_api, 'EnableServiceIfDisabled')
    properties.VALUES.app.cloud_build_timeout.Set('100')
    self._ExpectServiceDeployedWithBuildOptions(timeout='100s')
    self.Run(
        'app deploy --bucket=gs://default-bucket/ --version=1 {0}'.format(
            service_path))

  def testDeploy_UseRuntimeBuildersWithPinnedVersion(self):
    """Tests that using a pinned builder ends up passing through the runtime.
    """
    properties.VALUES.app.use_runtime_builders.Set(True)
    service_path = self.WriteApp('app.yaml', data=self.APP_DATA_ENV_FLEX,
                                 runtime='gs://runtime-builders/asdf-1234.yaml')
    self.StartObjectPatch(enable_api, 'EnableServiceIfDisabled')
    self._ExpectServiceDeployedWithBuildOptions(
        runtime='gs://runtime-builders/asdf-1234.yaml')

    self.Run('app deploy --bucket=gs://default-bucket/ --version=1 ' +
             service_path)

  def testDeploy_UsePinnedVersionWithoutRuntimeBuilders(self):
    """Tests that using a pinned builder without runtime builders is an error.
    """
    self.ExpectGetApplicationRequest(self.Project())
    self.ExpectListServicesRequest(self.Project())
    properties.VALUES.app.use_runtime_builders.Set(False)
    service_path = self.WriteApp('app.yaml', data=self.APP_DATA_ENV_FLEX,
                                 runtime='gs://runtime-builders/asdf-1234.yaml')
    self.StartObjectPatch(enable_api, 'EnableServiceIfDisabled')

    with self.assertRaises(deploy_util.InvalidRuntimeNameError):
      self.Run('app deploy --bucket=gs://default-bucket/ --version=1 ' +
               service_path)

    self.load_cloud_build_mock.assert_not_called()

  def testDeploy_NoCache(self):
    """Check that --no-cache correctly populates Version.betaSettings."""
    self.WriteApp('app.yaml')
    self.ExpectServiceDeployed(
        'default', '1',
        deployment=self.GetDeploymentMessage(filenames=['app.yaml']),
        beta_settings=self.BetaSettings(**{'no-cache': 'true'}))

    self.Run('app deploy --no-cache --version=1 {0}'.format(
        self.FullPath('app.yaml')))

    url = 'https://{project}.appspot.com'.format(project=self.Project())
    self.AssertErrContains('Deployed service [default] to [{0}]'.format(url))
    self.AssertPostDeployHints(default_service=True)

  def testDeploy_DispatchYaml(self):
    """Dispatch.yaml is deployed through Admin API."""
    self.WriteConfig(self.DISPATCH_DATA)
    self.ExpectGetApplicationRequest(self.Project())

    # expect patch
    rule = self.messages.UrlDispatchRule(
        domain='*',
        path='/tasks/hello_module2',
        service='module2')
    self.mock_client.apps.Patch.Expect(
        request=self.messages.AppengineAppsPatchRequest(
            name='apps/{}'.format(self.Project()),
            application=self.messages.Application(
                dispatchRules=[rule]),
            updateMask='dispatchRules,'),
        response=self.messages.Operation(done=True))
    structured_output = self.Run('app deploy {0}'.format(
        self.FullPath(self.DISPATCH_DATA[0])))

    self.assertEqual(structured_output, {
        'configs': ['dispatch'],
        'versions': []
    })
    self.AssertNotRequested('https://appengine.google.com/api/dispatch/update',
                            {'app_id': self.Project()})
    self.AssertPostDeployHints(dispatch=True)

if __name__ == '__main__':
  test_case.main()
