# Nuitka Compiler Docker Images

This repository builds and publishes a matrix of Docker images designed for **Nuitka compilation**. The images are intended for CI/CD and local build pipelines that need consistent Linux toolchains, pinned OpenSSL, and pinned CPython versions when compiling Python applications to native binaries with Nuitka.

## Tag schema

`androsh7/nuitka-compiler:<VERSION>-<architecture>-<libc>-py<python>`

Every image is published to both Docker Hub and the GitHub Container
Registry. The two are identical, pick whichever you prefer:

- `docker.io/androsh7/nuitka-compiler:...`
- `ghcr.io/androsh7/nuitka-compiler:...`

| field        | options                                       |
| ------------ | --------------------------------------------- |
| version      | `latest`, `0.1.0`, `0.2.0`, `0.3.0`, `0.4.0`  |
| architecture | `x86_64`, `aarch64`                           |
| libc         | `glibc-2.17`, `glibc-2.28`, `musl-1.2`        |
| python       | `3.14`, `3.13`, `3.12`, `3.11`, `3.10`, `3.9` |

Examples:

- `androsh7/nuitka-compiler:latest-x86_64-glibc-2.17-py3.13`
- `androsh7/nuitka-compiler:latest-x86_64-glibc-2.28-py3.11`
- `androsh7/nuitka-compiler:0.3.0-aarch64-musl-1.2-py3.11`

## Why does this exist?

I love nuitka, it creates compact, fast, and portable python executables however it makes CI/CD a bit tricky.

Windows is relatively straight forward, either run the nuitka build baremetal on a windows machine or use third-party CI/CD like github actions.

Linux is complicated because every executable must be built against a version of glibc or musl and cannot run on a system with an older version. This means that if you build an executable using glibc 2.24 and run it on CentOS 7 which runs glibc 2.17 you will get an error. The solution is to either build the executable on the oldest system you plan to support or ignore users on older platforms.

This project aims to solve this issue by creating a series of easy-to-use docker images for CI/CD that contain all the requirements for building with nuitka using python (3.9 - 3.14) on x86 or arm using glibc 2.17 (released 2012), glibc 2.28 (released 2018), or musl 1.2 (released 2020).

## Usage

### Docker run

This method involves starting the image in the background and then using cli commands to build the executable.

I recommend this when using CI/CD tools like github actions

```
# Run the docker container in the background
docker run --name nuitka-compiler --detach --rm androsh7/nuitka-compiler:latest-x86_64-glibc-2.17-py3.13 sleep infinity

# Copy in the project files
docker cp /path/to/project/files nuitka-compiler:/src

# Install dependencies
docker exec nuitka-compiler pip install -r /src/requirements.txt

# Run nuitka build
docker exec nuitka-compiler python3 -m nuitka --standalone --onefile /src/main.py --output-filename=/src/main.bin

# Copy out executable
docker cp nuitka-compiler:/src/main.bin main.bin

# Stop the container
docker stop nuitka-compiler
```

### Dockerfile

This method involves create a custom dockerfile to build the images

I recommend this for more complex builds.

Example dockerfile:

```
ARG ARCHITECTURE="x86_64" # Set the architecture "x86_64" or "aarch64"
ARG LIBC="glibc2.17" # Set the libc version "glibc-2.17", "glibc-2.28", "musl-1.2"
ARG PYTHON_VERSION="3.13" # Set the python version (major.minor) "3.14", "3.13", "3.12", "3.11", "3.10", "3.9"

FROM androsh7/nuitka-compiler:latest-${ARCHITECTURE}-${LIBC}-py${PYTHON_VERSION}

# Copy project files into container
COPY /your/project/files /src

# Install dependencies
RUN pip install -r /src/requirements.txt

# Build executable
RUN nuitka --onefile --standalone /src/main.py --output-filename=/src/main.bin

# Test the executable
ENTRYPOINT ["/src/main.bin", "--version"]
```

The run the following commands:

```
# Build the image, this will build the nuitka executable
docker build -t nuitka-compiler-my_project:latest .

# Turn the image into a container
docker run --name nuitka-compiler-my_project nuitka-compiler-my_project:latest

# Copy the executable out of the container
docker cp nuitka-compiler-my_project:/src/main.bin main.bin

# Delete the container and image
docker rm nuitka-compiler-my_project
docker rmi nuitka-compiler-my_project:latest
```
