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

"""Integration tests for Type Registry commands."""

from googlecloudsdk.core import log
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


DUMMY_DESCRIPTOR_URL = 'https://dummy-resource-service.appspot.com/swagger-2.0.json'
DESCRIPTION_0 = 'A great description of a type.'
DESCRIPTION_1 = 'Something fairly exciting.'


def TypeProviderCommandFor(verb,
                           provider,
                           options_file=None,
                           description=None,
                           descriptor_url=None,
                           additional_args=None):
  """Build a type-providers command.

  Args:
    verb: The command verb, e.g. create.
    provider: The type provider name.
    options_file: The path to an API options file.
    description: String description of the type provider.
    descriptor_url: API descriptor doc url.
    additional_args: Any additional arguments suffixed explicitly.

  Returns:
    The full command string (minus 'gcloud') for use with self.Run in a test.
  """
  command_string = 'beta deployment-manager type-providers {0} {1} '.format(
      verb, provider)
  if options_file is not None:
    command_string += ' --api-options-file={0}'.format(options_file)
  if description is not None:
    command_string += ' --description="{0}"'.format(description)
  if descriptor_url is not None:
    command_string += ' --descriptor-url={0}'.format(descriptor_url)
  if additional_args is not None:
    command_string += additional_args
  return command_string


def CompositeTypeCommandFor(verb,
                            type_name,
                            template_file=None,
                            description=None,
                            additional_args=None):
  """Build a types command.

  Args:
    verb: The command verb, e.g. create.
    type_name: The composite type name.
    template_file: The path to a template file.
    description: String description of the composite type.
    additional_args: Any additional arguments suffixed explicitly.

  Returns:
    The full command string (minus 'gcloud') for use with self.Run in a test.
  """
  command_string = 'beta deployment-manager types {0} {1} '.format(
      verb, type_name)
  if template_file is not None:
    command_string += ' --template=' + template_file
  if description is not None:
    command_string += ' --description="{0}"'.format(description)
  if additional_args is not None:
    command_string += additional_args

  return command_string


class TypeRegistryIntegrationTest(e2e_base.WithServiceAuth):
  """Tests basic functionality of the Service Registry client."""

  def SetUp(self):
    self.type_provider_name = e2e_utils.GetResourceNameGenerator(
        prefix='type-registry-integ-tp').next()
    self.composite_type_name = e2e_utils.GetResourceNameGenerator(
        prefix='type-registry-integ-ct').next()
    self.type_provider_options = self.FilePathFor(
        'type_providers/simple_dummy_config.yaml')
    self.composite_type_template = self.FilePathFor(
        'simple_configs/simple.jinja')
    self.type_provider_exists = False
    self.composite_type_exists = False

  def FilePathFor(self, path):
    """Build a path to the DM resource specified by the *path argument.

    Args:
      path: Path under the DM test data directory leading to a resource.

    Returns:
      The full resource path in gcloud's test data directories.
    """
    return self.Resource('tests', 'lib', 'surface', 'deployment_manager',
                         'test_data', path)

  def TearDown(self):
    if self.type_provider_exists:
      try:
        self.Run(TypeProviderCommandFor('delete',
                                        self.type_provider_name,
                                        additional_args=' --quiet'))
      except Exception as err:  # pylint: disable=broad-except
        log.Print('Caught an exception during cleanup: [{0}]'.format(err))
    if self.composite_type_exists:
      try:
        self.Run(CompositeTypeCommandFor('delete',
                                         self.composite_type_name,
                                         additional_args=' --quiet'))
      except Exception as err:  # pylint: disable=broad-except
        log.Print('Caught an exception during cleanup: [{0}]'.format(err))

  def testTypeProviderLifecycle(self):
    self.Run(TypeProviderCommandFor('create',
                                    self.type_provider_name,
                                    options_file=self.type_provider_options,
                                    description=DESCRIPTION_0,
                                    descriptor_url=DUMMY_DESCRIPTOR_URL))
    self.type_provider_exists = True
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Created type_provider [{0}].'.format(self.type_provider_name))
    self.ClearOutputAndErr()

    self.Run(TypeProviderCommandFor('describe', self.type_provider_name))
    self.AssertOutputContains(DUMMY_DESCRIPTOR_URL)
    self.AssertOutputContains(DESCRIPTION_0)
    self.ClearOutputAndErr()

    self.Run(TypeProviderCommandFor('update',
                                    self.type_provider_name,
                                    options_file=self.type_provider_options,
                                    description=DESCRIPTION_1,
                                    descriptor_url=DUMMY_DESCRIPTOR_URL))
    self.AssertErrContains(
        'Updated type_provider [{0}].'.format(self.type_provider_name))
    self.ClearOutputAndErr()

    self.Run(TypeProviderCommandFor('describe', self.type_provider_name))
    self.AssertOutputContains(DUMMY_DESCRIPTOR_URL)
    self.AssertOutputContains(DESCRIPTION_1)
    self.AssertOutputContains(DESCRIPTION_1)
    self.AssertOutputNotContains(DESCRIPTION_0)
    self.ClearOutputAndErr()

    self.Run(TypeProviderCommandFor('delete',
                                    self.type_provider_name,
                                    additional_args=' --quiet'))
    self.AssertErrContains(
        'Deleted type_provider [{0}].'.format(self.type_provider_name))
    self.type_provider_exists = False

  def testCompositeTypeLifecycle(self):
    self.Run(CompositeTypeCommandFor('create',
                                     self.composite_type_name,
                                     template_file=self.composite_type_template,
                                     description=DESCRIPTION_0))
    self.composite_type_exists = True
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Created composite_type [{0}].'.format(self.composite_type_name))
    self.ClearOutputAndErr()

    self.Run(
        CompositeTypeCommandFor(
            'describe',
            self.composite_type_name,
            additional_args=(' --provider=composite'
                             ' --format="[json-decode] (composite_type)"')))
    self.AssertErrContains(self.composite_type_name)
    self.AssertErrContains(self.Project())
    self.AssertOutputContains(DESCRIPTION_0)
    self.ClearOutputAndErr()

    self.Run(CompositeTypeCommandFor('update',
                                     self.composite_type_name,
                                     description=DESCRIPTION_1))
    self.AssertErrContains(
        'Updated composite_type [{0}].'.format(self.composite_type_name))
    self.ClearOutputAndErr()

    self.Run(
        CompositeTypeCommandFor(
            'describe',
            self.composite_type_name,
            additional_args=(' --provider=composite'
                             ' --format="[json-decode] (composite_type)"')))
    self.AssertErrContains(self.composite_type_name)
    self.AssertErrContains(self.Project())
    self.AssertOutputContains(DESCRIPTION_1)
    self.AssertOutputContains(DESCRIPTION_1)
    self.AssertOutputNotContains(DESCRIPTION_0)
    self.ClearOutputAndErr()

    self.Run(CompositeTypeCommandFor('delete',
                                     self.composite_type_name,
                                     additional_args=' --quiet'))
    self.AssertErrContains(
        'Deleted composite_type [{0}].'.format(self.composite_type_name))
    self.composite_type_exists = False

  def ClearOutputAndErr(self):
    self.ClearOutput()
    self.ClearErr()


if __name__ == '__main__':
  test_case.main()
