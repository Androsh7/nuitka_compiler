# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0]

### Added

- Per-image build matrix in CI, every libc/python/architecture combination builds in its own job
- Native aarch64 builds on GitHub ARM runners, ARM images are no longer skipped
- Build verification on pull requests and pushes to main, without publishing
- `--libc`, `--python` and `--architecture` filters for building a subset of the matrix
- `--progress` flag for selecting the docker buildx progress output mode
- `push` input on the manual workflow trigger for publishing on demand

### Changed

- OpenSSL is fetched from the openssl GitHub releases instead of www.openssl.org
- Base images are pinned to a dated tag instead of `latest`
- Docker Hub publishing is skipped when its credentials are absent, so forks build without secrets
- Registry logins only run when the workflow is publishing
- `--show-build-steps` is superseded by `--progress`, it remains supported as a shorthand for `--progress auto`
- The generated bake file no longer emits a per-target `allow` attribute, the equivalent entitlement is passed on the buildx command line

## [0.3.0]

### Added

- GHCR publishing workflow
- Github CI/CD

## [0.2.0]

### Added

- Zstandard package to docker image
- Option to configure parallelism
- License (whoops)

### Changed

- Docker images pull cpython from git instead of python ftp

## [0.1.0]

### Added

- Support for glibc-2.17, glibc-2.28, and musl-1.2 images
- Support for x86 and arm architectures
- Support for python 3.9 - 3.14
