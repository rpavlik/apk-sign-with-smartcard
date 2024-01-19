#!/usr/bin/env python3
# Copyright 2023-2024, Collabora, Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# Original author: Rylie Pavlik <rylie.pavlik@collabora.com>
"""Sign a CTS APK using keys on a smartcard (RSA 4096)."""

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
APK_KEY_ALIAS = "cts_s1"


def _sign_apk(apksigner, apk_dir: Path, ver: str, ver_code: str, env: dict[str, str]):
    unsigned_path = apk_dir / "conformance-release-unsigned.apk"
    out_path = apk_dir / f"OpenXR-CTS-{ver}-versionCode-{ver_code}-signed.apk"
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


def _sign(extract_root: str):
    extract_dir = Path(extract_root).expanduser()
    env = get_pin_environment_dict()
    apksigner = get_apksigner_path()

    # Getting the version from the metadata that the CI uploads
    with open(extract_dir / "output-metadata.json", "r", encoding="utf-8") as fp:
        metadata = json.load(fp)

    data = metadata["elements"][0]

    _sign_apk(
        apksigner,
        extract_dir,
        ver=data["versionName"],
        ver_code=data["versionCode"],
        env=env,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("extract_root")
    args = parser.parse_args()

    _sign(args.extract_root)
