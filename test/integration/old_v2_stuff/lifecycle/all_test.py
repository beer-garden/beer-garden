import os
import sys
import time

import pytest

# This is the recommended import pattern, see https://github.com/google/python-subprocess32
if os.name == "posix" and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess


@pytest.mark.timeout(20)
class TestShutdown(object):
    @pytest.mark.parametrize(
        "command",
        [
            ("brew-view",),
            ("bartender",),
        ],
    )
    def test_solo(self, command):
        proc = subprocess.Popen(command)
        time.sleep(3)
        proc.terminate()

        proc.wait()

        assert proc.poll() == 0

    def test_both(self):
        bv_proc = subprocess.Popen("brew-view")
        bt_proc = subprocess.Popen("bartender")

        time.sleep(10)

        bt_proc.terminate()
        bt_proc.wait()
        assert bt_proc.poll() == 0

        bv_proc.terminate()
        bv_proc.wait()
        assert bv_proc.poll() == 0
