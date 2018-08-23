# -*- coding: utf-8 -*- #
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
"""Tests that exercise cloudbuild config parsing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.api_lib.cloudbuild import config
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import subtests
from tests.lib import test_case


class ConfigTest(sdk_test_base.WithTempCWD):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudbuild', 'v1')

  def testNoFile(self):
    with self.assertRaises(config.NotFoundException):
      config.LoadCloudbuildConfigFromPath('not-here.json', self.messages)

  def testBadEncoding(self):
    self.Touch('.', 'garbage.garbage', """
this file is neither json nor yaml
        """)
    with self.assertRaisesRegex(
        config.ParserError, 'Could not parse into a message'):
      config.LoadCloudbuildConfigFromPath('garbage.garbage', self.messages)

  def testLoadJson(self):
    self.Touch('.', 'basic.json', """
{
  "steps": [
    {"name": "gcr.io/cloud-builders/docker",
     "args": ["build", "-t", "gcr.io/my-project/simple"]
    }
   ],
  "images": "gcr.io/my-project/simple"
}
        """)
    build = config.LoadCloudbuildConfigFromPath('basic.json', self.messages)
    self.assertEqual(build, self.messages.Build(
        steps=[
            self.messages.BuildStep(
                name='gcr.io/cloud-builders/docker',
                args=['build', '-t', 'gcr.io/my-project/simple'],
            ),
        ],
        images=['gcr.io/my-project/simple'],
    ))

  def testLoadJsonWithParameters(self):
    self.Touch('.', 'basic.json', """
{
  "steps": [
    {"name": "gcr.io/cloud-builders/docker",
     "args": ["build", "-t", "gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR"]
    }
   ],
  "substitutions": {
    "_DAY_OF_WEEK": "monday",
    "_BEST_BEER": "orval"
  },
  "images": "gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR",
  "timeout": "gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR"
}
        """)
    build = config.LoadCloudbuildConfigFromPath(
        'basic.json', self.messages, {'_DAY_OF_WEEK': 'tuesday',
                                      '_FAVORITE_COLOR': 'blue'})

    # Only substitute images/steps, not any other fields (see `timeout`)
    # (there are very few string fields in Build that aren't output only, so use
    # a nonsensical one to test this.)
    self.assertEqual(build, self.messages.Build(
        steps=[
            self.messages.BuildStep(
                name='gcr.io/cloud-builders/docker',
                args=['build', '-t', 'gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR'],
            ),
        ],
        substitutions=self.messages.Build.SubstitutionsValue(
            additionalProperties=[
                self.messages.Build.SubstitutionsValue.AdditionalProperty(
                    key='_BEST_BEER', value='orval'),
                self.messages.Build.SubstitutionsValue.AdditionalProperty(
                    key='_DAY_OF_WEEK', value='tuesday'),
                self.messages.Build.SubstitutionsValue.AdditionalProperty(
                    key='_FAVORITE_COLOR', value='blue'),
            ]
        ),
        images=['gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR'],
        timeout='gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR'
    ))

  def testLoadYaml(self):
    self.Touch('.', 'basic.yaml', """
steps:
 - name: gcr.io/cloud-builders/docker
   args:
   - build
   - -t
   - gcr.io/my-project/simple
images: gcr.io/my-project/simple
        """)
    build = config.LoadCloudbuildConfigFromPath('basic.yaml', self.messages)
    self.assertEqual(build, self.messages.Build(
        steps=[
            self.messages.BuildStep(
                name='gcr.io/cloud-builders/docker',
                args=['build', '-t', 'gcr.io/my-project/simple'],
            ),
        ],
        images=['gcr.io/my-project/simple'],
    ))

  def testWaitForSnake(self):
    self.Touch('.', 'waitFor.yaml', """
steps:
 - name: gcr.io/cloud-builders/docker
   args:
   - build
   - -t
   - gcr.io/my-project/simple
   wait_for: ['foo', 'bar']
