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

"""Tests for the calliope.markdown module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import cli
from googlecloudsdk.calliope import markdown
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


class MarkdownTest(test_case.Base):

  def testSplitLongCommandExampleLineActuallyShort(self):
    example = """\
$ gcloud compute instances list --verbosity=info\
"""
    expected = example
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testSplitLongCommandExampleLineWithFlags(self):
    example = """\
$ gcloud compute instances list --verbosity=info --format=json --xyz abc --abc=xyz\
"""
    expected = """\
$ gcloud compute instances list --verbosity=info --format=json \\
      --xyz abc --abc=xyz\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineWithSingleQuote(self):
    example = """\
$ gcloud compute instances list --format='table[box,title=Instances](name:sort=1, zone:title=zone, status)'\
"""
    expected = """\
$ gcloud compute instances list \\
      --format='table[box,title=Instances](name:sort=1,
   zone:title=zone, status)'\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineWithSingleQuoteSplit(self):
    example = """\
$ gcloud alpha dns record-sets transaction remove -z MANAGED_ZONE --name my.domain. --ttl 2345 --type TXT 'Hello world','Bye world'\
"""
    expected = """\
$ gcloud alpha dns record-sets transaction remove -z MANAGED_ZONE \\
      --name my.domain. --ttl 2345 --type TXT \\
      'Hello world','Bye world'\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineWithDoubleQuote(self):
    example = """\
$ gcloud compute instances list --format="table[box,title=Instances](name:sort=1, zone:title=zone, status)"\
"""
    expected = """\
$ gcloud compute instances list \\
      --format="table[box,title=Instances](name:sort=1,\\
   zone:title=zone, status)"\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineWithDoubleQuoteSplit(self):
    example = """\
$ gcloud alpha dns record-sets transaction remove -z MANAGED_ZONE --name my.domain. --ttl 2345 --type TXT "Hello world","Bye world"\
"""
    expected = """\
$ gcloud alpha dns record-sets transaction remove -z MANAGED_ZONE \\
      --name my.domain. --ttl 2345 --type TXT \\
      "Hello world","Bye world"\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineWithNestedQuotes(self):
    example = """\
$ gcloud beta logging write LOG_NAME extra args '{"key": "value"}' --payload-type=struct\
"""
    expected = """\
$ gcloud beta logging write LOG_NAME extra args '{"key": "value"}' \\
      --payload-type=struct\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineWithReallyLongArg(self):
    example = """\
$ gcloud compute instances list --format=abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz\
"""
    expected = """\
$ gcloud compute instances list \\
      --format=abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabc\\
  defghijklmnopqrstuvwxyz\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineWithReallyLongArgWithComma(self):
    example = """\
$ gcloud compute instances list --format=http://zyx.bca/abcdefghijklmnopqrstuvwxyz,abcdefghijklmnopqrstuvwxyz\
"""
    expected = """\
$ gcloud compute instances list \\
      --format=http://zyx.bca/abcdefghijklmnopqrstuvwxyz,\\
  abcdefghijklmnopqrstuvwxyz\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineWithReallyLongArgWithSlash(self):
    example = """\
$ gcloud compute instances list --format=http://zyx.bca/abcdefg/hijklmno/pqrstuvwxyz/abcdefg/hijklmno/pqrstuvwxyz\
"""
    expected = """\
$ gcloud compute instances list \\
      --format=http://zyx.bca/abcdefg/hijklmno/pqrstuvwxyz/abcdefg/\\
  hijklmno/pqrstuvwxyz\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineWithReallyLongSingleQuote(self):
    example = """\
$ gcloud compute instances list --format='table(name:sort=2:align=center:label=INSTANCE, zone:sort=1:reverse, creationTimestamp.date("%Y-%m-%d"):label=START)'\
"""
    expected = """\
$ gcloud compute instances list \\
      --format='table(name:sort=2:align=center:label=INSTANCE,
   zone:sort=1:reverse,
   creationTimestamp.date("%Y-%m-%d"):label=START)'\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineWithReallyLongDoubleQuote(self):
    example = """\
