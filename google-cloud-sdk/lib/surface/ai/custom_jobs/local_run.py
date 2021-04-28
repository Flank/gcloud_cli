# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to run a training application locally."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.ai import local_util
from googlecloudsdk.command_lib.ai.custom_jobs import flags
from googlecloudsdk.command_lib.ai.docker import build as docker_builder
from googlecloudsdk.command_lib.ai.docker import run as docker_runner
from googlecloudsdk.command_lib.ai.docker import utils as docker_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


def _ValidateArgs(args, workdir, script):
  """Validates arguments specified via flags."""

  # Validate main script's existence:
  script_path = os.path.normpath(os.path.join(workdir, script))
  if not os.path.exists(script_path) or not os.path.isfile(script_path):
    raise errors.ArgumentError(
        r"File '{}' is not found under the working directory: '{}'.".format(
            script, workdir))

  # Validate extra custom packages specified:
  for package in (args.extra_packages or []):
    package_path = os.path.normpath(os.path.join(workdir, package))
    if not os.path.exists(package_path) or not os.path.isfile(package_path):
      raise errors.ArgumentError(
          r"Package file '{}' is not found under the working directory: '{}'."
          .format(package, workdir))

  # Validate extra directorys specified:
  for directory in (args.extra_dirs or []):
    dir_path = os.path.normpath(os.path.join(workdir, directory))
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
      raise errors.ArgumentError(
          r"Directory '{}' is not found under the working directory: '{}'."
          .format(directory, workdir))

  # Validate output image uri is in valid format
  if args.output_image_uri:
    output_image = args.output_image_uri
    try:
      docker_utils.ValidateRepositoryAndTag(output_image)
    except ValueError as e:
      raise errors.ArgumentError(
          r'"{}" is not a valid container image uri: {}'.format(
              output_image, e))


# TODO(b/176214485): Keep this hidden until public preview
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Run a custom training locally.

  Packages your training code into a Docker image and executes it locally.
  """
  detailed_help = {
      'DESCRIPTION':
          textwrap.dedent("""\
          {description}

          You should execute this command in the top folder which includes all
          the code and resources you want to pack and run, or specify the
          'work-dir' flag to point to it. Any other path you specified via flags
          should be a relative path to the work-dir and under it; otherwise it
          will be unaccessible.

          Supposing your directories are like the following structures:

            /root
              - my_project
                  - my_training
                      - task.py
                      - util.py
                      - setup.py
                  - other_modules
                      - some_module.py
                  - dataset
                      - small.dat
                      - large.dat
                  - config
                  - dep
                      - foo.tar.gz
                  - bar.whl
                  - requirements.txt
              - another_project
                  - something

          If you set 'my_project' as the working directory, then you should
          execute the task.py by specifying "--script=my_training/task.py" or
          "--python-module=my_training.task", the 'requirements.txt' will be
          processed. And you will also be able to install extra packages by,
          e.g. specifying "--extra-packages=dep/foo.tar.gz,bar.whl" or include
          extra directories, e.g. specifying "--extra-dirs=dataset,config".

          If you set 'my_training' as the working directory, then you should
          execute the task.py by specifying "--script=task.py" or
          "--python-module=task", the 'setup.py' will be processed. However, you
          won't be able to access any other files or directories that are not in
          'my_training' folder.

          See more details in the HELP info of the corresponding flags.
          """),
      'EXAMPLES':
          """\
          To execute an python module with required dependencies, run:

            $ {command} --python-module=my_training.task --base-image=gcr.io/my/image --requirements=pandas,scipy>=1.3.0

          To execute a python script using local GPU, run:

            $ {command} --script=my_training/task.py --base-image=gcr.io/my/image --gpu

          To execute an arbitrary script with custom arguments, run:

            $ {command} --script=my_run.sh --base-image=gcr.io/my/image -- --my-arg bar --enable_foo
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddLocalRunCustomJobFlags(parser)

  def Run(self, args):
    working_dir = args.work_dir or files.GetCWD()
    working_dir = os.path.abspath(files.ExpandHomeDir(working_dir))

    script = args.script or local_util.ModuleToPath(args.python_module)

    _ValidateArgs(args, working_dir, script)

    output_image_name = args.output_image_uri or docker_utils.GenerateImageName(
        base_name=script)

    with files.ChDir(working_dir):
      log.status.Print('Working directory is set to {}.'.format(working_dir))
      # TODO(b/176214485): Consider including the image id in the build result.
      built_image = docker_builder.BuildImage(
          base_image=args.base_image,
          host_workdir=working_dir,
          main_script=script,
          python_module=args.python_module,
          requirements=args.requirements,
          extra_packages=args.extra_packages,
          extra_dirs=args.extra_dirs,
          output_image_name=output_image_name)

      log.status.Print('A training image is ready. Starting to run ...')
      docker_runner.RunContainer(
          image=built_image, enable_gpu=args.gpu, user_args=args.args)

      log.out.Print(
          'A local run is finished successfully and build image: {}.'.format(
              built_image.name))

      # Clean generated cache
      script_dir, _ = os.path.split(script) or working_dir
      if local_util.ClearPyCache(script_dir):
        log.status.Print(
            'Cleaned Python cache from directory: {}'.format(script_dir))
