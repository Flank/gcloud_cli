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

"""Basic unit tests for DmV2 util library."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import resource_printer
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import six
from six.moves import range  # pylint: disable=redefined-builtin
from six.moves import zip  # pylint: disable=redefined-builtin


MANIFEST_NAME = 'manifest-1459974826470'
MANIFEST_URL = ('https://content.googleapis.com/deploymentmanager/v2/projects/'
                'theta-marking-627/global/deployments/gcloud/manifests/'
                'manifest-1459974826470')
OPERATION_NAME = 'operation-name'
DEPLOYMENT_NAME = 'deployment-name'
DEPLOYMENT_ID = 12345


class DmV2UtilTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Tests basic functionality of the DmV2Util library."""

  messages = core_apis.GetMessagesModule('deploymentmanager', 'v2')

  def SetUp(self):
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('deploymentmanager', 'v2'),
        real_client=core_apis.GetClientInstance('deploymentmanager', 'v2',
                                                no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.context = {
        'deploymentmanager-client': self.mocked_client,
        'deploymentmanager-messages': self.messages,
    }

  def createDeployment(self, identifier=None):
    """Helper function to create a simple deployment, used in list util tests.

    Args:
      identifier: Optional integer to act as id and append to name.

    Returns:
      Deployment with name and id set.
    """
    if identifier is not None:
      name = DEPLOYMENT_NAME + str(identifier)
      deployment_id = identifier
    else:
      name = DEPLOYMENT_NAME
      deployment_id = DEPLOYMENT_ID
    return self.messages.Deployment(
        name=name,
        id=deployment_id
    )

  def testExtractManifestName(self):
    deployment_response = self.messages.Deployment(manifest=MANIFEST_URL)
    self.assertEqual(MANIFEST_NAME,
                     dm_api_util.ExtractManifestName(deployment_response))

  def testExtractManifestName_Update(self):
    deployment_response = self.messages.Deployment(
        manifest='no/no',
        update={'manifest': MANIFEST_URL})
    self.assertEqual(MANIFEST_NAME,
                     dm_api_util.ExtractManifestName(deployment_response))

  def testExtractManifestName_NoManifest(self):
    deployment_response = self.messages.Deployment()
    self.assertEqual(None,
                     dm_api_util.ExtractManifestName(deployment_response))

  def testFlattenLayoutOutput_Simple(self):
    outputs = [{'name': 'foo', 'finalValue': 'bar'},
               {'name': ' Constantinople', 'finalValue': 'Istanbul'}]
    self.assertEqual(outputs,
                     dm_api_util.FlattenLayoutOutputs(
                         yaml.dump({
                             'outputs': outputs
                         })))

  def testFlattenLayoutOutput_ExtraField(self):
    outputs = [{'name': 'foo', 'finalValue': 'bar', 'value': 'bar'}]
    expected = [{'name': 'foo', 'finalValue': 'bar'}]
    self.assertEqual(expected,
                     dm_api_util.FlattenLayoutOutputs(
                         yaml.dump({
                             'outputs': outputs
                         })))

  def testFlattenLayout_Empty(self):
    self.assertEqual([], dm_api_util.FlattenLayoutOutputs(yaml.dump('')))
    self.assertEqual([],
                     dm_api_util.FlattenLayoutOutputs(
                         yaml.dump({
                             'resources': []
                         })))

  def testFlattenLayoutOutput_List(self):
    outputs = [{'name': 'foo', 'finalValue': [1, 2]},
               {'name': 'russia', 'finalValue': [
                   ['Tsaritsyn', 'Stalingrad', 'Volgograd'],
                   ['Saint Petersburg', 'Petrograd', 'Leningrad',
                    'Saint Petersburg']]}]
    expected = [{'name': 'foo[0]', 'finalValue': 1},
                {'name': 'foo[1]', 'finalValue': 2},
                {'name': 'russia[0]', 'finalValue': ['Tsaritsyn', 'Stalingrad',
                                                     'Volgograd']},
                {'name': 'russia[1]', 'finalValue': ['Saint Petersburg',
                                                     'Petrograd', 'Leningrad',
                                                     'Saint Petersburg']}]
    self.assertEqual(expected,
                     dm_api_util.FlattenLayoutOutputs(
                         yaml.dump({
                             'outputs': outputs
                         })))

  def testFlattenLayoutOutput_Dict(self):
    outputs = [{'name': 'foobar', 'finalValue': {'a': 1}}]
    expected = [{'name': 'foobar[a]', 'finalValue': 1}]
    self.assertEqual(expected,
                     dm_api_util.FlattenLayoutOutputs(
                         yaml.dump({
                             'outputs': outputs
                         })))

    multiple_outputs = [{'name': 'foobar', 'finalValue': {'a': 1, 'b': 2}}]
    multiple_result = dm_api_util.FlattenLayoutOutputs(
        yaml.dump({
            'outputs': multiple_outputs
        }))
    self.assertEqual(2, len(multiple_result))

    # We have to validate this way because dictionary key iteration order
    # is undefinied.
    for item in multiple_result:
      name = item['name']
      self.assertTrue('foobar[a]' == name or 'foobar[b]' == name)

    nested = [{'name': 'a', 'finalValue': {'b': {'c': 'd'}}}]
    nested_expected = [{'name': 'a[b]', 'finalValue': {'c': 'd'}}]
    self.assertEqual(nested_expected,
                     dm_api_util.FlattenLayoutOutputs(
                         yaml.dump({
                             'outputs': nested
                         })))

  def testPrintTable(self):
    header = ['aField', 'bField', 'cField']
    resources = [
        {'aField': 'A1', 'bField': 'B1', 'cField': 'C1'},
        {'aField': 'A2', 'bField': 'B2', 'cField': 'C2'}
    ]
    dm_api_util.PrintTable(header, resources)
    output = self.GetOutput().strip().split('\n')
    self.assertEqual(3, len(output))  # two lines of output plus header line
    self.assertEqual(header, output[0].split())
    for i in range(2):
      self.assertEqual(sorted(resources[i].values()), output[i+1].split())
    self.assertFalse(self.GetErr())

  def testPrintTableMissingFields(self):
    # Test that missing fields are skipped, no errors
    header = ['aField', 'bField', 'cField']
    resources = [
        {'aField': 'A1', 'cField': 'C1'},
        {'aField': 'A2', 'bField': 'B2'}
    ]
    dm_api_util.PrintTable(header, resources)
    output = self.GetOutput().strip().split('\n')
    self.assertEqual(3, len(output))  # two lines of output plus header line
    self.assertEqual(header, output[0].split())
    for i in range(2):
      self.assertEqual(sorted(resources[i].values()), output[i+1].split())
    self.assertFalse(self.GetErr())

  def testPrettyPrint_Json(self):
    resource = self.messages.Resource(
        id=123,
        name='name',
        update=self.messages.ResourceUpdate(
            error=self.messages.ResourceUpdate.ErrorValue(
                errors=[
                    self.messages.ResourceUpdate.ErrorValue.
                    ErrorsValueListEntry(message=error, code=str(code))
                    for error, code in zip(['a', 'b', 'c'], [400, 404, 500])
                ]
            )
        ),
    )
    self.assertEqual(
        resource_printer.Print([resource], 'json'),
        dm_api_util.PrettyPrint(resource))  # json is default

  def testPrettyPrint_Yaml(self):
    resource = self.messages.Resource(
        id=123,
        name='name',
        update=self.messages.ResourceUpdate(
            error=self.messages.ResourceUpdate.ErrorValue(
                errors=[
                    self.messages.ResourceUpdate.ErrorValue.
                    ErrorsValueListEntry(message=error, code=str(code))
                    for error, code in zip(['a', 'b', 'c'], [400, 404, 500])
                ]
            )
        ),
    )
    self.assertEqual(
        resource_printer.Print([resource], 'yaml'),
        dm_api_util.PrettyPrint(resource, print_format='yaml'))

  def testPrettyPrint_Text(self):
    resource = self.messages.Resource(
        id=123,
        name='name',
        update=self.messages.ResourceUpdate(
            error=self.messages.ResourceUpdate.ErrorValue(
                errors=[
                    self.messages.ResourceUpdate.ErrorValue.
                    ErrorsValueListEntry(message=error, code=str(code))
                    for error, code in zip(['a', 'b', 'c'], [400, 404, 500])
                ]
            )
        ),
    )
    self.assertEqual(
        resource_printer.Print([resource], 'text'),
        dm_api_util.PrettyPrint(resource, print_format='text'))

  _DEPRECATION_WARNING = ("Delimiter '=' is deprecated for properties flag. "
                          "Use ':' instead.")

  def testParseStrings_String(self):
    s = 'foo'
    self.assertEqual(s,
                     dm_api_util.StringPropertyParser().ParseStringsAndWarn(s))
    self.AssertErrContains(self. _DEPRECATION_WARNING)

  def testParseStrings_Int(self):
    s = '3'
    self.assertEqual(s,
                     dm_api_util.StringPropertyParser().ParseStringsAndWarn(s))
    self.AssertErrContains(self. _DEPRECATION_WARNING)

  def testParseStrings_Bool(self):
    s = 'true'
    self.assertEqual(s,
                     dm_api_util.StringPropertyParser().ParseStringsAndWarn(s))
    self.AssertErrContains(self. _DEPRECATION_WARNING)

  def testParseYaml_String(self):
    s = 'foo'
    self.assertEqual(s, dm_api_util.ParseAsYaml(s))
    self.AssertErrNotContains(self. _DEPRECATION_WARNING)

  def testParseYaml_Int(self):
    self.assertEqual(3, dm_api_util.ParseAsYaml('3'))
    self.AssertErrNotContains(self. _DEPRECATION_WARNING)

  def testParseYaml_Bool(self):
    result = dm_api_util.ParseAsYaml('true')
    self.assertTrue(result)
    self.assertTrue(isinstance(result, bool))
    self.AssertErrNotContains(self. _DEPRECATION_WARNING)

  def testParseYaml_IntAsString(self):
    result = dm_api_util.ParseAsYaml('"foo"')
    self.assertEqual('foo', result)
    self.assertTrue(isinstance(result, six.string_types))
    self.AssertErrNotContains(self. _DEPRECATION_WARNING)

  def testGetActionResourceIntent(self):
    self.assertEqual('none/NOT_RUN',
                     dm_api_util.GetActionResourceIntent('none', ['DELETE']))
    self.assertEqual('none', dm_api_util.GetActionResourceIntent('none', None))
    self.assertEqual('/NOT_RUN',
                     dm_api_util.GetActionResourceIntent('', ['DELETE']))
    self.assertEqual('', dm_api_util.GetActionResourceIntent('', None))
    self.assertEqual('PATCH/TO_RUN',
                     dm_api_util.GetActionResourceIntent(
                         'PATCH', ['UPDATE_ALWAYS', 'DELETE']))
    self.assertEqual('PATCH/NOT_RUN',
                     dm_api_util.GetActionResourceIntent('PATCH', ['CREATE']))
    self.assertEqual('PATCH', dm_api_util.GetActionResourceIntent(
        'PATCH', None))
    self.assertEqual('UPDATE/TO_RUN',
                     dm_api_util.GetActionResourceIntent(
                         'UPDATE', ['UPDATE_ON_CHANGE', 'DELETE']))
    self.assertEqual('UPDATE/NOT_RUN',
                     dm_api_util.GetActionResourceIntent('UPDATE', ['CREATE']))
    self.assertEqual('UPDATE',
                     dm_api_util.GetActionResourceIntent('UPDATE', None))
    self.assertEqual('DELETE/TO_RUN',
                     dm_api_util.GetActionResourceIntent(
                         'DELETE', ['UPDATE_ON_CHANGE', 'DELETE']))
    self.assertEqual('DELETE/NOT_RUN',
                     dm_api_util.GetActionResourceIntent(
                         'DELETE', ['UPDATE_ALWAYS']))
    self.assertEqual('DELETE',
                     dm_api_util.GetActionResourceIntent('DELETE', None))
    self.assertEqual('CREATE_OR_ACQUIRE/TO_RUN',
                     dm_api_util.GetActionResourceIntent(
                         'CREATE_OR_ACQUIRE', ['UPDATE_ON_CHANGE', 'CREATE']))
    self.assertEqual('CREATE_OR_ACQUIRE/NOT_RUN',
                     dm_api_util.GetActionResourceIntent(
                         'CREATE_OR_ACQUIRE', ['DELETE']))
    self.assertEqual('CREATE_OR_ACQUIRE',
                     dm_api_util.GetActionResourceIntent(
                         'CREATE_OR_ACQUIRE', None))
    self.assertEqual('ACQUIRE/NOT_RUN',
                     dm_api_util.GetActionResourceIntent(
                         'ACQUIRE', ['UPDATE_ON_CHANGE', 'CREATE']))
    self.assertEqual('ACQUIRE',
                     dm_api_util.GetActionResourceIntent('ACQUIRE', None))


if __name__ == '__main__':
  test_case.main()
