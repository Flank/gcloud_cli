# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Unit tests for api_lib.app.runtime_builders."""

import cStringIO
import re

from googlecloudsdk.api_lib.app import runtime_builders
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from tests.lib import sdk_test_base
from tests.lib import test_case


def _URLFromFile(*args):
  return 'file:///' + '/'.join([arg.replace('\\', '/').strip('/')
                                for arg in args])


class BuilderReferenceTest(sdk_test_base.WithOutputCapture,
                           sdk_test_base.WithFakeAuth):
  BUILD_FILE = """\
  steps:
  - name: 'gcr.io/my-project/erlang-builder:v2'
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '$_OUTPUT_IMAGE', '.']
  images: ['$_OUTPUT_IMAGE']
  """

  # Already has GAE_APPLICATION_YAML_PATH in env for one step
  BUILD_FILE_WITH_APPLICATION_YAML_PATH = """\
  steps:
  - name: 'gcr.io/my-project/erlang-builder:v2'
    env:
    - GAE_APPLICATION_YAML_PATH=$_GAE_APPLICATION_YAML_PATH
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '$_OUTPUT_IMAGE', '.']
  images: ['$_OUTPUT_IMAGE']
  """

  def SetUp(self):
    self.messages = cloudbuild_util.GetMessagesModule()
    # For brevity
    self.substitution_types = (
        self.messages.BuildOptions.SubstitutionOptionValueValuesEnum)

  def testLocalFile(self):
    self.Touch(self.temp_path, 'erlang-v2.yaml',
               contents=BuilderReferenceTest.BUILD_FILE)
    br = runtime_builders.BuilderReference(
        'foo', _URLFromFile(self.temp_path, 'erlang-v2.yaml'))
    self.assertEqual(br.runtime, 'foo')
    self.assertEqual(
        br.LoadCloudBuild({'_OUTPUT_IMAGE': 'gcr.io/my/image',
                           '_GAE_APPLICATION_YAML_PATH': 'app.yaml'}),
        self.messages.Build(
            images=['$_OUTPUT_IMAGE'],
            steps=[
                self.messages.BuildStep(
                    name='gcr.io/my-project/erlang-builder:v2',
                    env=['GAE_APPLICATION_YAML_PATH='
                         '${_GAE_APPLICATION_YAML_PATH}']
                ),
                self.messages.BuildStep(
                    name='gcr.io/cloud-builders/docker',
                    args=['build', '-t', '$_OUTPUT_IMAGE', '.'],
                    env=['GAE_APPLICATION_YAML_PATH='
                         '${_GAE_APPLICATION_YAML_PATH}']
                )
            ],
            substitutions=self.messages.Build.SubstitutionsValue(
                additionalProperties=[
                    self.messages.Build.SubstitutionsValue.AdditionalProperty(
                        key='_GAE_APPLICATION_YAML_PATH', value='app.yaml'),
                    self.messages.Build.SubstitutionsValue.AdditionalProperty(
                        key='_OUTPUT_IMAGE', value='gcr.io/my/image')
                ]
            ),
            options=self.messages.BuildOptions(
                substitutionOption=self.substitution_types.ALLOW_LOOSE
            ),
        )
    )

  def testLocalFileWithApplicationYamlPath(self):
    self.Touch(self.temp_path, 'erlang-v2.yaml',
               contents=self.BUILD_FILE_WITH_APPLICATION_YAML_PATH)
    br = runtime_builders.BuilderReference(
        'foo', _URLFromFile(self.temp_path, 'erlang-v2.yaml'))
    self.assertEqual(br.runtime, 'foo')
    self.assertEqual(
        br.LoadCloudBuild({'_OUTPUT_IMAGE': 'gcr.io/my/image',
                           '_GAE_APPLICATION_YAML_PATH': 'app.yaml'}),
        self.messages.Build(
            images=['$_OUTPUT_IMAGE'],
            steps=[
                self.messages.BuildStep(
                    name='gcr.io/my-project/erlang-builder:v2',
                    env=['GAE_APPLICATION_YAML_PATH='
                         '$_GAE_APPLICATION_YAML_PATH']),
                self.messages.BuildStep(
                    name='gcr.io/cloud-builders/docker',
                    args=['build', '-t', '$_OUTPUT_IMAGE', '.'],
                    env=['GAE_APPLICATION_YAML_PATH='
                         '${_GAE_APPLICATION_YAML_PATH}']),
            ],
            substitutions=self.messages.Build.SubstitutionsValue(
                additionalProperties=[
                    self.messages.Build.SubstitutionsValue.AdditionalProperty(
                        key='_GAE_APPLICATION_YAML_PATH', value='app.yaml'),
                    self.messages.Build.SubstitutionsValue.AdditionalProperty(
                        key='_OUTPUT_IMAGE', value='gcr.io/my/image')
                ]
            ),
            options=self.messages.BuildOptions(
                substitutionOption=self.substitution_types.ALLOW_LOOSE
            ),
        )
    )

  def testGCSFile(self):
    builder_path = 'gs://mybucket/erlang-v2.yaml'
    read_object_mock = self.StartObjectPatch(
        storage_api.StorageClient, 'ReadObject', side_effect=
        lambda x: cStringIO.StringIO(BuilderReferenceTest.BUILD_FILE))
    br = runtime_builders.BuilderReference(builder_path, builder_path)
    self.assertEqual(br.runtime, builder_path)
    self.assertEqual(
        br.LoadCloudBuild({'_OUTPUT_IMAGE': 'gcr.io/my/image',
                           '_GAE_APPLICATION_YAML_PATH': 'app.yaml'}),
        self.messages.Build(
            images=['$_OUTPUT_IMAGE'],
            steps=[
                self.messages.BuildStep(
                    name='gcr.io/my-project/erlang-builder:v2',
                    env=['GAE_APPLICATION_YAML_PATH='
                         '${_GAE_APPLICATION_YAML_PATH}']),
                self.messages.BuildStep(
                    name='gcr.io/cloud-builders/docker',
                    args=['build', '-t', '$_OUTPUT_IMAGE', '.'],
                    env=['GAE_APPLICATION_YAML_PATH='
                         '${_GAE_APPLICATION_YAML_PATH}']
                )
            ],
            substitutions=self.messages.Build.SubstitutionsValue(
                additionalProperties=[
                    self.messages.Build.SubstitutionsValue.AdditionalProperty(
                        key='_GAE_APPLICATION_YAML_PATH', value='app.yaml'),
                    self.messages.Build.SubstitutionsValue.AdditionalProperty(
                        key='_OUTPUT_IMAGE', value='gcr.io/my/image')
                ]
            ),
            options=self.messages.BuildOptions(
                substitutionOption=self.substitution_types.ALLOW_LOOSE
            ),
        )
    )
    config_object = storage_util.ObjectReference.FromUrl(builder_path)
    read_object_mock.assert_called_once_with(config_object)

  def testDeprecationMessage(self):
    br = runtime_builders.BuilderReference('foo', 'file:///junkpath')
    br.WarnIfDeprecated()
    self.AssertErrEquals('')
    br = runtime_builders.BuilderReference('foo', 'file:///junkpath',
                                           'deprecated')
    br.WarnIfDeprecated()
    self.AssertErrEquals('WARNING: deprecated\n')

  def testUnsupportedPath(self):
    for root in ('bad-url', 'badprotocol://bad-url', 'http://foo'):
      path = root + '/erlang-v2.yaml'
      with self.assertRaisesRegexp(
          runtime_builders.InvalidRuntimeBuilderURI,
          re.escape('[{}] is not a valid runtime builder URI'.format(path))):
        br = runtime_builders.BuilderReference('foo', path)
        br.LoadCloudBuild({'_OUTPUT_IMAGE': 'gcr.io/my/image',
                           '_GAE_APPLICATION_YAML_PATH': 'app.yaml'})

  def testReadError(self):
    with self.assertRaises(runtime_builders.FileReadError):
      br = runtime_builders.BuilderReference('foo', 'file:///junkpath')
      br.LoadCloudBuild({'_OUTPUT_IMAGE': 'gcr.io/my/image',
                         '_GAE_APPLICATION_YAML_PATH': 'app.yaml'})

    with self.assertRaisesRegexp(
        runtime_builders.CloudBuildLoadError,
        r'There is no build file associated with runtime \[foo\]'):
      br = runtime_builders.BuilderReference('foo', None)
      br.LoadCloudBuild({'_OUTPUT_IMAGE': 'gcr.io/my/image',
                         '_GAE_APPLICATION_YAML_PATH': 'app.yaml'})


