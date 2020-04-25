# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests for the command_lib.meta.generate_cli_trees module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import re
import subprocess

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.meta import generate_cli_trees
from googlecloudsdk.command_lib.meta import list_cli_trees
from googlecloudsdk.core import http
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import files
from tests.lib import calliope_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.unit.calliope import testdata

import mock


class _MockResponse(object):
  """httplib2 mock response."""

  def __init__(self, status):
    self.status = status


def _MockHttpResult(url):
  if url != 'http://man7.org/linux/man-pages/man1/ls.1.html':
    return _MockResponse(404), 'Not found.'
  return _MockResponse(200), _MAN_URL_OUTPUT['ls'].encode('utf-8')


_BQ_COMMAND_OUTPUT = {
    'help': """\
Python script for interacting with BigQuery.


USAGE: bq [--global_flags] <command> [--command_flags] [args]


Any of the following commands:
  cancel, cp, extract, head, help, init, insert, load, ls, mk, mkdef, partition,
  query, rm, shell, show, update, version, wait


cancel     Request a cancel and waits for the job to be cancelled.

           Requests a cancel and then either: a) waits until the job is done if
           the sync flag is set [default], or b) returns immediately if the sync
           flag is not set. Not all job types support a cancel, an error is
           returned if it cannot be cancelled. Even for jobs that support a
           cancel, success is not guaranteed, the job may have completed by the
           time the cancel request is noticed, or the job may be in a stage
           where it cannot be cancelled.

           Examples:
           bq cancel job_id # Requests a cancel and waits until the job is done.
           bq --nosync cancel job_id # Requests a cancel and returns
           immediately.

           Arguments:
           job_id: Job ID to cancel.

query      Execute a query.

           Query should be specified on command line, or passed on stdin.

           Examples:
           bq query 'select count(*) from publicdata:samples.shakespeare'
           echo 'select count(*) from publicdata:samples.shakespeare' | bq query

           Usage:
           query [<sql_query>]


Run 'bq --help' to get help for global flags.
Run 'bq help <command>' to get help for <command>.
""",
    '--help': """\
Python script for interacting with BigQuery.


USAGE: bq [--global_flags] <command> [--command_flags] [args]



Global flags:

bq_flags:
  --api: API endpoint to talk to.
    (default: 'https://www.googleapis.com')
  --[no]debug_mode: Show tracebacks on Python exceptions.
    (default: 'false')
  --discovery_file: Filename for JSON document to read for discovery.
    (default: '')
  -q,--[no]quiet: If True, ignore status updates while jobs are running.
    (default: 'false')
  -sync,--[no]synchronous_mode: If True, wait for command completion before
    returning, and use the job completion status for error codes. If False,
    simply create the job, and use the success of job creation as the error
    code.
    (default: 'true')

google.apputils.app:
  --[no]helpxml: like --help, but generates XML output

oauth2client.old_run:
  --auth_host_name: Host name to use when running a local web server to handle
    redirects during OAuth authorization.
    (default: 'localhost')

gflags:
  --flagfile: Insert flag definitions from the given file into the command line.
    (default: '')

Run 'bq help' to see the list of available commands.
Run 'bq help <command>' to get help for <command>.
""",
    'version': """\
This is BigQuery CLI 2.0.27

""",
}


class BqCliGeneratorTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.StartObjectPatch(
        generate_cli_trees.BqCliTreeGenerator,
        'Run',
        side_effect=lambda cmd: _BQ_COMMAND_OUTPUT['.'.join(cmd)])

  def testBqCliTreeGenerator(self):
    generator = generate_cli_trees.BqCliTreeGenerator('bq')
    tree = generator.Generate()
    resource_printer.Print(tree, 'json')
    self.AssertOutputIsGolden(__file__, 'bq.json')


