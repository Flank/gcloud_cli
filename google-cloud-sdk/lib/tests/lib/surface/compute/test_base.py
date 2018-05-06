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
"""Module for test base classes."""

from __future__ import absolute_import
from __future__ import unicode_literals
import datetime
import difflib
import os

from apitools.base.py import base_api
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.surface.compute import list_test_utils
import mock
from six.moves import zip  # pylint: disable=redefined-builtin


SAMPLE_WRAPPED_CSEK_KEY = ('ea2QS4AIhWKprsmuk/mh7g3vdBDGiTcSynFASvJC/rs/3BmOnW'
                           'G8/kBsy/Ql9AnLaQ/EQtkCQgyUZcLlM+OmEqduWuoCkorp8xG8'
                           'h9Y5UrlVz4AZbmQd99UhPejuH2L1+qmU1bGmGVhV4mcJtZNDwO'
                           'o4rCHdMuu9czHCsvDQZtseJQmnjZO2e8NGOa0rd6CZkJtammM1'
                           '7wYEAixZ+DbLgvAvtl16p1FMsLQ8ArsjrNBd9ll9pb/+9dKMCy'
                           'NXyY/jOKRDrtg+AyKWjg0FifmjCvzZ0pYC+DCM6jJIc9IsX6Kp'
                           '4gNhJTPfzXCvhviqUNGM6xMMXUvq4fCaBoaHOdm66w==')


def CreateImageAliasExpansionRequests(messages, compute):
  return [
      (compute.images,
       'List',
       messages.ComputeImagesListRequest(
           filter='name eq ^debian-8-jessie(-.+)*-v.+',
           maxResults=500,
           project='debian-cloud')),
      (compute.images,
       'List',
       messages.ComputeImagesListRequest(
           filter='name eq ^debian-8$',
           maxResults=500,
           project='my-project')),
  ]


class FakeDateTime(datetime.datetime):

  @classmethod
  def now(cls, _=None):  # pylint: disable=invalid-name
    return datetime.datetime(2014, 1, 2, 3, 4, 5, 6)


class ApitoolsClientCache(object):
  """This class facilitates caching of created clients.

  This is only needed for testing where we check that various functions are
  called with exact clients.
  """

  def __init__(self, get_client_func):
    self._cache = {}
    self._get_client_func = get_client_func

  def AddClient(self, api_name, api_version, client):
    self._cache.setdefault(api_name, {})[api_version] = client

  # This function must match signature of core_apis.GetClientInstance.
  # pylint:disable=unused-argument
  def GetClientInstance(self, api_name, api_version, no_http=False):
    versions = self._cache.setdefault(api_name, {})
    if api_version not in versions:
      client = self._get_client_func(api_name, api_version)
      self.AddClient(api_name, api_version, client)
      return client
    return versions[api_version]


