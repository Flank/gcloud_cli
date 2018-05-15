# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests for `gcloud app versions` commands."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.api_lib.app import service_util
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from tests.lib import test_case
from tests.lib.surface.app import api_test_util
import mock
import six


class VersionsApiTestBase(api_test_util.ApiTestBase):

  NO_MATCHING_VERSIONS_MSG = 'No matching versions found.'

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())

  def _ExpectListAllServicesAndVersions(self):
    services = {'default': {'v6': {'traffic_split': 0},
                            'v7': {'traffic_spilt': 1.0}},
                'service1': {'v1': {'traffic_split': 0},
                             'v2': {'traffic_split': 0},
                             'v3': {'traffic_split': 1.0},
                             'v4': {'traffic_split': 0}},
                'service2': {'v1': {'traffic_split': 0},
                             'v2': {'traffic_split': 0}},
                'service3': {'v5': {'traffic_split': 1.0}},
                'emptyservice': {},}
    self.ExpectListServicesRequest(self.Project(), services=services)
    for service in sorted(services):
      self.ExpectListVersionsRequest(self.Project(), service, services)


class VersionsDescribeTest(VersionsApiTestBase):

  def testDescribe_NoProject(self):
    """Test `describe` command fails if project not set."""
    self.UnsetProject()
    with self.assertRaisesRegex(properties.RequiredPropertyError,
                                'is not currently set.'):
      self.Run('app versions describe --service service1 version1')

  def testDescribe(self):
    """Test `describe` command output."""
    name = 'apps/{}/services/service1/versions/version1'.format(self.Project())
    serving_statuses = self.messages.Version.ServingStatusValueValuesEnum
    self.mock_client.apps_services_versions.Get.Expect(
        request=self.messages.AppengineAppsServicesVersionsGetRequest(
            name=name,
            view=(self.messages.AppengineAppsServicesVersionsGetRequest
                  .ViewValueValuesEnum.FULL)),
        response=self.messages.Version(name=name,
                                       createTime='2016-01-01T12:00:00.000Z',
                                       createdBy='user@gmail.com',
                                       id='version1',
                                       runtime='intercal',
                                       servingStatus=serving_statuses.SERVING,
                                       vm=True))
    self.Run('app versions describe --service service1 version1')
    self.AssertOutputEquals("""\
        createTime: '2016-01-01T12:00:00.000Z'
        createdBy: user@gmail.com
        id: version1
        name: apps/{}/services/service1/versions/version1
        runtime: intercal
        servingStatus: SERVING
        vm: true
        """.format(self.Project()), normalize_space=True)


