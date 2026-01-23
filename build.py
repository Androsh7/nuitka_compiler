"""Builds docker images"""

# Standard libraries
import subprocess
from pathlib import Path
from dataclasses import dataclass

# Constants
with open("VERSION.txt", "r", encoding="utf-8") as version_file:
    VERSION = version_file.read().strip()
PARENT_DIRECTORY = Path(__file__).parent

#---------------------------------------------------------------------------------#
#================================= CONFIGURATION =================================#
#---------------------------------------------------------------------------------#
LIBC_TO_DOCKERFILE = [
        (
            "glibc-2.17",
            PARENT_DIRECTORY / "docker_files" / "glibc-2_17-compiler-Dockerfile",
        ),
        (
            "glibc-2.28",
            PARENT_DIRECTORY / "docker_files" / "glibc-2_28-compiler-Dockerfile",
        ),
        (
            "musl-1.2",
            PARENT_DIRECTORY / "docker_files" / "musl-1_2-compiler-Dockerfile",
        ),
    ]
ARCHITECTURES = ["x86_64", "aarch64"]
PYTHON_VERSIONS = ["3.13.11", "3.14.2"]
OPENSSL_VERSION = "3.0.18"
#---------------------------------------------------------------------------------#
#================================= CONFIGURATION =================================#
#---------------------------------------------------------------------------------#

@dataclass(frozen=True)
class ImageSpec:
    name: str
    dockerfile: Path
    architecture: str | None = None
    build_args: dict[str, str] | None = None




def build_docker_image(image_spec: ImageSpec):
    """Build a docker image based on the given ImageSpec"""
    command = [
        "docker",
        "build",
        "-f",
        str(image_spec.dockerfile),
        f"--label=VERSION={VERSION}",
        "-t",
        f"androsh7/{image_spec.name}:{VERSION}",
        "-t",
        f"androsh7/{image_spec.name}:latest",
    ]

    # Add build arguments
    if image_spec.build_args:
        for arg_key, arg_value in image_spec.build_args.items():
            command.append("--build-arg")
            command.append(f"{arg_key}={arg_value}")
            command.append(f"--label={arg_key}={arg_value}")

    # Add working directory label
    command.extend(["--push", str(image_spec.dockerfile.parent)])

    # Execute the build command
    print(f"Building image: {image_spec.name}\nRunning command: {' '.join(command)}")
    subprocess.run(command, check=True)


def main():
    """Build docker images"""
    subprocess.run(["docker", "login"], check=True)

    # Generate image list
    BUILD_IMAGES = []
    for libc, dockerfile in LIBC_TO_DOCKERFILE:
        for architecture in ARCHITECTURES:
            for python_version in PYTHON_VERSIONS:
                BUILD_IMAGES.append(
                    ImageSpec(
                        name=f"nuitka-compiler-{architecture}-{libc}-python-{python_version.rsplit('.', 1)[0]}",
                        dockerfile=dockerfile,
                        build_args={
                            "ARCHITECTURE": architecture,
                            "PYTHON_VERSION": python_version,
                            "OPENSSL_VERSION": OPENSSL_VERSION,
                        },
                    )
                )

    # Build each image
    for image_spec in BUILD_IMAGES:
        build_docker_image(image_spec)

    # Logout from docker
    subprocess.run(["docker", "logout"], check=True)


if __name__ == "__main__":
    main()