class BaseTest(cli_test_base.CliTestBase, sdk_test_base.WithOutputCapture):
  """Base class for gcloud compute.tests.unit."""

  def Project(self):
    return 'my-project'

  def SetUp(self):
    self.mock_http = self.StartPatch(
        'googlecloudsdk.core.credentials.http.Http', autospec=True)

    api_cache = ApitoolsClientCache(core_apis.GetClientInstance)
    for api_version in core_apis.GetVersions('compute'):
      client = api_cache.GetClientInstance('compute', api_version)
      setattr(self, 'compute_' + api_version, client)
      setattr(self, api_version + '_messages',
              core_apis.GetMessagesModule('compute', api_version))

    make_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_requests_patcher.stop)
    self.make_requests = make_requests_patcher.start()

    patcher = mock.patch('googlecloudsdk.api_lib.util.apis.GetClientInstance',
                         new=api_cache.GetClientInstance)
    self.addCleanup(patcher.stop)
    patcher.start()

    # For now, we have MakeRequests return one empty response. Most tests should
    # result in at least one call to MakeRequests.
    self.make_requests.side_effect = iter([[]])

    time_patcher = mock.patch(
        'googlecloudsdk.command_lib.util.time_util.CurrentTimeSec',
        autospec=True)
    self.addCleanup(time_patcher.stop)
    self.time = time_patcher.start()

    sleep_patcher = mock.patch(
        'googlecloudsdk.command_lib.util.time_util.Sleep',
        autospec=True)
    self.addCleanup(sleep_patcher.stop)
    self.sleep = sleep_patcher.start()

    self.StartPatch('time.sleep')

    self.lister_invoke_helper = list_test_utils.Helper()
    self.lister_invoke_helper.Setup(self.addCleanup)

    self.image_alias_expansion_requests_v1 = (
        CreateImageAliasExpansionRequests(self.v1_messages,
                                          self.compute_v1))

    self.image_alias_expansion_requests_beta = (
        CreateImageAliasExpansionRequests(self.beta_messages,
                                          self.compute_beta))

    self.image_alias_expansion_requests_alpha = (
        CreateImageAliasExpansionRequests(self.alpha_messages,
                                          self.compute_alpha))

    self.regions_list_request_v1 = [
        (self.compute_v1.regions,
         'List',
         self.v1_messages.ComputeRegionsListRequest(
             maxResults=500,
             project='my-project')),
    ]

    self.regions_list_request_beta = [
        (self.compute_beta.regions,
         'List',
         self.beta_messages.ComputeRegionsListRequest(
             maxResults=500,
             project='my-project')),
    ]

    self.regions_list_request_alpha = [
        (self.compute_alpha.regions,
         'List',
         self.alpha_messages.ComputeRegionsListRequest(
             maxResults=500,
             project='my-project')),
    ]

    self.zone_get_request_v1 = [
        (self.compute_v1.zones,
         'Get',
         self.v1_messages.ComputeZonesGetRequest(
             project='my-project',
             zone='central2-a'))
    ]

    self.zone_get_request_beta = [
        (self.compute_beta.zones,
         'Get',
         self.beta_messages.ComputeZonesGetRequest(
             project='my-project',
             zone='central2-a'))
    ]

    self.zone_get_request_alpha = [
        (self.compute_alpha.zones,
         'Get',
         self.alpha_messages.ComputeZonesGetRequest(
             project='my-project',
             zone='central2-a'))
    ]

    self.zone_get_request_beta = [
        (self.compute_beta.zones,
         'Get',
         self.beta_messages.ComputeZonesGetRequest(
             project='my-project',
             zone='central2-a'))
    ]

    self.zones_list_request_v1 = [
        (self.compute_v1.zones,
         'List',
         self.v1_messages.ComputeZonesListRequest(
             maxResults=500,
             project='my-project')),
    ]

    self.filtered_zones_list_request_v1 = [
        (self.compute_v1.zones, 'List',
         self.v1_messages.ComputeZonesListRequest(
             filter='name eq us-central2.*',
             maxResults=500,
             project='my-project')),
    ]

    self.zones_list_request_beta = [
        (self.compute_beta.zones,
         'List',
         self.beta_messages.ComputeZonesListRequest(
             maxResults=500,
             project='my-project')),
    ]

    self.zones_list_request_alpha = [
        (self.compute_alpha.zones,
         'List',
         self.alpha_messages.ComputeZonesListRequest(
             maxResults=500,
             project='my-project')),
    ]

    # By default assume 'v1' api
    self.SelectApi('v1')

  def TearDown(self):
    for _, actual in self.make_requests.call_args_list:
      self.CheckRequestsConsistency(actual['requests'])

    self.lister_invoke_helper.Teardown()

  def SelectApi(self, api, resource_api=None):

    self.api = api
    self.resource_api = resource_api or api
    self.batch_url = ('https://www.googleapis.com/batch/compute/{0}'
                      .format(self.resource_api))
    self.compute_uri = ('https://www.googleapis.com/compute/{0}'
                        .format(self.resource_api))

    # TODO(b/19503581): Refactor test_base.py and test_resources.py s.t.
    # SelectApi also selects resource versions.  This will let us simplify
    # the `instances create` and `instances attach-disk` tests.

    compute_versions = core_apis.GetVersions('compute')
    if api not in compute_versions:
      raise ValueError(
          'api must be one of {0}. Got {1}'.format(compute_versions, api))

    self.compute = getattr(self, 'compute_' + api)
    self.messages = getattr(self, api + '_messages')
    self.regions_list_request = getattr(
        self, 'regions_list_request_' + api, None)
    self.zones_list_request = getattr(self, 'zones_list_request_' + api, None)
    self.filtered_zones_list_request = getattr(
        self, 'filtered_zones_list_request_' + api, None)
    self.zone_get_request = getattr(self, 'zone_get_request_' + api, None)
    self.project_get_request = getattr(self, 'project_get_request_' + api, None)
    self.image_alias_expansion_requests = (
        getattr(self, 'image_alias_expansion_requests_' + api, None))

  def GetKeyFileContent(self, include_rsa_encrypted=False, api=None):
    if not api:
      api = self.api
    result = """
        [ {{ "uri": "https://www.googleapis.com/compute/{api}/\
projects/my-project/zones/central2-a/disks/hamlet",
             "key": "abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=",
             "key-type": "raw"}},
          {{ "uri": "https://www.googleapis.com/compute/{api}/\
projects/my-project/zones/central2-a/disks/ophelia",
             "key": "OpheliaOphelia0000000000000000000000000000X=",
             "key-type": "raw"}},
          {{ "uri": "https://www.googleapis.com/compute/{api}/\
projects/my-project/global/images/yorik",
             "key": "aFellowOfInfiniteJestOfMostExcellentFancy00=",
             "key-type": "raw"}},
          {{ "uri": "https://www.googleapis.com/compute/{api}/\
projects/my-project/global/snapshots/laertes",
             "key": "AsAWoodcockToMineOwnSpringet00000000000000X=",
             "key-type": "raw"}}""".format(api=api)
    if include_rsa_encrypted:
      result += """,
          {{ "uri": "https://www.googleapis.com/compute/{api}/\
projects/my-project/zones/central2-a/disks/wrappedkeydisk",
             "key": "{wrapped_key}",
             "key-type": "rsa-encrypted"}}""".format(
                 api=api, wrapped_key=SAMPLE_WRAPPED_CSEK_KEY)
    result += """
             ]
    """
    return result

  def WriteKeyFile(self, include_rsa_encrypted=False, api=None):
    private_key_fname = os.path.join(self.CreateTempDir(), 'key-file.json')
    private_key_file = open(private_key_fname, 'w')
    private_key_file.write(self.GetKeyFileContent(include_rsa_encrypted,
                                                  api=api))
    private_key_file.close()
    return private_key_fname

  def AssertEqual(self, expected, actual):
    """Like unittest.assertEqual with a diff in the exception message."""

    def ProcessResultsForDiff(result):
      # Before doing a diff, we strip Unicode modifiers from strings
      # (e.g., u'x' -> 'x'). For our purposes, if two strings are
      # unequal, we should be able to tell visually. The Unicode
      # modifiers complicate diffing because they will show
      # differences that don't exist since it's possible for one
      # protocol buffer to contain Unicode strings while the other
      # contains byte strings.
      return repr(result).replace("u'", "'").splitlines()

    if expected != actual:
      unified_diff = difflib.unified_diff(
          ProcessResultsForDiff(expected),
          ProcessResultsForDiff(actual))

      raise AssertionError(
          'Expected: >>>>>>\n{0}\n<<<<<<< != actual>>>>>>\n{1}\n<<<<<<\n{2}'
          .format(expected, actual, '\n'.join(unified_diff)))

  def CheckRequests(self, *request_sets):
    """Ensures that the given requests were made to the server."""
    expected_calls = []
    for requests in request_sets:
      expected_calls.append(mock.call(
          requests=requests,
          http=self.mock_http(),
          batch_url=self.batch_url,
          errors=mock.ANY))

    # Check request against request helper function
    # googlecloudsdk.api_lib.compute.request_helper.MakeRequests.
    required_method_args = set(['requests', 'http', 'batch_url', 'errors'])
    optional_method_args = set(['progress_tracker'])

    for (_, _, expected), (_, actual) in zip(
        expected_calls, self.make_requests.call_args_list):
      self.assertTrue(required_method_args.issubset(set(actual)))
      self.assertTrue(
          set(actual).issubset(required_method_args | optional_method_args))
      self.AssertEqual(expected['requests'], actual['requests'])
      self.AssertEqual(expected['http'], actual['http'])
      self.AssertEqual(expected['batch_url'], actual['batch_url'])
      self.AssertEqual(expected['errors'], actual['errors'])
      self.CheckRequestsConsistency(actual['requests'])
    if len(expected_calls) > len(self.make_requests.call_args_list):
      self.fail(
          'Expected more requests {0}'
          .format(expected_calls[len(self.make_requests.call_args_list):]))
    elif len(expected_calls) < len(self.make_requests.call_args_list):
      self.fail(
          'Unexpected requests {0}'
          .format(self.make_requests.call_args_list[len(expected_calls):]))
    self.make_requests.reset_mock()

  def FilteredInstanceAggregateListRequest(self, instance_name):
    return [(self.compute.instances,
             'AggregatedList',
             self.messages.ComputeInstancesAggregatedListRequest(
                 maxResults=constants.MAX_RESULTS_PER_PAGE,
                 filter='name eq ^{0}$'.format(instance_name),
                 project='my-project'))]

  def CheckRequestsConsistency(self, requests):
    """Detects issues with requests service/method/message.

    Detect attempts to call non-services, non-existent methods of services and
    calling service methods with wrong argument type.

    Args:
      requests: list of (service, method, message) tuples
    """
    for service, method, message in requests:
      # Check if service is a service
      self.assertTrue(isinstance(service, base_api.BaseApiService))

      # Check if service contains given method
      self.assertIsNotNone(getattr(service, method, None))

      # Check if message has type expected by given method
      self.assertIs(service.GetRequestType(method), type(message))

  def ExpectListerInvoke(self,
                         scope_set,
                         filter_expr=None,
                         max_results=None,
                         result=None,
                         with_implementation=None):
    self.lister_invoke_helper.ExpectListerInvoke(
        scope_set, filter_expr, max_results, result, with_implementation)

  def MakeAllScopes(self, projects=None, zonal=False, regional=False):
    if projects is None:
      projects = [None]
    return lister.AllScopes(
        projects=[
            resources.REGISTRY.Parse(
                p,
                params={'project': properties.VALUES.core.project.Get()},
                collection='compute.projects') for p in projects
        ],
        zonal=zonal,
        regional=regional)

  def MakeZoneSet(self, zones=None, project=None):
    if zones is None:
      zones = [None]
    if project is None:
      project = properties.VALUES.core.project.Get()
    return lister.ZoneSet([
        resources.REGISTRY.Parse(
            z,
            params={
                'project': project,
                'zone': properties.VALUES.compute.zone.Get()
            },
            collection='compute.zones') for z in zones
    ])

  def MakeGlobalScope(self, projects=None):
    """Make GlobalScope in unit tests environment."""
    if projects is None:
      projects = [None]
    return lister.GlobalScope([
        resources.REGISTRY.Parse(
            p,
            params={
                'project': properties.VALUES.core.project.Get,
            },
            collection='compute.projects') for p in projects
    ])