$ gcloud compute instances list --format="table(name:sort=2:align=center:label=INSTANCE, zone:sort=1:reverse, creationTimestamp.date('%Y-%m-%d'):label=START)"\
"""
    expected = """\
$ gcloud compute instances list \\
      --format="table(name:sort=2:align=center:label=INSTANCE,\\
   zone:sort=1:reverse,\\
   creationTimestamp.date('%Y-%m-%d'):label=START)"\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineCloseToBoundary(self):
    example = """\
$ gcloud alpha compute instance-templates create example-instance --scopes compute-rw,me@project.gserviceaccount.com=storage-rw\
"""
    expected = """\
$ gcloud alpha compute instance-templates create example-instance \\
      --scopes compute-rw,me@project.gserviceaccount.com=storage-rw\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineOffByOne(self):
    example = """\
$ gcloud alpha compute ssh example-instance --zone us-central1-a -- -vvv -L 80:%INSTANCE%:80\
"""
    expected = """\
$ gcloud alpha compute ssh example-instance --zone us-central1-a \\
      -- -vvv -L 80:%INSTANCE%:80\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)

  def testgSplitLongCommandExampleLineStrangeSplit(self):
    example = """\
$ python -c "from time import mktime, strptime; print int(mktime(strptime('01 July 2015', '%d %B %Y')))"\
"""
    expected = """\
$ python \\
      -c \\
      "from time import mktime, strptime; print\\
   int(mktime(strptime('01 July 2015', '%d %B %Y')))"\
"""
    actual = markdown.ExampleCommandLineSplitter().Split(example)
    self.assertEqual(expected, actual)