class VersionsListTest(VersionsApiTestBase):

  def _Services(self, **kwargs):
    services = {'service1': {'v1': {'traffic_split': 0},
                             'v2': {'traffic_split': 2.0/3.0},
                             'v3': {'traffic_split': 1.0/3.0}},
                'service2': {'v1': {'traffic_split': 1.0},
                             'v2': {'traffic_split': 0}}}
    for service_info in six.itervalues(services):
      for version_info in six.itervalues(service_info):
        version_info.update(kwargs)
    return services

  def testList_NoProject(self):
    """Test that error is raised correctly if project not set."""
    self.UnsetProject()
    with self.assertRaisesRegex(properties.RequiredPropertyError,
                                'is not currently set.'):
      self.Run('app versions list')

  def testList_NoResponse(self):
    """Test correct output if no services exist."""
    self.ExpectListServicesRequest(self.Project())
    self.Run('app versions list')
    self.AssertErrContains('Listed 0 items.')

  def testList_AllServices(self):
    """Basic test of output with two services, no flags passed."""
    services = self._Services()
    self.ExpectListServicesRequest(self.Project(), services)
    for service in sorted(services):
      self.ExpectListVersionsRequest(self.Project(), service, services)
    self.Run('app versions list')
    self.AssertOutputContains(
        """\
        SERVICE   VERSION  TRAFFIC_SPLIT  LAST_DEPLOYED SERVING_STATUS
        service1  v1       0.00           -             SERVING
        service1  v2       0.67           -             SERVING
        service1  v3       0.33           -             SERVING
        service2  v1       1.00           -             SERVING
        service2  v2       0.00           -             SERVING""",
        normalize_space=True)

  def testList_AllServices_Uri(self):
    """Basic test of output with two services, uri flag passed."""
    services = self._Services()
    self.ExpectListServicesRequest(self.Project(), services)
    for service in sorted(services):
      self.ExpectListVersionsRequest(self.Project(), service, services)
    self.Run('app versions list --uri')
    self.AssertOutputContains(
        """\
        https://v1-dot-service1-dot-fake-project.appspot.com
        https://v2-dot-service1-dot-fake-project.appspot.com
        https://v3-dot-service1-dot-fake-project.appspot.com
        https://v1-dot-service2-dot-fake-project.appspot.com
        https://v2-dot-service2-dot-fake-project.appspot.com""",
        normalize_space=True)

  def testList_AllServicesWithCreationTime(self):
    """Test that the LAST_DEPLOYED column displays correctly."""
    services = self._Services(creation_time='1970-01-01T00:00:00.000000Z')
    self.ExpectListServicesRequest(self.Project(), services)
    for service in sorted(services):
      self.ExpectListVersionsRequest(self.Project(), service, services)
    # This prevents this test from depending on the local time zone
    self.StartObjectPatch(times, 'LocalizeDateTime', side_effect=lambda x: x)

    self.Run('app versions list')
    self.AssertOutputContains(
        """\
        SERVICE  VERSION TRAFFIC_SPLIT LAST_DEPLOYED             SERVING_STATUS
        service1 v1      0.00          1970-01-01T00:00:00+00:00 SERVING
        service1 v2      0.67          1970-01-01T00:00:00+00:00 SERVING
        service1 v3      0.33          1970-01-01T00:00:00+00:00 SERVING
        service2 v1      1.00          1970-01-01T00:00:00+00:00 SERVING
        service2 v2      0.00          1970-01-01T00:00:00+00:00 SERVING""",
        normalize_space=True)

  def testList_AllServicesMissingSplit(self):
    """Test correct output if traffic split is None for all versions.

    API sometimes returns Service resources that have None for the 'split'
    field.
    """
    services = self._Services(traffic_split=None)
    self.ExpectListServicesRequest(self.Project(), services)
    for service in sorted(services):
      self.ExpectListVersionsRequest(self.Project(), service, services)

    self.Run('app versions list')
    self.AssertOutputContains(
        """\
        SERVICE   VERSION  TRAFFIC_SPLIT  LAST_DEPLOYED SERVING_STATUS
        service1  v1       0.00           -             SERVING
        service1  v2       0.00           -             SERVING
        service1  v3       0.00           -             SERVING
        service2  v1       0.00           -             SERVING
        service2  v2       0.00           -             SERVING""",
        normalize_space=True)

  def testList_SelectService1(self):
    """Test requests and output when service1 is selected."""
    services = self._Services()
    self.ExpectListServicesRequest(self.Project(), services)
    self.ExpectListVersionsRequest(self.Project(), 'service1', services)
    self.Run('app versions list --service=service1')
    self.AssertOutputContains(
        """\
        SERVICE   VERSION  TRAFFIC_SPLIT  LAST_DEPLOYED SERVING_STATUS
        service1    v1     0.00           -             SERVING
        service1    v2     0.67           -             SERVING
        service1    v3     0.33           -             SERVING""",
        normalize_space=True)
    self.AssertOutputNotContains('service2')

  def testList_SelectService2(self):
    """Test requests and output when service2 is selected."""
    services = self._Services()
    self.ExpectListServicesRequest(self.Project(), services)
    self.ExpectListVersionsRequest(self.Project(), 'service2', services)
    self.Run('app versions list --service=service2')
    self.AssertOutputContains(
        """\
        SERVICE   VERSION  TRAFFIC_SPLIT  LAST_DEPLOYED SERVING_STATUS
        service2  v1       1.00           -             SERVING
        service2  v2       0.00           -             SERVING""",
        normalize_space=True)
    self.AssertOutputNotContains('service1')

  def testList_SelectService1_Uri(self):
    """Test requests and output when service1 is selected with uri flag."""
    services = self._Services()
    self.ExpectListServicesRequest(self.Project(), services)
    self.ExpectListVersionsRequest(self.Project(), 'service1', services)
    self.Run('app versions list --service=service1 --uri')
    self.AssertOutputContains(
        """\
        https://v1-dot-service1-dot-fake-project.appspot.com
        https://v2-dot-service1-dot-fake-project.appspot.com
        https://v3-dot-service1-dot-fake-project.appspot.com""",
        normalize_space=True)
    self.AssertOutputNotContains('service2')

  def testList_AllServicesHideNoTraffic(self):
    """Test requests and output when --hide-no-traffic is passed."""
    services = self._Services()
    self.ExpectListServicesRequest(self.Project(), services)
    for service in sorted(services):
      self.ExpectListVersionsRequest(self.Project(), service, services)
    self.Run('app versions list --hide-no-traffic')
    self.AssertOutputContains(
        """\
        SERVICE   VERSION  TRAFFIC_SPLIT  LAST_DEPLOYED SERVING_STATUS
        service1  v2       0.67           -             SERVING
        service1  v3       0.33           -             SERVING
        service2  v1       1.00           -             SERVING""",
        normalize_space=True)
    self.AssertOutputNotContains('service1 v1', normalize_space=True)
    self.AssertOutputNotContains('service2 v2', normalize_space=True)

  def testList_SelectService_NotFound(self):
    """Test error raised to user when a service is not found.

    Can't test for errors defined in list.py because any classes defined in
    the command are created during Calliope registration and therefore hard to
    get a reference to.
    """
    services = self._Services()
    self.ExpectListServicesRequest(self.Project(), services)
    with self.assertRaisesRegex(exceptions.Error,
                                r'Service \[notfound] not found\.'):
      self.Run('app versions list --service=notfound')

  def testList_SelectService_NotFound_Uri(self):
    """Test error raised to user when a service is not found with uri flag.

    Can't test for errors defined in list.py because any classes defined in
    the command are created during Calliope registration and therefore hard to
    get a reference to.
    """
    services = self._Services()
    self.ExpectListServicesRequest(self.Project(), services)
    with self.assertRaisesRegex(exceptions.Error,
                                r'Service \[notfound] not found\.'):
      self.Run('app versions list --service=notfound --uri')