_GSUTIL_COMMAND_OUTPUT = {
    '--help': """\
Usage: gsutil [-D] [-DD] [-h header]... [-m] [-o] [-q] [command [opts...] args...]
Available commands:
  acl             Get, set, or change bucket and/or object ACLs
  help            Get help about commands and topics

Additional help topics:
  creds           Credential Types Supporting Various Use Cases

Use gsutil help <command or topic> for detailed help.
""",
    'acl.--help': """\
NAME
  acl - Get, set, or change bucket and/or object ACLs


SYNOPSIS
  gsutil acl set [-f] [-r] [-a] file-or-canned_acl_name url...

  where each <grant> is one of the following forms:

    -u <id|email>:<perm>
    -g <id|email|domain|All|AllAuth>:<perm>
    -p <viewers|editors|owners>-<project number>
    -d <id|email|domain|All|AllAuth|<viewers|editors|owners>-<project number>>



DESCRIPTION
  The acl command has three sub-commands:

SET
  The "acl set" command allows you to set an Access Control List on one or
  more buckets and objects. The simplest way to use it is to specify one of
  the canned ACLs, e.g.,:

    gsutil acl set private gs://bucket

  If you want to make an object or bucket publicly readable or writable, it is
  recommended to use "acl ch", to avoid accidentally removing OWNER permissions.
  See "gsutil help acl ch" for details.

  See "gsutil help acls" for a list of all canned ACLs.

  If you want to define more fine-grained control over your data, you can
  retrieve an ACL using the "acl get" command, save the output to a file, edit
  the file, and then use the "acl set" command to set that ACL on the buckets
  and/or objects. For example:

    gsutil acl get gs://bucket/file.txt > acl.txt

  Make changes to acl.txt such as adding an additional grant, then:

    gsutil acl set acl.txt gs://cats/file.txt

  Note that you can set an ACL on multiple buckets or objects at once,
  for example:

    gsutil acl set acl.txt gs://bucket/*.jpg

  If you have a large number of ACLs to update you might want to use the
  gsutil -m option, to perform a parallel (multi-threaded/multi-processing)
  update:

    gsutil -m acl set acl.txt gs://bucket/*.jpg

  Note that multi-threading/multi-processing is only done when the named URLs
  refer to objects, which happens either if you name specific objects or
  if you enumerate objects by using an object wildcard or specifying
  the acl -r flag.


SET OPTIONS
  The "set" sub-command has the following options

    -R, -r      Performs "acl set" request recursively, to all objects under
                the specified URL.

    -a          Performs "acl set" request on all object versions.

    -f          Normally gsutil stops at the first error. The -f option causes
                it to continue when it encounters errors. If some of the ACLs
                couldn't be set, gsutil's exit status will be non-zero even if
                this flag is set. This option is implicitly set when running
                "gsutil -m acl...".
""",
    'acl.set.--help': """\
NAME
  acl set - Get, set, or change bucket and/or object ACLs


SYNOPSIS
  gsutil acl set [-f] [-r] [-a] file-or-canned_acl_name url...

DESCRIPTION
SET
  The "acl set" command allows you to set an Access Control List on one or
  more buckets and objects. The simplest way to use it is to specify one of
  the canned ACLs, e.g.,:

    gsutil acl set private gs://bucket

  If you want to make an object or bucket publicly readable or writable, it is
  recommended to use "acl ch", to avoid accidentally removing OWNER permissions.
  See "gsutil help acl ch" for details.

  See "gsutil help acls" for a list of all canned ACLs.


SET OPTIONS
  The "set" sub-command has the following options

    -R, -r      Performs "acl set" request recursively, to all objects under
                the specified URL.

    -a          Performs "acl set" request on all object versions.

    -f          Normally gsutil stops at the first error. The -f option causes
                it to continue when it encounters errors. If some of the ACLs
                couldn't be set, gsutil's exit status will be non-zero even if
                this flag is set. This option is implicitly set when running
                "gsutil -m acl...".
""",
    'help': """\
NAME
  help - Get help about commands and topics


SYNOPSIS

  gsutil help [command or topic]



DESCRIPTION
  Running:

    gsutil help

  will provide a summary of all commands and additional topics on which
  help is available.
""",
    'help.creds': """\
NAME
  creds - Credential Types Supporting Various Use Cases


OVERVIEW
  gsutil currently supports several types of credentials/authentication, as
  well as the ability to access public data anonymously (see "gsutil help anon"
  for more on anonymous access).


Configuring/Using Credentials via Cloud SDK Distribution of gsutil
  When gsutil is installed/used via the Cloud SDK ("gcloud"), credentials are
  stored by Cloud SDK in a non-user-editable file located under


Configuring/Using Credentials via Standalone gsutil Distribution
  If you installed a standalone distribution of gsutil (downloaded from
  https://pub.storage.googleapis.com/gsutil.tar.gz,
  https://pub.storage.googleapis.com/gsutil.zip, or PyPi), credentials are


SUPPORTED CREDENTIAL TYPES
  gsutil supports several types of credentials (the specific subset depends on
  which distribution of gsutil you are using; see above discussion).

  OAuth2 User Account:
    This is the preferred type of credentials for authenticating requests on
    behalf of a specific user (which is probably the most common use of gsutil).
""",
    'help.options': """\
NAME
  options - Top-Level Command-Line Options


DESCRIPTION
  gsutil supports separate options for the top-level gsutil command and
  the individual sub-commands (like cp, rm, etc.)

OPTIONS
  -D          Shows HTTP requests/headers and additional debug info needed when
              posting support requests, including exception stack traces.

  -DD         Shows HTTP requests/headers, additional debug info,
              exception stack traces, plus HTTP upstream payload.

  -q          Causes gsutil to perform operations quietly, i.e., without
              reporting progress indicators of files being copied or removed,
              etc. Errors are still reported. This option can be useful for
              running gsutil from a cron job that logs its output to a file, for
              which the only information desired in the log is failures.
""",
    'version': """\
gsutil version: 4.27
""",
}


class GsutilCliGeneratorTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.StartObjectPatch(
        generate_cli_trees.GsutilCliTreeGenerator,
        'Run',
        side_effect=lambda cmd: _GSUTIL_COMMAND_OUTPUT['.'.join(cmd)])

  def testGsutilCliTreeGenerator(self):
    generator = generate_cli_trees.GsutilCliTreeGenerator('gsutil')
    tree = generator.Generate()
    resource_printer.Print(tree, 'json')
    self.AssertOutputIsGolden(__file__, 'gsutil.json')


_KUBECTL_COMMAND_OUTPUT = {
    '--help': """\
kubectl controls the Kubernetes cluster manager.

Find more information at https://github.com/kubernetes/kubernetes.

Basic Commands (Beginner):
  create         Create a resource by filename or stdin

Troubleshooting and Debugging Commands:
  describe       Show details of a specific resource or group of resources

Use "kubectl <command> --help" for more information about a given command.
Use "kubectl options" for a list of global command-line options (applies to all commands).
""",
    'create.--help': """\
Create a resource by filename or stdin.

JSON and YAML formats are accepted.

Examples:
  # Create a pod using the data in pod.json.
  kubectl create -f ./pod.json

  # Create a pod based on the JSON passed into stdin.
  cat pod.json | kubectl create -f -

  # Edit the data in docker-registry.yaml in JSON using the v1 API format then create the resource using the edited data.
  kubectl create -f docker-registry.yaml --edit --output-version=v1 -o json

Available Commands:
  deployment          Create a deployment with the specified name.

Options:
      --allow-missing-template-keys=true: If true, ignore any errors in templates when a field or map key is missing in the template. Only applies to golang and jsonpath output formats.
  -f, --filename=[]: Filename, directory, or URL to files to use to create the resource

Usage:
  kubectl create -f FILENAME [options]

Use "kubectl <command> --help" for more information about a given command.
Use "kubectl options" for a list of global command-line options (applies to all commands).
""",
    'create.deployment.--help': """\
Create a deployment with the specified name.

Aliases:
deployment, deploy

Examples:
  # Create a new deployment named my-dep that runs the busybox image.
  kubectl create deployment my-dep --image=busybox

Options:
      --dry-run=false: If true, only print the object that would be sent, without sending it.
      --generator='deployment-basic/v1beta1': The name of the API generator to use.

Usage:
  kubectl create deployment NAME --image=image [--dry-run] [options]

Use "kubectl options" for a list of global command-line options (applies to all commands).
""",
    'describe.--help': """\
Show details of a specific resource or group of resources. This command joins many API calls together to form a detailed description of a given resource or group of resources.

  $ kubectl describe TYPE NAME_PREFIX

will first check for an exact match on TYPE and NAME PREFIX. If no such resource exists, it will output details for every resource that has a name prefixed with NAME PREFIX.

Valid resource types include:

  * all
  * namespaces (aka 'ns')

Examples:
  # Describe a node
  kubectl describe nodes kubernetes-node-emt8.c.myproject.internal

Options:
  -f, --filename=[]: Filename, directory, or URL to files containing the resource to describe
      --show-events=true: If true, display events related to the described object.

Usage:
  kubectl describe (-f FILENAME | TYPE [NAME_PREFIX | -l label] | TYPE/NAME) [options]

Use "kubectl options" for a list of global command-line options (applies to all commands).
""",
    'options': """\
The following options can be passed to any command:

      --alsologtostderr=false: log to standard error as well as files
      --client-certificate='': Path to a client certificate file for TLS
      --vmodule=: comma-separated list of pattern=N settings for file-filtered logging
""",
    'version.--client': """\
Client Version: version.Info{Major:"1", Minor:"7", GitVersion:"v1.7.6", GitCommit:"4bc5e7f9a6c25dc4c03d4d656f2cefd21540e28c", GitTreeState:"clean", BuildDate:"2017-09-14T06:55:55Z", GoVersion:"go1.8.3", Compiler:"gc", Platform:"linux/amd64"}
""",
}


class KubectlCliGeneratorTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.StartObjectPatch(
        generate_cli_trees.CliTreeGenerator,
        'Run',
        side_effect=lambda cmd: _KUBECTL_COMMAND_OUTPUT['.'.join(cmd)])

  def testKubectlCliTreeGenerator(self):
    generator = generate_cli_trees.KubectlCliTreeGenerator('kubectl')
    tree = generator.Generate()
    resource_printer.Print(tree, 'json')
    self.AssertOutputIsGolden(__file__, 'kubectl.json')


class ListCliTreesTest(calliope_test_base.CalliopeTestBase):

  def testListCliTrees(self):
    cli_tree_dir = os.path.dirname(testdata.__file__)
    cli_tree_config_dir = os.path.join(os.path.dirname(__file__), 'testdata')
    self.StartObjectPatch(cli_tree, 'CliTreeDir', return_value=cli_tree_dir)
    self.StartObjectPatch(cli_tree, 'CliTreeConfigDir',
                          return_value=cli_tree_config_dir)

    items = []
    for item in list_cli_trees.ListAll():
      if item.path.endswith('.pyc') or item.path.endswith('.yaml'):
        # race condition with other tests
        continue
      directory, base = os.path.split(item.path)
      directory = directory.replace(os.path.sep, '/')
      if directory.endswith('/meta/testdata'):
        prefix = 'CONFIG'
      elif directory.endswith('/calliope/testdata'):
        prefix = 'INSTALL'
      else:
        prefix = 'ERROR'
      item.path = '/'.join([prefix, base])
      items.append(item)
    items = sorted(items, key=lambda x: (x.command, x.path))

    resource_printer.Print(items, 'csv(command,cli_version,version,path,error)')
    self.AssertOutputEquals("""\
command,cli_version,version,path,error
bq,2.0.27,1,CONFIG/bq.json,
gcloud,TEST,1,INSTALL/gcloud.json,
gcloud-branch,TEST,1,INSTALL/gcloud-branch.json,
gcloud-deserialized,TEST,1,INSTALL/gcloud-deserialized.json,
gcloud_commands,UNKNOWN,UNKNOWN,INSTALL/gcloud_commands.py,
gcloud_completions_branch,UNKNOWN,UNKNOWN,INSTALL/gcloud_completions_branch.golden,
gsutil,4.27,1,CONFIG/gsutil.json,
kubectl,v1.7.6,1,CONFIG/kubectl.json,
ls-man,man-0.1,1,CONFIG/ls-man.json,
ls-url,man7.org-0.1,1,CONFIG/ls-url.json,
""")


_MAN_COMMAND_OUTPUT = {
    'ls': """\
LS(1)                            User Commands                           LS(1)



NAME
       ls - list directory contents

SYNOPSIS
       ls [OPTION]... [FILE]...

DESCRIPTION
       List  information  about  the FILEs (the current directory by default).
       Sort entries alphabetically if none of -cftuvSUX nor --sort  is  speci‐
       fied.

       Mandatory  arguments  to  long  options are mandatory for short options
       too.

       -a, --all
              do not ignore entries starting with .

       -A, --almost-all
              do not list implied . and ..

       --author
              with -l, print the author of each file

       -b, --escape
              print C-style escapes for nongraphic characters

       --block-size=SIZE
              scale   sizes   by   SIZE   before   printing    them.     E.g.,
              '--block-size=M'  prints sizes in units of 1,048,576 bytes.  See
              SIZE format below.

       -B, --ignore-backups
              do not list implied entries ending with ~

       -c     with -lt: sort by, and show, ctime (time of last modification of
              file  status  information)  with -l: show ctime and sort by name
              otherwise: sort by ctime, newest first

       -C     list entries by columns

       --color[=WHEN]
              colorize the output.   WHEN  defaults  to  'always'  or  can  be
              'never' or 'auto'.  More info below

       -d, --directory
              list  directory entries instead of contents, and do not derefer‐
              ence symbolic links

       -D, --dired
              generate output designed for Emacs' dired mode

       -f     do not sort, enable -aU, disable -ls --color

       -F, --classify
              append indicator (one of */=>@|) to entries

       --file-type
              likewise, except do not append '*'

       --format=WORD
              across -x, commas -m, horizontal -x, long -l, single-column  -1,
              verbose -l, vertical -C

       --full-time
              like -l --time-style=full-iso

       -g     like -l, but do not list owner

       --group-directories-first
              group directories before files.

              augment  with  a  --sort option, but any use of --sort=none (-U)
              disables grouping

       -G, --no-group
              in a long listing, don't print group names

       -h, --human-readable
              with -l, print sizes in human readable format (e.g., 1K 234M 2G)

       --si   likewise, but use powers of 1000 not 1024

       -H, --dereference-command-line
              follow symbolic links listed on the command line

       --dereference-command-line-symlink-to-dir
              follow each command line symbolic link that points to  a  direc‐
              tory

       --hide=PATTERN
              do  not  list implied entries matching shell PATTERN (overridden
              by -a or -A)

       --indicator-style=WORD
              append indicator with style WORD to entry names: none (default),
              slash (-p), file-type (--file-type), classify (-F)

       -i, --inode
              print the index number of each file

       -I, --ignore=PATTERN
              do not list implied entries matching shell PATTERN

       -k, --kibibytes
              use 1024-byte blocks

       -l     use a long listing format

       -L, --dereference
              when showing file information for a symbolic link, show informa‐
              tion for the file the link references rather than for  the  link
              itself

       -m     fill width with a comma separated list of entries

       -n, --numeric-uid-gid
              like -l, but list numeric user and group IDs

       -N, --literal
              print  raw entry names (don't treat e.g. control characters spe‐
              cially)

       -o     like -l, but do not list group information

       -p, --indicator-style=slash
              append / indicator to directories

       -q, --hide-control-chars
              print ? instead of non graphic characters

       --show-control-chars
              show non graphic characters as-is  (default  unless  program  is
              'ls' and output is a terminal)

       -Q, --quote-name
              enclose entry names in double quotes

       --quoting-style=WORD
              use  quoting style WORD for entry names: literal, locale, shell,
              shell-always, c, escape

       -r, --reverse
              reverse order while sorting

       -R, --recursive
              list subdirectories recursively

       -s, --size
              print the allocated size of each file, in blocks

       -S     sort by file size

       --sort=WORD
              sort by WORD instead of name: none -U, extension  -X,  size  -S,
              time -t, version -v

       --time=WORD
              with  -l,  show time as WORD instead of modification time: atime
              -u, access -u, use -u, ctime -c, or  status  -c;  use  specified
              time as sort key if --sort=time

       --time-style=STYLE
              with  -l, show times using style STYLE: full-iso, long-iso, iso,
              locale, +FORMAT.  FORMAT is interpreted like 'date';  if  FORMAT
              is  FORMAT1<newline>FORMAT2, FORMAT1 applies to non-recent files
              and FORMAT2 to recent files; if STYLE is prefixed with 'posix-',
              STYLE takes effect only outside the POSIX locale

       -t     sort by modification time, newest first

       -T, --tabsize=COLS
              assume tab stops at each COLS instead of 8

       -u     with  -lt:  sort  by, and show, access time with -l: show access
              time and sort by name otherwise: sort by access time

       -U     do not sort; list entries in directory order

       -v     natural sort of (version) numbers within text

       -w, --width=COLS
              assume screen width instead of current value

       -x     list entries by lines instead of by columns

       -X     sort alphabetically by entry extension

       -Z, --context
              print any SELinux security context of each file

       -1     list one file per line

       --help display this help and exit

       --version
              output version information and exit

       SIZE is an integer and optional unit (example:  10M  is  10*1024*1024).
       Units  are K, M, G, T, P, E, Z, Y (powers of 1024) or KB, MB, ... (pow‐
       ers of 1000).

       Using color to distinguish file types is disabled both by  default  and
       with  --color=never.  With --color=auto, ls emits color codes only when
       standard output is connected to a terminal.  The LS_COLORS  environment
       variable can change the settings.  Use the dircolors command to set it.

   Exit status:
       0      if OK,

       1      if minor problems (e.g., cannot access subdirectory),

       2      if serious trouble (e.g., cannot access command-line argument).

AUTHOR
       Written by Richard M. Stallman and David MacKenzie.

REPORTING BUGS
       Report ls bugs to bug-coreutils@gnu.org
       GNU coreutils home page: <http://www.gnu.org/software/coreutils/>
       General help using GNU software: <http://www.gnu.org/gethelp/>
       Report ls translation bugs to <http://translationproject.org/team/>

COPYRIGHT
       Copyright  ©  2013  Free Software Foundation, Inc.  License GPLv3+: GNU
       GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
       This is free software: you are free  to  change  and  redistribute  it.
       There is NO WARRANTY, to the extent permitted by law.

SEE ALSO
       The  full  documentation  for ls is maintained as a Texinfo manual.  If
       the info and ls programs are properly installed at your site, the  com‐
       mand

              info coreutils 'ls invocation'

       should give you access to the complete manual.



GNU coreutils 8.21                March 2016                             LS(1)
""",
    'unicode': u'Ṳᾔḯ¢◎ⅾℯ',
}

