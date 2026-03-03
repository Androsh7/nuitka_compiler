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
with open("VERSION.txt", "r", encoding="utf-8") as version_file:
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


def build_docker_bake_file(build_images: list[ImageSpec]) -> Path:
    """Creates a docker bake file based on the list of images

    Args:
        build_images: list of images to build

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
                f'  allow = ["fs.read={str(PARENT_DIRECTORY).replace("\\", "/")}/*"]\n'
            )
            bake_file.write(
                f'  dockerfile = "{image_spec.dockerfile}"\n'.replace("\\", "/")
            )
            bake_file.write(
                f'  tags = ["{NAMESPACE}/nuitka-compiler:{VERSION}-{image_spec.tag}", "{NAMESPACE}/nuitka-compiler:latest-{image_spec.tag}"]\n'
            )
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
                f'    "build-date" = "{datetime.now(timezone.utc).strftime("%Y-%m-%d")}"\n'
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


def main():
    """Build docker images"""
    parser = argparse.ArgumentParser(prog="build.py")
    parser.add_argument("--version", action="version", version=f"Nuitka Compiler Images v{VERSION}")
    parser.add_argument("--show-build-steps", action="store_true", help="Displays the python build steps")
    parser.add_argument("--parallelism", type=int, default=DEFAULT_PARALLELISM, help=f"Number of simultaneous builds that can run, default {DEFAULT_PARALLELISM}")
    args = parser.parse_args()

    # Login to docker hub
    print("Logging in to Docker Hub", file=sys.stderr)
    if (docker_password := os.environ.get("DOCKER_PASSWORD")) is None or (docker_username := os.environ.get("DOCKER_USERNAME")) is None:
        docker_username = input("Docker username: ")
        docker_password = input("Docker PAT token: ")
    subprocess.run(
        f"echo {docker_password} | docker login -u {docker_username} --password-stdin",
        shell=True,
        check=True,
    )

    # Create buildx constants
    os.environ["BUILDX_BAKE_ENTITLEMENTS_FS"] = "0"
    buildx_allow_list = []
    for BUILD_IMAGE in LIBC_TO_DOCKERFILE:
        buildx_allow_list.append(
            f"--allow=fs.read={str(BUILD_IMAGE[1]).replace('\\', '/')}"
        )

    # Generate image list
    BUILD_IMAGES = []
    for libc, dockerfile in LIBC_TO_DOCKERFILE:
        for architecture in ARCHITECTURES:
            for python_version in PYTHON_VERSIONS:
                BUILD_IMAGES.append(
                    ImageSpec(
                        tag=f"{architecture}-{libc}-py{python_version.rsplit('.', 1)[0]}",
                        dockerfile=dockerfile,
                        architecture=architecture,
                        build_args={
                            "ARCHITECTURE": architecture,
                            "PYTHON_VERSION": python_version,
                            "OPENSSL_VERSION": OPENSSL_VERSION,
                        },
                    )
                )

    # Generate docker-bake.hcl file
    build_list = []
    for index, image in enumerate(BUILD_IMAGES, start=1):
        build_list.append(image)
        if len(build_list) == args.parallelism or index == len(BUILD_IMAGES):
            # Log start
            print(
                f"Building images {index - len(build_list) + 1}-{index} out of {len(BUILD_IMAGES)} images",
                end="",
                file=sys.stderr,
            )
            for build in build_list:
                print(f" - {build.tag}", end="", file=sys.stderr)
            print("\n", file=sys.stderr)

            # Create bake file
            bake_file_path = build_docker_bake_file(build_list)

            # Build and push images using docker bake
            subprocess.run(
                [
                    "docker",
                    "bake",
                    *buildx_allow_list,
                    "--file",
                    str(bake_file_path),
                    "--push",
                    f'--progress={"auto" if args.show_build_steps else "quiet"}',
                ],
                check=True,
            )

            # Log completion
            print(
                f"Completed building images {index - len(build_list) + 1}-{index} out of {len(BUILD_IMAGES)} images",
                file=sys.stderr,
            )

            # Remove the bake file
            os.remove(bake_file_path)

            # Clear the build list
            build_list.clear()

    # Logout from docker hub
    print("Logging out from Docker Hub", file=sys.stderr)
    subprocess.run("docker logout", shell=True, check=True)


if __name__ == "__main__":
    main()