class VersionsMigrateTest(VersionsApiTestBase):

  def SetUp(self):
    super(VersionsMigrateTest, self).SetUp()
    self.services = {'service1': {'v1': {'traffic_split': 0},
                                  'v2': {'traffic_split': 1.0}},
                     'service2': {'v1': {'traffic_split': 0},
                                  'v2': {'traffic_split': 1.0}}}
    self.split = [('v1', 0.0), ('v2', 1.0)]

  def testMigrateOne(self):
    """Tests simple usage of migrate command."""
    services = {'service1': {'v1': {'traffic_split': 0},
                             'v2': {'traffic_split': 1.0}}}

    self.ExpectListServicesRequest(self.Project(), services)
    self.ExpectListVersionsRequest(self.Project(), 'service1', services)
    self.ExpectMigrateTraffic(self.Project(), 'service1', 'v1')
    self.Run('app versions migrate v1')
    self.AssertErrContains('Migrating all traffic from version '
                           '[service1/v2] to [service1/v1]')

  def testMigrateMultiple(self):
    """Tests migrating multiple services to a new version."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    self.ExpectListVersionsRequest(self.Project(), 'service1', self.services)
    self.ExpectListVersionsRequest(self.Project(), 'service2', self.services)
    self.ExpectMigrateTraffic(self.Project(), 'service1', 'v1')
    self.ExpectMigrateTraffic(self.Project(), 'service2', 'v1')
    self.Run('app versions migrate v1')
    self.AssertErrContains('Migrating all traffic from version '
                           '[service1/v2] to [service1/v1]')
    self.AssertErrContains('Migrating all traffic from version '
                           '[service2/v2] to [service2/v1]')

  def testMigrateMultipleWithService(self):
    """Tests migrating a specific service to a new version."""
    self.ExpectGetServiceRequest(self.Project(), 'service1', self.split)
    self.ExpectListVersionsRequest(self.Project(), 'service1', self.services)
    self.ExpectMigrateTraffic(self.Project(), 'service1', 'v1')
    self.Run('app versions migrate v1 --service=service1')
    self.AssertErrContains('Migrating all traffic from version '
                           '[service1/v2] to [service1/v1]')

  def testMigrateVersionDoesNotExist(self):
    """Tests migrating to an invalid version."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    self.ExpectListVersionsRequest(self.Project(), 'service1', self.services)
    self.ExpectListVersionsRequest(self.Project(), 'service2', self.services)
    with self.assertRaises(exceptions.Error):
      self.Run('app versions migrate v3')