_MAN_URL_OUTPUT = {
    'ls': """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
        "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <link rel="stylesheet" type="text/css" href="../../../style.css" title="style" />
    <link rel="stylesheet" type="text/css" href="../style.css" title="style" />
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />

    <title>ls(1) - Linux manual page</title>
</head>

<body>

<div class="page-top"><a id="top_of_page"></a></div>
<!--%%%TOP_BAR%%%-->
    <div class="nav-bar">
        <table class="nav-table">
            <tr>
                <td class="nav-cell">
                    <p class="nav-text">
                        <a href="../../../index.html">man7.org</a> &gt; Linux &gt; <a href="../index.html">man-pages</a>
                    </p>
                </td>
                <td class="training-cell">
                    <p class="training-text"><a class="training-link" href="http://man7.org/training/">Linux/UNIX system programming training</a></p>
                </td>
            </tr>
        </table>
    </div>

<hr class="nav-end" />

<!--%%%PAGE_START%%%-->


<table class="sec-table">
<tr>
    <td>
        <p class="section-dir">
<a href="#NAME">NAME</a> | <a href="#SYNOPSIS">SYNOPSIS</a> | <a href="#DESCRIPTION">DESCRIPTION</a> | <a href="#AUTHOR">AUTHOR</a> | <a href="#REPORTING_BUGS">REPORTING&nbsp;BUGS</a> | <a href="#COPYRIGHT">COPYRIGHT</a> | <a href="#SEE_ALSO">SEE&nbsp;ALSO</a> | <a href="#COLOPHON">COLOPHON</a>
        </p>
    </td>
    <td class="search-box">
        <div class="man-search-box">

            <form method="get" action="http://www.google.com/search">
                <fieldset class="man-search">
                    <input type="text" name="q" size="10" maxlength="255" value="" />
                    <input type="hidden" name="sitesearch" value="man7.org/linux/man-pages" />
                    <input type="submit" name="sa" value="Search online pages" />
                </fieldset>
            </form>

        </div>
    </td>
    <td> </td>
</tr>
</table>

<pre>
<span class="headline">LS(1)                           User Commands                          LS(1)</span>
</pre>
<h2><a id="NAME" href="#NAME"></a>NAME  &nbsp; &nbsp; &nbsp; &nbsp; <a href="#top_of_page"><span class="top-link">top</span></a></h2><pre>
       ls - list directory contents
</pre>
<h2><a id="SYNOPSIS" href="#SYNOPSIS"></a>SYNOPSIS  &nbsp; &nbsp; &nbsp; &nbsp; <a href="#top_of_page"><span class="top-link">top</span></a></h2><pre>
       <b>ls </b>[<i>OPTION</i>]... [<i>FILE</i>]...
</pre>
<h2><a id="DESCRIPTION" href="#DESCRIPTION"></a>DESCRIPTION  &nbsp; &nbsp; &nbsp; &nbsp; <a href="#top_of_page"><span class="top-link">top</span></a></h2><pre>
       List information about the FILEs (the current directory by default).
       Sort entries alphabetically if none of <b>-cftuvSUX </b>nor <b>--sort </b>is
       specified.

       Mandatory arguments to long options are mandatory for short options
       too.

       <b>-a</b>, <b>--all</b>
              do not ignore entries starting with .

       <b>-A</b>, <b>--almost-all</b>
              do not list implied . and ..

       <b>--author</b>
              with <b>-l</b>, print the author of each file

       <b>-b</b>, <b>--escape</b>
              print C-style escapes for nongraphic characters

       <b>--block-size</b>=<i>SIZE</i>
              scale sizes by SIZE before printing them; e.g.,
              '--block-size=M' prints sizes in units of 1,048,576 bytes; see
              SIZE format below

       <b>-B</b>, <b>--ignore-backups</b>
              do not list implied entries ending with ~

       <b>-c     </b>with <b>-lt</b>: sort by, and show, ctime (time of last modification
              of file status information); with <b>-l</b>: show ctime and sort by
              name; otherwise: sort by ctime, newest first

       <b>-C     </b>list entries by columns

       <b>--color</b>[=<i>WHEN</i>]
              colorize the output; WHEN can be 'always' (default if
              omitted), 'auto', or 'never'; more info below

       <b>-d</b>, <b>--directory</b>
              list directories themselves, not their contents

       <b>-D</b>, <b>--dired</b>
              generate output designed for Emacs' dired mode

       <b>-f     </b>do not sort, enable <b>-aU</b>, disable <b>-ls --color</b>

       <b>-F</b>, <b>--classify</b>
              append indicator (one of */=&gt;@|) to entries

       <b>--file-type</b>
              likewise, except do not append '*'

       <b>--format</b>=<i>WORD</i>
              across <b>-x</b>, commas <b>-m</b>, horizontal <b>-x</b>, long <b>-l</b>, single-column
              <b>-1</b>, verbose <b>-l</b>, vertical <b>-C</b>

       <b>--full-time</b>
              like <b>-l --time-style</b>=<i>full-iso</i>

       <b>-g     </b>like <b>-l</b>, but do not list owner

       <b>--group-directories-first</b>
              group directories before files;

              can be augmented with a <b>--sort </b>option, but any use of
              <b>--sort</b>=<i>none</i> (<b>-U</b>) disables grouping

       <b>-G</b>, <b>--no-group</b>
              in a long listing, don't print group names

       <b>-h</b>, <b>--human-readable</b>
              with <b>-l </b>and/or <b>-s</b>, print human readable sizes (e.g., 1K 234M
              2G)

       <b>--si   </b>likewise, but use powers of 1000 not 1024

       <b>-H</b>, <b>--dereference-command-line</b>
              follow symbolic links listed on the command line

       <b>--dereference-command-line-symlink-to-dir</b>
              follow each command line symbolic link

              that points to a directory

       <b>--hide</b>=<i>PATTERN</i>
              do not list implied entries matching shell PATTERN (overridden
              by <b>-a </b>or <b>-A</b>)

       <b>--hyperlink</b>[=<i>WHEN</i>]
              hyperlink file names; WHEN can be 'always' (default if
              omitted), 'auto', or 'never'

       <b>--indicator-style</b>=<i>WORD</i>
              append indicator with style WORD to entry names: none
              (default), slash (<b>-p</b>), file-type (<b>--file-type</b>), classify (<b>-F</b>)

       <b>-i</b>, <b>--inode</b>
              print the index number of each file

       <b>-I</b>, <b>--ignore</b>=<i>PATTERN</i>
              do not list implied entries matching shell PATTERN

       <b>-k</b>, <b>--kibibytes</b>
              default to 1024-byte blocks for disk usage

       <b>-l     </b>use a long listing format

       <b>-L</b>, <b>--dereference</b>
              when showing file information for a symbolic link, show
              information for the file the link references rather than for
              the link itself

       <b>-m     </b>fill width with a comma separated list of entries

       <b>-n</b>, <b>--numeric-uid-gid</b>
              like <b>-l</b>, but list numeric user and group IDs

       <b>-N</b>, <b>--literal</b>
              print entry names without quoting

       <b>-o     </b>like <b>-l</b>, but do not list group information

       <b>-p</b>, <b>--indicator-style</b>=<i>slash</i>
              append / indicator to directories

       <b>-q</b>, <b>--hide-control-chars</b>
              print ? instead of nongraphic characters

       <b>--show-control-chars</b>
              show nongraphic characters as-is (the default, unless program
              is 'ls' and output is a terminal)

       <b>-Q</b>, <b>--quote-name</b>
              enclose entry names in double quotes

       <b>--quoting-style</b>=<i>WORD</i>
              use quoting style WORD for entry names: literal, locale,
              shell, shell-always, shell-escape, shell-escape-always, c,
              escape

       <b>-r</b>, <b>--reverse</b>
              reverse order while sorting

       <b>-R</b>, <b>--recursive</b>
              list subdirectories recursively

       <b>-s</b>, <b>--size</b>
              print the allocated size of each file, in blocks

       <b>-S     </b>sort by file size, largest first

       <b>--sort</b>=<i>WORD</i>
              sort by WORD instead of name: none (<b>-U</b>), size (<b>-S</b>), time (<b>-t</b>),
              version (<b>-v</b>), extension (<b>-X</b>)

       <b>--time</b>=<i>WORD</i>
              with <b>-l</b>, show time as WORD instead of default modification
              time: atime or access or use (<b>-u</b>); ctime or status (<b>-c</b>); also
              use specified time as sort key if <b>--sort</b>=<i>time</i> (newest first)

       <b>--time-style</b>=<i>STYLE</i>
              with <b>-l</b>, show times using style STYLE: full-iso, long-iso,
              iso, locale, or +FORMAT; FORMAT is interpreted like in 'date';
              if FORMAT is FORMAT1&lt;newline&gt;FORMAT2, then FORMAT1 applies to
              non-recent files and FORMAT2 to recent files; if STYLE is
              prefixed with 'posix-', STYLE takes effect only outside the
              POSIX locale

       <b>-t     </b>sort by modification time, newest first

       <b>-T</b>, <b>--tabsize</b>=<i>COLS</i>
              assume tab stops at each COLS instead of 8

       <b>-u     </b>with <b>-lt</b>: sort by, and show, access time; with <b>-l</b>: show access
              time and sort by name; otherwise: sort by access time, newest
              first

       <b>-U     </b>do not sort; list entries in directory order

       <b>-v     </b>natural sort of (version) numbers within text

       <b>-w</b>, <b>--width</b>=<i>COLS</i>
              set output width to COLS.  0 means no limit

       <b>-x     </b>list entries by lines instead of by columns

       <b>-X     </b>sort alphabetically by entry extension

       <b>-Z</b>, <b>--context</b>
              print any security context of each file

       <b>-1     </b>list one file per line.  Avoid '\n' with <b>-q </b>or <b>-b</b>

       <b>--help </b>display this help and exit

       <b>--version</b>
              output version information and exit

       The SIZE argument is an integer and optional unit (example: 10K is
       10*1024).  Units are K,M,G,T,P,E,Z,Y (powers of 1024) or KB,MB,...
       (powers of 1000).

       Using color to distinguish file types is disabled both by default and
       with <b>--color</b>=<i>never</i>.  With <b>--color</b>=<i>auto</i>, ls emits color codes only
       when standard output is connected to a terminal.  The LS_COLORS
       environment variable can change the settings.  Use the dircolors
       command to set it.

   <b>Exit status:</b>
       0      if OK,

       1      if minor problems (e.g., cannot access subdirectory),

       2      if serious trouble (e.g., cannot access command-line
              argument).
</pre>
<h2><a id="AUTHOR" href="#AUTHOR"></a>AUTHOR  &nbsp; &nbsp; &nbsp; &nbsp; <a href="#top_of_page"><span class="top-link">top</span></a></h2><pre>
       Written by Richard M. Stallman and David MacKenzie.
</pre>
<h2><a id="REPORTING_BUGS" href="#REPORTING_BUGS"></a>REPORTING BUGS  &nbsp; &nbsp; &nbsp; &nbsp; <a href="#top_of_page"><span class="top-link">top</span></a></h2><pre>
       GNU coreutils online help: &lt;<a href="http://www.gnu.org/software/coreutils/">http://www.gnu.org/software/coreutils/</a>&gt;
       Report ls translation bugs to &lt;<a href="http://translationproject.org/team/">http://translationproject.org/team/</a>&gt;
</pre>
<h2><a id="COPYRIGHT" href="#COPYRIGHT"></a>COPYRIGHT  &nbsp; &nbsp; &nbsp; &nbsp; <a href="#top_of_page"><span class="top-link">top</span></a></h2><pre>
       Copyright © 2017 Free Software Foundation, Inc.  License GPLv3+: GNU
       GPL version 3 or later &lt;<a href="http://gnu.org/licenses/gpl.html">http://gnu.org/licenses/gpl.html</a>&gt;.
       This is free software: you are free to change and redistribute it.
       There is NO WARRANTY, to the extent permitted by law.
</pre>
<h2><a id="SEE_ALSO" href="#SEE_ALSO"></a>SEE ALSO  &nbsp; &nbsp; &nbsp; &nbsp; <a href="#top_of_page"><span class="top-link">top</span></a></h2><pre>
       Full documentation at: &lt;<a href="http://www.gnu.org/software/coreutils/ls">http://www.gnu.org/software/coreutils/ls</a>&gt;
       or available locally via: info '(coreutils) ls invocation'
</pre>
<h2><a id="COLOPHON" href="#COLOPHON"></a>COLOPHON  &nbsp; &nbsp; &nbsp; &nbsp; <a href="#top_of_page"><span class="top-link">top</span></a></h2><pre>
       This page is part of the <i>coreutils</i> (basic file, shell and text
       manipulation utilities) project.  Information about the project can
       be found at ⟨<a href="http://www.gnu.org/software/coreutils/">http://www.gnu.org/software/coreutils/</a>⟩.  If you have a
       bug report for this manual page, see
       ⟨<a href="http://www.gnu.org/software/coreutils/">http://www.gnu.org/software/coreutils/</a>⟩.  This page was obtained from
       the tarball coreutils-8.28.tar.xz fetched from
       ⟨<a href="http://www.gnutls.org/download.html">http://www.gnutls.org/download.html</a>⟩ on 2017-09-15.  If you discover
       any rendering problems in this HTML version of the page, or you
       believe there is a better or more up-to-date source for the page, or
       you have corrections or improvements to the information in this
       COLOPHON (which is <i>not</i> part of the original manual page), send a mail
       to man-pages@man7.org

<span class="footline">GNU coreutils 8.28             September 2017                          LS(1)</span>
</pre>

<hr class="end-man-text" />
<p>Pages that refer to this page:
    <a href="../man1/column.1.html">column(1)</a>,&nbsp;
    <a href="../man1/find.1.html">find(1)</a>,&nbsp;
    <a href="../man1/namei.1.html">namei(1)</a>,&nbsp;
    <a href="../man2/stat.2.html">stat(2)</a>,&nbsp;
    <a href="../man2/statx.2.html">statx(2)</a>,&nbsp;
    <a href="../man3/glob.3.html">glob(3)</a>,&nbsp;
    <a href="../man3/strverscmp.3.html">strverscmp(3)</a>,&nbsp;
    <a href="../man5/dir_colors.5.html">dir_colors(5)</a>,&nbsp;
    <a href="../man5/passwd.5.html">passwd(5)</a>,&nbsp;
    <a href="../man7/mq_overview.7.html">mq_overview(7)</a>,&nbsp;
    <a href="../man7/symlink.7.html">symlink(7)</a>,&nbsp;
    <a href="../man8/lsblk.8.html">lsblk(8)</a>,&nbsp;
    <a href="../man8/lsof.8.html">lsof(8)</a>,&nbsp;
    <a href="../man8/setfiles.8.html">setfiles(8)</a>
</p>
<hr/>


<hr class="start-footer" />

<div class="footer">

<table class="colophon-table">
    <tr>
    <td class="pub-info">
        <p>
            HTML rendering created 2017-09-15
            by <a href="http://man7.org/mtk/index.html">Michael Kerrisk</a>,
            author of
            <a href="http://man7.org/tlpi/"><em>The Linux Programming Interface</em></a>,
            maintainer of the
            <a href="https://www.kernel.org/doc/man-pages/">Linux <em>man-pages</em> project</a>.
        </p>
        <p>
            For details of in-depth
            <strong>Linux/UNIX system programming training courses</strong>
            that I teach, look <a href="http://man7.org/training/">here</a>.
        </p>
        <p>
            Hosting by <a href="http://www.jambit.com/index_en.html">jambit GmbH</a>.
        </p>
        <p>
            <a href="http://validator.w3.org/check?uri=referer">
            <img src="http://www.w3.org/Icons/valid-xhtml11"
                alt="Valid XHTML 1.1" height="31" width="88" />
            </a>
        </p>
    </td>
    <td class="colophon-divider">
    </td>
    <td class="tlpi-cover">
        <a href="http://man7.org/tlpi/"><img src="http://man7.org/tlpi/cover/TLPI-front-cover-vsmall.png" alt="Cover of TLPI" /></a>
    </td>
    </tr>
</table>

</div>

<hr class="end-footer" />



<!--BEGIN-SITETRACKING-->
<!-- SITETRACKING.man7.org_linux_man-pages -->

<!-- Start of StatCounter Code (xhtml) -->

<script type="text/javascript">
//<![CDATA[
var sc_project=7422636;
var sc_invisible=1;
var sc_security="9b6714ff";
//]]>
</script>
<script type="text/javascript"
src="http://www.statcounter.com/counter/counter_xhtml.js"></script>
<noscript><div class="statcounter"><a title="website
statistics" href="http://statcounter.com/"
class="statcounter"><img class="statcounter"
src="http://c.statcounter.com/7422636/0/9b6714ff/1/"
alt="website statistics" /></a></div></noscript>

<!-- End of StatCounter Code -->


<!-- Start of Google Analytics Code -->

<script type="text/javascript">

  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-9830363-8']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();

</script>

<!-- End of Google Analytics Code -->

<!--END-SITETRACKING-->

</body>
</html>
""",
}


class ManCommandCollectorTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.SetEncoding('utf-8')

  def testManCommandCollectorDecodeOutput(self):
    check_out_mock = self.StartObjectPatch(subprocess, 'check_output')
    check_out_mock.return_value = _MAN_COMMAND_OUTPUT['unicode'].encode('utf8')

    collector = generate_cli_trees._ManCommandCollector('unicode')
    self.assertEqual(_MAN_COMMAND_OUTPUT['unicode'],
                     collector._GetRawManPageText())


class ManPageCliGeneratorTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.SetEncoding('utf-8')

  def testManPageCliTreeGeneratorConfigDirNotInitialized(self):
    cli_tree_config_dir = cli_tree.CliTreeConfigDir()
    self.StartObjectPatch(
        files,
        'FindExecutableOnPath',
        side_effect=
        lambda command, allow_extensions=False: command == 'man')
    self.StartObjectPatch(
        generate_cli_trees._ManCommandCollector,
        '_GetRawManPageText',
        side_effect=lambda: _MAN_COMMAND_OUTPUT['ls'])
    generate_cli_trees.LoadOrGenerate('ls')
    ls_json = os.path.join(cli_tree_config_dir, 'ls.json')
    self.AssertFileIsGolden(ls_json, __file__, 'ls-man.json')

  def testManPageCliTreeGeneratorConfigDirNotInitializedMakeDirFails(self):
    self.StartObjectPatch(
        files,
        'MakeDir',
        side_effect=files.Error('oops'))
    self.StartObjectPatch(
        files,
        'FindExecutableOnPath',
        side_effect=
        lambda command, allow_extensions=False: command == 'man')
    self.StartObjectPatch(
        generate_cli_trees._ManCommandCollector,
        '_GetRawManPageText',
        side_effect=lambda: _MAN_COMMAND_OUTPUT['ls'])
    self.StartObjectPatch(
        generate_cli_trees,
        '_GetDirectories',
        return_value=[os.path.join(self.temp_path, '-_no-such-dir_-')])

    tree = generate_cli_trees.LoadOrGenerate('ls', warn_on_exceptions=True)
    self.assertIsNone(tree)
    self.AssertErrContains('WARNING')

    with self.assertRaises(files.Error):
      generate_cli_trees.LoadOrGenerate('ls')

  def testManPageCliTreeGenerator(self):
    cli_tree_config_dir = cli_tree.CliTreeConfigDir()
    os.makedirs(cli_tree_config_dir)
    self.StartObjectPatch(
        files,
        'FindExecutableOnPath',
        side_effect=
        lambda command, allow_extensions=False: command == 'man')
    self.StartObjectPatch(
        generate_cli_trees._ManCommandCollector,
        '_GetRawManPageText',
        side_effect=lambda: _MAN_COMMAND_OUTPUT['ls'])
    generate_cli_trees.LoadOrGenerate('ls')
    ls_json = os.path.join(cli_tree_config_dir, 'ls.json')
    self.AssertFileIsGolden(ls_json, __file__, 'ls-man.json')

  def testManPageCliTreeGeneratorNoManCommandNoUrl(self):
    self.StartObjectPatch(
        generate_cli_trees.ManPageCliTreeGenerator,
        '_GetManPageCollectorType',
        return_value=None)
    tree = generate_cli_trees.LoadOrGenerate('ls', verbose=True)
    self.assertIsNone(tree)
    self.AssertErrContains('Generating the [ls] CLI tree')

  def testManUrlCliTreeGenerator(self):
    cli_tree_config_dir = cli_tree.CliTreeConfigDir()
    os.makedirs(cli_tree_config_dir)
    self.StartObjectPatch(
        files,
        'FindExecutableOnPath',
        side_effect=lambda command, allow_extensions=False: command != 'man')
    mock_http = self.StartObjectPatch(http, 'HttpClient')
    mock_http.return_value.request.side_effect = _MockHttpResult
    generate_cli_trees.LoadOrGenerate('ls')
    ls_json = os.path.join(cli_tree_config_dir, 'ls.json')
    self.AssertFileIsGolden(ls_json, __file__, 'ls-url.json')

  def testManUrlCliTreeGeneratorNoUrl(self):
    self.StartObjectPatch(
        files,
        'FindExecutableOnPath',
        side_effect=lambda command, allow_extensions=False: command != 'man')
    mock_http = self.StartObjectPatch(http, 'HttpClient')
    mock_http.return_value.request.side_effect = _MockHttpResult
    tree = generate_cli_trees.LoadOrGenerate('no-such-command', verbose=True)
    self.assertIsNone(tree)
    self.AssertErrContains('Generating the [no-such-command] CLI tree')