images: gcr.io/my-project/simple
        """)
    build = config.LoadCloudbuildConfigFromPath('waitFor.yaml', self.messages)
    self.assertEqual(build, self.messages.Build(
        steps=[
            self.messages.BuildStep(
                name='gcr.io/cloud-builders/docker',
                args=['build', '-t', 'gcr.io/my-project/simple'],
                waitFor=['foo', 'bar'],
            ),
        ],
        images=['gcr.io/my-project/simple'],
    ))

  def testLoadYamlWithParameters(self):
    self.Touch('.', 'basic.yaml', """
steps:
 - name: gcr.io/cloud-builders/docker
   args:
   - build
   - -t
   - gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR
images: gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR
timeout: gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR
        """)
    build = config.LoadCloudbuildConfigFromPath(
        'basic.yaml', self.messages, {'_DAY_OF_WEEK': 'tuesday',
                                      '_FAVORITE_COLOR': 'blue'})
        #
    # Only substitute images/steps, not any other fields (see `timeout`)
    # (there are very few string fields in Build that aren't output only, so use
    # a nonsensical one to test this.)
    self.assertEqual(build, self.messages.Build(
        steps=[
            self.messages.BuildStep(
                name='gcr.io/cloud-builders/docker',
                args=['build', '-t', 'gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR'],
            ),
        ],
        substitutions=self.messages.Build.SubstitutionsValue(
            additionalProperties=[
                self.messages.Build.SubstitutionsValue.AdditionalProperty(
                    key='_DAY_OF_WEEK', value='tuesday'),
                self.messages.Build.SubstitutionsValue.AdditionalProperty(
                    key='_FAVORITE_COLOR', value='blue'),
            ]
        ),
        images=['gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR'],
        timeout='gcr.io/$_DAY_OF_WEEK/$_FAVORITE_COLOR'
    ))

  def testYamlSyntaxError(self):
    """Misplaced brace at the end of the document."""
    self.Touch('.', 'error.yaml', """
steps:
 - name: gcr.io/cloud-builders/docker
   args:
   - build
   - -t
   - gcr.io/my-project/simple
images: gcr.io/my-project/simple
}
        """)
    with self.assertRaisesRegex(config.ParserError, 'error.yaml'):
      config.LoadCloudbuildConfigFromPath('error.yaml', self.messages)

  def testBadConfigSource(self):
    """Not allowed to specify the source since it comes in from an argument."""
    self.Touch('.', 'has_source.yaml', """
source:
  storageSource:
    bucket: boo
    object: oo
        """)
    with self.assertRaisesRegex(
        config.BadConfigException, 'config cannot specify source'):
      config.LoadCloudbuildConfigFromPath('has_source.yaml', self.messages)

    self.Touch('.', 'no_steps.yaml', """
images: foobar
        """)
    with self.assertRaisesRegex(
        config.BadConfigException, 'config must list at least one step'):
      config.LoadCloudbuildConfigFromPath('no_steps.yaml', self.messages)

  def testYamlSubs(self):
    """Make sure that $PROJECT_ID gets replaced as appropriate."""
    properties.VALUES.core.project.Set('myproj')
    self.Touch('.', 'subs.yaml', """
steps:
 - name: gcr.io/$PROJECT_ID/step
   args: gcr.io/$PROJECT_ID/simple
   env: project=$PROJECT_ID