class VersionsStopTest(VersionsApiTestBase):

  STOP_VERSION_MSG = 'Stopping the following versions:'

  def testStop_OneServiceRetry(self):
    """Tests that the `stop` command handles retries.

    If the operation does not initially succeed, stop should poll until it does.
    """
    self.StartPatch('time.sleep')
    self._ExpectListAllServicesAndVersions()
    self.ExpectStopVersionRequest(self.Project(), 'service1', 'v1',
                                  num_retries=2)
    self.Run('app versions stop --service=service1  v1')
    self.AssertErrContains(self.STOP_VERSION_MSG)

  def testStop_AllServices(self):
    """Tests `stop` with a version that exists in two services."""
    self._ExpectListAllServicesAndVersions()
    for service in ['service1', 'service2']:
      self.ExpectStopVersionRequest(self.Project(), service, 'v2')
    self.Run('app versions stop v2')
    self.AssertErrContains(self.STOP_VERSION_MSG)

  def testStop_VersionAllServicesButNotInAllServices(self):
    """Tests stopping a version that exists in one service."""
    self._ExpectListAllServicesAndVersions()
    self.ExpectStopVersionRequest(self.Project(), 'service1', 'v3')
    self.Run('app versions stop v3')
    self.AssertErrContains(self.STOP_VERSION_MSG)

  def testStop_VersionAllServicesNoneFound(self):
    """Tests stopping a version that doesn't exist."""
    self._ExpectListAllServicesAndVersions()
    self.Run('app versions stop notfound')
    self.AssertErrContains(self.NO_MATCHING_VERSIONS_MSG)

  def testStop_VersionAllServicesMulti(self):
    """Tests stopping multiple versions that exist in multiple services."""
    self._ExpectListAllServicesAndVersions()
    for service in ['service1', 'service2']:
      for version in ['v1', 'v2']:
        self.ExpectStopVersionRequest(self.Project(), service, version)
    self.Run('app versions stop v1 v2')
    self.AssertErrContains(self.STOP_VERSION_MSG)

  def testStop_OneVersionOneService(self):
    """Tests stopping version in only one service with --service flag."""
    self._ExpectListAllServicesAndVersions()
    self.ExpectStopVersionRequest(self.Project(), 'service1', 'v1')
    self.Run('app versions stop --service=service1 v1')
    self.AssertErrContains(self.STOP_VERSION_MSG)

  def testStop_OneVersionServiceNotFound(self):
    """Tests error raised if --service flag has service that doesn't exist."""
    self._ExpectListAllServicesAndVersions()
    with self.assertRaisesRegex(exceptions.Error,
                                r'Service \[badservice\] not found.'):
      self.Run('app versions stop --service=badservice v1')

  def testStop_MultiVersionServiceNotFound(self):
    """Same as above, with two versions given."""
    self._ExpectListAllServicesAndVersions()
    with self.assertRaisesRegex(exceptions.Error,
                                r'Service \[badservice\] not found.'):
      self.Run('app versions stop --service=badservice v1 v2')

  def testStop_ResourcePath(self):
    """Tests version arg in form [SERVICE]/[VERSION] does not work."""
    self._ExpectListAllServicesAndVersions()
    self.Run('app versions stop service1/v1')
    self.AssertErrContains(self.NO_MATCHING_VERSIONS_MSG)

  def testStop_MultiVersionsOneService(self):
    """Tests stopping multiple versions, with --service flag."""
    self._ExpectListAllServicesAndVersions()
    for version in ['v1', 'v2']:
      self.ExpectStopVersionRequest(self.Project(), 'service1', version)
    self.Run('app versions stop --service=service1 v1 v2')
    self.AssertErrContains(self.STOP_VERSION_MSG)

  def testStop_AllVersionsAllServices(self):
    """Ensure `stop` command raises error if no version is given."""
    with self.AssertRaisesArgumentErrorMatches(
        'argument VERSIONS [VERSIONS ...]: Must be specified.'):
      self.Run('app versions stop')

  def testStop_AllVersionsOneService(self):
    """Same as above, with --service flag."""
    with self.AssertRaisesArgumentErrorMatches(
        'argument VERSIONS [VERSIONS ...]: Must be specified.'):
      self.Run('app versions stop --service=service1')


