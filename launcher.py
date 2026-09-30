#!/usr/bin/env python3
"""Command picker for zsh functions, aliases, and a few prompted actions.

Parses ``zsh/common.zsh`` plus whatever ``DOTFILES_OPTS`` sources (network,
phone, not-cloud, other overlays). The cache invalidates when any of those
files change. ``# launcher-hidden`` commands stay out of the list until the
TUI toggle shows them.

With arguments, the picker stays non-interactive so it works over SSH:

    l remind milk tomorrow
    l foodlog pizza 800
    l v buy milk
    l cdd plex
"""

from __future__ import annotations

import argparse
import os
import pickle
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from fuzzywuzzy import fuzz, process  # pyright: ignore[reportMissingImports]
except ImportError:  # pragma: no cover - dependency is listed in requirements.txt
    fuzz = None
    process = None


PARSER_VERSION = "1"
HIDDEN_MARKERS = {"launcher-hidden", "launcher-hide"}
RECENT_LIMIT = 20

NETWORK_HOSTS = {
    "cloud",
    "ice",
    "icecream",
    "drop",
    "fog",
    "rain",
    "steam",
    "flow",
    "rainbow",
}
LIFE_OPS = {
    "remind",
    "rmm",
    "rmmt",
    "rmmy",
    "rmmty",
    "rmml",
    "rmmsl",
    "rmme",
    "rmmst",
    "rmmsw",
    "diary",
    "foodlog",
    "milestone",
    "lifelog",
    "cabbie",
    "v",
    "notes",
    "docs",
    "work",
    "bluesky",
    "amazon",
    "shorten",
    "one-hour-of-distraction",
    "llama",
    "cheat",
    "backloggist",
    "lofi",
}
GIT_COMMANDS = {
    "git",
    "gcam",
    "gbr",
    "pullall",
    "gtag",
    "wrong-branch",
    "glog",
    "gcm",
    "gch",
    "gb",
    "gs",
    "gclean",
    "gd",
    "gdd",
    "gp",
}
CATEGORIES = {"git", "life-ops", "docker", "network", "other"}

_OPT_BLOCK = re.compile(
    r'if \[\[ " \$\{DOTFILES_OPTS\[@\]\} " =~ " (?:not-cloud|phone|nnn) " \]\]; then'
    r".*?"
    r"^fi\n",
    re.S | re.M,
)
_FUNCTION = re.compile(
    r"(?:^#\s*([^\n]+)\s*\n)?[ \t]*(?:function[ \t]+)?([\w-]+)[ \t]*\(\s*\)\s*\{",
    re.M,
)
_CLOUD_ARRAY = re.compile(r"cloud_commands=\((.*?)\)", re.S)


@dataclass
class ActionSpec:
    """How a first-class verb collects arguments."""

    kind: str  # "fields", "projects", or "none"
    prompts: tuple[tuple[str, str], ...] = ()


ACTIONS: dict[str, ActionSpec] = {
    "remind": ActionSpec("fields", (("title", "Title"), ("when", "When"))),
    "foodlog": ActionSpec(
        "fields",
        (("food", "Food"), ("calories", "Calories (blank looks up)")),
    ),
    "milestone": ActionSpec("fields", (("text", "Milestone"),)),
    "diary": ActionSpec("none"),
    "v": ActionSpec("fields", (("title", "Ticket title"),)),
    "cdd": ActionSpec("projects"),
}

ACTION_TEMPLATES = {
    "remind": "remind --title '<title>' --when '<when>'",
    "foodlog": "foodlog '<food>' [calories]",
    "milestone": "milestone '<text>'",
    "diary": "diary",
    "v": "v '<title>'",
    "cdd": "cd ~/git/docker/<project>",
}

DEFAULT_DESCRIPTIONS = {
    "remind": "create a reminder",
    "foodlog": "log food",
    "milestone": "log milestone",
    "diary": "diary",
    "v": "create Vikunja ticket",
    "cdd": "docker project",
}


@dataclass
class Command:
    """One launcher row."""

    name: str
    description: str
    command_type: str
    raw_command: str
    host: str = "local"
    category: str = "other"
    hidden: bool = False
    source: str = ""
    action: str = ""
    record_name: str = ""


class ActionError(Exception):
    """The request was recognized but the arguments are not usable."""


class TextualMissing(Exception):
    """Textual is not installed, so the TUI cannot start."""


class NoMatch(Exception):
    """Nothing in the catalog matches the free-text request."""

    def __init__(self, tokens: list[str]):
        text = " ".join(tokens)
        super().__init__(
            f"No command matched {text!r}.\n"
            f"AI path (cabbie): l --cabbie {text}"
        )


