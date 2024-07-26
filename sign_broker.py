#!/usr/bin/env python3
# Copyright 2023-2024, Collabora, Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# Original author: Rylie Pavlik <rylie.pavlik@collabora.com>
"""Sign a broker APK/AAB using the new keys (RSA 4096, issued by our trust root)."""

import argparse
from pathlib import Path
import subprocess
import json

from apk_pkcs11_tools import (
    get_apksigner_path,
    get_apksigner_sign_args_end,
    get_apksigner_sign_args_start,
    get_pin_environment_dict,
    get_apksigner_per_signer_args,
)

# when importing into the smartcard, these are the key "label"

# Key for APK
APK_KEY_ALIAS = "signer_s1"

# Key for AAB (Bundle upload key)
UPLOAD_KEY_ALIAS = "upload_u1"


def _sign_apk(apksigner, apk_dir: Path, ver: str, ver_code: str, env: dict[str, str]):
    unsigned_path = apk_dir / "installable_runtime_broker-official-release-unsigned.apk"
    out_path = (
        apk_dir
        / f"OpenXR-Android-Broker-official-release-signed-{ver}-versionCode-{ver_code}.apk"
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


def _sign_bundle(
    apksigner, bundle_dir: Path, ver: str, ver_code: str, env: dict[str, str]
):
    unsigned_path = bundle_dir / "installable_runtime_broker-official-release.aab"
    out_path = (
        bundle_dir / "OpenXR-Android-Broker-official-release-signed"
        f"-{ver}-versionCode-{ver_code}.aab"
    )
    assert unsigned_path.exists()

    cmd = get_apksigner_sign_args_start(apksigner)
    cmd.extend(get_apksigner_per_signer_args(UPLOAD_KEY_ALIAS))
    cmd.extend(get_apksigner_sign_args_end(unsigned_path, out_path))

    print(f"\nUsing {apksigner}...")
    print(f"\nSigning {unsigned_path} to create {out_path}...")
    subprocess.check_call(cmd, env=env)


def _sign(extract_root: str):
    extract_dir = (
        Path(extract_root).expanduser()
        / "installable_runtime_broker"
        / "build"
        / "outputs"
    )
    env = get_pin_environment_dict()
    apksigner = get_apksigner_path()

    # Getting the version from the metadata that the CI uploads
    with open(
        extract_dir / "apk" / "official" / "release" / "output-metadata.json",
        "r",
        encoding="utf-8",
    ) as fp:
        metadata = json.load(fp)

    data = metadata["elements"][0]

    # needs ./gradlew installable_runtime_broker:assembleOfficialRelease
    apk_release_dir = extract_dir / "apk" / "official" / "release"
    _sign_apk(
        apksigner,
        apk_release_dir,
        ver=data["versionName"],
        ver_code=data["versionCode"],
        env=env,
    )

    # needs ./gradlew installable_runtime_broker:bundleOfficialRelease -Ptrademark
    bundle_release_dir = extract_dir / "bundle" / "officialRelease"
    _sign_bundle(
        apksigner,
        bundle_release_dir,
        ver=data["versionName"],
        ver_code=data["versionCode"],
        env=env,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("extract_root")
    args = parser.parse_args()

    _sign(args.extract_root)