images: gcr.io/$PROJECT_ID/simple
        """)
    build = config.LoadCloudbuildConfigFromPath('subs.yaml', self.messages)
    self.assertEqual(build, self.messages.Build(
        steps=[
            self.messages.BuildStep(
                name='gcr.io/$PROJECT_ID/step',
                args=['gcr.io/$PROJECT_ID/simple'],
                env=['project=$PROJECT_ID'],
            ),
        ],
        images=['gcr.io/$PROJECT_ID/simple'],
    ))

  def testJsonSubs(self):
    """Make sure that $PROJECT_ID gets replaced as appropriate."""
    properties.VALUES.core.project.Set('myproj')
    self.Touch('.', 'subs.json', """
{
  "steps": [
    {"name": "gcr.io/$PROJECT_ID/step",
     "args": "gcr.io/$PROJECT_ID/simple",
     "env": "project=$PROJECT_ID"
    }
   ],
  "images": "gcr.io/$PROJECT_ID/simple"
}
        """)
    build = config.LoadCloudbuildConfigFromPath('subs.json', self.messages)
    self.assertEqual(build, self.messages.Build(
        steps=[
            self.messages.BuildStep(
                name='gcr.io/$PROJECT_ID/step',
                args=['gcr.io/$PROJECT_ID/simple'],
                env=['project=$PROJECT_ID'],
            ),
        ],
        images=['gcr.io/$PROJECT_ID/simple'],
    ))

  def testYamlUnusedField(self):
    """testYamlUnusedField checks the misindented tags field."""
    self.Touch('.', 'error.yaml', """
steps:
 - name: gcr.io/cloud-builders/docker
   args:
   - build
   - -t
   - gcr.io/my-project/simple
   tags: sometag
images: gcr.io/my-project/simple1
""")
    with self.assertRaisesRegex(
        config.BadConfigException,
        r'error.yaml: .steps\[0\].tags: unused'):
      config.LoadCloudbuildConfigFromPath('error.yaml', self.messages)

  def testJsonUnusedField(self):
    """testJsonUnusedField checks the misplaced tags field."""
    self.Touch('.', 'error.json', """
{
  "steps": [
    {"name": "gcr.io/cloud-builders/docker",
     "args": ["build", "-t", "gcr.io/$PROJECT_ID/simple", "."],
     "tags": "sometag"
    }
   ],
  "images": "gcr.io/$PROJECT_ID/simple"
}
        """)
    with self.assertRaisesRegex(
        config.BadConfigException,
        r'error.json: .steps\[0\].tags: unused'):
      config.LoadCloudbuildConfigFromPath('error.json', self.messages)

  def testYamlUnusedNested(self):
    """Only present an error for the highest-level mistake."""
    self.Touch('.', 'error.yaml', """
steps:
 - name: gcr.io/cloud-builders/docker
   args:
   - build
   - -t
   - gcr.io/my-project/simple
extra:
  data:
    is: "bad"
images: gcr.io/my-project/simple1
        """)
    with self.assertRaisesRegex(
        config.BadConfigException,
        r'error\.yaml: \.extra: unused'):
      config.LoadCloudbuildConfigFromPath('error.yaml', self.messages)

  def testYamlMultipleUnused(self):
    """More than one mistake on the same level gets a more interesting error."""
    self.Touch('.', 'error.yaml', """
steps:
 - name: gcr.io/cloud-builders/docker
   args:
   - build
   - -t
   - gcr.io/my-project/simple
extra:
  data:
    is: "bad"
