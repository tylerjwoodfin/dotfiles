#!/usr/bin/env python3
"""
Interactive TUI launcher for zsh functions and aliases.
Parses common.zsh and provides fuzzy search functionality.
"""

import os
import re
import subprocess
import sys
import pickle
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import Header, Footer, Input, Static, ListView, ListItem, Label
    from textual.binding import Binding
    from textual.message import Message
except ImportError:
    print("Error: textual library not found. Install with: pip install textual")
    sys.exit(1)

try:
    from fuzzywuzzy import fuzz, process
except ImportError:
    print("Error: fuzzywuzzy library not found. Install with: pip install fuzzywuzzy")
    sys.exit(1)


@dataclass
class Command:
    """Represents a command (function or alias) with its description."""
    name: str
    description: str
    command_type: str  # 'function' or 'alias'
    raw_command: str  # The original command string for execution


class ZshParser:
    """Parses zsh files to extract functions, aliases, and their descriptions."""
    
    def __init__(self, zsh_file_path: str):
        self.zsh_file_path = Path(zsh_file_path)
        self.commands: List[Command] = []
        self.cache_file = Path.home() / '.cache' / 'launcher_cache.pkl'
        
    def parse(self) -> List[Command]:
        if not self.zsh_file_path.exists():
            raise FileNotFoundError(f"Zsh file not found: {self.zsh_file_path}")
        
        # 🔴 Disable cache while debugging
        # if self._load_cache():
        #     return self.commands
        
        with open(self.zsh_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self._parse_functions(content)
        self._parse_aliases(content)

        self.commands.sort(key=lambda x: x.name)

        # self._save_cache()   # disable saving too while debugging

        return self.commands
    
    def _load_cache(self) -> bool:
        """Load commands from cache if valid."""
        try:
            if not self.cache_file.exists():
                return False
                
            # Check if cache is newer than zsh file
            cache_time = self.cache_file.stat().st_mtime
            zsh_time = self.zsh_file_path.stat().st_mtime
            
            if cache_time < zsh_time:
                return False
                
            with open(self.cache_file, 'rb') as f:
                self.commands = pickle.load(f)
            return True
        except Exception:
            return False
    
    def _save_cache(self):
        """Save commands to cache."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.commands, f)
        except Exception:
            pass  # Ignore cache errors
    
    def _parse_functions(self, content: str):
        """Parse function definitions and their comments."""
        # Pattern to match function definitions with optional comments
        function_pattern = r'(?:^#\s*(.+)\s*$)?\s*(?:function\s+)?(\w+)\s*\(\s*\)\s*\{'
        
        for match in re.finditer(function_pattern, content, re.MULTILINE):
            comment = match.group(1) or ""
            func_name = match.group(2)
            
            # Skip the launcher function itself
            if func_name == 'l':
                continue
                
            # Extract the function body
            start_pos = match.end()
            brace_count = 1
            end_pos = start_pos
            
            while end_pos < len(content) and brace_count > 0:
                if content[end_pos] == '{':
                    brace_count += 1
                elif content[end_pos] == '}':
                    brace_count -= 1
                end_pos += 1
            
            if brace_count == 0:
                func_body = content[start_pos:end_pos-1].strip()
                description = comment.strip()
                
                # Skip functions with launcher-hidden or launcher-hide description
                if description in ["launcher-hidden", "launcher-hide"]:
                    continue
                    
                self.commands.append(Command(
                    name=func_name,
                    description=description,
                    command_type='function',
                    raw_command=func_name
                ))
    
    def _parse_aliases(self, content: str):
        lines = content.splitlines()
        debug_path = Path.home() / "test.md"
        with open(debug_path, "w", encoding="utf-8") as dbg:
            dbg.write("# Alias Debug Output\n\n")

            for line in lines:
                if not line.strip().startswith("alias "):
                    continue
                if "=" not in line:
                    continue

                dbg.write(f"RAW: {line}\n")

                alias_def, alias_rest = line.split("=", 1)
                alias_name = alias_def.replace("alias", "").strip()
                if alias_name == "l":
                    continue

                # Default values
                comment_inline = ""
                alias_value = alias_rest.strip()

                # Split off inline comment if present
                if "#" in alias_rest:
                    alias_value, comment_inline = alias_rest.split("#", 1)
                    alias_value = alias_value.strip()
                    comment_inline = comment_inline.strip()

                # Strip quotes around alias value
                if alias_value.startswith(("'", '"')) and alias_value.endswith(("'", '"')):
                    alias_value = alias_value[1:-1]

                description = comment_inline  # only inline

                # Skip aliases with launcher-hidden or launcher-hide description
                if description in ["launcher-hidden", "launcher-hide"]:
                    continue

                dbg.write(f"  alias_name: {alias_name}\n")
                dbg.write(f"  alias_value: {alias_value}\n")
                dbg.write(f"  comment_inline: {comment_inline}\n")
                dbg.write(f"  description: {description}\n\n")

                self.commands.append(Command(
                    name=alias_name,
                    description=description,
                    command_type="alias",
                    raw_command=alias_value
                ))


class CommandItem(ListItem):
    """A list item representing a command."""
    
    def __init__(self, command: Command):
        self.command = command
        super().__init__()
    
    def compose(self):
        yield Label(f"{self.command.name} - {self.command.description or 'No description'}")


class LauncherApp(App):
    """Interactive TUI launcher for commands using Textual."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("ctrl+j", "focus_list", "Focus List"),
        Binding("ctrl+k", "focus_search", "Focus Search"),
    ]
    
    def __init__(self, commands: List[Command], zsh_file_path: str):
        super().__init__()
        self.commands = commands
        self.zsh_file_path = zsh_file_path
        self.filtered_commands = commands.copy()
        
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(
            Input(placeholder="Search commands...", id="search"),
            ListView(id="command_list"),
            id="main"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self._populate_list()
        # Focus the search input so user can immediately type
        search_input = self.query_one("#search", Input)
        search_input.focus()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Called when the search input changes."""
        if event.input.id == "search":
            self._filter_commands(event.value)
    
    def on_key(self, event) -> None:
        """Handle global key events."""
        # Handle arrow keys globally
        if event.key == "up":
            self.action_move_up()
        elif event.key == "down":
            self.action_move_down()
        elif event.key == "enter":
            # If we're in the search input, execute the first command
            if isinstance(self.focused, Input):
                self.action_execute_first()
            else:
                # Otherwise execute the currently selected item
                self.action_select_item()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Called when a list item is selected."""
        # Don't auto-execute commands on selection
        # Commands should only be executed when user presses Enter
        pass
    
    def action_move_up(self) -> None:
        """Move selection up."""
        list_view = self.query_one("#command_list", ListView)
        current_index = list_view.index or 0
        if current_index > 0:
            list_view.index = current_index - 1
    
    def action_move_down(self) -> None:
        """Move selection down."""
        list_view = self.query_one("#command_list", ListView)
        current_index = list_view.index or 0
        max_index = len(list_view.children) - 1
        if current_index < max_index:
            list_view.index = current_index + 1
    
    def action_select_item(self) -> None:
        """Select the current item."""
        list_view = self.query_one("#command_list", ListView)
        current_index = list_view.index or 0
        if current_index < len(list_view.children):
            selected_item = list_view.children[current_index]
            if hasattr(selected_item, 'command'):
                self._execute_command(selected_item.command)
    
    def action_focus_list(self) -> None:
        """Focus the list view."""
        list_view = self.query_one("#command_list", ListView)
        list_view.focus()
    
    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search", Input)
        search_input.focus()
    
    def action_execute_first(self) -> None:
        """Execute the first command in the filtered list."""
        if self.filtered_commands:
            first_command = self.filtered_commands[0]
            self._execute_command(first_command)
    
    def _populate_list(self):
        """Populate the list with commands."""
        list_view = self.query_one("#command_list", ListView)
        list_view.clear()
        
        for cmd in self.filtered_commands:  # Show all commands
            item = CommandItem(cmd)
            list_view.append(item)
        
        # Don't auto-select the first item to prevent automatic execution
        list_view.index = None
    
    def _filter_commands(self, query: str):
        """Filter commands based on query."""
        if not query:
            self.filtered_commands = self.commands.copy()
        else:
            # Use optimized fuzzy matching
            query_lower = query.lower()
            
            # First try exact substring matches for speed
            exact_matches = []
            for cmd in self.commands:
                if query_lower in cmd.name.lower() or query_lower in cmd.description.lower():
                    exact_matches.append(cmd)
            
            if exact_matches:
                self.filtered_commands = exact_matches
            else:
                # Fall back to fuzzy matching for partial matches
                # Create a list of command names for fuzzy matching
                command_names = [cmd.name for cmd in self.commands]
                matches = process.extract(
                    query,
                    command_names,
                    scorer=fuzz.ratio,
                    limit=10
                )
                
                # Extract command names from matches
                matched_names = [match[0] for match in matches if match[1] > 30]
                
                self.filtered_commands = [
                    cmd for cmd in self.commands 
                    if cmd.name in matched_names
                ]
        
        self._populate_list()
    
    def _execute_command(self, command: Command):
        """Show a fake terminal with the command."""
        print(f"DEBUG: Executing command: {command.name} = {command.raw_command}")
        # Store the command to show in fake terminal
        self._command_to_execute = command.raw_command
        
        # Exit the launcher
        self.exit()


class FakeTerminalApp(App):
    """A fake terminal app that shows an editable command."""
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Cancel"),
        Binding("escape", "quit", "Cancel"),
    ]
    
    def __init__(self, initial_command: str, zsh_file_path: str):
        super().__init__()
        self.initial_command = initial_command
        self.zsh_file_path = zsh_file_path
        
    def compose(self) -> ComposeResult:
        """Create the fake terminal interface."""
        yield Header()
        yield Container(
            Static("Command-", id="prompt"),
            Input(value=self.initial_command, id="command_input"),
            Static("Enter to execute", id="instructions"),
            id="terminal"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the fake terminal starts."""
        # Focus the input field
        input_field = self.query_one("#command_input", Input)
        input_field.focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Called when Enter is pressed in the input field."""
        if event.input.id == "command_input":
            self._execute_command(event.value)
    
    def _execute_command(self, command: str):
        """Execute the command and exit."""
        # Store the command to execute after the app exits
        self._command_to_execute = command
        self._zsh_file = self.zsh_file_path
        
        # Exit the fake terminal
        self.exit()


class Launcher:
    """Wrapper class for the Textual app."""
    
    def __init__(self, commands: List[Command], zsh_file_path: str):
        self.commands = commands
        self.zsh_file_path = zsh_file_path
        
    def run(self, command_file=None):
        """Run the interactive launcher."""
        app = LauncherApp(self.commands, self.zsh_file_path)
        app.run()
        
        # Handle command execution based on how we're called
        if hasattr(app, '_command_to_execute'):
            if command_file:
                # Being called from shell function, write command to file
                with open(command_file, 'w') as f:
                    f.write(app._command_to_execute)
            else:
                # Being called directly, execute the command
                self._execute_command_directly(app._command_to_execute)
    
    def _show_fake_terminal(self, command: str):
        """Show a fake terminal with the command ready to execute."""
        # Create and run a fake terminal app
        fake_terminal = FakeTerminalApp(command, self.zsh_file_path)
        fake_terminal.run()
        
        # Output the command for the shell function to execute
        if hasattr(fake_terminal, '_command_to_execute'):
            # Just output the command - the shell function will execute it
            print(fake_terminal._command_to_execute)
    
    def _execute_command_directly(self, command: str):
        """Execute the command directly in the current shell context."""
        try:
            print(f"\nExecuting: {command}")
            print("-" * 40)
            
            # Execute the command using subprocess with shell=True to maintain shell context
            import subprocess
            result = subprocess.run(
                command,
                shell=True,
                executable='/bin/zsh',  # Use zsh as the shell
                cwd=os.getcwd()  # Start from current directory
            )
            
            # If it's a directory change command, we need to handle it specially
            if command.startswith('cd '):
                # For cd commands, we need to change to the target directory
                target_dir = command[3:].strip()
                # Expand ~ and other shell variables
                expanded_dir = os.path.expanduser(target_dir)
                expanded_dir = os.path.expandvars(expanded_dir)
                if os.path.exists(expanded_dir):
                    os.chdir(expanded_dir)
                    print(f"Changed to directory: {expanded_dir}")
                else:
                    print(f"Directory not found: {expanded_dir}")
            
        except Exception as e:
            print(f"\nError: {e}")
    


def main():
    """Main entry point."""
    # Get the path to common.zsh
    script_dir = Path(__file__).parent
    zsh_file = script_dir / "zsh" / "common.zsh"
    
    if not zsh_file.exists():
        print(f"Error: {zsh_file} not found")
        sys.exit(1)
    
    try:
        # Parse the zsh file
        parser = ZshParser(str(zsh_file))
        commands = parser.parse()
        
        if not commands:
            print("No commands found in zsh file")
            sys.exit(1)
        
        # Create and run launcher
        launcher = Launcher(commands, str(zsh_file))
        # Check if a command file argument was provided
        command_file = sys.argv[1] if len(sys.argv) > 1 else None
        launcher.run(command_file)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