class ManifestTest(sdk_test_base.WithFakeAuth):
  MANIFEST_FILE = """\
  schema_version: 1
  runtimes:
    erlang:
      target:
        runtime: erlang-1
    erlang-1:
      target:
        runtime: erlang-1.2
    erlang-1.2:
      target:
        file: erlang-1.2-12345.yaml
    erlang-0:
      target:
        runtime: erlang-0.1
      deprecation:
        message: "erlang-0 is deprecated."
    erlang-0.1:
      deprecation:
        message: "erlang-0.1 is deprecated."
  """

  def testLoadManifest(self):
    self.Touch(self.temp_path, 'runtimes.yaml',
               contents=ManifestTest.MANIFEST_FILE)
    self.StartObjectPatch(
        storage_api.StorageClient, 'ReadObject', side_effect=
        lambda x: cStringIO.StringIO(ManifestTest.MANIFEST_FILE))
    for builder_root in [_URLFromFile(self.temp_path), 'gs://mybucket']:
      m = runtime_builders.Manifest.LoadFromURI(builder_root + '/runtimes.yaml')
      self.assertEqual(m._data, yaml.load(ManifestTest.MANIFEST_FILE))
      self.assertEqual(
          set(m.Runtimes()),
          {'erlang', 'erlang-1', 'erlang-1.2', 'erlang-0', 'erlang-0.1'})
      self.assertIsNone(m.GetBuilderReference('foo'))
      self.assertEqual(
          m.GetBuilderReference('erlang-1.2'),
          runtime_builders.BuilderReference(
              'erlang-1.2',
              builder_root + '/erlang-1.2-12345.yaml'))
      self.assertEqual(
          m.GetBuilderReference('erlang'),
          runtime_builders.BuilderReference(
              'erlang-1.2',
              builder_root + '/erlang-1.2-12345.yaml'))
      self.assertEqual(
          m.GetBuilderReference('erlang-0'),
          runtime_builders.BuilderReference(
              'erlang-0.1',
              None,
              'erlang-0.1 is deprecated.'))

  def testLoadEmpty(self):
    m = runtime_builders.Manifest(None, {'schema_version': 1})
    self.assertIsNone(m.GetBuilderReference('foo'))
    m = runtime_builders.Manifest(None, {'schema_version': 1, 'runtimes': {}})
    self.assertIsNone(m.GetBuilderReference('foo'))

  def testSchemaVersion(self):
    runtime_builders.Manifest('gs://runtimes.yaml', {'schema_version': 0})
    runtime_builders.Manifest('gs://runtimes.yaml', {'schema_version': 1})
    with self.assertRaisesRegexp(
        runtime_builders.ManifestError,
        r'Your client supports schema version \[{supported}\] but requires '
        r'\[2\]'.format(supported=runtime_builders.Manifest.SCHEMA_VERSION)):
      runtime_builders.Manifest('gs://runtimes.yaml', {'schema_version': 2})
    with self.assertRaisesRegexp(
        runtime_builders.ManifestError,
        r'Unable to parse the runtimes manifest: \[gs://runtimes.yaml\]'):
      runtime_builders.Manifest('gs://runtimes.yaml', {})

  def testLoadCircularDep(self):
    m = runtime_builders.Manifest(
        None,
        {'schema_version': 1,
         'runtimes': {
             'foo': {'target': {'runtime': 'bar'}},
             'bar': {'target': {'runtime': 'foo'}}}})
    with self.assertRaisesRegexp(
        runtime_builders.ManifestError,
        r'A circular dependency was found while resolving the builder for '
        r'runtime \[foo\]'):
      print m.GetBuilderReference('foo')


