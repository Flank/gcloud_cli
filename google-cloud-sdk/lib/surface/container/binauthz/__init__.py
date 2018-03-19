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
"""The base surface for Binary Authorization signatures."""

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Binauthz(base.Group):
  r"""Manage attestations for Binary Authorization on Google Cloud Platform.

    Binary Authorization is a feature which allows binaries to run on Google
    Cloud Platform only if they are appropriately attested.  Binary
    Authorization is configured by creating a policy.

    ## EXAMPLES

    This example assumes that you have created a keypair using gpg, usually
    by running `gpg --gen-key ...`, with `Name-Email` set to
    `attesting_user@example.com` for your attesting authority.

    First, some convenience variables for brevity:

    ```sh
    ATTESTING_USER="attesting_user@example.com"
    DIGEST="000000000000000000000000000000000000000000000000000000000000abcd"
    ARTIFACT_URL="gcr.io/example-project/example-image@sha256:${DIGEST}"
    ```

    Export your keypair's public key:

        ```sh
        gpg \
            --armor \
            --export "${ATTESTING_USER}" \
            --output build_key1.pgp
        ```

    Or if you're creating v2 kind=ATTESTATION_AUTHORITY attestations,
    export your key's fingerprint (note this may differ based on version and
    implementations of gpg):

        ```sh
        gpg \
            --with-colons \
            --with-fingerprint \
            --force-v4-certs \
            --list-keys \
            "${ATTESTING_USER}" | grep fpr | cut --delimiter=':' --fields 10
        ```

    This should produce a 40 character, hexidecimal encoded string.  See
    https://tools.ietf.org/html/rfc4880#section-12.2 for more information on
    key fingerprints.

    Create your attestation payload:

        ```sh
        {command} create-signature-payload \
            --artifact-url="${ARTIFACT_URL}" \
          > example_payload.txt
        ```

    Create a signature from your attestation payload:

        ```sh
        gpg \
          --local-user "${ATTESTING_USER}" \
          --armor \
          --clearsign \
          --output example_signature.pgp \
          example_payload.txt
        ```

    Upload the attestation to Container Analysis:

        ```sh
        {command} attestations create \
          --public-key-file=build_key1.pgp \
          --signature-file=example_signature.pgp \
          --artifact-url="${ARTIFACT_URL}"
        ```

    Or if you're creating v2 kind=ATTESTATION_AUTHORITY attestations:

        ```sh
        {command} attestations create \
          --pgp-key-fingerprint=${KEY_FINGERPRINT} \
          --signature-file=example_signature.pgp \
          --artifact-url="${ARTIFACT_URL}" \
          --attestation-authority-note=providers/example-prj/notes/note-id
        ```

    List the attestation by artifact URL.  `--format` can be passed to
    output the attestations as json or another supported format:

        ```sh
        {command} attestations list \
          --artifact-url="${ARTIFACT_URL}" \
          --format=yaml

          ---
          - |
            -----BEGIN PGP PUBLIC KEY BLOCK-----
            Version: GnuPG v1
            ... SNIP ...
            -----END PGP PUBLIC KEY BLOCK-----
          - |
            -----BEGIN PGP SIGNED MESSAGE-----
            Hash: SHA1
            ... SNIP ...
            -----BEGIN PGP SIGNATURE-----
            Version: GnuPG v1
            ... SNIP ...
            -----END PGP SIGNATURE-----
        ```

    List all artifact URLs on the project for which Container Analysis
    Occurrences exist.  This list includes the list of all URLs with BinAuthz
    attestations:

        ```sh
        {command} attestations list

          ---
          https://gcr.io/example-project/example-image@sha256:000000000000000000000000000000000000000000000000000000000000abcd
          ...
        ```

    Listing also works for kind=ATTESTATION_AUTHORITY attestations, just pass
    the attestation authority note:

        ```sh
        {command} attestations list \
          --artifact-url="${ARTIFACT_URL}" \
          --attestation-authority-note=providers/exmple-prj/notes/note-id \
          --format=yaml

          ...
        ```
  """
