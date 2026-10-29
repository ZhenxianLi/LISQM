"""Tests for the automated review: scripts/review_agent.py (without the API) and scripts/review_guard.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent / "scripts"))

import review_agent as RA  # noqa: E402
import review_guard as RG  # noqa: E402

ISSUE = """Automated review of 2026-11-01 ([workflow run](https://example.org/run)).

## Repository and package metadata

Routine changes (new commits, versions, releases) were committed without review.

1 item in the repository and package metadata to check:

- **SQAT** (`sqat`): GitHub release [v2.1](https://github.com/ggrecow/SQAT/releases/tag/v2.1) (2026-10-30)

## New candidates

### GitHub (2)

- [a/b](https://github.com/a/b) (Python, ★ 0): Loudness after ISO 532-1.
  Matched `"ISO 532"`.
- [c/d](https://github.com/c/d) (C, ★ 1): An audio codec.

## Standards

No changes in the watched standards (3 sources checked).
"""

PROJECT = """id: alpha
name: Alpha
standing: developing
summary: A project.
"""


def make_repo(folder: Path) -> Path:
    """A small git repository with the files the guard, the version bump and the system prompt read."""
    folder = folder / "repo"
    files = {name: f"# {name}\n" for name in RA.DOCUMENTS}
    files |= {
        "data/projects/alpha.yaml": PROJECT,
        "data/ignored.yaml": "- url: https://example.org/x\n  reason: no\n",
        "data/site.yaml": "name: LISQM\nversion: 0.5.10\n",
        "data/updates.yaml": "# Notes\n\n- date: 2026-10-27\n  title: \"Version 0.5.10: x\"\n  body: |\n    X.\n",
        "CITATION.cff": 'cff-version: 1.2.0\ndate-released: "2026-10-27"\nversion: "0.5.10"\n',
        "scripts/tool.py": "print(1)\n",
    }
    for rel, text in files.items():
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / rel).write_text(text, encoding="utf-8")
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.name=t", "-c", "user.email=t@example.org", "commit", "-q", "-m", "start"]):
        subprocess.run(["git", *args], cwd=folder, check=True, capture_output=True)
    return folder


class IssueAndToolsTest(unittest.TestCase):
    def test_items_of_the_issue(self) -> None:
        items = RA.split_items(ISSUE)
        self.assertEqual([s for s, _ in items], ["Repository and package metadata", "New candidates",
                                                 "New candidates"])
        self.assertTrue(items[0][1].startswith("**SQAT** (`sqat`)"))
        self.assertEqual(items[1][1].splitlines()[1], 'Matched `"ISO 532"`.')
        self.assertEqual(RA.split_items("## Links\n\nNo broken links.\n"), [])

    def test_input_validation(self) -> None:
        schema = RA.SCHEMAS["report_item"]
        self.assertIsNone(RA.invalid_input(schema, {"outcome": "changed", "summary": "s"}))
        self.assertIn("missing", RA.invalid_input(schema, {"outcome": "changed"}))
        self.assertIn("one of", RA.invalid_input(schema, {"outcome": "done", "summary": "s"}))
        self.assertIn("not a field", RA.invalid_input(schema, {"outcome": "changed", "summary": "s", "x": 1}))
        self.assertIn("integer", RA.invalid_input(RA.SCHEMAS["inspect_repository"],
                                                  {"url": "u", "action": "read", "start_line": True}))
        self.assertIsNone(RA.invalid_input(RA.SCHEMAS["check_data"], {}))

    def test_repository_urls(self) -> None:
        self.assertEqual(RA.clone_url("https://github.com/a/b/tree/main/src"), "https://github.com/a/b")
        self.assertEqual(RA.clone_url("https://github.com/a/b.git"), "https://github.com/a/b")
        self.assertEqual(RA.clone_url("https://git.code.sf.net/p/x/code"), "https://git.code.sf.net/p/x/code")
        for bad in ("http://github.com/a/b", "https://127.0.0.1/a/b", "https://user:pw@github.com/a/b",
                    "https://localhost/a", "https://github.com/a", "file:///etc", "https://intranet/a/b"):
            with self.assertRaises(RA.ToolError, msg=bad):
                RA.clone_url(bad)

    def test_editor_is_confined(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp))
            self.assertIn("alpha.yaml", RA.edit_file({"command": "view", "path": "data/projects"}, root))
            self.assertIn("1\tid: alpha", RA.edit_file({"command": "view", "path": "/data/projects/alpha.yaml"}, root))
            self.assertIn("print(1)", RA.edit_file({"command": "view", "path": "scripts/tool.py"}, root))
            for path in ("../outside.txt", ".git/config"):
                with self.assertRaises(RA.ToolError, msg=path):
                    RA.edit_file({"command": "view", "path": path}, root)
            with self.assertRaises(RA.ToolError):
                RA.edit_file({"command": "create", "path": "scripts/tool.py", "file_text": "x"}, root)
            with self.assertRaises(RA.ToolError):
                RA.edit_file({"command": "create", "path": "data/site.yaml", "file_text": "x"}, root)
            RA.edit_file({"command": "create", "path": "data/projects/beta.yaml", "file_text": "id: beta\n"}, root)
            self.assertTrue((root / "data/projects/beta.yaml").is_file())
            with self.assertRaises(RA.ToolError):  # "a" occurs more than once
                RA.edit_file({"command": "str_replace", "path": "data/projects/alpha.yaml", "old_str": "a",
                              "new_str": "b"}, root)
            RA.edit_file({"command": "str_replace", "path": "data/projects/alpha.yaml", "old_str": "A project.",
                          "new_str": "A library."}, root)
            RA.edit_file({"command": "insert", "path": "data/projects/alpha.yaml", "insert_line": 1,
                          "insert_text": "name_note: x"}, root)
            self.assertEqual((root / "data/projects/alpha.yaml").read_text().splitlines()[:2], ["id: alpha",
                                                                                                "name_note: x"])
            self.assertIn("A library.", (root / "data/projects/alpha.yaml").read_text())


class GuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, rel: str, text: str) -> None:
        (self.root / rel).write_text(text, encoding="utf-8")

    def test_allowed_changes_pass(self) -> None:
        self.write("data/projects/alpha.yaml", PROJECT + "checked: 2026-11-01\n")
        self.write("data/projects/gamma.yaml", "id: gamma\nstanding: newly-released\n")
        self.write("data/ignored.yaml", "- url: https://example.org/x\n  reason: no\n- url: https://e.org/y\n")
        self.assertEqual(RG.check(self.root), [])

    def test_owner_fields_and_files(self) -> None:
        self.write("data/projects/alpha.yaml", PROJECT.replace("developing", "established") + "rank: 1\n")
        self.write("data/projects/delta.yaml", "id: delta\nstanding: established\nhighlight: true\n")
        self.write("data/projects/eps.yaml", "id: other\n")
        self.write("scripts/tool.py", "print(2)\n")
        problems = "\n".join(RG.check(self.root))
        for text in ("alpha.yaml: standing is the owner's", "alpha.yaml: rank is the owner's",
                     "delta.yaml: highlight is the owner's to set", "delta.yaml: only the owner lists a new project "
                     "as established", "eps.yaml: id must be 'eps'", "scripts/tool.py: only data files"):
            self.assertIn(text, problems)

    def test_deletions_and_e_mail(self) -> None:
        (self.root / "data/ignored.yaml").unlink()
        self.write("data/projects/alpha.yaml", PROJECT + "maintainers: [someone@example.org]\n")
        problems = "\n".join(RG.check(self.root))
        self.assertIn("data/ignored.yaml: files are not deleted", problems)
        self.assertIn("e-mail address", problems)

    def test_version_and_update_note(self) -> None:
        report = {"date": "2026-11-01", "items": [{"public_note": "Added Gamma, a\nlibrary."}, {"public_note": None}]}
        self.write("data/ignored.yaml", "[]\n")
        self.assertIsNone(RG.finish(self.root, report))  # ignored.yaml alone does not show on the website
        self.write("data/projects/alpha.yaml", PROJECT + "checked: 2026-11-01\n")
        self.assertEqual(RG.finish(self.root, report), "0.5.11")
        self.assertIn("version: 0.5.11", (self.root / "data/site.yaml").read_text())
        cff = (self.root / "CITATION.cff").read_text()
        self.assertIn('version: "0.5.11"', cff)
        self.assertIn('date-released: "2026-11-01"', cff)
        updates = (self.root / "data/updates.yaml").read_text()
        self.assertTrue(updates.startswith("# Notes\n\n- date: 2026-11-01\n  title: \"Version 0.5.11: automated"))
        self.assertIn("    - Added Gamma, a library.\n", updates)
        self.assertLess(updates.index("0.5.11"), updates.index("0.5.10"))

    def test_comment(self) -> None:
        report = {"date": "2026-11-01", "model": RA.MODEL, "cost_usd": 3.456, "issue_body_sha256": "abc",
                  "items": [{"item": "[a/b](https://github.com/a/b)", "outcome": "changed", "summary": "Added. @x"},
                            {"item": "c/d", "outcome": "needs_owner", "summary": "Borderline.",
                             "question": "List it?"}]}
        text = RG.comment(report, "https://example.org/run")
        self.assertIn("1 of 2 items settled", text)
        self.assertIn("- [x] a/b (https://github.com/a/b): Added.", text)
        self.assertIn("**Question:** List it?", text)
        self.assertIn("@​x", text)  # no mention
        self.assertIn("estimated API cost $3.46", text)
        self.assertTrue(text.rstrip().endswith(RG.MARKER.format(sha="abc")))
        self.assertFalse(RG.can_close(report))
        report["items"].pop()
        self.assertTrue(RG.can_close(report))
        self.assertFalse(RG.can_close({**report, "stopped_early": True}))


def block(kind: str, **fields: object) -> SimpleNamespace:
    return SimpleNamespace(type=kind, **fields)


class FakeStream:
    def __init__(self, response: SimpleNamespace) -> None:
        self.response = response

    def __enter__(self) -> "FakeStream":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def get_final_message(self) -> SimpleNamespace:
        return self.response


class FakeClient:
    """Answers each request with the next scripted response and records the requests."""

    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self.responses = responses
        self.requests: list[dict] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self.stream))

    def stream(self, **request: object) -> FakeStream:
        self.requests.append({**request, "messages": list(request["messages"])})  # as it was when sent
        return FakeStream(self.responses.pop(0))


def reply(*content: SimpleNamespace, stop: str = "tool_use") -> SimpleNamespace:
    usage = SimpleNamespace(input_tokens=1000, output_tokens=500, cache_creation_input_tokens=0,
                            cache_read_input_tokens=20000, server_tool_use=None)
    return SimpleNamespace(content=list(content), stop_reason=stop, usage=usage)


class AgentLoopTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(Path(self.tmp.name))
        self.check = mock.patch.object(RA, "check_data", return_value=(True, "Data OK"))
        self.check.start()
        self.tests = mock.patch.object(RA, "run_tests", return_value=(True, "OK"))
        self.ran_tests = self.tests.start()

    def tearDown(self) -> None:
        self.tests.stop()
        self.check.stop()
        self.tmp.cleanup()

    def agent(self, responses: list[SimpleNamespace], limit: float = 20.0) -> tuple[RA.Agent, FakeClient]:
        client = FakeClient(responses)
        agent = RA.Agent(client, RA.Repositories(Path(self.tmp.name)), RA.Budget(limit), self.root,
                         errors=((), ()))
        return agent, client

    def test_item_changed_and_kept(self) -> None:
        edit = block("tool_use", id="t1", name="str_replace_based_edit_tool",
                     input={"command": "str_replace", "path": "data/projects/alpha.yaml", "old_str": "A project.",
                            "new_str": "A library."})
        report = block("tool_use", id="t2", name="report_item",
                       input={"outcome": "changed", "summary": "Updated.", "public_note": "Alpha updated."})
        agent, client = self.agent([reply(edit), reply(report), reply(block("text", text="Done."), stop="end_turn")])
        record = agent.settle("New candidates", "alpha", "task")
        self.assertEqual((record["outcome"], record["public_note"]), ("changed", "Alpha updated."))
        self.assertIn("A library.", (self.root / "data/projects/alpha.yaml").read_text())
        self.assertEqual(self.ran_tests.call_count, 1)
        first = client.requests[0]
        self.assertEqual((first["model"], first["output_config"], first["fallbacks"]),
                         ("claude-opus-5-5", {"effort": "high"}, "default"))
        self.assertEqual(first["betas"], [RA.FALLBACK_BETA])
        self.assertEqual(first["system"][0]["cache_control"], {"type": "ephemeral"})
        results = client.requests[1]["messages"][-1]["content"]
        self.assertEqual((results[0]["tool_use_id"], results[0].get("is_error")), ("t1", None))
        self.assertTrue(all(t.get("eager_input_streaming") for t in RA.CUSTOM))

    def test_changes_that_fail_the_guard_are_undone(self) -> None:
        edit = block("tool_use", id="t1", name="str_replace_based_edit_tool",
                     input={"command": "str_replace", "path": "data/projects/alpha.yaml", "old_str": "developing",
                            "new_str": "established"})
        new = block("tool_use", id="t2", name="str_replace_based_edit_tool",
                    input={"command": "create", "path": "data/projects/zeta.yaml", "file_text": "id: zeta\n"})
        report = block("tool_use", id="t3", name="report_item", input={"outcome": "changed", "summary": "Moved."})
        agent, _ = self.agent([reply(edit, new), reply(report), reply(stop="end_turn")])
        record = agent.settle("New candidates", "alpha", "task")
        self.assertEqual(record["outcome"], "failed")
        self.assertIn("standing is the owner's", record["summary"])
        self.assertEqual((self.root / "data/projects/alpha.yaml").read_text(), PROJECT)
        self.assertFalse((self.root / "data/projects/zeta.yaml").exists())

    def test_changes_that_fail_the_tests_are_undone(self) -> None:
        edit = block("tool_use", id="t1", name="str_replace_based_edit_tool",
                     input={"command": "str_replace", "path": "data/projects/alpha.yaml", "old_str": "A project.",
                            "new_str": "A library."})
        report = block("tool_use", id="t2", name="report_item", input={"outcome": "changed", "summary": "Done."})
        self.ran_tests.return_value = (False, "FAIL: test_whole_map_order")
        agent, _ = self.agent([reply(edit), reply(report), reply(stop="end_turn")])
        record = agent.settle("New candidates", "alpha", "task")
        self.assertEqual(record["outcome"], "failed")
        self.assertIn("the tests failed: FAIL: test_whole_map_order", record["summary"])
        self.assertEqual((self.root / "data/projects/alpha.yaml").read_text(), PROJECT)

    def test_bad_input_missing_report_and_budget(self) -> None:
        bad = block("tool_use", id="t1", name="report_item", input={"outcome": "changed"})
        agent, client = self.agent([reply(bad), reply(stop="end_turn"), reply(stop="end_turn")])
        record = agent.settle("Links", "x", "task")
        self.assertEqual(record["outcome"], "failed")
        error = client.requests[1]["messages"][-1]["content"][0]
        self.assertTrue(error["is_error"])
        self.assertIn("INVALID_JSON", error["content"])
        self.assertEqual(client.requests[2]["messages"][-1]["content"], "Call report_item now with the outcome "
                                                                        "of this item.")
        agent, client = self.agent([], limit=0.0)
        self.assertEqual(agent.settle("Links", "x", "task")["outcome"], "failed")
        self.assertEqual(client.requests, [])

    def test_run_writes_the_report(self) -> None:
        issue = Path(self.tmp.name) / "issue.md"
        issue.write_text(ISSUE, encoding="utf-8")
        out = Path(self.tmp.name) / "report.json"
        responses = [reply(block("tool_use", id=f"r{n}", name="report_item",
                                 input={"outcome": "no_change", "summary": "Checked."})) for n in range(3)]
        responses = [r for pair in zip(responses, [reply(stop="end_turn")] * 3) for r in pair]
        client = FakeClient(responses)
        with mock.patch.object(RA, "make_client", return_value=client), \
                mock.patch.object(RA, "api_errors", return_value=((), ())), \
                mock.patch.object(RA, "REPO_ROOT", self.root):
            RA.main(["--issue", str(issue), "--report", str(out), "--date", "2026-11-01"])
        report = json.loads(out.read_text())
        self.assertEqual((report["mode"], len(report["items"])), ("review", 3))
        self.assertGreater(report["cost_usd"], 0)
        self.assertIn('section "New candidates"', client.requests[2]["messages"][0]["content"])


if __name__ == "__main__":
    unittest.main()
