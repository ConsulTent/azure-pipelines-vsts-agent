# syntax=docker/dockerfile:1
ARG UBUNTU_VERSION=26.04
FROM ubuntu:${UBUNTU_VERSION}

ARG UBUNTU_VERSION
LABEL org.opencontainers.image.source="https://github.com/ConsulTent/azure-pipelines-vsts-agent" \
      org.opencontainers.image.base.name="docker.io/library/ubuntu" \
      org.opencontainers.image.base.version="${UBUNTU_VERSION}" \
      "vendor.name"="ConsulTent Pte. Ltd." \
      "vendor.url"="https://consultent.ltd"

# Define an ENV variable to be picked by the agent 'System capabilities' and used in pipeline demands
ENV AGENT_GROUP default

# To make it easier for build and release pipelines to run apt-get,
# configure apt to not require confirmation (assume the -y argument by default)
ENV DEBIAN_FRONTEND=noninteractive
ENV AGENT_ALLOW_RUNASROOT=1
RUN echo "APT::Get::Assume-Yes \"true\";" > /etc/apt/apt.conf.d/90assumeyes

# Version-specific library names differ per release: the 24.04 "t64" transition
# renamed several libs, libicu changes every release, and pcregrep was dropped
# in 26.04. netcat-openbsd is what Ubuntu 22.04's "netcat" resolves to today
# (its nc supports the -q flag start.sh relies on); the virtual "netcat"
# name no longer resolves on 24.04+.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get dist-upgrade -y && apt-get install -y --no-install-recommends \
        ca-certificates \
        unzip \
        curl \
        jq \
        git \
        iputils-ping \
        libkrb5-3 \
        zlib1g \
        libunwind8 \
        netcat-openbsd \
        wget \
        sudo \
        make \
    && case "${UBUNTU_VERSION}" in \
           22.04) apt-get install -y --no-install-recommends libcurl4 libicu70 libssl3 liblttng-ust1 pcregrep ;; \
           24.04) apt-get install -y --no-install-recommends libcurl4t64 libicu74 libssl3t64 liblttng-ust1t64 pcregrep ;; \
           26.04) apt-get install -y --no-install-recommends libcurl4t64 libicu78 libssl3t64 liblttng-ust1t64 ;; \
       esac

# We need this because Azure Agent installdependencies.sh is broken.
RUN case "${UBUNTU_VERSION}" in \
        22.04) apt-mark hold libcurl4 ;; \
        *) apt-mark hold libcurl4t64 ;; \
    esac

# Install AZ CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash
RUN echo "AZURE_EXTENSION_DIR=/usr/local/lib/azureExtensionDir" | tee -a /etc/environment \
    && mkdir -p /usr/local/lib/azureExtensionDir

# Install powershell core
# Microsoft's apt repo has no powershell package for 26.04 yet; install the
# binary archive there instead (latest GitHub release, pinned fallback if the
# API is unavailable).
ARG POWERSHELL_VERSION=7.6.8
RUN if [ "${UBUNTU_VERSION}" = "26.04" ]; then \
        PSVER="$(curl -fsSL https://api.github.com/repos/PowerShell/PowerShell/releases/latest | jq -r .tag_name || true)"; \
        PSVER="${PSVER:-v${POWERSHELL_VERSION}}"; \
        curl -fsSL -o /tmp/ps.tar.gz "https://github.com/PowerShell/PowerShell/releases/download/${PSVER}/powershell-${PSVER#v}-linux-x64.tar.gz" \
        && mkdir -p /opt/microsoft/powershell/7 \
        && tar zxf /tmp/ps.tar.gz -C /opt/microsoft/powershell/7 \
        && chmod +x /opt/microsoft/powershell/7/pwsh \
        && ln -s /opt/microsoft/powershell/7/pwsh /usr/bin/pwsh \
        && rm -f /tmp/ps.tar.gz; \
    else \
        wget -q https://packages.microsoft.com/config/ubuntu/${UBUNTU_VERSION}/packages-microsoft-prod.deb \
        && dpkg -i packages-microsoft-prod.deb \
        && apt-get update \
        && apt-get install -y powershell; \
    fi

# Download an older Agent and install Dependencies (update this once in a while)
RUN mkdir -p /vsts

WORKDIR /vsts

RUN echo "XXGITVERXX" > /etc/git_version

COPY ./start.sh .
COPY ./start-once.sh .
COPY ./start-none.sh .
RUN chmod +x start.sh
RUN chmod +x start-once.sh
RUN chmod +x start-none.sh
CMD ["./start.sh"]
