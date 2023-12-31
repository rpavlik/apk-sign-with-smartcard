# Copyright 2023, Collabora, Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# Original author: Rylie Pavlik <rylie.pavlik@collabora.com>
"""Helpers for doing Android signing stuff with smartcards over PKCS#11."""

from pathlib import Path
import getpass

_PKCS_CFG = Path(__file__).parent.resolve() / "pkcs11_java_opensc.cfg"

_PASS_ENV_VAR = "PKCS11_PIN"

BUILD_TOOLS_VERSION = "33.0.1"


def get_apksigner_path(build_tools_version=BUILD_TOOLS_VERSION):
    """Return the default installation path of apksigner on Linux."""
    return (
        Path("~").expanduser()
        / "Android"
        / "Sdk"
        / "build-tools"
        / build_tools_version
        / "apksigner"
    )


def get_pin_environment_dict() -> dict[str, str]:
    """Get a dictionary for the env parameter of subprocess to safely pass the PIN."""
    pin = getpass.getpass("Passphrase/PIN:")
    return {_PASS_ENV_VAR: pin}


def get_apksigner_sign_args_start(apksigner, min_sdk=24, max_sdk=33):
    """Get initial args for an apksigner sign call using PKCS#11."""
    # Make sure Java can find our pkcs11 module
    library_path = ";".join(
        ("/usr/lib/x86_64-linux-gnu/pkcs11", "/usr/lib/x86_64-linux-gnu")
    )
    return [
        apksigner,
        # see https://issuetracker.google.com/issues/277298127
        # for why we have this add-opens thing
        f"-JDjava.library.path={library_path}",
        "-J-add-opens=jdk.crypto.cryptoki/sun.security.pkcs11=ALL-UNNAMED ",
        # back to normal arguments again
        "sign",
        "--min-sdk-version",
        str(min_sdk),
        "--max-sdk-version",
        str(max_sdk),
        "--provider-class",
        "sun.security.pkcs11.SunPKCS11",
        "--provider-arg",
        str(_PKCS_CFG),
    ]


def get_apksigner_per_signer_args(key_alias=None):
    """
    Get arguments to add to an apksigner call to use a key from pkcs11.

    Note that you also have to pass an environment dict with the pin
    when actually invoking the command!
    """
    # could be called multiple times to add multiple signers, etc.
    args = [
        "--ks",
        "NONE",
        "--ks-type",
        "PKCS11",
        "--ks-pass",
        f"env:{_PASS_ENV_VAR}",
    ]
    if key_alias:
        args.extend(("--ks-key-alias", key_alias))
    return args


def get_apksigner_sign_args_end(
    unsigned_apk: Path,
    out_apk: Path,
):
    """Get final args for an apksigner sign call."""
    return [
        "--out",
        str(out_apk),
        str(unsigned_apk),
    ]
