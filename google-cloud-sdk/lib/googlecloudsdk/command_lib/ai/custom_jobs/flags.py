# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Flags definition specifically for gcloud aiplatform custom-jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import flags as shared_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers

_DISPLAY_NAME = base.Argument(
    '--display-name',
    required=True,
    help=('Display name of the custom job to create.'))
_PYTHON_PACKAGE_URIS = base.Argument(
    '--python-package-uris',
    metavar='PYTHON_PACKAGE_URIS',
    type=arg_parsers.ArgList(),
    help='The common python package uris that will be used by python image. '
    'e.g. --python-package-uri=path1,path2'
    'If customizing the python package is needed, please use config instead.')

_CUSTOM_JOB_CONFIG = base.Argument(
    '--config',
    help=textwrap.dedent("""\
      Path to the job configuration file. This file should be a YAML document containing a CustomJobSpec.
      If an option is specified both in the configuration file **and** via command line arguments, the command line arguments
      override the configuration file. Note that keys with underscore are invalid.

      Example(YAML):

        workerPoolSpecs:
          machineSpec:
            machineType: n1-highmem-2
          replicaCount: 1
          containerSpec:
            imageUri: gcr.io/ucaip-test/ucaip-training-test
            args:
            - port=8500
            command:
            - start"""))

_WORKER_POOL_SPEC = base.Argument(
    '--worker-pool-spec',
    action='append',
    type=arg_parsers.ArgDict(
        # TODO(b/184350069): check `machine－type` specified for non-empty spec.
        spec={
            'replica-count': int,
            'machine-type': str,
            'container-image-uri': str,
            'executor-image-uri': str,
            # TODO(b/185461224): remove `python-image-uri` after the public docs
            # and demos are updated and before the promotion to GA.
            'python-image-uri': str,
            'python-module': str,
        }),
    metavar='WORKER_POOL_SPEC',
    help=textwrap.dedent("""\
      Define the worker pool configuration used by the custom job. You can
      specify multiple worker pool specs in order to create a custom job with
      multiple worker pools.

      The spec can contain the following fields, which are listed with
      corresponding fields in the WorkerPoolSpec API message:

      *machine-type*::: (Required): machineSpec.machineType
      *replica-count*::: replicaCount
      *container-image-uri*::: containerSpec.imageUri
      *executor-image-uri*::: pythonPackageSpec.executorImageUri
      *python-image-uri*::: (DEPRECATED) use `executor-image-uri` instead.
      *python-module*::: pythonPackageSpec.pythonModule

      For example:
      `--worker-pool-spec=replica-count=1,machine-type=n1-highmem-2,container-image-uri=gcr.io/ucaip-test/ucaip-training-test`
      """))

_CUSTOM_JOB_COMMAND = base.Argument(
    '--command',
    type=arg_parsers.ArgList(),
    metavar='COMMAND',
    action=arg_parsers.UpdateAction,
    help="""\
    Command to be invoked when containers are started.
    It overrides the entrypoint instruction in Dockerfile when provided.
    """)
_CUSTOM_JOB_ARGS = base.Argument(
    '--args',
    metavar='ARG',
    type=arg_parsers.ArgList(),
    action=arg_parsers.UpdateAction,
    help='Comma-separated arguments passed to containers or python tasks.')


def AddCreateCustomJobFlags(parser):
  """Adds flags related to create a custom job."""
  shared_flags.AddRegionResourceArg(parser, 'to create a custom job')
  shared_flags.TRAINING_SERVICE_ACCOUNT.AddToParser(parser)
  shared_flags.NETWORK.AddToParser(parser)
  shared_flags.AddKmsKeyResourceArg(parser, 'custom job')

  _DISPLAY_NAME.AddToParser(parser)
  _PYTHON_PACKAGE_URIS.AddToParser(parser)
  _CUSTOM_JOB_ARGS.AddToParser(parser)
  _CUSTOM_JOB_COMMAND.AddToParser(parser)
  worker_pool_spec_group = base.ArgumentGroup(
      help='Worker pool specification.', required=True)
  worker_pool_spec_group.AddArgument(_CUSTOM_JOB_CONFIG)
  worker_pool_spec_group.AddArgument(_WORKER_POOL_SPEC)
  worker_pool_spec_group.AddToParser(parser)


def _GetCustomJobResourceSpec(resource_name='custom_job'):
  return concepts.ResourceSpec(
      constants.CUSTOM_JOB_COLLECTION,
      resource_name=resource_name,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=shared_flags.RegionAttributeConfig(),
      disable_auto_completers=False)