class BaseEditTest(BaseTest):
  """Base class for edit subcommand tests."""

  def SetUp(self):
    edit_patcher = mock.patch('googlecloudsdk.core.util.edit.OnlineEdit',
                              autospec=True)
    self.addCleanup(edit_patcher.stop)
    self.mock_edit = edit_patcher.start()

  def AssertFileOpenedWith(self, *expected_contents_list):
    """Ensures that a text editor was opened for each argument."""
    calls = self.mock_edit.call_args_list

    while calls and expected_contents_list:
      call = calls[0]
      calls = calls[1:]
      expected_contents = expected_contents_list[0]
      expected_contents_list = expected_contents_list[1:]

      # The mock.call object is a very unpleasant object. To get the
      # first positional argument, we have to do a bit of gymnastics
      # involving two index accesses.
      actual_contents = call[0][0]

      self.assertMultiLineEqual(
          expected_contents,
          actual_contents,
          msg='the text editor was not opened with the expected text')

    if calls:
      raise AssertionError(
          'the text editor was opened more times than expected; unexpected '
          'open contained these contents: <{0}>'.format(calls[0][0][0]))

    if expected_contents_list:
      raise AssertionError(
          'the text editor was not opened the same number of times as '
          'expected; the text editor should have been opened with: <{0}>'
          .format(expected_contents_list[0]))