def wrap_host(host: str, command: str) -> str:
    """Prefix a command that should run on the cloud shell."""
    if host == "cloud" and not command.startswith("cloud "):
        return f"cloud {command}"
    return command


def split_inline_comment(text: str) -> tuple[str, str]:
    """Split ``value # comment`` without treating hashes inside quotes as comments."""
    quote = ""
    for index, char in enumerate(text):
        if quote:
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
            continue
        if char == "#":
            return text[:index].strip(), text[index + 1 :].strip()
    return text.strip(), ""


def strip_opt_blocks(content: str) -> str:
    """Drop opt-gated blocks. Callers reapply the ones that are actually enabled."""
    return _OPT_BLOCK.sub("\n", content)


def cloud_command_names(content: str) -> list[str]:
    """Names aliased to ``cloud <name>`` when ``not-cloud`` is set."""
    match = _CLOUD_ARRAY.search(content)
    if not match:
        return []
    return re.findall(r'"([^"]+)"', match.group(1))


def category_for(cmd: Command) -> str:
    """Bucket a command for the picker."""
    if cmd.source == "network" or cmd.name in NETWORK_HOSTS:
        return "network"
    if cmd.name in LIFE_OPS or cmd.name.startswith("rmm"):
        return "life-ops"
    if cmd.name in {"cdd", "syncsure"} or (
        cmd.raw_command.startswith("cd ") and "/docker" in cmd.raw_command
    ):
        return "docker"
    if (
        cmd.name in GIT_COMMANDS
        or cmd.raw_command == "git"
        or cmd.raw_command.startswith("git ")
    ):
        return "git"
    if cmd.name.startswith("cd") and cmd.description.strip().lower() == "git":
        return "git"
    return "other"


def decorate(cmd: Command) -> None:
    """Fill category, action, and network host after parsing."""
    if cmd.name in ACTIONS:
        cmd.action = cmd.name
    if cmd.source == "network" and cmd.host == "local":
        cmd.host = cmd.name
    if cmd.source == "network" and not cmd.description:
        cmd.description = f"SSH to {cmd.name}"
    cmd.category = category_for(cmd)


def mark_cloud(commands: dict[str, Command], name: str) -> None:
    """Point ``name`` at the cloud wrapper, keeping its description when it exists."""
    existing = commands.get(name)
    if existing is None:
        commands[name] = Command(
            name=name,
            description=DEFAULT_DESCRIPTIONS.get(name, "run on cloud"),
            command_type="alias",
            raw_command=f"cloud {name}",
            host="cloud",
            source="overlay",
        )
        return
    existing.host = "cloud"
    existing.hidden = False
    existing.raw_command = f"cloud {name}"


def ensure_actions(commands: dict[str, Command]) -> None:
    """Register prompted verbs even when zsh never defined them."""
    for name, description in DEFAULT_DESCRIPTIONS.items():
        if name in commands:
            continue
        commands[name] = Command(
            name=name,
            description=description,
            command_type="action",
            raw_command=name,
            source="registry",
        )


def apply_remote_wrappers(
    commands: dict[str, Command], common_text: str, opts: set[str]
) -> None:
    """Honor not-cloud and phone overlays."""
    if "not-cloud" in opts:
        for name in cloud_command_names(common_text):
            mark_cloud(commands, name)
    if "phone" in opts:
        for name in ("cal", "llama"):
            mark_cloud(commands, name)


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _hidden_comment(comment: str) -> bool:
    return comment.strip() in HIDDEN_MARKERS


def _line_at(content: str, pos: int) -> str:
    start = content.rfind("\n", 0, pos) + 1
    end = content.find("\n", pos)
    if end == -1:
        end = len(content)
    return content[start:end]


def collect_commands(content: str, source: str) -> list[tuple[int, Command]]:
    """Extract functions and aliases in source order."""
    found: list[tuple[int, Command]] = []
    cleaned = strip_opt_blocks(content)

    for match in _FUNCTION.finditer(cleaned):
        name = match.group(2)
        if name == "l" or "$" in name:
            continue
        description = (match.group(1) or "").strip()
        line = _line_at(cleaned, match.end() - 1)
        hidden = _hidden_comment(description) or any(
            marker in line for marker in HIDDEN_MARKERS
        )
        if hidden:
            description = ""
        found.append(
            (
                match.start(),
                Command(
                    name=name,
                    description=description,
                    command_type="function",
                    raw_command=name,
                    hidden=hidden,
                    source=source,
                ),
            )
        )

    offset = 0
    for line in cleaned.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("alias ") and "=" in stripped:
            left, right = stripped.split("=", 1)
            name = _unquote(left[len("alias") :].strip())
            if name and name != "l" and "$" not in name:
                raw_value, comment = split_inline_comment(right.strip())
                hidden = _hidden_comment(comment)
                found.append(
                    (
                        offset,
                        Command(
                            name=name,
                            description="" if hidden else comment,
                            command_type="alias",
                            raw_command=_unquote(raw_value.strip()),
                            hidden=hidden,
                            source=source,
                        ),
                    )
                )
        offset += len(line)

    found.sort(key=lambda item: item[0])
    return found