class VersionsStartTest(VersionsApiTestBase):

  STARTING_VERSION_MSG = 'Starting the following versions:'

  def testStart_AllServices(self):
    """Test `start` command with a single version."""
    self._ExpectListAllServicesAndVersions()
    for service in ['service1', 'service2']:
      self.ExpectStartVersionRequest(self.Project(), service, 'v2')
    self.Run('app versions start v2')
    self.AssertErrContains(self.STARTING_VERSION_MSG)

  def testStart_VersionAllServicesButNotInAllServices(self):
    """Test starting a single version that exists in just one service."""
    self._ExpectListAllServicesAndVersions()
    self.ExpectStartVersionRequest(self.Project(), 'service1', 'v3')
    self.Run('app versions start v3')
    self.AssertErrContains(self.STARTING_VERSION_MSG)

  def testStart_VersionAllServicesNoneFound(self):
    """Test `start` command with version that does not exist."""
    self._ExpectListAllServicesAndVersions()
    self.Run('app versions start notfound')
    self.AssertErrContains(self.NO_MATCHING_VERSIONS_MSG)

  def testStart_VersionAllServicesMulti(self):
    """Test starting multiple versions that exist in multiple services."""
    self._ExpectListAllServicesAndVersions()
    for service in ['service1', 'service2']:
      for version in ['v1', 'v2']:
        self.ExpectStartVersionRequest(self.Project(), service, version)
    self.Run('app versions start v1 v2')
    self.AssertErrContains(self.STARTING_VERSION_MSG)

  def testStart_OneVersionOneService(self):
    """Test starting one version with --service specified."""
    self._ExpectListAllServicesAndVersions()
    self.ExpectStartVersionRequest(self.Project(), 'service1', 'v1')
    self.Run('app versions start --service=service1 v1')
    self.AssertErrContains(self.STARTING_VERSION_MSG)

  def testStart_OneVersionServiceNotFound(self):
    """Test with --service flag if service does not exist."""
    self._ExpectListAllServicesAndVersions()
    with self.assertRaisesRegex(exceptions.Error,
                                r'Service \[badservice\] not found.'):
      self.Run('app versions start --service=badservice v1')

  def testStart_MultiVersionServiceNotFound(self):
    """Same as above, but with multiple versions."""
    self._ExpectListAllServicesAndVersions()
    with self.assertRaisesRegex(exceptions.Error,
                                r'Service \[badservice\] not found.'):
      self.Run('app versions start --service=badservice v1 v2')

  def testStart_ResourcePath(self):
    """Test that a version arg in {service}/{version} format does not work."""
    self._ExpectListAllServicesAndVersions()
    self.Run('app versions start service1/v1')
    self.AssertErrContains(self.NO_MATCHING_VERSIONS_MSG)

  def testStart_MultiVersionsOneService(self):
    """Test starting multiple versions with single service specified."""
    self._ExpectListAllServicesAndVersions()
    for version in ['v1', 'v2']:
      self.ExpectStartVersionRequest(self.Project(), 'service1', version)
    self.Run('app versions start --service=service1 v1 v2')
    self.AssertErrContains(self.STARTING_VERSION_MSG)

  def testStart_AllVersionsAllServices(self):
    """Test `start` command errors if version not given."""
    with self.AssertRaisesArgumentErrorMatches(
        'argument VERSIONS [VERSIONS ...]: Must be specified.'):
      self.Run('app versions start')

  def testStart_AllVersionsOneService(self):
    """Same as above, with --service flag given."""
    with self.AssertRaisesArgumentErrorMatches(
        'argument VERSIONS [VERSIONS ...]: Must be specified.'):
      self.Run('app versions start --service=service1')


