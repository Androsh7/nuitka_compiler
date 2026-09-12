"""Builds docker images"""

# Standard libraries
import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Project libraries
from config import (
    ARCHITECTURES,
    LIBC_TO_DOCKERFILE,
    NAMESPACE,
    OPENSSL_VERSION,
    DEFAULT_PARALLELISM,
    PARENT_DIRECTORY,
    PYTHON_VERSIONS,
    SOURCE_URL,
)

# Constants
with open(PARENT_DIRECTORY / "VERSION.txt", "r", encoding="utf-8") as version_file:
    VERSION = version_file.read().strip()
COMMIT_HASH = (
    subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True)
    .stdout.decode()
    .strip()
)
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S+00:00"


@dataclass(frozen=True)
class ImageSpec:
    tag: str
    dockerfile: Path
    architecture: str | None = None
    build_args: dict[str, str] | None = None


def parse_build_date(build_date: str) -> datetime:
    """The date to stamp built images with, read from its compact form

    Args:
        build_date: The date in YYYYMMDD form

    Returns:
        The parsed date, at midnight UTC

    Raises:
        argparse.ArgumentTypeError: If the value is not a valid YYYYMMDD date
    """
    try:
        return datetime.strptime(build_date, "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"{build_date!r} is not a YYYYMMDD date") from error


def build_docker_bake_file(
    build_images: list[ImageSpec], registries: list[str], build_date: datetime
) -> Path:
    """Creates a docker bake file based on the list of images

    Args:
        build_images: list of images to build
        registries: list of registry/namespace prefixes; one tag trio is
            emitted per registry (e.g. ``ghcr.io/androsh7``, ``docker.io/androsh7``)
        build_date: the date the images are stamped and tagged with

    Returns:
        Path to the generated docker bake file
    """
    bake_file_path = PARENT_DIRECTORY / "docker-bake.hcl"
    with open(file=bake_file_path, mode="w", encoding="utf-8") as bake_file:
        bake_file.write('group "default" {\n  targets = [')
        for image_spec in build_images:
            bake_file.write(f'"{image_spec.tag.replace(".", "-")}", ')
        bake_file.write("]\n}\n\n")

        for image_spec in build_images:
            bake_file.write(f'target "{image_spec.tag.replace(".", "-")}" {{\n')
            bake_file.write('  context = "."\n')
            bake_file.write(
                f'  dockerfile = "{image_spec.dockerfile}"\n'.replace("\\", "/")
            )
            tag_entries = []
            for registry in registries:
                tag_entries.append(f'"{registry}/nuitka-compiler:{VERSION}-{image_spec.tag}"')
                tag_entries.append(f'"{registry}/nuitka-compiler:latest-{image_spec.tag}"')
                tag_entries.append(
                    f'"{registry}/nuitka-compiler:'
                    f'{VERSION}-{build_date.strftime("%Y%m%d")}-{image_spec.tag}"'
                )
            bake_file.write(f'  tags = [{", ".join(tag_entries)}]\n')
            bake_file.write(
                f'  platforms = ["linux/{"arm64" if image_spec.architecture == "aarch64" else "amd64"}"]\n'
            )

            # Set labels
            bake_file.write("  labels = {\n")
            bake_file.write(f'    "maintainer" = "{NAMESPACE}"\n')
            bake_file.write(f'    "author" = "{NAMESPACE}"\n')
            bake_file.write('    "license" = "MIT"\n')
            bake_file.write(f'    "version" = "{VERSION}"\n')
            bake_file.write(f'    "source" = "{SOURCE_URL}"\n')
            bake_file.write(f'    "commit-hash" = "{COMMIT_HASH}"\n')
            bake_file.write(
                f'    "python-version" = "{image_spec.build_args.get("PYTHON_VERSION", "not specified")}"\n'
            )
            bake_file.write(
                f'    "architecture" = "{image_spec.build_args.get("ARCHITECTURE", "no specified")}"\n'
            )
            bake_file.write(
                f'    "openssl-version" = "{image_spec.build_args.get("OPENSSL_VERSION", "not specified")}"\n'
            )
            bake_file.write(
                f'    "build-date" = "{build_date.strftime("%Y-%m-%d")}"\n'
            )
            bake_file.write('    "base-image-maintainer" = "The ManyLinux project"\n')
            bake_file.write("  }\n")

            # Set build arguments
            if image_spec.build_args:
                bake_file.write("  args = {\n")
                for arg_key, arg_value in image_spec.build_args.items():
                    bake_file.write(f'    {arg_key} = "{arg_value}"\n')
                bake_file.write("  }\n")
            bake_file.write("}\n\n")
    return bake_file_path


def select_build_images(
    libc_filters: list[str] | None = None,
    architecture_filters: list[str] | None = None,
    python_version_filters: list[str] | None = None,
    skip_arm_build: bool = False,
) -> list[ImageSpec]:
    """Selects the images to build from the configured build matrix

    An empty or omitted filter matches every configured value for that dimension,
    so calling this function with no arguments returns the full build matrix

    Args:
        libc_filters: libc identifiers to keep, for example ``glibc-2.17``
        architecture_filters: architectures to keep, for example ``x86_64``
        python_version_filters: python versions to keep, for example ``3.13``
        skip_arm_build: excludes every aarch64 image when True

    Returns:
        Image specifications matching every supplied filter, in configuration order
    """
    build_images = []
    for libc, dockerfile in LIBC_TO_DOCKERFILE:
        if libc_filters and libc not in libc_filters:
            continue
        for architecture in ARCHITECTURES:
            if architecture == "aarch64" and skip_arm_build:
                continue
            if architecture_filters and architecture not in architecture_filters:
                continue
            for python_version in PYTHON_VERSIONS:
                if python_version_filters and python_version not in python_version_filters:
                    continue
                build_images.append(
                    ImageSpec(
                        tag=f"{architecture}-{libc}-py{python_version}",
                        dockerfile=dockerfile,
                        architecture=architecture,
                        build_args={
                            "ARCHITECTURE": architecture,
                            "PYTHON_VERSION": python_version,
                            "OPENSSL_VERSION": OPENSSL_VERSION,
                        },
                    )
                )
    return build_images


def main():
    """Build docker images"""
    parser = argparse.ArgumentParser(prog="build.py")
    parser.add_argument("--version", action="version", version=f"Nuitka Compiler Images v{VERSION}")
    parser.add_argument("--show-build-steps", action="store_true", help="Displays the python build steps")
    parser.add_argument("--skip-arm-build", action="store_true", help="Skips all ARM builds")
    parser.add_argument(
        "--libc",
        action="append",
        dest="libc_filters",
        metavar="LIBC",
        choices=[libc for libc, _ in LIBC_TO_DOCKERFILE],
        help=(
            "Only build images for this libc version. May be passed multiple "
            "times. Defaults to every configured libc version"
        ),
    )
    parser.add_argument(
        "--python",
        action="append",
        dest="python_version_filters",
        metavar="PYTHON_VERSION",
        choices=PYTHON_VERSIONS,
        help=(
            "Only build images for this python version. May be passed multiple "
            "times. Defaults to every configured python version"
        ),
    )
    parser.add_argument(
        "--architecture",
        action="append",
        dest="architecture_filters",
        metavar="ARCHITECTURE",
        choices=ARCHITECTURES,
        help=(
            "Only build images for this architecture. May be passed multiple "
            "times. Defaults to every configured architecture"
        ),
    )
    parser.add_argument(
        "--build-date",
        type=parse_build_date,
        default=parse_build_date(datetime.now(timezone.utc).strftime("%Y%m%d")),
        metavar="YYYYMMDD",
        help=(
            "Date used for the dated image tag and the build-date label. "
            "Defaults to today in UTC. Pass one value across a matrix build so "
            "every image shares a tag even if the build spans midnight"
        ),
    )
    parser.add_argument(
        "--progress",
        choices=["auto", "plain", "tty", "quiet"],
        default=None,
        help=(
            "Docker buildx progress output mode, overrides --show-build-steps. "
            "Defaults to 'auto' when --show-build-steps is set and 'quiet' otherwise"
        ),
    )
    parser.add_argument("--parallelism", type=int, default=DEFAULT_PARALLELISM, help=f"Number of simultaneous builds that can run, default {DEFAULT_PARALLELISM}")
    parser.add_argument("--push", action="store_true", help="Push images to the configured registries")
    parser.add_argument(
        "--registry",
        action="append",
        dest="registries",
        metavar="REGISTRY",
        help=(
            "Registry/namespace prefix to publish under "
            "(e.g. ghcr.io/androsh7, docker.io/androsh7). May be passed multiple "
            f"times. Defaults to '{NAMESPACE}' when omitted."
        ),
    )
    args = parser.parse_args()

    registries = args.registries if args.registries else [NAMESPACE]
    progress = args.progress if args.progress else ("auto" if args.show_build_steps else "quiet")

    # Generate image list
    build_images = select_build_images(
        libc_filters=args.libc_filters,
        architecture_filters=args.architecture_filters,
        python_version_filters=args.python_version_filters,
        skip_arm_build=args.skip_arm_build,
    )
    if not build_images:
        parser.error(
            "no images match the supplied --libc, --python, --architecture and --skip-arm-build filters"
        )

    # Create buildx constants
    os.environ["BUILDX_BAKE_ENTITLEMENTS_FS"] = "0"
    buildx_allow_list = [
        f"--allow=fs.read={dockerfile.as_posix()}"
        for dockerfile in dict.fromkeys(image_spec.dockerfile for image_spec in build_images)
    ]

    # Generate docker-bake.hcl file
    build_list = []
    for index, image in enumerate(build_images, start=1):
        build_list.append(image)
        if len(build_list) == args.parallelism or index == len(build_images):
            # Log start
            print(
                f"Building images {index - len(build_list) + 1}-{index} out of {len(build_images)} images",
                end="",
                file=sys.stderr,
            )
            for build in build_list:
                print(f" - {build.tag}", end="", file=sys.stderr)
            print("\n", file=sys.stderr)

            # Create bake file
            bake_file_path = build_docker_bake_file(build_list, registries, args.build_date)

            # Build (and optionally push) images using docker bake
            bake_cmd = [
                "docker",
                "buildx",
                "bake",
                *buildx_allow_list,
                "--file",
                str(bake_file_path),
                f"--progress={progress}",
            ]
            if args.push:
                bake_cmd.append("--push")
            subprocess.run(bake_cmd, check=True)

            # Log completion
            print(
                f"Completed building images {index - len(build_list) + 1}-{index} out of {len(build_images)} images",
                file=sys.stderr,
            )

            # Remove the bake file
            os.remove(bake_file_path)

            # Clear the build list
            build_list.clear()


if __name__ == "__main__":
    main()
