# Nuitka Compiler Docker Images

**manylinux-based, reproducible build environments for Nuitka**

This repository builds and publishes a matrix of Docker images designed for **Nuitka compilation**. The images are intended for CI/CD and local build pipelines that need consistent Linux toolchains, pinned OpenSSL, and pinned CPython versions when compiling Python applications to native binaries with Nuitka.

---

## Overview

Each image is built on top of official `manylinux` base images from [quay.io](https://quay.io/organization/pypa) and layers in:

- A **pinned OpenSSL build** (compiled from source)
- A **pinned CPython build** (compiled from source with optimizations)
- Updated Python packaging tools (`pip`, `setuptools`, `wheel`)
- **Nuitka**, preinstalled and ready to use

The build system generates a full build matrix across:

- **libc baselines** (e.g., manylinux / glibc variants)
- **CPU architectures** (e.g., `x86_64`, `aarch64`)
- **Python minor versions** (e.g., 3.9 → 3.13)

This ensures predictable, repeatable compilation environments regardless of where the build runs.

---

## Supported x86_64 versions

| Architecture | libc baseline | Python version | OpenSSL | Tag suffix                       |
| ------------ | ------------- | -------------- | ------- | -------------------------------- |
| x86_64       | glibc-2.28    | 3.13           | 3.0.18  | VERSION-x86_64-glibc-2.28-py3.13 |
| x86_64       | glibc-2.28    | 3.11           | 3.0.18  | VERSION-x86_64-glibc-2.28-py3.12 |
| x86_64       | glibc-2.28    | 3.12           | 3.0.18  | VERSION-x86_64-glibc-2.28-py3.11 |
| x86_64       | glibc-2.28    | 3.10           | 3.0.18  | VERSION-x86_64-glibc-2.28-py3.10 |
| x86_64       | glibc-2.28    | 3.9            | 3.0.18  | VERSION-x86_64-glibc-2.28-py3.9  |
| x86_64       | glibc-2.17    | 3.13           | 3.0.18  | VERSION-x86_64-glibc-2.17-py3.13 |
| x86_64       | glibc-2.17    | 3.12           | 3.0.18  | VERSION-x86_64-glibc-2.17-py3.12 |
| x86_64       | glibc-2.17    | 3.11           | 3.0.18  | VERSION-x86_64-glibc-2.17-py3.11 |
| x86_64       | glibc-2.17    | 3.10           | 3.0.18  | VERSION-x86_64-glibc-2.17-py3.10 |
| x86_64       | glibc-2.17    | 3.9            | 3.0.18  | VERSION-x86_64-glibc-2.17-py3.9  |
| x86_64       | musl-1.1      | 3.13           | 3.0.18  | VERSION-x86_64-musl-1.1-py3.13   |
| x86_64       | musl-1.1      | 3.12           | 3.0.18  | VERSION-x86_64-musl-1.1-py3.12   |
| x86_64       | musl-1.1      | 3.11           | 3.0.18  | VERSION-x86_64-musl-1.1-py3.11   |
| x86_64       | musl-1.1      | 3.10           | 3.0.18  | VERSION-x86_64-musl-1.1-py3.10   |
| x86_64       | musl-1.1      | 3.9            | 3.0.18  | VERSION-x86_64-musl-1.1-py3.9    |
