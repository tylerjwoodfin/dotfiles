#!/usr/bin/env python3
"""Tests for the command launcher."""

import os
import shlex
import shutil
import tempfile
import time
import unittest
from pathlib import Path

import launcher
from launcher import (
    ActionError,
    Command,
    NoMatch,
    UsageStore,
    ZshParser,
    cabbie_suggestion,
    cloud_command_names,
    filter_commands,
    load_opts,
    preview_text,
    render_action,
    resolve_invocation,
    split_inline_comment,
    strip_opt_blocks,
)


FIXTURE = """\
# list files
lsf() { ls; }

alias vim='nvim' # launcher-hidden
alias gs='git status' # git status
alias foodlog='python3 ~/git/tools/foodlog/main.py' # log food
alias cal='cal -3' # calendar
alias cdd='cd ~/git/docker' # docker
alias cabbie='python3 ~/git/tools/cabbie/main.py' # ai commands
alias v='echo v' # create ticket
alias say='echo "#hi"' # said

precmd() { vcs_info } # launcher-hidden

if [[ " ${DOTFILES_OPTS[@]} " =~ " not-cloud " ]]; then
    cloud_commands=(
        "foodlog" "v" "remind"
    )
    for cmd in "${cloud_commands[@]}"; do
        alias "$cmd"="cloud $cmd" # launcher-hidden
    done
fi

if [[ " ${DOTFILES_OPTS[@]} " =~ " phone " ]]; then
    alias cal="cloud cal" # launcher-hidden
    alias llama="cloud llama" # launcher-hidden
fi

alias grep='grep --color=auto'
"""

NETWORK = """\
cloud() {
    ssh cloud.example
}

ice() {
    ssh ice.example
}

export SHORTEN_TOKEN="not-a-command"
"""