def load_opts(
    environ: dict[str, str] | None = None, zshrc: Path | None = None
) -> list[str]:
    """Read DOTFILES_OPTS from the launcher env var, then ~/.zshrc."""
    env = os.environ if environ is None else environ
    if "LAUNCHER_DOTFILES_OPTS" in env:
        return env["LAUNCHER_DOTFILES_OPTS"].split()
    path = Path.home() / ".zshrc" if zshrc is None else zshrc
    if path.is_file():
        match = re.search(
            r"(?m)^[ \t]*(?:export[ \t]+)?DOTFILES_OPTS=\(([^)]*)\)",
            path.read_text(encoding="utf-8"),
        )
        if match:
            return match.group(1).split()
    return ["common"]


def discover_sources(
    dotfiles_dir: Path, opts: list[str], network_file: Path | None = None
) -> list[Path]:
    """common.zsh plus each sourced overlay named by DOTFILES_OPTS."""
    files = [dotfiles_dir / "zsh" / "common.zsh"]
    network = network_file or (Path.home() / "git" / "backend" / "zsh" / "network.zsh")
    for opt in opts:
        if opt == "network":
            files.append(network)
        elif opt in {"common", "not-cloud", "phone", "nnn"}:
            continue
        else:
            files.append(dotfiles_dir / "zsh" / opt)
    return files


def source_signature(files: list[Path], opts: list[str]) -> str:
    """Change this whenever parser logic or any sourced file changes."""
    parts = [f"v={PARSER_VERSION}", "opts=" + ",".join(sorted(opts))]
    for path in files:
        if path.exists():
            stat = path.stat()
            parts.append(f"{path}:{stat.st_mtime_ns}:{stat.st_size}")
        else:
            parts.append(f"{path}:missing")
    return "\n".join(parts)


class ZshParser:
    """Parse sourced zsh files, with a cache keyed by every file's mtime."""

    def __init__(
        self,
        files: list[Path],
        opts: list[str],
        cache_file: Path | None = None,
    ):
        self.files = files
        self.opts = opts
        self.cache_file = cache_file or default_cache_path()
        self.commands: list[Command] = []

    def parse(self) -> list[Command]:
        """Return every command, including ones hidden until the TUI toggle."""
        if not self.files:
            raise FileNotFoundError("No zsh files to parse")
        if not self.files[0].exists():
            raise FileNotFoundError(f"Zsh file not found: {self.files[0]}")

        signature = source_signature(self.files, self.opts)
        if self._load_cache(signature):
            return self.commands

        commands: dict[str, Command] = {}
        common_text = self.files[0].read_text(encoding="utf-8")
        for path in self.files:
            if not path.exists():
                continue
            source = "network" if path.name == "network.zsh" else path.stem
            text = path.read_text(encoding="utf-8")
            for _pos, command in collect_commands(text, source):
                commands[command.name] = command

        apply_remote_wrappers(commands, common_text, set(self.opts))
        ensure_actions(commands)
        for command in commands.values():
            decorate(command)
        self.commands = sorted(commands.values(), key=lambda item: item.name)
        if self.commands:
            self._save_cache(signature)
        return self.commands

    def _load_cache(self, signature: str) -> bool:
        try:
            if not self.cache_file.exists():
                return False
            with open(self.cache_file, "rb") as handle:
                payload = pickle.load(handle)
            if not isinstance(payload, dict) or payload.get("signature") != signature:
                return False
            commands = payload.get("commands")
            if not isinstance(commands, list):
                return False
            self.commands = commands
            return True
        except (OSError, pickle.UnpicklingError, EOFError, AttributeError):
            return False

    def _save_cache(self, signature: str) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "wb") as handle:
                pickle.dump(
                    {"signature": signature, "commands": self.commands}, handle
                )
        except OSError:
            pass