class ResolverTest(sdk_test_base.SdkBase):
  _BUILDER_FILES = {
      'runtimes.yaml': """\
        schema_version: 1
        runtimes:
          erlang:
            target:
              runtime: erlang-1
          erlang-1:
            target:
              file: erlang-1.yaml
        """,
      'fortran.version': '3\n'
  }

  def SetUp(self):
    for name, contents in ResolverTest._BUILDER_FILES.iteritems():
      self.Touch(self.temp_path, name, contents)
    properties.VALUES.app.runtime_builders_root.Set(
        _URLFromFile(self.temp_path))

  def _GetReferenceFromYaml(self, contents):
    path = self.Touch(self.temp_path, 'app.yaml', contents)
    return runtime_builders.FromServiceInfo(
        yaml_parsing.ServiceYamlInfo.FromFile(path), self.temp_path)

  def testCustom(self):
    ref = self._GetReferenceFromYaml("""\
        env: flex
        runtime: custom
        """)
    path = _URLFromFile(self.temp_path,
                        runtime_builders.Resolver.CLOUDBUILD_FILE)
    self.assertEqual(ref, runtime_builders.BuilderReference('custom', path))

  def testPinned(self):
    ref = self._GetReferenceFromYaml("""\
      env: flex
      runtime: gs://my-bucket/my-builder.yaml
      """)
    self.assertEqual(
        ref,
        runtime_builders.BuilderReference('gs://my-bucket/my-builder.yaml',
                                          'gs://my-bucket/my-builder.yaml'))

  def testManifest(self):
    ref = self._GetReferenceFromYaml("""\
      env: flex
      runtime: erlang
      """)
    path = _URLFromFile(self.temp_path, 'erlang-1.yaml')
    self.assertEqual(
        ref,
        runtime_builders.BuilderReference('erlang-1', path))

    self.StartObjectPatch(
        runtime_builders, '_Read',
        side_effect=runtime_builders.FileReadError('No manifest'))
    with self.assertRaisesRegexp(
        runtime_builders.BuilderResolveError,
        r'Unable to resolve a builder for runtime: \[erlang\]'):
      self._GetReferenceFromYaml("""\
        env: flex
        runtime: erlang
        """)

  def testLegacyDefaultVersion(self):
    ref = self._GetReferenceFromYaml("""\
      env: flex
      runtime: fortran
      """)
    path = _URLFromFile(self.temp_path, 'fortran-3.yaml')
    self.assertEqual(
        ref,
        runtime_builders.BuilderReference('fortran', path))

  def testLegacyPinnedVersion(self):
    ref = self._GetReferenceFromYaml("""\
      env: flex
      runtime: fortran
      runtime_config:
        runtime_version: 2
      """)
    path = _URLFromFile(self.temp_path, 'fortran-2.yaml')
    self.assertEqual(
        ref,
        runtime_builders.BuilderReference('fortran', path))

  def testResolutionFailed(self):
    with self.assertRaisesRegexp(
        runtime_builders.BuilderResolveError,
        r'Unable to resolve a builder for runtime: \[asdf\]'):
      self._GetReferenceFromYaml("""\
        env: flex
        runtime: asdf
        """)


