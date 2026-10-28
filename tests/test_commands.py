import importlib.machinery
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "plugins/base/scripts" / name))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


renamer = load("renamer")
catalog = load("dotcommands")


class PythonRunnerTests(unittest.TestCase):
    def run_runner(self, environment):
        runner = ROOT / "plugins/base/lib/python-launcher.bash"
        script = ROOT / "plugins/base/scripts/renamer"
        return subprocess.run(["/bin/bash", "-c", 'source "$1"; _dotfiles_python_run "$2" --help',
                               "runner-test", str(runner), str(script)],
                              env=environment, capture_output=True, text=True)

    def test_explicit_runner_and_invalid_override(self):
        environment = {**os.environ, "DOTFILES_PYTHON": sys.executable}
        result = self.run_runner(environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: renamer", result.stdout)
        environment["DOTFILES_PYTHON"] = "/does/not/exist"
        result = self.run_runner(environment)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DOTFILES_PYTHON", result.stderr)

    def test_selects_versioned_python_if_default_is_too_old(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            old = directory / "python3"
            old.write_text("#!/bin/sh\nexit 1\n")
            old.chmod(0o755)
            (directory / "python3.12").symlink_to(sys.executable)
            environment = {**os.environ, "PATH": temp}
            environment.pop("DOTFILES_PYTHON", None)
            result = self.run_runner(environment)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("usage: renamer", result.stdout)
            runner = ROOT / "plugins/base/lib/python-launcher.bash"
            script = ROOT / "plugins/base/scripts/renamer"
            shell = 'source "$1"; before="$PATH"; _dotfiles_python_run "$2" --help >/dev/null || exit; [[ "$PATH" == "$before" ]] || exit 2; command -v python3'
            result = subprocess.run(["/bin/bash", "-c", shell, "runner-test", str(runner), str(script)],
                                    env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), str(old))


class RenameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def file(self, name):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        return path

    def test_regex_syntax_colors(self):
        self.assertEqual(renamer.regex_colors("*.md"), ["error", "syntax", "plain", "plain"])
        self.assertEqual(renamer.regex_colors(r".*\.md$"), ["syntax", "syntax", "escape", "escape", "plain", "plain", "syntax"])
        self.assertEqual(renamer.regex_colors("(abc"), ["error", "plain", "plain", "plain"])
        self.assertEqual(renamer.regex_colors("abc)"), ["plain", "plain", "plain", "error"])
        self.assertEqual(renamer.regex_colors("[abc"), ["error", "plain", "plain", "plain"])
        self.assertEqual(renamer.regex_colors(r"\*"), ["escape", "escape"])
        self.assertEqual(renamer.regex_colors("(?:a)+"), ["syntax", "syntax", "plain", "plain", "syntax", "syntax"])

    def test_option_persistence_and_invalid_state(self):
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root)}):
            options, error = renamer.load_options()
            self.assertEqual(options, renamer.OPTION_DEFAULTS)
            self.assertFalse(error)
            options.update(hidden=False, links=False, follow=True, protect=True)
            self.assertFalse(renamer.save_options(options))
            self.assertEqual(renamer.load_options(), (options, ""))
            renamer.options_path().write_text('{"hidden": "false"}')
            options, error = renamer.load_options()
            self.assertEqual(options, renamer.OPTION_DEFAULTS)
            self.assertIn("hidden", error)
            with mock.patch.object(renamer.os, "replace", side_effect=OSError("denied")):
                self.assertIn("denied", renamer.save_options(options))
            self.assertEqual(list(renamer.options_path().parent.glob(".options-*")), [])

    def test_options_menu_navigation_and_save(self):
        screen = mock.Mock()
        screen.getmaxyx.return_value = (24, 80)
        menu = mock.Mock()
        menu.get_wch.side_effect = [renamer.curses.KEY_DOWN, " ", renamer.curses.KEY_UP, " ", "q"]
        with mock.patch.object(renamer.curses, "newwin", return_value=menu), mock.patch.object(renamer, "save_options", return_value="") as save:
            options, error = renamer.options_menu(screen, renamer.OPTION_DEFAULTS.copy())
        self.assertFalse(error)
        self.assertFalse(options["hidden"])
        self.assertFalse(options["links"])
        self.assertEqual(save.call_count, 2)
        screen.getmaxyx.return_value = (8, 20)
        self.assertIn("too small", renamer.options_menu(screen, options)[1])

    def test_rename_match_colors(self):
        pattern = r"(foo)(bar)"
        self.assertEqual(renamer.rename_colors(pattern), ["group0"] * 5 + ["group1"] * 5)
        self.assertEqual(renamer.match_colors(re.compile(pattern), "xfoobar!"), ["plain"] + ["group0"] * 3 + ["group1"] * 3 + ["plain"])
        self.assertEqual(renamer.match_colors(re.compile(r"(a(b))"), "ab"), ["group0", "group1"])
        self.assertEqual(renamer.match_colors(re.compile(r"x"), "x-x"), ["match", "plain", "match"])
        self.assertEqual(renamer.match_colors(re.compile(""), "abc"), ["plain"] * 3)
        self.assertEqual(renamer.rename_colors("*.md")[0], "error")
        self.assertEqual(renamer.filename_match_colors(re.compile(r"(foo)|\.cpp"), "foo/foo.cpp"), ["plain"] * 4 + ["group0"] * 3 + ["match"] * 4)
        self.assertEqual(renamer.filename_match_colors(re.compile(r"(foo)|\.cpp"), "foo/foo.cpp", True), ["plain"] * 4 + ["group0"] * 3 + ["plain"] * 4)

    def test_replacement_group_colors(self):
        regex = re.compile(r"(foo)(bar)?")
        self.assertEqual(renamer.replacement_colors("$2-$$-$1-$3", regex), ["group1"] * 2 + ["changed"] * 4 + ["group0"] * 2 + ["changed"] + ["error"] * 2)
        self.assertEqual(renamer.reconstructed_colors(regex, "$2-$1", "dir/foobar.cpp", True), ["plain"] * 4 + ["group1"] * 3 + ["plain"] + ["group0"] * 3 + ["plain"] * 4)
        self.assertEqual(renamer.reconstructed_colors(regex, "$2-$1", "foo_foo", False), ["plain"] + ["group0"] * 3 + ["plain"] * 2 + ["group0"] * 3)
        self.assertEqual(renamer.reconstructed_colors(regex, "$9", "foo"), ["plain"] * 3)

    def test_result_colors_highlight_changes_and_groups(self):
        regex = re.compile(r"(old)")
        self.assertEqual(renamer.result_colors(regex, "new", "dir/old.cpp", "dir/new.cpp"), ["plain"] * 4 + ["changed"] * 3 + ["unchanged"] * 4)
        self.assertEqual(renamer.result_colors(regex, "$1_new", "old.cpp", "old_new.cpp"), ["group0"] * 3 + ["changed"] * 4 + ["unchanged"] * 4)
        self.assertEqual(renamer.result_colors(regex, "", "old.cpp", "old.cpp"), ["unchanged"] * 7)

    def test_capture_hints_choose_most_populated_groups(self):
        first, second = self.file("a"), self.file("ab.txt")
        rows = [(first, first, "a"), (second, second, "ab.txt")]
        self.assertEqual(renamer.capture_hints(re.compile(r"(a)(b)?"), rows), ("ab.txt", ("a", "b")))
        self.assertEqual(renamer.capture_hints(re.compile(r"(a)(b)(\.txt)?"), rows, True), ("ab.txt", ("a", "b", None)))
        self.assertEqual(renamer.capture_hints(re.compile(r"(a)+"), rows), ("a", ("a",)))
        self.assertIsNone(renamer.capture_hints(re.compile("a"), rows))

    def test_preview_groups_filter_and_extension(self):
        source = self.file("src/foo_old.cpp")
        self.file("src/foo_old.h")
        candidates, errors = renamer.collect([str(self.root)])
        self.assertFalse(errors)
        moves, errors = renamer.preview(candidates, r"\.cpp$", r"_(\w+)(\.cpp)$", r"_translator$2")
        self.assertFalse(errors)
        self.assertEqual(moves[0][1], source.with_name("foo_translator.cpp"))
        moves, _ = renamer.preview(candidates, r"\.cpp$", "old", "new", True)
        self.assertEqual(moves[0][1].name, "foo_new.cpp")
        self.assertTrue(renamer.preview(candidates, "", "(x)", "$2")[1])
        self.assertEqual(renamer.replacement_template("$$$1", __import__("re").compile("(x)")), r"$\g<1>")

    def test_replace_only_matches_including_extensions(self):
        source = self.file("old_file.cpp")
        candidates = [(source, source.name)]
        rows, errors = renamer.preview(candidates, "", r"\.cpp$", ".h")
        self.assertFalse(errors)
        self.assertEqual(rows[0][1].name, "old_file.h")
        rows, _ = renamer.preview(candidates, "", r"\.cpp$", ".h", True)
        self.assertEqual(rows[0][1].name, "old_file.cpp")
        rows, _ = renamer.preview(candidates, "", r"old", "new")
        self.assertEqual(rows[0][1].name, "new_file.cpp")
        rows, _ = renamer.preview(candidates, "", r"(old)", "$1_new")
        self.assertEqual(rows[0][1].name, "old_new_file.cpp")

    def test_preview_includes_unchanged_filtered_files(self):
        cpp = self.file("file.cpp")
        header = self.file("file.h")
        candidates, _ = renamer.collect([str(self.root)])
        rows, errors = renamer.preview(candidates, "", "", "")
        self.assertFalse(errors)
        self.assertEqual({(source, target) for source, target, _ in rows}, {(cpp, cpp), (header, header)})
        rows, _ = renamer.preview(candidates, r"\.cpp$", "missing", "new")
        self.assertEqual([(source, target) for source, target, _ in rows], [(cpp, cpp)])
        rows, errors = renamer.preview(candidates, r"\.cpp$", "(", "")
        self.assertTrue(errors)
        self.assertEqual([(source, target) for source, target, _ in rows], [(cpp, cpp)])
        rows, errors = renamer.preview(candidates, r"\.cpp$", r"\.cpp$", "")
        self.assertFalse(errors)
        self.assertEqual([(source, target) for source, target, _ in rows], [(cpp, cpp)])
        self.assertEqual(renamer.reconstructed_colors(re.compile(r"\.cpp$"), "", "file.cpp"), ["plain"] * 8)

    def test_links_hidden_and_loops(self):
        self.file(".secret")
        self.file("dir/file")
        (self.root / "dir/loop").symlink_to(self.root, target_is_directory=True)
        candidates, errors = renamer.collect([str(self.root)], hidden=False, links=False, follow=True)
        self.assertFalse(errors)
        self.assertEqual([item[1] for item in candidates], ["dir/file"])
        candidates, _ = renamer.collect([str(self.root / "dir" / "*")])
        self.assertEqual({p.name for p, _ in candidates}, {"file", "loop"})

    def test_conflicts_and_swap(self):
        a, b = self.file("a"), self.file("b")
        moves = [(a, b, "a"), (b, a, "b")]
        self.assertEqual(renamer.conflicts(moves), set())
        self.assertIsNone(renamer.apply_moves(moves))
        self.assertEqual(a.read_text(), "b")
        self.assertEqual(b.read_text(), "a")
        c = self.file("c")
        self.assertEqual(renamer.conflicts([(a, c, "a"), (b, a, "b")]), {a, b})

    def test_rollback_if_destination_appears(self):
        a, b = self.file("a"), self.file("b")
        error = renamer.apply_moves([(a, b, "a")])
        self.assertIsNotNone(error)
        self.assertEqual(a.read_text(), "a")
        self.assertEqual(b.read_text(), "b")

    def test_interrupt_rolls_back_staged_files(self):
        source = self.file("a")
        with mock.patch.object(renamer.os, "link", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                renamer.apply_moves([(source, self.root / "b", "a")])
        self.assertEqual(source.read_text(), "a")
        self.assertFalse((self.root / "b").exists())


class CatalogTests(unittest.TestCase):
    def test_format_multiline_descriptions_and_usage(self):
        entries = [{"plugin": "base", "name": "cdr", "usage": "cdr [directory]", "type": "function", "description": "First line\nSecond line", "available": True},
                   {"plugin": "base", "name": "tool", "type": "script", "description": "Other", "available": True}]
        lines = catalog.format_entries(entries, 100).splitlines()
        cdr = next(line for line in lines if "cdr" in line)
        second = next(line for line in lines if "Second line" in line)
        tool = next(line for line in lines if "Other" in line)
        self.assertEqual(cdr.index("First line"), second.index("Second line"))
        self.assertEqual(cdr.index("First line"), tool.index("Other"))
        self.assertIn(" |  ", cdr)
        self.assertIn("Usage: cdr [directory]", "\n".join(lines))
        self.assertNotIn("Usage: cdr [directory]", catalog.format_entries(entries, 100, show_usage=False))

    def test_pager_only_for_interactive_output(self):
        stdout, stdin = mock.Mock(), mock.Mock()
        stdout.isatty.return_value = True
        stdin.isatty.return_value = True
        with mock.patch.object(catalog.sys, "stdout", stdout), mock.patch.object(catalog.sys, "stdin", stdin), mock.patch.object(catalog.shutil, "which", return_value="/usr/bin/less"), mock.patch.object(catalog.subprocess, "run") as run:
            catalog.print_catalog("hello\n")
            self.assertEqual(run.call_args.args[0], ["/usr/bin/less"])
            self.assertEqual(run.call_args.kwargs["input"], "hello\n")
            stdout.isatty.return_value = False
            catalog.print_catalog("hello\n")
            stdout.write.assert_called_once_with("hello\n")
            self.assertEqual(run.call_count, 1)

    def test_category_flags_and_json(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plugin = root / "plugins/base"
            plugin.mkdir(parents=True)
            (plugin / "commands.json").write_text(json.dumps([
                {"name": "script", "type": "script"}, {"name": "command"},
                {"name": "alias", "type": "alias"}, {"name": "function", "type": "function"},
                {"name": "custom", "type": "custom"},
            ]))
            def listed(*flags):
                result = subprocess.run([str(ROOT / "plugins/base/scripts/dotcommands"), "--json", "-u", *flags],
                                        env={**os.environ, "DOTFILES_ROOT": str(root)},
                                        check=True, capture_output=True, text=True)
                return {entry["name"] for entry in json.loads(result.stdout)}
            self.assertEqual(listed(), {"script", "command", "function"})
            self.assertEqual(listed("-a"), {"script", "command", "function", "alias"})
            self.assertEqual(listed("-f", "-t", "custom"), {"script", "command", "custom"})
            self.assertEqual(listed("-s"), {"command", "function"})
            self.assertEqual(listed("-A", "-fs"), {"command", "alias", "custom"})
            self.assertEqual(listed("-A"), {"script", "command", "alias", "function", "custom"})

    def test_availability_hooks_shell_and_disabled_plugins(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plugin = root / "plugins/example"
            (plugin / "scripts").mkdir(parents=True)
            script = plugin / "scripts/tool"
            script.write_text("#!/bin/sh\n")
            script.chmod(0o755)
            script_entry = {"name": "tool", "type": "script", "plugin": "example", "plugin_enabled": True}
            function_entry = {"name": "fun", "type": "function", "plugin": "example", "plugin_enabled": True}
            with mock.patch.dict(os.environ, {"PATH": str(script.parent), "DOTCOMMANDS_BASH_FUNCTIONS": "declare -f fun", "DOTCOMMANDS_BASH_ALIASES": "alias shortcut='fun'"}):
                self.assertTrue(catalog.availability(script_entry, root)[0])
                self.assertTrue(catalog.availability(function_entry, root)[0])
                self.assertTrue(catalog.availability({**function_entry, "name": "shortcut", "type": "alias"}, root)[0])
                self.assertFalse(catalog.availability({**function_entry, "name": "missing"}, root)[0])
                hook = plugin / "commands-status"
                hook.write_text("#!/bin/sh\ncase \"$1\" in tool) echo 'not active'; exit 1;; fun) exit 0;; *) exit 3;; esac\n")
                hook.chmod(0o755)
                self.assertEqual(catalog.availability(script_entry, root), (False, "not active"))
                self.assertTrue(catalog.availability(function_entry, root)[0])
                self.assertTrue(catalog.availability({**function_entry, "name": "shortcut", "type": "alias"}, root)[0])
                self.assertEqual(catalog.availability({**script_entry, "plugin_enabled": False}, root), (False, "plugin disabled"))
                hook.write_text("#!/bin/sh\nexit 2\n")
                with mock.patch("sys.stderr"):
                    self.assertEqual(catalog.availability(script_entry, root), (False, "availability hook failed"))

    def test_unavailable_output_and_disabled_discovery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plugin = root / "plugins/disabled"
            plugin.mkdir(parents=True)
            (plugin / "commands.json").write_text('[{"name":"not-installed", "type":"script"}]')
            (root / "generated").mkdir()
            (root / "generated/.disabled_plugins").write_text("disabled\n")
            env = {**os.environ, "DOTFILES_ROOT": str(root)}
            command = [str(ROOT / "plugins/base/scripts/dotcommands"), "--json"]
            self.assertEqual(json.loads(subprocess.run(command, env=env, check=True, capture_output=True, text=True).stdout), [])
            output = json.loads(subprocess.run(command + ["-u"], env=env, check=True, capture_output=True, text=True).stdout)
            self.assertFalse(output[0]["available"])
            self.assertEqual(output[0]["availability_reason"], "plugin disabled")

    def test_enabled_plugins_and_base_discovery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / "plugins/base"
            (base / "bash").mkdir(parents=True)
            (base / "scripts").mkdir()
            (base / "bash/alias.bash").write_text("alias hi='hello'\n")
            script = base / "scripts/tool"
            script.write_text("#!/bin/sh\n# Tool description\n")
            script.chmod(0o755)
            (base / "commands.json").write_text(json.dumps([{"name": "hi", "description": "Greeting"}]))
            plugin = root / "plugins/extra"
            plugin.mkdir()
            (plugin / "commands.json").write_text('[{"name":"extra-tool"}]')
            entries = catalog.discover(root)
            self.assertEqual({e["name"] for e in entries}, {"hi", "tool", "extra-tool"})
            self.assertEqual(next(e for e in entries if e["name"] == "hi")["description"], "Greeting")
            (root / "generated").mkdir()
            (root / "generated/.disabled_plugins").write_text("extra\n")
            self.assertNotIn("extra-tool", {e["name"] for e in catalog.discover(root)})


if __name__ == "__main__":
    unittest.main()