class UsageStore:
    """Recent commands and favorites, kept beside the parse cache."""

    def __init__(self, path: Path | None = None):
        self.path = path or default_usage_path()
        self.recent: list[str] = []
        self.favorites: list[str] = []
        self.load()

    def load(self) -> None:
        """Load usage, or start empty when the file is missing or unreadable."""
        try:
            with open(self.path, "rb") as handle:
                payload = pickle.load(handle)
            if isinstance(payload, dict):
                self.recent = [str(item) for item in payload.get("recent") or []]
                self.favorites = [str(item) for item in payload.get("favorites") or []]
        except (OSError, pickle.UnpicklingError, EOFError, AttributeError):
            self.recent = []
            self.favorites = []

    def save(self) -> None:
        """Persist usage. Failures are ignored so the picker still runs."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "wb") as handle:
                pickle.dump(
                    {"recent": self.recent, "favorites": self.favorites}, handle
                )
        except OSError:
            pass

    def remember(self, name: str) -> None:
        """Move ``name`` to the front of the recent list."""
        if not name:
            return
        self.recent = [name] + [item for item in self.recent if item != name]
        self.recent = self.recent[:RECENT_LIMIT]
        self.save()

    def toggle(self, name: str) -> bool:
        """Favorite or unfavorite ``name``. Returns whether it is now a favorite."""
        if name in self.favorites:
            self.favorites = [item for item in self.favorites if item != name]
            self.save()
            return False
        self.favorites.append(name)
        self.save()
        return True


def default_cache_path() -> Path:
    """Parse cache, overridable so tests do not touch the real one."""
    override = os.environ.get("LAUNCHER_CACHE")
    if override:
        return Path(override)
    return Path.home() / ".cache" / "launcher_cache.pkl"


def default_usage_path() -> Path:
    """Usage cache, overridable so tests do not touch the real one."""
    override = os.environ.get("LAUNCHER_USAGE")
    if override:
        return Path(override)
    return Path.home() / ".cache" / "launcher_usage.pkl"


def docker_projects(docker_root: Path) -> list[str]:
    """Immediate child directories of the docker repo."""
    if not docker_root.is_dir():
        return []
    names = []
    for child in docker_root.iterdir():
        if child.name.startswith(".") or not child.is_dir():
            continue
        names.append(child.name)
    return sorted(names)


def cdd_command(project: str, docker_root: Path) -> str:
    """``cd`` into the docker root or one project directory."""
    if project in {".", "(root)"}:
        return f"cd {shlex.quote(str(docker_root))}"
    path = docker_root / project
    if not path.is_dir():
        names = ", ".join(docker_projects(docker_root)) or "(none)"
        raise ActionError(f"unknown docker project {project!r}\nprojects: {names}")
    return f"cd {shlex.quote(str(path))}"


def render_action(
    action: str, values: dict[str, str], host: str, docker_root: Path
) -> str:
    """Turn prompted fields into a shell command."""
    if action == "remind":
        title = values.get("title", "").strip()
        when = values.get("when", "").strip()
        if not title or not when:
            raise ActionError("title and when are required")
        return wrap_host(
            host,
            f"remind --title {shlex.quote(title)} --when {shlex.quote(when)}",
        )
    if action == "foodlog":
        food = values.get("food", "").strip()
        calories = values.get("calories", "").strip()
        if not food and not calories:
            return wrap_host(host, "foodlog")
        if not food:
            raise ActionError("food is required")
        if calories and not calories.isnumeric():
            raise ActionError("calories must be a number")
        if calories:
            return wrap_host(host, f"foodlog {shlex.quote(food)} {calories}")
        return wrap_host(host, f"foodlog {shlex.quote(food)}")
    if action == "milestone":
        text = values.get("text", "").strip()
        if not text:
            raise ActionError("milestone text is required")
        return wrap_host(host, f"milestone {shlex.quote(text)}")
    if action == "diary":
        return wrap_host(host, "diary")
    if action == "v":
        title = values.get("title", "").strip()
        if not title:
            raise ActionError("title is required")
        if title == "ls":
            return wrap_host(host, "v ls")
        return wrap_host(host, f"v {shlex.quote(title)}")
    if action == "cdd":
        return cdd_command(values.get("project", "").strip(), docker_root)
    raise ActionError(f"unknown action {action}")


def cli_values(action: str, rest: list[str], docker_root: Path) -> dict[str, str]:
    """Map non-TUI argv onto action fields."""
    if action == "remind":
        if len(rest) < 2:
            raise ActionError("usage: l remind <title> <when>")
        return {"title": " ".join(rest[:-1]), "when": rest[-1]}
    if action == "foodlog":
        if not rest:
            return {"food": "", "calories": ""}
        if len(rest) >= 2 and rest[-1].isnumeric():
            return {"food": " ".join(rest[:-1]), "calories": rest[-1]}
        return {"food": " ".join(rest), "calories": ""}
    if action == "milestone":
        if not rest:
            raise ActionError("usage: l milestone <text>")
        return {"text": " ".join(rest)}
    if action == "diary":
        if rest:
            raise ActionError("usage: l diary")
        return {}
    if action == "v":
        if not rest:
            raise ActionError("usage: l v <title>")
        return {"title": " ".join(rest)}
    if action == "cdd":
        if len(rest) != 1:
            names = ", ".join(docker_projects(docker_root)) or "(none)"
            raise ActionError(f"usage: l cdd <project>\nprojects: {names}")
        return {"project": rest[0]}
    raise ActionError(f"unknown action {action}")


def resolve_invocation(
    tokens: list[str],
    commands: list[Command],
    *,
    cabbie: bool,
    docker_root: Path,
) -> str:
    """Resolve a non-TUI invocation to one shell command."""
    by_name = {cmd.name: cmd for cmd in commands}
    if cabbie:
        text = " ".join(tokens).strip()
        if not text:
            raise ActionError("usage: l --cabbie <request>")
        host = by_name["cabbie"].host if "cabbie" in by_name else "local"
        return wrap_host(host, f"cabbie {shlex.quote(text)}")

    if not tokens:
        raise ActionError("usage: l <command> [args]")

    verb, rest = tokens[0], list(tokens[1:])
    cmd = by_name.get(verb)
    if verb == "v" and rest and rest[0] == "ls":
        host = cmd.host if cmd else "local"
        extra = " ".join(shlex.quote(part) for part in rest[1:])
        line = "v ls" + (f" {extra}" if extra else "")
        return wrap_host(host, line)

    if cmd and cmd.action:
        values = cli_values(cmd.action, rest, docker_root)
        return render_action(cmd.action, values, cmd.host, docker_root)
    if cmd:
        if rest:
            extra = " ".join(shlex.quote(part) for part in rest)
            return f"{cmd.raw_command} {extra}"
        return cmd.raw_command
    raise NoMatch(tokens)


def split_category_query(query: str) -> tuple[str | None, str]:
    """Support ``git: status`` style filters."""
    if ":" in query:
        head, tail = query.split(":", 1)
        if head in CATEGORIES:
            return head, tail.strip()
    return None, query


def _substring_match(cmd: Command, text: str) -> bool:
    needle = text.lower()
    haystacks = (
        cmd.name,
        cmd.description,
        cmd.category,
        cmd.host,
        cmd.raw_command,
    )
    return any(needle in value.lower() for value in haystacks)


def _order_idle(
    pool: list[Command], favorites: list[str], recent: list[str]
) -> list[Command]:
    fav_index = {name: index for index, name in enumerate(favorites)}
    recent_index = {name: index for index, name in enumerate(recent)}

    def key(cmd: Command) -> tuple[int, int, str]:
        if cmd.name in fav_index:
            return (0, fav_index[cmd.name], "")
        if cmd.name in recent_index:
            return (1, recent_index[cmd.name], "")
        return (2, 0, cmd.name)

    return sorted(pool, key=key)


def _order_query(
    matches: list[Command], text: str, favorites: list[str]
) -> list[Command]:
    favs = set(favorites)
    needle = text.lower()

    def key(cmd: Command) -> tuple[int, int, str]:
        name = cmd.name.lower()
        if name == needle:
            rank = 0
        elif name.startswith(needle):
            rank = 1
        else:
            rank = 2
        return (rank, 0 if cmd.name in favs else 1, name)

    return sorted(matches, key=key)


def _fuzzy(pool: list[Command], text: str) -> list[Command]:
    if process is None or fuzz is None or not pool:
        return []
    by_name: dict[str, Command] = {}
    for cmd in pool:
        by_name.setdefault(cmd.name, cmd)
    matches = process.extract(text, list(by_name), scorer=fuzz.ratio, limit=10)
    ordered = []
    for match in matches:
        name, score = match[0], match[1]
        if score <= 30:
            continue
        ordered.append(by_name[name])
    return ordered


def cabbie_suggestion(query: str, host: str) -> Command:
    """Labeled optional AI row shown when nothing else matches."""
    return Command(
        name="cabbie",
        description=f"AI path (optional) — ask cabbie: {query}",
        command_type="action",
        raw_command=wrap_host(host, f"cabbie {shlex.quote(query)}"),
        host=host,
        category="life-ops",
        source="cabbie",
        record_name="cabbie",
    )


def filter_commands(
    commands: list[Command],
    query: str,
    *,
    show_hidden: bool,
    favorites: list[str],
    recent: list[str],
) -> list[Command]:
    """Filter and order rows for the picker."""
    category, text = split_category_query(query.strip())
    pool = [cmd for cmd in commands if show_hidden or not cmd.hidden]
    if category:
        pool = [cmd for cmd in pool if cmd.category == category]
    if not text:
        return _order_idle(pool, favorites, recent)

    substring = [cmd for cmd in pool if _substring_match(cmd, text)]
    if substring:
        return _order_query(substring, text, favorites)
    fuzzy = _fuzzy(pool, text)
    if fuzzy:
        return fuzzy
    if category:
        return []
    host = "local"
    for cmd in commands:
        if cmd.name == "cabbie":
            host = cmd.host
            break
    return [cabbie_suggestion(query.strip(), host)]


def preview_text(command: Command | None, *, favorite: bool = False) -> str:
    """Preview pane: command, host, and category."""
    if command is None:
        return "No command selected."
    if command.action and command.action in ACTION_TEMPLATES:
        shown = wrap_host(command.host, ACTION_TEMPLATES[command.action])
    else:
        shown = command.raw_command
    lines = [
        command.name,
        f"category: {command.category}",
        f"host: {command.host}",
        f"type: {command.command_type}",
        "",
        "command:",
        f"  {shown}",
    ]
    if command.description:
        lines.extend(["", command.description])
    if command.action:
        spec = ACTIONS[command.action]
        if spec.kind == "fields":
            labels = ", ".join(label for _key, label in spec.prompts)
            lines.extend(["", f"prompts: {labels}"])
        elif spec.kind == "projects":
            lines.extend(["", "prompts: docker project"])
    if command.hidden:
        lines.extend(["", "hidden by default (ctrl+h shows these)"])
    if favorite:
        lines.extend(["", "favorite"])
    return "\n".join(lines)


def command_label(command: Command, *, favorite: bool) -> str:
    """One list row."""
    star = "* " if favorite else ""
    description = command.description or "No description"
    return (
        f"{star}{command.name}  [{command.category} · {command.host}]  {description}"
    )


def deliver(command: str, cmd_file: str | None) -> None:
    """Hand the command to the shell wrapper, or run it when launched directly."""
    if cmd_file:
        Path(cmd_file).write_text(command, encoding="utf-8")
        return
    print(f"\nExecuting: {command}")
    print("-" * 40)
    subprocess.run(
        command,
        shell=True,
        executable="/bin/zsh",
        check=False,
    )
    if command.startswith("cd "):
        target = shlex.split(command)[1] if len(shlex.split(command)) > 1 else ""
        expanded = os.path.expandvars(os.path.expanduser(target))
        if os.path.isdir(expanded):
            os.chdir(expanded)
            print(f"Changed to directory: {expanded}")
        else:
            print(f"Directory not found: {expanded}")


def build_launcher_app():
    """Import Textual and return the picker app class."""
    try:
        from textual.app import App, ComposeResult  # pylint: disable=import-outside-toplevel
        from textual.binding import Binding  # pylint: disable=import-outside-toplevel
        from textual.containers import Horizontal, Vertical  # pylint: disable=import-outside-toplevel
        from textual.widgets import (  # pylint: disable=import-outside-toplevel
            Footer,
            Header,
            Input,
            Label,
            ListItem,
            ListView,
            Static,
        )
    except ImportError:
        print(
            "Error: textual library not found. Install with: "
            "pip install -r ~/git/dotfiles/requirements.txt",
            file=sys.stderr,
        )
        return None

    class CommandItem(ListItem):
        """A list row bound to a command."""

        def __init__(self, command: Command, favorite: bool):
            super().__init__()
            self.command = command
            self.favorite = favorite

        def compose(self) -> ComposeResult:
            yield Label(
                command_label(self.command, favorite=self.favorite), markup=False
            )

    class LauncherApp(App):
        """Textual picker with preview, favorites, and action prompts."""

        CSS = """
        #body { height: 1fr; }
        #command_list { width: 2fr; height: 1fr; }
        #preview { width: 1fr; height: 1fr; padding: 0 1; border: solid $primary; }
        #form { height: 1fr; padding: 1 2; display: none; }
        """
        BINDINGS = [
            Binding("escape", "back", "Back"),
            Binding("ctrl+h", "toggle_hidden", "Hidden"),
            Binding("ctrl+f", "toggle_favorite", "Favorite"),
            Binding("ctrl+j", "focus_list", "List"),
            Binding("ctrl+k", "focus_search", "Search"),
        ]

        def __init__(
            self,
            commands: list[Command],
            usage: UsageStore,
            docker_root: Path,
        ):
            super().__init__()
            self.commands = commands
            self.usage = usage
            self.docker_root = docker_root
            self.show_hidden = False
            self.mode = "search"
            self.filtered_commands: list[Command] = []
            self._highlighted: Command | None = None
            self._pending: Command | None = None
            self._field_ids: list[str] = []
            self.preview_text = ""
            self.command_to_execute: str | None = None
            self.title = "launcher"
            self.sub_title = "esc back · ctrl+h hidden · ctrl+f favorite"

        def compose(self) -> ComposeResult:
            yield Header()
            yield Input(
                placeholder="Search — git:, life-ops:, docker:, network:",
                id="search",
            )
            yield Horizontal(
                ListView(id="command_list"),
                Static("", id="preview", markup=False),
                id="body",
            )
            yield Vertical(id="form")
            yield Footer()

        def on_mount(self) -> None:
            """Fill the list and focus search."""
            self._apply_query("")
            self.query_one("#search", Input).focus()

        def on_input_changed(self, event: Input.Changed) -> None:
            """Refilter as the user types. Typing leaves the project picker."""
            if event.input.id != "search":
                return
            if self.mode == "projects":
                self.mode = "search"
            self._apply_query(event.value)

        def on_input_submitted(self, event: Input.Submitted) -> None:
            """Enter in search runs the highlighted row. Enter walks the form."""
            if event.input.id == "search":
                self._activate(self._highlighted)
                return
            if event.input.id and event.input.id.startswith("field-"):
                self._advance_form(event.input.id)

        def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
            """Keep the preview in sync with the highlight."""
            item = event.item
            if isinstance(item, CommandItem):
                self._highlighted = item.command
                self._show_preview(item.command)

        def on_list_view_selected(self, event: ListView.Selected) -> None:
            """Enter on a row runs it or opens its prompt."""
            item = event.item
            if isinstance(item, CommandItem):
                self._activate(item.command)

        def on_key(self, event) -> None:
            """Move the highlight while focus is still in the search box."""
            if self.mode == "form":
                return
            focused = self.focused
            in_search = isinstance(focused, Input) and focused.id == "search"
            if not in_search:
                return
            if event.key == "up":
                self.action_move_up()
                event.stop()
            elif event.key == "down":
                self.action_move_down()
                event.stop()

        def action_back(self) -> None:
            """Leave a prompt, or quit from the picker."""
            if self.mode != "search":
                self.mode = "search"
                self.query_one("#form").display = False
                self.query_one("#body").display = True
                self._apply_query(self.query_one("#search", Input).value)
                self.query_one("#search", Input).focus()
                return
            self.exit()

        def action_toggle_hidden(self) -> None:
            """Show or hide ``# launcher-hidden`` commands."""
            self.show_hidden = not self.show_hidden
            search = self.query_one("#search", Input)
            if self.show_hidden:
                search.placeholder = "Search commands (showing hidden)..."
            else:
                search.placeholder = "Search — git:, life-ops:, docker:, network:"
            if self.mode == "search":
                self._apply_query(search.value)

        def action_toggle_favorite(self) -> None:
            """Favorite the highlighted command."""
            if self.mode != "search" or self._highlighted is None:
                return
            name = self._highlighted.record_name or self._highlighted.name
            self.usage.toggle(name)
            self._apply_query(self.query_one("#search", Input).value)

        def action_focus_list(self) -> None:
            """Focus the list."""
            self.query_one("#command_list", ListView).focus()

        def action_focus_search(self) -> None:
            """Focus the search box."""
            self.query_one("#search", Input).focus()

        def action_move_up(self) -> None:
            """Move the highlight up."""
            list_view = self.query_one("#command_list", ListView)
            if not list_view.children:
                return
            current = list_view.index if list_view.index is not None else 0
            if current > 0:
                list_view.index = current - 1

        def action_move_down(self) -> None:
            """Move the highlight down."""
            list_view = self.query_one("#command_list", ListView)
            if not list_view.children:
                return
            current = list_view.index if list_view.index is not None else 0
            if current < len(list_view.children) - 1:
                list_view.index = current + 1

        def _apply_query(self, query: str) -> None:
            self.filtered_commands = filter_commands(
                self.commands,
                query,
                show_hidden=self.show_hidden,
                favorites=self.usage.favorites,
                recent=self.usage.recent,
            )
            self._populate_list()

        def _populate_list(self) -> None:
            list_view = self.query_one("#command_list", ListView)
            list_view.clear()
            favorites = set(self.usage.favorites)
            for cmd in self.filtered_commands:
                name = cmd.record_name or cmd.name
                list_view.append(CommandItem(cmd, favorite=name in favorites))
            if self.filtered_commands:
                list_view.index = 0
                self._highlighted = self.filtered_commands[0]
                self._show_preview(self._highlighted)
            else:
                self._highlighted = None
                self._show_preview(None)

        def _show_preview(self, command: Command | None) -> None:
            favorite = False
            if command is not None and self.mode == "search":
                name = command.record_name or command.name
                favorite = name in self.usage.favorites
            self.preview_text = preview_text(command, favorite=favorite)
            self.query_one("#preview", Static).update(self.preview_text)

        def _activate(self, command: Command | None) -> None:
            if command is None or self.mode == "form":
                return
            if command.action and self.mode == "search":
                self._open_action(command)
                return
            self._finish(command, command.raw_command)

        def _open_action(self, command: Command) -> None:
            spec = ACTIONS[command.action]
            if spec.kind == "none":
                self._finish(command, wrap_host(command.host, command.name))
                return
            if spec.kind == "projects":
                self._open_projects(command)
                return
            self.mode = "form"
            self._pending = command
            form = self.query_one("#form", Vertical)
            form.remove_children()
            intro = Static(
                f"{command.name}   host: {command.host}\n"
                "Enter on the last field runs it. Esc goes back.",
                markup=False,
            )
            error = Static("", id="form_error", markup=False)
            fields: list = [intro, error]
            self._field_ids = []
            for key, label in spec.prompts:
                field_id = f"field-{key}"
                self._field_ids.append(field_id)
                fields.append(Label(label))
                fields.append(Input(placeholder=label, id=field_id))
            form.mount(*fields)
            self.query_one("#body").display = False
            form.display = True

            def focus_first() -> None:
                if self._field_ids:
                    self.query_one(f"#{self._field_ids[0]}", Input).focus()

            self.call_after_refresh(focus_first)

        def _open_projects(self, command: Command) -> None:
            self.mode = "projects"
            root = self.docker_root
            items = [
                Command(
                    name="(root)",
                    description="docker root",
                    command_type="action",
                    raw_command=f"cd {shlex.quote(str(root))}",
                    host="local",
                    category="docker",
                    record_name="cdd",
                )
            ]
            for name in docker_projects(root):
                path = root / name
                items.append(
                    Command(
                        name=name,
                        description="docker project",
                        command_type="action",
                        raw_command=f"cd {shlex.quote(str(path))}",
                        host="local",
                        category="docker",
                        record_name="cdd",
                    )
                )
            self.filtered_commands = items
            self._populate_list()
            self._show_preview(self._highlighted)
            if not docker_projects(root) and not root.is_dir():
                self.preview_text = f"No docker directory at {root}"
                self.query_one("#preview", Static).update(self.preview_text)

        def _advance_form(self, field_id: str) -> None:
            if field_id not in self._field_ids:
                return
            index = self._field_ids.index(field_id)
            if index < len(self._field_ids) - 1:
                nxt = self._field_ids[index + 1]
                self.query_one(f"#{nxt}", Input).focus()
                return
            self._submit_form()

        def _submit_form(self) -> None:
            if self._pending is None:
                return
            values = {}
            for field_id in self._field_ids:
                key = field_id.removeprefix("field-")
                values[key] = self.query_one(f"#{field_id}", Input).value
            try:
                rendered = render_action(
                    self._pending.action,
                    values,
                    self._pending.host,
                    self.docker_root,
                )
            except ActionError as exc:
                self.query_one("#form_error", Static).update(str(exc))
                return
            self._finish(self._pending, rendered)

        def _finish(self, command: Command, rendered: str) -> None:
            self.usage.remember(command.record_name or command.name)
            self.command_to_execute = rendered
            self.exit()

    return LauncherApp


