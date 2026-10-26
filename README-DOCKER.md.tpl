```
   ___                      _ _____           _       ___ _             __ _      _   
  / __\___  _ __  ___ _   _| /__   \___ _ __ | |_    / _ \ |_ ___      / /| |_ __| |  
 / /  / _ \| '_ \/ __| | | | | / /\/ _ \ '_ \| __|  / /_)/ __/ _ \    / / | __/ _` |  
/ /__| (_) | | | \__ \ |_| | |/ / |  __/ | | | |_  / ___/| ||  __/_  / /__| || (_| |_ 
\____/\___/|_| |_|___/\__,_|_|\/   \___|_| |_|\__| \/     \__\___(_) \____/\__\__,_(_)
```                                                                     
https://consultent.ltd/

ATTENTION: Ubuntu 18.04 is Deprecated as per (GitHub Announcement)[https://github.com/actions/runner-images/issues/6002].  Use tag ```ubuntu-18.04``` for the last available Ubuntu 18.04 image.
Base image updated to Ubuntu 22.04, using tag ```ubuntu-22.04```

DROP-IN replacement for Microsoft VSTS Agent containers. Updated to Ubuntu 18.04 with 100% VSTS Agent compatibility for https://hub.docker.com/r/microsoft/vsts-agent/

This image is rebuilt monthly by GitHub Actions (1st of the month, ~04:17 UTC) with the latest OS packages, Azure CLI, and PowerShell.

### This update includes pool cleanup code for dead agents.

See documentation in the Microsoft link above or:

## VSTS agents must be started with account connection information, which is provided through two environment variables:

* VSTS_ACCOUNT: the name of the Visual Studio account
* VSTS_TOKEN: a personal access token (PAT) for the Visual Studio account that has been given at least the Agent Pools (read, manage) scope.
To run the default VSTS agent image for a specific Visual Studio account:

```
docker run \
  -e VSTS_ACCOUNT=<name> \
  -e VSTS_TOKEN=<pat> \
  -it mcr.microsoft.com/azure-pipelines/vsts-agent
```

Includes the versions below as of %BUILD_DATE% (tag:%BUILD_TAG%):
```
%AZURE_CLI_VERSION%
%POWERSHELL_CLI_VERSION%
```

Azure CLI and Powershell are automatically updated to latest version upon build.  Please use tags to pin versions.

Tags come in two kinds: rolling tags (`latest`, `ubuntu-22.04`, `ubuntu-24.04`, `ubuntu-26.04`) are mutable and re-pointed by every build; per-build tags (`<ubuntu>-<run_number>-<run_id>`, e.g. `26.04-2-40245352308`) are immutable — protected by Docker Hub's selective tag immutability — and always resolve to exactly the image built that day.

Support available: <a href="mailto:consul+client@consultent.ltd?Subject=Support+Needed+for+Azure" target="_blank">consul+docker@consultent.ltd</a>