"""Tests for the bundle's Python: the HTML converter and the two heading commands.

A bundle command is a program that reads environment variables and writes to
standard output, which makes it about as testable as anything gets. These run
the real scripts in a subprocess rather than importing them.

Run from the bundle's directory:

    "$TM_PYTHON" Tests/python_commands_tests.py
"""

import os
import plistlib
import subprocess
import sys
import unittest

BUNDLE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HTML2TEXT = os.path.join(BUNDLE, "Support/bin/html2text")


def command_script(name):
    """The script out of a command's property list."""
    with open(os.path.join(BUNDLE, "Commands", name), "rb") as plist:
        return plistlib.load(plist)["command"]


def run_heading_command(name, line):
    script = command_script(name)
    return subprocess.run(
        [sys.executable, "-c", script],
        env={**os.environ, "TM_CURRENT_LINE": line},
        capture_output=True,
        text=True,
        check=True,
    ).stdout


class HtmlToMarkdown(unittest.TestCase):
    def convert(self, html):
        return subprocess.run(
            [sys.executable, HTML2TEXT],
            input=html,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def test_a_heading_becomes_hashes(self):
        self.assertIn("# Title", self.convert("<h1>Title</h1>"))

    def test_a_link_keeps_its_target(self):
        self.assertIn("[here](https://example.com)", self.convert('<a href="https://example.com">here</a>'))

    def test_emphasis_survives(self):
        self.assertIn("**bold**", self.convert("<p>a <b>bold</b> word</p>"))

    def test_a_list_becomes_bullets(self):
        converted = self.convert("<ul><li>one</li><li>two</li></ul>")
        self.assertIn("one", converted)
        self.assertIn("two", converted)

    def test_long_lines_are_not_wrapped_since_the_editor_wraps(self):
        sentence = "word " * 60
        converted = self.convert("<p>%s</p>" % sentence)
        self.assertEqual(len([line for line in converted.split("\n") if line.strip()]), 1)

    def test_nothing_in_is_nothing_out(self):
        self.assertEqual(self.convert("").strip(), "")


class IncreaseHeadingLevel(unittest.TestCase):
    NAME = "Increase Heading Level.tmCommand"

    def test_a_heading_gains_a_hash(self):
        self.assertEqual(run_heading_command(self.NAME, "## Two"), "### Two")

    def test_a_closed_heading_stays_closed(self):
        self.assertEqual(run_heading_command(self.NAME, "## Two ##"), "### Two ###")

    def test_a_line_that_is_not_a_heading_is_left_alone(self):
        self.assertEqual(run_heading_command(self.NAME, "plain text"), "plain text")

    def test_five_hashes_is_as_deep_as_it_goes(self):
        self.assertEqual(run_heading_command(self.NAME, "###### Six"), "###### Six")


class DecreaseHeadingLevel(unittest.TestCase):
    NAME = "Decrease Heading Level.tmCommand"

    def test_a_heading_loses_a_hash(self):
        self.assertEqual(run_heading_command(self.NAME, "### Three"), "## Three")

    def test_a_closed_heading_stays_closed(self):
        self.assertEqual(run_heading_command(self.NAME, "### Three ###"), "## Three ##")

    def test_a_line_that_is_not_a_heading_is_left_alone(self):
        self.assertEqual(run_heading_command(self.NAME, "plain text"), "plain text")


if __name__ == "__main__":
    unittest.main(verbosity=2)