class VersionsDeleteTest(VersionsApiTestBase):

  def AssertVersionMessages(self, versions):
    """Check error output for deleted versions."""
    if versions:
      self.AssertErrContains('Do you want to continue (Y/n)?')
    else:
      self.AssertErrContains('No matching versions found.')
    for version in versions:
      self.AssertErrContains(
          '{0}/{1}/{2}'.format(self.Project(), version.service, version.id))

  def AssertServiceMessages(self, services):
    """Check error output for deleted services."""
    self.AssertErrContains('Requested deletion of all existing versions')
    self.AssertErrContains('You cannot delete all versions of a service')
    for service in services:
      self.AssertErrContains(
          '{0}/{1}'.format(self.Project(), service.id))

  def ExpectDeleteServicesAndVersions(self, services=None, versions=None):
    """Helper function to set up mock client for deletions."""
    services = services or []
    versions = versions or []
    for service in services:
      self.ExpectDeleteServiceRequest(self.Project(), service.id)
    for version in versions:
      self.ExpectDeleteVersionRequest(self.Project(), version.service,
                                      version.id)

  def testDelete_OneServiceOneVersionError(self):
    """Ensure `delete` command raises if DeleteVersion raises error."""
    self._ExpectListAllServicesAndVersions()
    delete_version = self.StartObjectPatch(
        appengine_api_client.AppengineApiClient, 'DeleteVersion')
    delete_version.side_effect = operations_util.OperationError('foo')
    with self.assertRaisesRegex(
        exceptions.Error,
        r'Issue deleting version: \[service1/v1\]\n\n'
        r'\[service1/v1\]: foo'):
      self.Run('app versions delete v1 --service=service1')

  def testDelete_OneServiceOneVersion(self):
    """Ensure `delete` command deletes single version in single service."""
    self._ExpectListAllServicesAndVersions()
    versions = [
        version_util.Version(self.Project(), 'service1', 'v1')
    ]
    self.ExpectDeleteServicesAndVersions(versions=versions)
    self.Run('app versions delete v1 --service=service1')
    self.AssertVersionMessages(versions)

  def testDelete_DefaultServiceAllVersions(self):
    """Ensure `delete` command raises if default versions would be deleted."""
    self._ExpectListAllServicesAndVersions()
    with self.assertRaisesRegex(
        exceptions.Error,
        r'The default service \(module\) may not be deleted, and must '
        r'comprise at least one version.'):
      self.Run('app versions delete v6 v7 --service=default')

  def testDelete_DefaultServiceOneVersion(self):
    """Test delete single version from default service."""
    self._ExpectListAllServicesAndVersions()
    versions = [version_util.Version(self.Project(), 'default', 'v6')]
    self.ExpectDeleteServicesAndVersions(versions=versions)
    self.Run('app versions delete v6 --service=default')
    self.AssertVersionMessages(versions)

  def testDelete_OneServiceMultiVersion(self):
    """Test deletion of two versions in single service."""
    self._ExpectListAllServicesAndVersions()
    versions = [version_util.Version(self.Project(), 'service1', 'v1'),
                version_util.Version(self.Project(), 'service1', 'v2')]
    self.ExpectDeleteServicesAndVersions(versions=versions)
    self.Run('app versions delete v1 v2 --service=service1')
    self.AssertVersionMessages(versions)

  def testDelete_AllServicesOneVersionInMultiServices(self):
    """Test deletion of single version that exists in two services."""
    self._ExpectListAllServicesAndVersions()
    versions = [
        version_util.Version(self.Project(), 'service1', 'v2'),
        version_util.Version(self.Project(), 'service2', 'v2')
    ]
    self.ExpectDeleteServicesAndVersions(versions=versions)
    self.Run('app versions delete v2')
    self.AssertVersionMessages(versions)

  def testDelete_AllServicesOneVersionInOneService(self):
    """Same as above but version only exists in one service."""
    self._ExpectListAllServicesAndVersions()
    versions = [
        version_util.Version(self.Project(), 'service1', 'v4')
    ]
    self.ExpectDeleteServicesAndVersions(versions=versions)
    self.Run('app versions delete v4')
    self.AssertVersionMessages(versions)

  def testDelete_AllServicesOneVersionNotFound(self):
    """Test messaging when version to delete is not found."""
    versions = []
    self._ExpectListAllServicesAndVersions()
    self.Run('app versions delete notfound')
    self.AssertVersionMessages(versions)

  def testDelete_AllServicesMultiVersions(self):
    """Test deleting multiple versions that exist in multiple services."""
    self._ExpectListAllServicesAndVersions()
    versions = [
        version_util.Version(self.Project(), 'service1', 'v2'),
        version_util.Version(self.Project(), 'service1', 'v4'),
        version_util.Version(self.Project(), 'service2', 'v2'),
    ]
    self.ExpectDeleteServicesAndVersions(versions=versions)
    self.Run('app versions delete v2 v4')
    self.AssertVersionMessages(versions)

  def testDelete_WithTrafficVersion(self):
    """Test `delete` raises error if a version to delete has 100% of traffic."""
    self._ExpectListAllServicesAndVersions()
    with self.assertRaisesRegex(
        exceptions.Error,
        r'Version \[v3\] is currently serving 100.00% of traffic for service '
        r'\[service1\]'):
      self.Run('app versions delete --service service1 v3')

  def testDelete_OneVersionAllServicesOneWithTraffic(self):
    """Same as above, without restricting service.

    If a version has 100% of traffic in any service, then deleting that version
    should raise an error if --service flag is not given.
    """
    self._ExpectListAllServicesAndVersions()
    with self.assertRaisesRegex(
        exceptions.Error,
        r'Version \[v3\] is currently serving 100.00% of traffic for service '
        r'\[service1\]'):
      self.Run('app versions delete v3')

  def testDelete_MultiVersionOneWithTraffic(self):
    """Same as above with two version args, where one cannot be deleted."""
    self._ExpectListAllServicesAndVersions()
    with self.assertRaisesRegex(
        exceptions.Error,
        r'Version \[v3\] is currently serving 100.00% of traffic for service '
        r'\[service1\]'):
      self.Run('app versions delete v3 v2')

  def testDelete_OneServiceOnlyVersions(self):
    """Test `delete` command where all versions deleted in a service."""
    self._ExpectListAllServicesAndVersions()
    services = [service_util.Service(self.Project(), 'service3')]
    self.ExpectDeleteServicesAndVersions(services=services)
    self.Run('app versions delete v5 --service=service3')
    self.AssertServiceMessages(services)

  def testDelete_MultiServiceAllVersions(self):
    """Same as above, with multiple services whose versions are all deleted."""
    self._ExpectListAllServicesAndVersions()
    services = [service_util.Service(self.Project(), 'service2'),
                service_util.Service(self.Project(), 'service3')]
    versions = [version_util.Version(self.Project(), 'service1', 'v1'),
                version_util.Version(self.Project(), 'service1', 'v2')]
    self.ExpectDeleteServicesAndVersions(services, versions)
    self.Run('app versions delete v1 v2 v5')
    self.AssertServiceMessages(services)
    self.AssertVersionMessages(versions)

  def testDelete_NoVersionSpecified(self):
    """Test that `delete` fails if version not given."""
    with self.AssertRaisesArgumentErrorMatches(
        'argument VERSIONS [VERSIONS ...]: Must be specified.'):
      self.Run('app versions delete')

  def testDelete_NoVersionSpecifiedOneService(self):
    """Same as above, with --service flag given."""
    with self.AssertRaisesArgumentErrorMatches(
        'argument VERSIONS [VERSIONS ...]: Must be specified.'):
      self.Run('app versions delete --service=service1')

  def testDelete_ServiceNotFound(self):
    """Test that `delete` fails if service does not exist."""
    self._ExpectListAllServicesAndVersions()
    with self.assertRaisesRegex(exceptions.Error,
                                r'Service \[notfound\] not found.'):
      self.Run('app versions delete --service=notfound v1')

  def testDelete_NoVersionsFound(self):
    """Test `delete` runs and gives correct message if version not found."""
    self._ExpectListAllServicesAndVersions()
    self.Run('app versions delete --service=service1 notfound')
    self.AssertErrNotContains('Deleting the following versions:')
    self.AssertErrContains('No matching versions found.')

  def testDelete_ResourcePath(self):
    """Ensure not deleted if id given in {service}/{version} format."""
    self._ExpectListAllServicesAndVersions()
    self.Run('app versions delete service1/v1')
    self.AssertErrNotContains('Deleting the following versions:')
    self.AssertErrContains('No matching versions found.')


