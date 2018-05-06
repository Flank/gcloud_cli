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

"""Test all core.resources parsers by collection."""

from tests.lib import cli_test_base


class AllParsersTest(cli_test_base.CliTestBase):

  def testAllParsers(self):
    # Get the list of all collections.
    collections = self.Run('meta apis collections list --format=disable '
                           '--flatten=full_name '
                           '--filter=enable_uri_parsing:true')

    # Generate a list of example URIs, one per collection.
    uris = []
    for collection in collections:
      uris += self.Run('meta resources generate --format=disable '
                       '--collection={}'.format(collection))

    # Parse the list of sample URIs.
    errors = self.Run('meta resources parse --no-stack-trace '
                      '--format=disable --filter=error:* {}'.format(
                          ' '.join(uris)))

    # The list should be empty. Comparing against [] displays each failed URI
    # along with its error message.
    self.assertEqual([], sorted(errors))


if __name__ == '__main__':
  cli_test_base.main()
