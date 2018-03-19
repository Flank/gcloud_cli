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

"""Tests of the 'list' command."""

from tests.lib.surface.functions import base


EXPECTED_OUTPUT = """\
EVENT_PROVIDER EVENT_TYPE EVENT_TYPE_DEFAULT RESOURCE_TYPE RESOURCE_OPTIONAL
cloud.pubsub google.pubsub.topic.publish Yes topic No
cloud.pubsub providers/cloud.pubsub/eventTypes/topic.publish No topic No
cloud.storage google.storage.object.archive No bucket No
cloud.storage google.storage.object.delete No bucket No
cloud.storage google.storage.object.finalize Yes bucket No
cloud.storage google.storage.object.metadataUpdate No bucket No
cloud.storage providers/cloud.storage/eventTypes/object.change No bucket No
"""


class ListTest(base.FunctionsTestBase):

  def testSimple(self):
    self.Run('functions event-types list')
    self.AssertOutputContains(EXPECTED_OUTPUT, normalize_space=True)
