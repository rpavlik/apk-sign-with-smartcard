#!/usr/bin/env python3
# Copyright 2023, Collabora, Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# Original author: Rylie Pavlik <rylie.pavlik@collabora.com>
"""Sign a broker APK/AAB using the new keys (RSA 4096, issued by our trust root)."""

import argparse
from pathlib import Path
import subprocess

from apk_pkcs11_tools import (
    get_apksigner_path,
    get_apksigner_sign_args_end,
    get_apksigner_sign_args_start,
    get_pin_environment_dict,
    get_apksigner_per_signer_args,
)

# when importing into the smartcard, these are the key "label"
APK_KEY_ALIAS = "signer_s1"
# UPLOAD_KEY_ALIAS = "upload_u1"
# TODO change this once the upload key is fixed
# UPLOAD_KEY_ALIAS = "old_upload"
UPLOAD_KEY_ALIAS = "signer_s2"


def _sign_apk(apksigner, apk_release_dir: Path, env: dict[str, str]):
    unsigned_path = (
        apk_release_dir / "installable_runtime_broker-official-release-unsigned.apk"
    )
    out_path = (
        apk_release_dir / "installable_runtime_broker-official-release-signed.apk"
    )
    assert unsigned_path.exists()

    cmd = get_apksigner_sign_args_start(apksigner)
    cmd.extend(get_apksigner_per_signer_args(APK_KEY_ALIAS))
    cmd.extend(get_apksigner_sign_args_end(unsigned_path, out_path))

    print(f"\nUsing {apksigner}...")
    print(f"\nSigning {unsigned_path} to create {out_path}...")
    subprocess.check_call(cmd, env=env)

    print(f"\nVerifying {out_path}...")
    subprocess.check_call(
        [str(apksigner), "verify", "--verbose", "--print-certs", str(out_path)]
    )


def _sign_bundle(apksigner, bundle_release_dir: Path, env: dict[str, str]):
    unsigned_path = (
        bundle_release_dir / "installable_runtime_broker-official-release.aab"
    )
    out_path = (
        bundle_release_dir / "installable_runtime_broker-official-release-signed.aab"
    )
    assert unsigned_path.exists()

    cmd = get_apksigner_sign_args_start(apksigner)
    cmd.extend(get_apksigner_per_signer_args(UPLOAD_KEY_ALIAS))
    cmd.extend(get_apksigner_sign_args_end(unsigned_path, out_path))

    print(f"\nUsing {apksigner}...")
    print(f"\nSigning {unsigned_path} to create {out_path}...")
    subprocess.check_call(cmd, env=env)

    # cannot verify a bundle


def _sign(repo_root: str):
    outputs_dir = (
        Path(repo_root).expanduser()
        / "installable_runtime_broker"
        / "build"
        / "outputs"
    )
    env = get_pin_environment_dict()
    apksigner = get_apksigner_path()

    # needs ./gradlew installable_runtime_broker:assembleOfficialRelease
    apk_release_dir = outputs_dir / "apk" / "official" / "release"
    _sign_apk(apksigner, apk_release_dir, env)

    # needs ./gradlew installable_runtime_broker:bundleOfficialRelease -Ptrademark
    bundle_release_dir = outputs_dir / "bundle" / "officialRelease"
    _sign_bundle(apksigner, bundle_release_dir, env)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root")
    args = parser.parse_args()

    _sign(args.repo_root)