def AddCustomJobResourceArg(parser, verb):
  """Add a resource argument for a Vertex AI custom job.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'custom_job',
      _GetCustomJobResourceSpec(),
      'The custom job {}.'.format(verb),
      required=True).AddToParser(parser)


def AddLocalRunCustomJobFlags(parser):
  """Add local-run related flags to the parser."""

  # Flags for entry point of the training application
  application_group = parser.add_mutually_exclusive_group(required=True)
  application_group.add_argument(
      '--python-module',
      metavar='PYTHON_MODULE',
      help=textwrap.dedent("""
      Name of the python module to execute, in 'trainer.train' or 'train'
      format. Its path should be relative to the `work_dir`.
      """))
  application_group.add_argument(
      '--script',
      metavar='SCRIPT',
      help=textwrap.dedent("""
      The relative path of the file to execute. Accepets a Python file,
      IPYNB file, or arbitrary bash script. This path should be relative to the
      `work_dir`.
      """))

  # Flags for working directory.
  parser.add_argument(
      '--work-dir',
      metavar='WORK_DIR',
      help=textwrap.dedent("""
      Path of the working directory where the python-module or script exists.
      If not specified, it use the directory where you run the this command.

      Only the contents of this directory will be accessible to the built
      container image.
      """))

  # Flags for extra directory
  parser.add_argument(
      '--extra-dirs',
      metavar='EXTRA_DIR',
      type=arg_parsers.ArgList(),
      help=textwrap.dedent("""
      Extra directories under the working directory to include, besides the one
      that contains the main executable.

      By default, only the parent directory of the main script or python module
      is copied to the container.
      For example, if the module is "training.task" or the script is
      "training/task.py", the whole "training" directory, including its
      sub-directories, will always be copied to the container. You may specify
      this flag to also copy other directories if necessary.

      Note: if no parent is specified in 'python_module' or 'scirpt', the whole
      working directory is copied, then you don't need to specify this flag.
      """))

  # Flags for base container image
  parser.add_argument(
      '--base-image',
      metavar='BASE_IMAGE',
      required=True,
      help=textwrap.dedent("""
      URI or ID of the container image in either the Container Registry or local
      that will run the application.
      See https://cloud.google.com/ai-platform-unified/docs/training/pre-built-containers
      for available pre-built container images provided by Vertex AI for training.
      """))

  # Flags for extra requirements.
  parser.add_argument(
      '--requirements',
      metavar='REQUIREMENTS',
      type=arg_parsers.ArgList(),
      help=textwrap.dedent("""
      Python dependencies from PyPI to be used when running the application.
      If this is not specified, and there is no "setup.py" or "requirements.txt"
      in the working directory, your application will only have access to what
      exists in the base image with on other dependencies.

      Example:
      'tensorflow-cpu, pandas==1.2.0, matplotlib>=3.0.2'
      """))

  # Flags for extra dependency .
  parser.add_argument(
      '--extra-packages',
      metavar='PACKAGE',
      type=arg_parsers.ArgList(),
      help=textwrap.dedent("""
      Local paths to Python archives used as training dependencies in the image
      container.
      These can be absolute or relative paths. However, they have to be under
      the work_dir; Otherwise, this tool will not be able to acces it.

      Example:
      'dep1.tar.gz, ./downloads/dep2.whl'
      """))

  # Flags for the output image
  parser.add_argument(
      '--output-image-uri',
      metavar='OUTPUT_IMAGE',
      help=textwrap.dedent("""
      Uri of the custom container image to be built with the your application
      packed in.
      """))

  # Flaga for GPU support
  parser.add_argument(
      '--gpu', action='store_true', default=False, help='Enable to use GPU.')

  # Flags for docker run
  parser.add_argument(
      '--docker-run-options',
      metavar='DOCKER_RUN_OPTIONS',
      type=arg_parsers.ArgList(),
      help=textwrap.dedent("""
      Custom Docker run options to pass to image during execution.
      For example, '--no-healthcheck, -a stdin'.

      See https://docs.docker.com/engine/reference/commandline/run/#options for
      more details.
      """))

  # User custom flags.
  parser.add_argument(
      'args',
      nargs=argparse.REMAINDER,
      default=[],
      help="""Additional user arguments to be forwarded to your application.""",
      example=('$ {command} --script=my_run.sh --base-image=gcr.io/my/image '
               '-- --my-arg bar --enable_foo'))