class LoadOrGenerateTest(parameterized.TestCase,
                         calliope_test_base.CalliopeTestBase):

  @parameterized.parameters(
      'gsutil',
      'no-such-dir/gsutil',
      'no-such-executable no-such-dir/gsutil')
  @mock.patch.object(subprocess, 'Popen', side_effect=OSError('Error'))
  def testCommandInvocationFailure(self, command, popen_mock):
    tree = generate_cli_trees.LoadOrGenerate(command, verbose=True)
    self.assertIsNone(tree)
    self.AssertErrMatches(r'Command .+ could not be invoked:\nError')

  @mock.patch.object(subprocess, 'check_output', side_effect=OSError('Error'))
  @mock.patch.object(files, 'FindExecutableOnPath', return_value=True)
  def testMemoizeFailures(self, find_executable_mock, check_output_mock):
    try:
      # Enable and reset failure memoization.
      generate_cli_trees.CliTreeGenerator.MemoizeFailures(True)

      tree = generate_cli_trees.LoadOrGenerate('no-such-command', verbose=True)
      self.assertIsNone(tree)

      self.ClearErr()
      tree = generate_cli_trees.LoadOrGenerate('no-such-command', verbose=True)
      self.assertIsNone(tree)
      self.AssertErrContains(
          'Skipping CLI tree generation for [no-such-command] due to previous '
          'failure.')

    finally:
      # Disable and clear failure memoization.
      generate_cli_trees.CliTreeGenerator.MemoizeFailures(False)


