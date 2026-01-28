"""Configuration for building images"""

# Standard libraries
from pathlib import Path

# --------------------------------------------------------------------------------- #
# ================================= CONFIGURATION ================================= #
# --------------------------------------------------------------------------------- #
PARENT_DIRECTORY = Path(__file__).parent
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
PYTHON_VERSIONS = ["3.9.24", "3.10.19", "3.11.14", "3.12.12", "3.13.11", "3.14.2"]
OPENSSL_VERSION = "3.0.18"
NAMESPACE = "androsh7"
SOURCE_URL = "https://github.com/Androsh7/nuitka_compiler_images"
PARALLELISM = 4
# --------------------------------------------------------------------------------- #
# ================================= CONFIGURATION ================================= #
# --------------------------------------------------------------------------------- #
