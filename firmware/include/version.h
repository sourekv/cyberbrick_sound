#pragma once
// The firmware version, printed at boot and reported to the web page (@info fw=...).
//
// FW_VERSION is raised by hand for every release, and the release gets the git tag v<FW_VERSION> (for example
// v0.1.0). FW_GIT and FW_BUILD come from firmware/version.py at build time: the short hash of the commit the build
// was made from, with "-dirty" when there were uncommitted changes, and the build date. So the full version
// "0.1.0+86e9882" says exactly which code runs, also for builds between releases.

#define FW_VERSION "0.1.0"

#ifndef FW_GIT
#define FW_GIT "unknown"   // built without version.py or outside git
#endif
#ifndef FW_BUILD
#define FW_BUILD __DATE__
#endif

#define FW_FULL_VERSION FW_VERSION "+" FW_GIT