class LauncherTests(unittest.TestCase):
    """Parser, overlays, actions, and non-TUI resolution."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def write_fixture(self, name: str, text: str) -> Path:
        """Write a zsh fixture and return its path."""
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def parse(self, opts: list[str], extra: Path | None = None) -> dict[str, Command]:
        """Parse the fixture plus an optional overlay."""
        common = self.write_fixture("common.zsh", FIXTURE)
        files = [common]
        if extra is not None:
            files.append(extra)
        parser = ZshParser(files, opts, cache_file=self.tmp / "cache.pkl")
        return {cmd.name: cmd for cmd in parser.parse()}

    def test_split_inline_comment_keeps_hash_inside_quotes(self):
        """A hash inside quotes is part of the alias value."""
        value, comment = split_inline_comment("""'echo "#hi"' # said""")
        self.assertEqual(value, """'echo "#hi"'""")
        self.assertEqual(comment, "said")

    def test_strip_opt_blocks_keeps_unconditional_aliases(self):
        """Gated overlays are removed; ordinary aliases stay."""
        stripped = strip_opt_blocks(FIXTURE)
        self.assertIn("alias grep=", stripped)
        self.assertNotIn("cloud_commands", stripped)
        self.assertNotIn('alias "$cmd"', stripped)
        self.assertEqual(cloud_command_names(FIXTURE), ["foodlog", "v", "remind"])

    def test_hidden_commands_and_actions(self):
        """Hidden markers stick, and prompted verbs are attached."""
        commands = self.parse([])
        self.assertTrue(commands["vim"].hidden)
        self.assertTrue(commands["precmd"].hidden)
        self.assertFalse(commands["gs"].hidden)
        self.assertEqual(commands["gs"].category, "git")
        self.assertEqual(commands["gs"].raw_command, "git status")
        self.assertEqual(commands["foodlog"].action, "foodlog")
        self.assertEqual(commands["foodlog"].host, "local")
        self.assertEqual(commands["v"].action, "v")
        self.assertEqual(commands["cdd"].category, "docker")
        self.assertIn("grep", commands)
        self.assertNotIn("$cmd", commands)
        self.assertNotIn("l", commands)
        self.assertEqual(commands["say"].raw_command, 'echo "#hi"')
        self.assertEqual(commands["remind"].host, "local")
        self.assertEqual(commands["remind"].description, "create a reminder")

    def test_not_cloud_wrappers_show_cloud_host(self):
        """Laptop overlays rewrite commands onto the cloud host."""
        commands = self.parse(["not-cloud"])
        self.assertEqual(commands["foodlog"].host, "cloud")
        self.assertEqual(commands["foodlog"].raw_command, "cloud foodlog")
        self.assertFalse(commands["foodlog"].hidden)
        self.assertEqual(commands["remind"].raw_command, "cloud remind")
        self.assertEqual(commands["cal"].host, "local")
        self.assertTrue(commands["vim"].hidden)

    def test_phone_overlay_wraps_cal_and_llama(self):
        """The phone opt only rewrites cal and llama."""
        commands = self.parse(["phone"])
        self.assertEqual(commands["cal"].host, "cloud")
        self.assertEqual(commands["cal"].raw_command, "cloud cal")
        self.assertEqual(commands["llama"].host, "cloud")
        self.assertEqual(commands["foodlog"].host, "local")

    def test_network_overlay_adds_ssh_hosts(self):
        """network.zsh contributes SSH helpers and ignores exports."""
        network = self.write_fixture("network.zsh", NETWORK)
        without = self.parse([])
        self.assertNotIn("ice", without)
        commands = self.parse(["network"], extra=network)
        self.assertEqual(commands["ice"].category, "network")
        self.assertEqual(commands["ice"].host, "ice")
        self.assertEqual(commands["ice"].description, "SSH to ice")
        self.assertNotIn("SHORTEN_TOKEN", commands)
        for cmd in commands.values():
            self.assertFalse(cmd.raw_command.startswith("export"))
            self.assertNotIn("TOKEN", cmd.name)

    def test_cache_invalidates_when_an_overlay_changes(self):
        """A newer overlay mtime forces a reparse."""
        common = self.write_fixture("common.zsh", "alias gs='git status' # git status\n")
        overlay = self.write_fixture("extra.zsh", "alias one='echo one' # one\n")
        cache = self.tmp / "cache.pkl"
        parser = ZshParser([common, overlay], ["extra.zsh"], cache_file=cache)
        first = {cmd.name for cmd in parser.parse()}
        self.assertIn("one", first)
        self.assertTrue(cache.exists())
        overlay.write_text(
            "alias one='echo one' # one\nalias two='echo two' # two\n",
            encoding="utf-8",
        )
        future = time.time() + 5
        os.utime(overlay, (future, future))
        second = {cmd.name for cmd in parser.parse()}
        self.assertIn("two", second)

    def test_render_and_resolve_actions(self):
        """Non-TUI verbs build quoted commands. Vikunja is `v`."""
        commands = list(self.parse(["not-cloud"]).values())
        docker = self.tmp / "docker"
        (docker / "plex").mkdir(parents=True)
        self.assertEqual(
            resolve_invocation(
                ["remind", "buy", "milk", "tomorrow"],
                commands,
                cabbie=False,
                docker_root=docker,
            ),
            "cloud remind --title "
            + shlex.quote("buy milk")
            + " --when "
            + shlex.quote("tomorrow"),
        )
        foodlog = resolve_invocation(
            ["foodlog", "pizza", "800"],
            commands,
            cabbie=False,
            docker_root=docker,
        )
        self.assertEqual(foodlog, f"cloud foodlog {shlex.quote('pizza')} 800")
        ticket = resolve_invocation(
            ["v", "buy", "milk"],
            commands,
            cabbie=False,
            docker_root=docker,
        )
        self.assertEqual(ticket, f"cloud v {shlex.quote('buy milk')}")
        self.assertEqual(
            resolve_invocation(["v", "ls"], commands, cabbie=False, docker_root=docker),
            "cloud v ls",
        )
        self.assertEqual(
            resolve_invocation(
                ["cdd", "plex"], commands, cabbie=False, docker_root=docker
            ),
            f"cd {docker / 'plex'}",
        )
        with self.assertRaises(ActionError):
            resolve_invocation(
                ["remind", "only-title"], commands, cabbie=False, docker_root=docker
            )
        with self.assertRaises(NoMatch) as caught:
            resolve_invocation(
                ["nope"], commands, cabbie=False, docker_root=docker
            )
        self.assertIn("cabbie", str(caught.exception))
        asked = resolve_invocation(
            ["disk", "free"], commands, cabbie=True, docker_root=docker
        )
        self.assertEqual(asked, f"cabbie {shlex.quote('disk free')}")

    def test_vikunja_preview_prompts_for_a_title(self):
        """Creating a ticket is the Vikunja `v` action."""
        commands = self.parse([])
        text = preview_text(commands["v"])
        self.assertIn("v '<title>'", text)
        self.assertIn("life-ops", text)

    def test_filter_hides_commands_until_asked(self):
        """Hidden rows, category filters, favorites, and the cabbie fallback."""
        commands = list(self.parse([]).values())
        visible = filter_commands(
            commands, "", show_hidden=False, favorites=[], recent=[]
        )
        names = [cmd.name for cmd in visible]
        self.assertNotIn("vim", names)
        self.assertIn("gs", names)
        shown = filter_commands(
            commands, "", show_hidden=True, favorites=[], recent=[]
        )
        self.assertIn("vim", [cmd.name for cmd in shown])
        git_only = filter_commands(
            commands, "git:", show_hidden=False, favorites=[], recent=[]
        )
        self.assertTrue(git_only)
        self.assertTrue(all(cmd.category == "git" for cmd in git_only))
        ranked = filter_commands(
            commands, "", show_hidden=False, favorites=["foodlog"], recent=["gs"]
        )
        self.assertEqual(ranked[0].name, "foodlog")
        self.assertEqual(ranked[1].name, "gs")
        fallback = filter_commands(
            commands, "zzzz-nope", show_hidden=False, favorites=[], recent=[]
        )
        self.assertEqual(len(fallback), 1)
        self.assertIn("AI path", fallback[0].description)
        self.assertTrue(fallback[0].raw_command.startswith("cabbie "))

    def test_usage_store_recent_and_favorites(self):
        """Favorites toggle and recent names stay on disk."""
        store = UsageStore(self.tmp / "usage.pkl")
        store.remember("gs")
        store.remember("foodlog")
        self.assertEqual(store.recent, ["foodlog", "gs"])
        self.assertTrue(store.toggle("gs"))
        self.assertFalse(store.toggle("gs"))
        again = UsageStore(self.tmp / "usage.pkl")
        self.assertEqual(again.recent[0], "foodlog")
        self.assertEqual(again.favorites, [])

    def test_load_opts_from_env_or_zshrc(self):
        """Opts come from the launcher env, then ~/.zshrc."""
        self.assertEqual(
            load_opts({"LAUNCHER_DOTFILES_OPTS": "common not-cloud"}),
            ["common", "not-cloud"],
        )
        zshrc = self.write_fixture(
            "zshrc", "export DOTFILES_OPTS=(common network nnn)\n"
        )
        self.assertEqual(load_opts({}, zshrc=zshrc), ["common", "network", "nnn"])

    def test_real_common_zsh(self):
        """The repo file parses, hides vim, and exposes Vikunja as `v`."""
        common = Path(__file__).resolve().parent / "zsh" / "common.zsh"
        parser = ZshParser([common], [], cache_file=self.tmp / "real.pkl")
        commands = {cmd.name: cmd for cmd in parser.parse()}
        self.assertTrue(commands["vim"].hidden)
        self.assertEqual(commands["foodlog"].action, "foodlog")
        self.assertEqual(commands["v"].action, "v")
        self.assertIn("Vikunja", commands["v"].description)
        self.assertNotIn("l", commands)
        self.assertNotIn("$cmd", commands)
        preview = preview_text(commands["v"])
        self.assertIn("host: local", preview)
        self.assertIn("life-ops", preview)

    def test_real_network_file_is_commands_only(self):
        """SSH helpers are listed. The shorten export is not a command."""
        network = Path.home() / "git" / "backend" / "zsh" / "network.zsh"
        if not network.is_file():
            self.skipTest("network.zsh not present")
        common = self.write_fixture("common.zsh", "alias gs='git status' # git status\n")
        parser = ZshParser(
            [common, network], ["network"], cache_file=self.tmp / "net.pkl"
        )
        commands = {cmd.name: cmd for cmd in parser.parse()}
        self.assertIn("ice", commands)
        self.assertEqual(commands["ice"].category, "network")
        self.assertNotIn("SHORTEN_TOKEN", commands)
        for cmd in commands.values():
            self.assertFalse(cmd.raw_command.startswith("export"))
            self.assertNotIn("TOKEN", cmd.name)

    def test_main_writes_command_file(self):
        """`l gs` writes the alias body for the shell wrapper."""
        cache = self.tmp / "main-cache.pkl"
        usage = self.tmp / "main-usage.pkl"
        cmd_file = self.tmp / "cmd"
        previous_cache = os.environ.get("LAUNCHER_CACHE")
        previous_usage = os.environ.get("LAUNCHER_USAGE")
        previous_opts = os.environ.get("LAUNCHER_DOTFILES_OPTS")
        os.environ["LAUNCHER_CACHE"] = str(cache)
        os.environ["LAUNCHER_USAGE"] = str(usage)
        os.environ["LAUNCHER_DOTFILES_OPTS"] = "common"
        try:
            code = launcher.main(["--cmd-file", str(cmd_file), "gs"])
        finally:
            self._restore_env("LAUNCHER_CACHE", previous_cache)
            self._restore_env("LAUNCHER_USAGE", previous_usage)
            self._restore_env("LAUNCHER_DOTFILES_OPTS", previous_opts)
        self.assertEqual(code, 0)
        self.assertIn("git status", cmd_file.read_text(encoding="utf-8"))

    def test_main_no_match_does_not_call_cabbie(self):
        """A miss explains the AI path and writes nothing."""
        cmd_file = self.tmp / "cmd"
        previous_cache = os.environ.get("LAUNCHER_CACHE")
        previous_opts = os.environ.get("LAUNCHER_DOTFILES_OPTS")
        os.environ["LAUNCHER_CACHE"] = str(self.tmp / "miss.pkl")
        os.environ["LAUNCHER_DOTFILES_OPTS"] = "common"
        try:
            code = launcher.main(["--cmd-file", str(cmd_file), "zzzz-nope"])
        finally:
            self._restore_env("LAUNCHER_CACHE", previous_cache)
            self._restore_env("LAUNCHER_DOTFILES_OPTS", previous_opts)
        self.assertEqual(code, 1)
        self.assertFalse(cmd_file.exists())

    def test_blank_foodlog_renders_bare_command(self):
        """An empty foodlog prompt shows today's log."""
        self.assertEqual(
            render_action("foodlog", {"food": "", "calories": ""}, "local", self.tmp),
            "foodlog",
        )

    def test_preview_shows_host_and_command(self):
        """The preview pane names the host and the command that will run."""
        cmd = Command(
            name="gs",
            description="git status",
            command_type="alias",
            raw_command="git status",
            host="local",
            category="git",
        )
        text = preview_text(cmd, favorite=True)
        self.assertIn("host: local", text)
        self.assertIn("git status", text)
        self.assertIn("category: git", text)
        self.assertIn("favorite", text)
        suggestion = cabbie_suggestion("make a note", "local")
        self.assertIn("AI path", suggestion.description)

    @staticmethod
    def _restore_env(key: str, previous: str | None) -> None:
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous


class LauncherTuiTests(unittest.IsolatedAsyncioTestCase):
    """Headless Textual checks for the preview and hidden toggle."""

    async def test_preview_and_hidden_toggle(self):
        """The preview shows host, and ctrl+h reveals hidden commands."""
        app_cls = launcher.build_launcher_app()
        self.assertIsNotNone(app_cls)
        commands = [
            Command(
                name="gs",
                description="git status",
                command_type="alias",
                raw_command="git status",
                host="local",
                category="git",
            ),
            Command(
                name="vim",
                description="",
                command_type="alias",
                raw_command="nvim",
                host="local",
                category="other",
                hidden=True,
            ),
        ]
        usage = UsageStore(Path(tempfile.mkdtemp()) / "usage.pkl")
        app = app_cls(commands, usage, Path("/tmp"))
        async with app.run_test() as pilot:
            await pilot.pause()
            self.assertIn("host: local", app.preview_text)
            self.assertIn("git status", app.preview_text)
            await pilot.press("ctrl+h")
            await pilot.pause()
            labels = [item.command.name for item in app.query("ListItem").results()]
            # CommandItem is a ListItem; names come from filtered commands.
            self.assertIn("vim", [cmd.name for cmd in app.filtered_commands])
            self.assertTrue(labels or app.show_hidden)


if __name__ == "__main__":
    unittest.main()