class BrowseTest(VersionsApiTestBase):

  def SetUp(self):
    self.open_mock = self.StartPatch('webbrowser.open_new_tab')
    # Mock ShouldLaunchBrowser with a function that ignores environment stuff,
    # and just returns whether the user *wanted* to launch the browser.
    self.launch_browser_mock = self.StartPatch(
        'googlecloudsdk.command_lib.util.check_browser.ShouldLaunchBrowser',
        wraps=lambda x: x)

  def testBrowse_NoProject(self):
    """Ensure `browse` raises if project not set."""
    self.UnsetProject()
    with self.assertRaisesRegex(properties.RequiredPropertyError,
                                'is not currently set.'):
      self.Run('app versions browse v1')

  def testBrowse_NoArgs(self):
    """Ensure error raised if no version given."""
    with self.AssertRaisesArgumentErrorMatches(
        'argument VERSIONS [VERSIONS ...]: Must be specified.'):
      self.Run('app versions browse')

  def testBrowse_NoLaunchBrowser(self):
    """Test when the user does not want to open the browser."""
    self.Run('app versions browse --no-launch-browser v1 v2')
    self.launch_browser_mock.assert_called_with(False)
    self.open_mock.assert_not_called()
    self.AssertOutputContains("""\
        VERSION   URL
        v1        https://v1-dot-{0}.appspot.com
        v2        https://v2-dot-{0}.appspot.com""".format(
            self.Project()
        ), normalize_space=True)

  def testBrowse_SpecifyVersionDefaultService(self):
    """Test `browse` command where version is given.

    If service is not given, should open default page.
    """
    self.Run('app versions browse v1')
    self.launch_browser_mock.assert_called_with(True)
    self.open_mock.assert_called_once_with(
        'https://v1-dot-{0}.appspot.com'.format(self.Project()))

  def testBrowse_SpecifyMultiVersionDefaultService(self):
    """Test `browse` command where two versions given."""
    self.Run('app versions browse v1 v2')
    self.open_mock.assert_has_calls([
        mock.call('https://v1-dot-{0}.appspot.com'.format(self.Project())),
        mock.call('https://v2-dot-{0}.appspot.com'.format(self.Project())),
    ], any_order=True)
    self.assertEqual(self.open_mock.call_count, 2)

  def testBrowse_SpecifyVersionNotDefaultService(self):
    """Test `browse` command where version and service specified.

    Should open the correct page for the service arg given.
    """
    self.Run('app versions browse --service=service1 v1')
    self.open_mock.assert_called_once_with(
        'https://v1-dot-service1-dot-{0}.appspot.com'.format(self.Project()))

  def testBrowse_SpecifyMultiVersionNotDefaultService(self):
    """Same as above, with multiple versions."""
    self.Run('app versions browse --service=service1 v1 v2')
    self.open_mock.assert_has_calls([
        mock.call(
            'https://v1-dot-service1-dot-{0}.appspot.com'.format(
                self.Project())),
        mock.call(
            'https://v2-dot-service1-dot-{0}.appspot.com'.format(
                self.Project())),
    ], any_order=True)
    self.assertEqual(self.open_mock.call_count, 2)


if __name__ == '__main__':
  test_case.main()
