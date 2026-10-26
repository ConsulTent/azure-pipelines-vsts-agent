```
   ___                      _ _____           _       ___ _             __ _      _   
  / __\___  _ __  ___ _   _| /__   \___ _ __ | |_    / _ \ |_ ___      / /| |_ __| |  
 / /  / _ \| '_ \/ __| | | | | / /\/ _ \ '_ \| __|  / /_)/ __/ _ \    / / | __/ _` |  
/ /__| (_) | | | \__ \ |_| | |/ / |  __/ | | | |_  / ___/| ||  __/_  / /__| || (_| |_ 
\____/\___/|_| |_|___/\__,_|_|\/   \___|_| |_|\__| \/     \__\___(_) \____/\__\__,_(_)
```                                                                     
https://consultent.ltd/
<br>
https://github.com/ConsulTent/azure-pipelines-vsts-agent/

DROP-IN replacement for Microsoft VSTS Agent containers, with 100% VSTS Agent compatibility for ~~https://hub.docker.com/r/microsoft/vsts-agent/~~ (now defunct)

**Variants**: Ubuntu <strike>18.04</strike> 22.04 / 24.04 / 26.04, plus a hardened flavor built on Docker Hardened Images (Debian 13 base)

ATTENTION: Ubuntu 18.04 is Deprecated as per GitHub Announcement https://github.com/actions/runner-images/issues/6002  
Use tag `ubuntu-18.04` for the last available Ubuntu 18.04 image.  
Base images are now Ubuntu 22.04 (`ubuntu-22.04`), Ubuntu 24.04 (`ubuntu-24.04`), Ubuntu 26.04 (`ubuntu-26.04`), and DHI-hardened Debian 13 (`dhi-debian13`).

This repository is rebuilt monthly by GitHub Actions (1st of the month, ~04:17 UTC). Each build automatically includes the latest Azure CLI and PowerShell.

### This image includes pool cleanup code for dead agents.

### Tags come in three kinds:

- **Rolling tags** (mutable, re-pointed by every build): `latest` (newest LTS, currently Ubuntu 26.04), `ubuntu-22.04`, `ubuntu-24.04`, `ubuntu-26.04`, `dhi-latest`, `dhi-debian13`
- **Per-build tags** (immutable, protected by Docker Hub tag immutability): `<variant>-<run_number>-<run_id>`, e.g. `26.04-7-40258889030` — always resolves to exactly the image built that run; pin one for reproducibility
- **Monthly version tags** (immutable): `<year>-<month>-<azure cli version>-<powershell version>`, e.g. `2026-10-2.91.0-7.6.9` — names the exact tool versions inside that month's `latest` build

VSTS agents must be started with account connection information, which is provided through environment variables:

* VSTS_ACCOUNT: the name of the Visual Studio account
* VSTS_TOKEN: a personal access token (PAT) for the Visual Studio account that has been given at least the Agent Pools (read, manage) scope
* VSTS_POOL: (optional) the agent pool to join; defaults to `Default`

To run the agent image for a specific Visual Studio account:

```
docker run \
  -e VSTS_ACCOUNT=<name> \
  -e VSTS_TOKEN=<pat> \
  -e VSTS_POOL=<pool> \
  -d consultent/azure-pipelines-vsts-agent:latest
```

Other entrypoints: `./start-once.sh` runs one job and exits; `./start-none.sh` starts no agent and sleeps (debug target).

The October 2026 build includes:

```
azure-cli 2.91.0
powershell 7.6.9
```

Azure CLI and PowerShell are automatically updated to the latest version upon build. Current per-variant versions are documented in the GitHub README. Please use tags to pin versions.

Support available: <a href="mailto:consul+client@consultent.ltd?Subject=Support+Needed+for+Azure" target="_blank">consul+docker@consultent.ltd</a>
