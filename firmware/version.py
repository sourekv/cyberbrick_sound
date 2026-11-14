# PlatformIO pre-script (extra_scripts in platformio.ini): passes the git commit and the build date to the firmware
# as FW_GIT and FW_BUILD (include/version.h). Without git it leaves them out and version.h uses its fallbacks.
import datetime
import subprocess

Import("env")  # noqa: F821 (provided by PlatformIO)


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=env["PROJECT_DIR"], capture_output=True, text=True,  # noqa: F821
                              timeout=10).stdout.strip()
    except Exception:
        return ""


commit = git("rev-parse", "--short=7", "HEAD")
if commit:
    if git("status", "--porcelain", "--untracked-files=no"):
        commit += "-dirty"
    env.Append(CPPDEFINES=[("FW_GIT", '\\"%s\\"' % commit)])  # noqa: F821
env.Append(CPPDEFINES=[("FW_BUILD", '\\"%s\\"' % datetime.date.today().isoformat())])  # noqa: F821
print("firmware version: git %s" % (commit or "unknown"))
