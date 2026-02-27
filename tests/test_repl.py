"""Tests for REPL shell"""

from repl.shell import MinesploitShell


def test_shell_initialization():
    shell = MinesploitShell()
    assert shell.target is None
    assert shell.port is None
    assert shell.current_exploit is None


def test_do_list():
    shell = MinesploitShell()
    shell.do_list("exploits")


def test_do_use():
    shell = MinesploitShell()
    shell.do_use("cve_2016_stratum_mass_duplicate")
    assert shell.current_exploit == "cve_2016_stratum_mass_duplicate"
    assert "cve_2016_stratum_mass_duplicate" in shell.prompt


def test_do_use_invalid():
    shell = MinesploitShell()
    shell.do_use("invalid_exploit")
    assert shell.current_exploit is None


def test_do_set_target():
    shell = MinesploitShell()
    shell.do_set("RHOSTS 192.168.1.1")
    assert shell.target == "192.168.1.1"


def test_do_set_port():
    shell = MinesploitShell()
    shell.do_set("RPORT 8333")
    assert shell.port == 8333


def test_do_show():
    shell = MinesploitShell()
    shell.target = "192.168.1.1"
    shell.port = 8333
    shell.do_show("options")