class RuntimeBuilderStrategyTest(test_case.TestCase):
  """Tests for runtime_builders.RuntimeBuilderStrategy.

   runtime |  strategy | needs_dockerfile | output
  ---------+-----------+------------------+--------
    canned |     NEVER |                * | False
    canned | WHITELIST |                * | True if whitelisted
    canned |    ALWAYS |                * | True
    custom |         * |                n | False
    custom |         * |                y | False

  For these tests:

  - 'erlang' is a non-whitelisted, canned runtime
  - 'test-beta' is a whitelisted, canned runtime for beta
  - 'test-ga' is a whitelisted, canned runtime for beta and GA
  - 'custom' is a custom runtime

  The whitelists are hard-coded in runtime_builders.py.
  """

  def testShouldUseRuntimeBuilders_Always(self):
    strategy = runtime_builders.RuntimeBuilderStrategy.ALWAYS
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('erlang', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('erlang', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-ga', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-ga', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-a', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-a', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-b', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-b', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-c', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-c', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-beta', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-beta', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('custom', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('custom', False))

  def testShouldUseRuntimeBuilders_WhitelistBeta(self):
    strategy = runtime_builders.RuntimeBuilderStrategy.WHITELIST_BETA
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('erlang', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('erlang', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-ga', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-ga', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-a', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-a', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-b', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-b', False))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-re-c', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-re-c', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-beta', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-beta', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('custom', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('custom', False))

  def testShouldUseRuntimeBuilders_WhitelistGa(self):
    strategy = runtime_builders.RuntimeBuilderStrategy.WHITELIST_GA
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('erlang', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('erlang', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-ga', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-ga', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-a', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-a', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-b', True))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('test-re-b', False))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-re-c', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-re-c', False))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-beta', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-beta', False))
    self.assertTrue(strategy.ShouldUseRuntimeBuilders('custom', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('custom', False))

  def testShouldUseRuntimeBuilders_Never(self):
    strategy = runtime_builders.RuntimeBuilderStrategy.NEVER
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('erlang', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('erlang', False))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-ga', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-ga', False))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-re-a', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-re-a', False))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-re-b', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-re-b', False))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-re-c', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-re-c', False))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-beta', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('test-beta', False))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('custom', True))
    self.assertFalse(strategy.ShouldUseRuntimeBuilders('custom', False))


if __name__ == '__main__':
  test_case.main()