nonsense: "bad as well"
images: gcr.io/my-project/simple1
        """)
    with self.assertRaisesRegex(
        config.BadConfigException,
        r'error\.yaml: \.\{extra,nonsense\}: unused'):
      config.LoadCloudbuildConfigFromPath('error.yaml', self.messages)

  def testJsonMultipleUnused(self):
    self.Touch('.', 'error.json', """
{
  "steps": [
    {"name": "gcr.io/cloud-builders/docker",
     "args": ["build", "-t", "gcr.io/$PROJECT_ID/simple", "."],
     "bogus": "200s",
     "foo": "bar"
    }
   ],
  "images": "gcr.io/$PROJECT_ID/simple"
}
        """)
    with self.assertRaisesRegex(
        config.BadConfigException,
        r'error\.json: \.steps\[0\]\.{bogus,foo}: unused'):
      config.LoadCloudbuildConfigFromPath('error.json', self.messages)

  def testLoadJson_FromStream(self):
    data = io.StringIO("""
{
  "steps": [
    {"name": "gcr.io/cloud-builders/docker",
     "args": ["build", "-t", "gcr.io/my-project/simple"]
    }
   ],
  "images": "gcr.io/my-project/simple"
}
        """)
    build = config.LoadCloudbuildConfigFromStream(data, self.messages)
    self.assertEqual(build, self.messages.Build(
        steps=[
            self.messages.BuildStep(
                name='gcr.io/cloud-builders/docker',
                args=['build', '-t', 'gcr.io/my-project/simple'],
            ),
        ],
        images=['gcr.io/my-project/simple'],
    ))

  def testJsonSyntaxError_FromStream(self):
    """Misplaced brace at the end of the document."""
    data = io.StringIO("""
{
  "steps": [
    {"name": "gcr.io/cloud-builders/docker",
     "args": ["build", "-t", "gcr.io/my-project/simple"]
    }
   ],
  "images": "gcr.io/my-project/simple"
}}
        """)
    with self.assertRaisesRegex(
        config.ParserError, 'parsing Cloud Build configuration'):
      config.LoadCloudbuildConfigFromStream(data, self.messages)

  def testSubstitution_FromStream(self):
    data = io.StringIO("""
{
  "steps": [
    {"name": "gcr.io/cloud-builders/docker",
     "args": ["build", "-t", "gcr.io/my-project/simple"]
    }
   ],
  "substitutions": {"_MESSAGE": "hello world"}
}
        """)
    build = config.LoadCloudbuildConfigFromStream(data, self.messages)
    self.assertEqual(build, self.messages.Build(
        steps=[
            self.messages.BuildStep(
                name='gcr.io/cloud-builders/docker',
                args=['build', '-t', 'gcr.io/my-project/simple'],
            ),
        ],
        substitutions=self.messages.Build.SubstitutionsValue(
            additionalProperties=[
                self.messages.Build.SubstitutionsValue.AdditionalProperty(
                    key='_MESSAGE', value='hello world'),
            ]
        ),
    ))

  def testSubstitutionError_FromStream(self):
    data = io.StringIO("""
{
  "steps": [
    {"name": "gcr.io/cloud-builders/docker",
     "args": ["build", "-t", "gcr.io/my-project/simple"]
    }
   ],
  "substitutions": {"COMMIT_SHA": "my-sha"}
}
        """)
    with self.assertRaisesRegex(
        config.BadConfigException,
        'config cannot specify built-in substitutions'):
      config.LoadCloudbuildConfigFromStream(data, self.messages)


class FieldMappingTest(subtests.Base):
  """Test the ability to normalize config field names.
  """

  def testSnakeToCamelString(self):
    cases = [
        ('_', '_'),
        ('__', '__'),
        ('wait_for', 'waitFor'),
        ('foozleBop', 'foozleBop'),
        ('_xyz', '_xyz'),
        ('__xyz', '__xyz'),
        ('a__b', 'aB'),
    ]
    for input_string, expected in cases:
      self.assertEqual(config._SnakeToCamelString(input_string), expected)

  def testSnakeToCamel(self):
    cases = [
        ({'wait_for': ['x', 'y', 'z']},
         {'waitFor': ['x', 'y', 'z']}),
        ({'super_duper': {'wait_for': ['x', 'y', 'z']}},
         {'superDuper': {'waitFor': ['x', 'y', 'z']}}),
        ({'super_list': [{'wait_for': ['x', 'y', 'z']}]},
         {'superList': [{'waitFor': ['x', 'y', 'z']}]}),
        # If the key is 'secret_env' the value is not transformed, while other
        # keys, and the key itself, are transformed.
        ({'camel_me': '', 'secret_env': {'FOO_BAR': 'asdf'}},
         {'camelMe': '', 'secretEnv': {'FOO_BAR': 'asdf'}}),
        # If the key is 'secretEnv' the value is not transformed.
        ({'secretEnv': {'FOO_BAR': 'asdf'}},
         {'secretEnv': {'FOO_BAR': 'asdf'}}),
    ]
    for input_string, expected in cases:
      self.assertEqual(config._SnakeToCamel(input_string), expected)

if __name__ == '__main__':
  test_case.main()