class MarkdownEditTest(sdk_test_base.SdkBase, parameterized.TestCase):

  def SetUp(self):
    calliope_test_home = self.Resource('tests', 'unit', 'calliope', 'testdata')
    loader = cli.CLILoader(
        name='gcloud',
        command_root_directory=os.path.join(calliope_test_home, 'sdk3'))
    self.generator = markdown.CommandMarkdownGenerator(
        loader.Generate()._TopElement())

  def testFixAirQuotesMarkdown(self):
    """Verify fix for _FixAirQuotesMarkdown RE that matched ```...```."""
    expected = "\n*```undefined```*:::\nUse :label=''.\n"
    actual = self.generator._FixAirQuotesMarkdown(expected)
    self.assertEqual(expected, actual)

  def testAddCommandLinkMarkdownSkipFirst(self):
    doc = '\n\n`gcloud markdown markdown-command` _MARKDOWN-FILE_\n'
    expected = doc
    actual = self.generator._AddCommandLinkMarkdown(doc)
    self.assertEqual(expected, actual)

  def testAddCommandLinkMarkdownSkipFirstWithAlpha(self):
    doc = '\n\n*(ALPHA)* `gcloud markdown markdown-command` _MARKDOWN-FILE_\n'
    expected = doc
    actual = self.generator._AddCommandLinkMarkdown(doc)
    self.assertEqual(expected, actual)

  def testAddCommandLinkMarkdownSkipFirstWithBeta(self):
    doc = '\n\n*(BETA)* `gcloud markdown markdown-command` _MARKDOWN-FILE_\n'
    expected = doc
    actual = self.generator._AddCommandLinkMarkdown(doc)
    self.assertEqual(expected, actual)

  def testAddCommandLinkMarkdownDontSkipFirstWithUnknown(self):
    doc = '\n\n*(UNKNOWN)* `gcloud markdown markdown-command` _MARKDOWN-FILE_\n'
    expected = ('\n\n*(UNKNOWN)* `link:gcloud/markdown/markdown-command'
                '[gcloud markdown markdown-command]` _MARKDOWN-FILE_\n')
    actual = self.generator._AddCommandLinkMarkdown(doc)
    self.assertEqual(expected, actual)

  def testAddCommandLinkMarkdownTwoSubcommands(self):
    doc = 'See `gcloud markdown markdown-command` for an overview.'
    expected = ('See `link:gcloud/markdown/markdown-command'
                '[gcloud markdown markdown-command]` for an overview.')
    actual = self.generator._AddCommandLinkMarkdown(doc)
    self.assertEqual(expected, actual)

  def testAddCommandLinkMarkdownOneSubcommand(self):
    doc = 'See `gcloud markdown` for an overview of markdown.'
    expected = ('See `link:gcloud/markdown'
                '[gcloud markdown]` for an overview of markdown.')
    actual = self.generator._AddCommandLinkMarkdown(doc)
    self.assertEqual(expected, actual)

  def testAddCommandLinkMarkdownNoSubcommand(self):
    doc = 'See `gcloud` for an overview of everything.'
    expected = 'See `link:gcloud[gcloud]` for an overview of everything.'
    actual = self.generator._AddCommandLinkMarkdown(doc)
    self.assertEqual(expected, actual)

  def testAddCommandLinkMarkdownSkipUnknownCommand(self):
    doc = 'See `gcloud no such command` for an overview of nothing.'
    expected = doc
    actual = self.generator._AddCommandLinkMarkdown(doc)
    self.assertEqual(expected, actual)

  def testMarkdownEditsInOrder(self):
    """Test the link: edit tests above in a single doc using all edits."""
    example = """\
# GCLOUD_CONFIG_CONFIGURATIONS_ACTIVATE(1)


## SYNOPSIS

`gcloud markdown markdown-command` _MARKDOWN-FILE_


## ALPHA SYNOPSIS

*(ALPHA)* `gcloud markdown markdown-command` _SHOULD_NOT_GENERATE_LINK_


## BETA SYNOPSIS

*(BETA)* `gcloud markdown markdown-command` _SHOULD_NOT_GENERATE_LINK_


## UNKNOWN SYNOPSIS

*(UNKNOWN)* `gcloud markdown markdown-command` _SHOULD_GENERATE_LINK_


## DESCRIPTION

One.

See `gcloud markdown markdown-command` for an overview of named
configurations.

Two.

See `gcloud markdown` for an overview of markdown.

Three.

See `gcloud` for an overview of everything.

Four.

See `gcloud no such command` for an overview of nothing.

Five.
"""
    expected = """\
# GCLOUD_CONFIG_CONFIGURATIONS_ACTIVATE(1)


## SYNOPSIS

`gcloud markdown markdown-command` _MARKDOWN-FILE_


## ALPHA SYNOPSIS

*(ALPHA)* `gcloud markdown markdown-command` _SHOULD_NOT_GENERATE_LINK_


## BETA SYNOPSIS

*(BETA)* `gcloud markdown markdown-command` _SHOULD_NOT_GENERATE_LINK_


## UNKNOWN SYNOPSIS

*(UNKNOWN)* `link:gcloud/markdown/markdown-command[gcloud markdown markdown-command]` _SHOULD_GENERATE_LINK_


## DESCRIPTION

One.

See `link:gcloud/markdown/markdown-command[gcloud markdown markdown-command]` for an overview of named
configurations.

Two.

See `link:gcloud/markdown[gcloud markdown]` for an overview of markdown.

Three.

See `link:gcloud[gcloud]` for an overview of everything.

Four.

See `gcloud no such command` for an overview of nothing.

Five.
"""
    actual = self.generator.Edit(example)
    self.assertEqual(expected, actual)

  @parameterized.parameters(
      (['gcloud', 'markdown', 'markdown-command'], ['--my-arg', 'x'], True,
       'link:gcloud/markdown/markdown-command[gcloud markdown markdown-command]'
       ' --my-arg x'),
      (['gcloud', 'markdown', 'markdown-command'], ['--my-arg', 'x'], False,
       None),
      (['gcloud', 'markdown', 'markdown-command'], [], True,
       'link:gcloud/markdown/markdown-command[gcloud markdown markdown-command]'
      ),
      (['gcloud', 'markdown', 'markdown-command'], [], False,
       'link:gcloud/markdown/markdown-command[gcloud markdown markdown-command]'
      ))
  def testEditExample(self, cmd, args, with_args, result):
    self.assertEqual(
        self.generator.FormatExample(cmd, args, with_args=with_args),
        result)


# TODO(b/35421257): Add disable_header=True tests.


if __name__ == '__main__':
  test_case.main()
