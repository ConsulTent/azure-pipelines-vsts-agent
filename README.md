# Azure Pipelines VSTS Agent

[![Docker Image](https://github.com/ConsulTent/azure-pipelines-vsts-agent/actions/workflows/docker-image.yml/badge.svg)](https://github.com/ConsulTent/azure-pipelines-vsts-agent/actions/workflows/docker-image.yml)
[![Docker Pulls](https://img.shields.io/docker/pulls/consultent/azure-pipelines-vsts-agent)](https://hub.docker.com/repository/docker/consultent/azure-pipelines-vsts-agent/general)
[![Image Size](https://img.shields.io/docker/image-size/consultent/azure-pipelines-vsts-agent/latest)](https://hub.docker.com/repository/docker/consultent/azure-pipelines-vsts-agent/general)
[![Version](https://img.shields.io/docker/v/consultent/azure-pipelines-vsts-agent?sort=date)](https://hub.docker.com/repository/docker/consultent/azure-pipelines-vsts-agent/tags)
[![Renovate enabled](https://img.shields.io/badge/renovate-enabled-brightgreen.svg?logo=renovatebot)](https://renovatebot.com)

An Ubuntu-based Docker image with the Azure CLI and PowerShell preinstalled that registers itself as a self-hosted Azure Pipelines agent on container start. It is a drop-in replacement for Microsoft's deprecated [`microsoft/vsts-agent`](https://hub.docker.com/r/microsoft/vsts-agent/) image, available on Docker Hub as [`consultent/azure-pipelines-vsts-agent`](https://hub.docker.com/repository/docker/consultent/azure-pipelines-vsts-agent/general).

The agent binary is not baked into the image — it is downloaded on every start, so each container always runs the newest agent release. Before registering, the container deletes any stale offline agent with the same name from the pool, so restarted pods do not collide with their old registration. Images are rebuilt monthly with fresh OS packages, Azure CLI, and PowerShell.

## Quick start

```bash
docker run -d --name vsts-agent \
  -e VSTS_ACCOUNT=<org> \
  -e VSTS_TOKEN=<pat> \
  -e VSTS_POOL=<pool> \
  consultent/azure-pipelines-vsts-agent:latest
```

`VSTS_TOKEN` must be a personal access token with **Agent Pools (read, manage)** scope. See Microsoft's [self-hosted Linux agent docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/v2-linux) for how tokens and pools work.

## Tags

| Tag | Ubuntu | Notes |
| --- | --- | --- |
| `latest` | 26.04 | Newest LTS; tracks the newest release |
| `ubuntu-26.04` | 26.04 | |
| `ubuntu-24.04` | 24.04 | |
| `ubuntu-22.04` | 22.04 | Long-standing tag, kept for existing deployments |
| `<ubuntu>-<run>-<id>` | any | Immutable per-build tag, e.g. `26.04-13-13852919624` |

## Environment variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `VSTS_ACCOUNT` | yes | — | Azure DevOps organization name |
| `VSTS_TOKEN` | yes | — | PAT with Agent Pools (read, manage) scope; written to `/vsts/.token`, then unset |
| `VSTS_POOL` | no | `Default` | Agent pool to join |
| `VSTS_AGENT` | no | `hostname` | Agent name; `$(...)` expressions are expanded |
| `VSTS_WORK` | no | — | Agent work directory; `$(...)` expressions are expanded |
| `VSTS_TOKEN_FILE` | no | — | Read the token from a file instead of `VSTS_TOKEN` |

## Run modes

| Entrypoint | Behavior |
| --- | --- |
| `./start.sh` *(default)* | Registers the agent and runs until stopped; deregisters on INT/TERM. A tiny HTTP server on port 80 redirects to your organization's agent pool page. |
| `./start-once.sh` | Registers, runs **one** job, then exits — for one-shot container jobs. |
| `./start-none.sh` | Registers nothing and sleeps 10 hours — a debug target for exec'ing into the image. |

```bash
# one job, then exit
docker run --rm \
  -e VSTS_ACCOUNT=<org> -e VSTS_TOKEN=<pat> -e VSTS_POOL=<pool> \
  consultent/azure-pipelines-vsts-agent:latest ./start-once.sh

# no agent; keep the container alive for debugging
docker run -it \
  -e VSTS_ACCOUNT=<org> \
  consultent/azure-pipelines-vsts-agent:latest ./start-none.sh
```

## Building and CI

The image builds monthly (1st of the month, ~04:17 UTC) and on manual dispatch via [`.github/workflows/docker-image.yml`](.github/workflows/docker-image.yml), as a matrix over Ubuntu 22.04 / 24.04 / 26.04 pushed to Docker Hub. Dependencies are kept current by [Renovate](https://renovatebot.com) (GitHub App).

To build locally:

```bash
docker build ubuntu/                                # defaults to Ubuntu 22.04
docker build --build-arg UBUNTU_VERSION=26.04 ubuntu/
```

The `XXGITVERXX` placeholder in the Dockerfile is replaced with `git describe --always --long` during CI; local builds keep the literal placeholder in `/etc/git_version`.

---

Vendor: **ConsulTent Pte. Ltd.** — [consultent.ltd](https://consultent.ltd) — support: [consul+docker@consultent.ltd](mailto:consul+docker@consultent.ltd)
