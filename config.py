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
PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]
# CPython is built from these release tags rather than from the major.minor
# maintenance branches, which move under us and have broken builds before.
# Bumping a tag here is a deliberate change, verified by CI like any other.
CPYTHON_TAGS = {
    "3.9": "v3.9.25",
    "3.10": "v3.10.21",
    "3.11": "v3.11.16",
    "3.12": "v3.12.14",
    "3.13": "v3.13.15",
    "3.14": "v3.14.7",
}
OPENSSL_VERSION = "3.0.18"
NAMESPACE = "androsh7"
SOURCE_URL = "https://github.com/Androsh7/nuitka_compiler_images"
DEFAULT_PARALLELISM = 4
# --------------------------------------------------------------------------------- #
# ================================= CONFIGURATION ================================= #
# --------------------------------------------------------------------------------- #
