"""Builds docker images"""

# Standard libraries
import os
import subprocess
from pathlib import Path
from dataclasses import dataclass

# Project libraries
from config import (
    LIBC_TO_DOCKERFILE,
    ARCHITECTURES,
    PYTHON_VERSIONS,
    OPENSSL_VERSION,
    NAMESPACE,
    PARENT_DIRECTORY,
    PARALLELISM,
)

# Constants
with open("VERSION.txt", "r", encoding="utf-8") as version_file:
    VERSION = version_file.read().strip()


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
            bake_file.write(
                f'  dockerfile = "{image_spec.dockerfile}"\n'.replace("\\", "/")
            )
            bake_file.write(
                f'  tags = ["{NAMESPACE}/nuitka-compiler:{VERSION}-{image_spec.tag}", "{NAMESPACE}/nuitka-compiler:latest-{image_spec.tag}"]\n'
            )
            bake_file.write(
                f'  platforms = ["linux/{"arm64" if image_spec.architecture == "aarch64" else "amd64"}"]\n'
            )
            bake_file.write(
                f'  context = "{str(PARENT_DIRECTORY).replace("\\", "/")}"\n'
            )
            if image_spec.build_args:
                bake_file.write("  args = {\n")
                for arg_key, arg_value in image_spec.build_args.items():
                    bake_file.write(f'    {arg_key} = "{arg_value}"\n')
                bake_file.write("  }\n")
            bake_file.write("}\n\n")
    return bake_file_path


def main():
    """Build docker images"""

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
        if len(build_list) == PARALLELISM or index == len(BUILD_IMAGES):

            # Create bake file
            bake_file_path = build_docker_bake_file(build_list)

            # Build and push images using docker bake
            os.environ["BUILDX_BAKE_ENTITLEMENTS_FS"] = "0"
            subprocess.run(
                ["docker", "bake", "--file", str(bake_file_path), "--push"], check=True
            )

            # Remove the bake file
            os.remove(bake_file_path)

            # Clear the build list
            build_list.clear()

if __name__ == "__main__":
    main()