def launch_tui(
    commands: list[Command], usage: UsageStore, docker_root: Path
) -> str | None:
    """Run the picker. Returns the command to eval, or None if cancelled."""
    app_cls = build_launcher_app()
    if app_cls is None:
        raise TextualMissing()
    app = app_cls(commands, usage, docker_root)
    app.run()
    return app.command_to_execute


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI for the shell wrapper and for direct use."""
    parser = argparse.ArgumentParser(prog="l", description="Command launcher")
    parser.add_argument(
        "--cmd-file",
        help="Write the chosen command here for the shell to eval",
    )
    parser.add_argument(
        "--cabbie",
        action="store_true",
        help="Send the remaining text to cabbie",
    )
    parser.add_argument("words", nargs="*", help="Non-TUI command and arguments")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Parse zsh, then open the TUI or resolve a non-interactive command."""
    args = parse_args(argv)
    opts = load_opts()
    root = Path(__file__).resolve().parent
    files = discover_sources(root, opts)
    parser = ZshParser(files, opts)
    try:
        commands = parser.parse()
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    docker_root = Path.home() / "git" / "docker"
    if args.cabbie or args.words:
        try:
            command = resolve_invocation(
                args.words,
                commands,
                cabbie=args.cabbie,
                docker_root=docker_root,
            )
        except (ActionError, NoMatch) as exc:
            print(exc, file=sys.stderr)
            return 1
        deliver(command, args.cmd_file)
        return 0

    if not any(not cmd.hidden for cmd in commands):
        print("No commands found in zsh file", file=sys.stderr)
        return 1

    try:
        chosen = launch_tui(commands, UsageStore(), docker_root)
    except TextualMissing:
        return 1
    if chosen:
        deliver(chosen, args.cmd_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