class BaseSSHTest(BaseTest):
  """Base class for ssh-related tests."""

  def SetUp(self):
    # A typical Unix environment
    self.env = ssh.Environment(ssh.Suite.OPENSSH)
    self.env.ssh = 'ssh'
    self.env.ssh_term = 'ssh'
    self.env.scp = 'scp'
    self.env.keygen = 'ssh-keygen'
    self.env_mock = self.StartObjectPatch(ssh.Environment, 'Current',
                                          return_value=self.env)

    self.home_dir = os.path.realpath(
        self.CreateTempDir(name=os.path.join('home', 'me')))
    self.ssh_dir = os.path.realpath(
        self.CreateTempDir(name=os.path.join(self.home_dir, '.ssh')))
    self.private_key_file = os.path.join(self.ssh_dir, 'id_rsa')
    self.public_key_file = self.private_key_file + '.pub'
    self.known_hosts_file = os.path.join(self.ssh_dir, 'known_hosts')
    self.StartObjectPatch(ssh.KnownHosts, 'DEFAULT_PATH', self.known_hosts_file)
    self.known_hosts_add = self.StartObjectPatch(ssh.KnownHosts, 'Add',
                                                 autospec=True)
    self.known_hosts_write = self.StartObjectPatch(ssh.KnownHosts, 'Write',
                                                   autospec=True)

    # Common test vars
    self.remote = ssh.Remote('23.251.133.75', user='me')
    self.options = {
        'UserKnownHostsFile': self.known_hosts_file,
        'IdentitiesOnly': 'yes',
        'CheckHostIP': 'no',
        'StrictHostKeyChecking': 'no',
    }

    # Keys
    self.pubkey = ssh.Keys.PublicKey(
        'ssh-rsa',
        'AAAAB3NzaC1yc2EAAAADAQABAAABAQCwFyCpWwERm3r1/snlgt9907rd5FcV2l'
        'vzdUxt04FCr+uNNusfx/9LUmRPVjHyIXZAcOeqRlnM8kKo765msDdyAn0n36M4LjmXBqnj'
        'edI+4OLhYPCDxGaHfnlOLIY3HCup7JSn1/u7iBddE0KnMQ13oBi010BK5iwNRe1Mr8m1ar'
        '06BK9n3UN/0DrbydTGbqcaOfYzKuMK5aeCEgvxu/TAOHsAG3fhJ0eR5orfRRUdIngP8kjZ'
        'rSrS12IRTEptaiR+NXd4/GVDcm1VvLcX8kyugVy3Md1i7kHV883jz9diMbhC/fVxERJK/7'
        'PfiEb/cYLCqWE6pTAFl+G6M4NvO3Bf', 'me@my-computer')
    self.keys = ssh.Keys(self.private_key_file)

    self.StartObjectPatch(ssh.Keys, 'FromFilename', return_value=self.keys)
    self.get_public_key = self.StartObjectPatch(
        ssh.Keys, 'GetPublicKey', autospec=True, return_value=self.pubkey)
    self.ensure_keys = self.StartObjectPatch(ssh.Keys, 'EnsureKeysExist',
                                             autospec=True)

    # User names
    self.StartObjectPatch(ssh, 'GetDefaultSshUsername', autospec=True,
                          return_value='me')

    # Commands
    self.keygen_run = self.StartObjectPatch(ssh.KeygenCommand, 'Run')

    self.ssh_init = self.StartObjectPatch(
        ssh.SSHCommand, '__init__', return_value=None, autospec=True)
    self.ssh_run = self.StartObjectPatch(
        ssh.SSHCommand, 'Run', autospec=True, return_value=0)

    self.scp_init = self.StartObjectPatch(
        ssh.SCPCommand, '__init__', return_value=None, autospec=True)
    self.scp_run = self.StartObjectPatch(ssh.SCPCommand, 'Run', autospec=True,
                                         return_value=0)
    self.scp_build = self.StartObjectPatch(
        ssh.SCPCommand, 'Build', autospec=True, return_value='')

    self.poller_init = self.StartObjectPatch(
        ssh.SSHPoller, '__init__', return_value=None, autospec=True)
    self.poller_poll = self.StartObjectPatch(
        ssh.SSHPoller, 'Poll', autospec=True, return_value=0)

    self.project_resource = self.v1_messages.Project(
        commonInstanceMetadata=self.v1_messages.Metadata(
            items=[
                self.v1_messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.v1_messages.Metadata.ItemsValueListEntry(
                    key='sshKeys',
                    value='me:{0}\n'.format(self.public_key_material)),
            ]),
        name='my-project',
    )

    self.project_resource_without_metadata = self.v1_messages.Project(
        name='my-project',
    )

    self.project_resource_with_oslogin_enabled = self.v1_messages.Project(
        name='my-project',
        commonInstanceMetadata=self.v1_messages.Metadata(
            items=[
                self.v1_messages.Metadata.ItemsValueListEntry(
                    key='enable-oslogin',
                    value='true'),
            ]),
    )

    self.make_requests.side_effect = iter([
        [self.project_resource],
    ])

  @property
  def public_key_material(self):
    return self.pubkey.ToEntry(include_comment=True)

  @property
  def max_metadata_value_size_in_bytes(self):
    return constants.MAX_METADATA_VALUE_SIZE_IN_BYTES