class UpdateCliTreesTest(calliope_test_base.CalliopeTestBase):

  def _MockManPageRun(self, cmd):
    raise subprocess.CalledProcessError(16, ' '.join(cmd))

  def SetUp(self):
    self.StartObjectPatch(
        generate_cli_trees.BqCliTreeGenerator,
        'Run',
        side_effect=lambda cmd: _BQ_COMMAND_OUTPUT['.'.join(cmd)])
    self.StartObjectPatch(
        generate_cli_trees.GsutilCliTreeGenerator,
        'Run',
        side_effect=lambda cmd: _GSUTIL_COMMAND_OUTPUT['.'.join(cmd)])
    self.StartObjectPatch(
        generate_cli_trees.CliTreeGenerator,
        'Run',
        side_effect=lambda cmd: _KUBECTL_COMMAND_OUTPUT['.'.join(cmd)])
    self.StartObjectPatch(
        generate_cli_trees.ManPageCliTreeGenerator,
        'Run',
        side_effect=self._MockManPageRun)
    self.StartObjectPatch(
        files,
        'FindExecutableOnPath',
        side_effect=
        lambda command, allow_extensions=False: command == 'man')

  @mock.patch.object(subprocess, 'Popen')
  def testUpdateCliTrees(self, popen_mock):
    popen_mock.return_value.communicate.return_value = (None, None)
    # The first update should create the trees.
    generate_cli_trees.UpdateCliTrees(
        commands=list(generate_cli_trees.GENERATORS.keys()),
        directory=self.temp_path,
        verbose=True)
    self.AssertErrContains('Generating the [bq] CLI tree')
    self.AssertErrContains('Generating the [gsutil] CLI tree')
    self.AssertErrContains('Generating the [kubectl] CLI tree')

    # The second update should accept the already generated trees.
    self.ClearErr()
    generate_cli_trees.UpdateCliTrees(
        commands=list(generate_cli_trees.GENERATORS.keys()),
        directory=self.temp_path,
        verbose=True)
    self.AssertErrContains("""\
[bq] CLI tree version [2.0.27] is up to date.
[gsutil] CLI tree version [4.27] is up to date.
[kubectl] CLI tree version [v1.7.6] is up to date.
""")

  def testUpdateCliTreesUnknownCommand(self):
    with self.AssertRaisesExceptionMatches(
        generate_cli_trees.CliTreeGenerationError,
        'CLI tree generation failed for [bar, foo].'):
      generate_cli_trees.UpdateCliTrees(
          commands=['bar', 'foo'],
          directory=self.temp_path)


class LoadAllTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.StartObjectPatch(cli_tree, '_IsRunningUnderTest', return_value=True)
    self.WalkTestCli('sdk4')

  def testLoadAll(self):
    cli_tree_dir = os.path.join(self.temp_path, 'cli_tree_dir')
    os.makedirs(cli_tree_dir)
    self.StartObjectPatch(cli_tree, 'CliTreeDir', return_value=cli_tree_dir)
    cli_tree_config_dir = os.path.join(self.temp_path, 'cli_tree_config_dir')
    os.makedirs(cli_tree_config_dir)
    self.StartObjectPatch(cli_tree, 'CliTreeConfigDir',
                          return_value=cli_tree_config_dir)
    self.StartObjectPatch(
        files,
        'FindExecutableOnPath',
        side_effect=
        lambda command, allow_extensions=False: command in ('man', 'cat'))

    cat_tree = cli_tree.Node(command='cat')
    cat_tree[cli_tree.LOOKUP_VERSION] = cli_tree.VERSION
    cat_tree[cli_tree.LOOKUP_CLI_VERSION] = (
        generate_cli_trees.ManPageCliTreeGenerator('cat').GetVersion())
    cat_tree_path = os.path.join(cli_tree_config_dir, 'cat.json')
    with open(cat_tree_path, 'w') as f:
      json.dump(cat_tree, f)

    # Load all CLI trees into one tree. 'gcloud' is not pre-populated in this
    # test, 'cat' is from CliTreeConfigDir.
    tree = generate_cli_trees.LoadAll()
    self.assertEqual(['cat'], list(tree[cli_tree.LOOKUP_COMMANDS].keys()))


@test_case.Filters.RunOnlyIf(test_case.Filters.IsInDeb() or
                             test_case.Filters.IsInRpm(),
                             'DEB and RPM CLI tree packaging.')
class InstalledCliTreesTest(calliope_test_base.CalliopeTestBase):
  """Checks that the CLI tree have some commands."""

  _AT_LEAST = 16  # sanity value so we don't fail every time a command is added

  def _VerifyCliTreeInstalled(self, command):
    tree = generate_cli_trees.LoadOrGenerate(command, generate=False)
    self.assertIsNotNone(tree)
    self.assertGreater(len(tree[cli_tree.LOOKUP_COMMANDS]), self._AT_LEAST)

  def testBqCliTreeInstalled(self):
    self._VerifyCliTreeInstalled('bq')

  def testGcloudCliTreeInstalled(self):
    self._VerifyCliTreeInstalled('gcloud')

  def testGsutilCliTreeInstalled(self):
    self._VerifyCliTreeInstalled('gsutil')

  def testKubectlCliTreeInstalled(self):
    expected = [
        ('bq', 'data/cli/bq.json', True),
        ('gcloud', 'data/cli/gcloud.json', True),
        ('gcloud_completions', 'data/cli/gcloud_completions.py', False),
        ('gcloud_completions', 'data/cli/gcloud_completions.pyc', False),
        ('gsutil', 'data/cli/gsutil.json', True),
        ('kubectl', 'data/cli/kubectl.json', False),
    ]

    def _Chop(path):
      return re.sub('.*/google-cloud-sdk/', '', path)

    actual = [(p.command, _Chop(p.path), p.command_installed)
              for p in list_cli_trees.ListAll()]
    self.assertEqual(expected, actual)


if __name__ == '__main__':
  calliope_test_base.main()
