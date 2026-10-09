#!/usr/bin/env python3
"""Behavioral boundaries for normalization, trigger precedence and co-occurrence."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from match_trigger import match, normalize, load_registration


class TriggerBehaviorTests(unittest.TestCase):
    def test_boundary_cases(self):
        cases = [
            ("Skills<Web-Design>", True, "explicit"),
            ("skills<web-design>", True, "explicit"),
            ("SKILLS<WEB-DESIGN>", True, "explicit"),
            (" \tSkills<Web-Design>\n ", True, "explicit"),
            ("ＳＫＩＬＬＳ＜ＷＥＢ－ＤＥＳＩＧＮ＞", True, "explicit"),
            ("设计网页", True, "core"),
            ("请设计网站，谢谢", True, "core"),
            ("设计工作台布局", True, "core"),
            ("优化 React 页面性能", False, "extended_without_domain"),
            ("优化 Next.js 页面性能", False, "extended_without_domain"),
            ("测试 webapp", False, "extended_without_domain"),
            ("测试  WEBAPP", False, "extended_without_domain"),
            ("React 项目：优化\tReact   页面性能", True, "extended_with_domain"),
            ("网站：测试 WEBAPP", True, "extended_with_domain"),
            ("优化 Next.js 页面性能；网页", True, "extended_with_domain"),
            ("工作台布局：测试 webapp", True, "extended_with_domain"),
            ("优化 React 页面性能；Next.js 项目", True, "extended_with_domain"),
            ("优化 React 页面性能；测试 webapp", False, "extended_without_domain"),
            ("优化 React 页面性能；优化 React 页面性能", False, "extended_without_domain"),
            ("SKILLS<WEB-DESIGN>，测试 webapp", True, "explicit"),
            ("设计网页，优化 React 页面性能", True, "core"),
            ("skills <Web-Design>", False, "no_trigger"),
            ("skills< Web-Design >", False, "no_trigger"),
            ("设计 网页", False, "no_trigger"),
            ("做个网页", False, "no_trigger"),
            ("网页", False, "no_trigger"),
            ("优化React页面性能；React", False, "no_trigger"),
            ("优化 React 页面性能；ReactNative", False, "extended_without_domain"),
            ("测试 webapp；webapplication", False, "extended_without_domain"),
            ("测试 webapp；react组件", True, "extended_with_domain"),
            ("测试 webapp；Next.jsX", False, "extended_without_domain"),
            ("测试 webapp；REACT", True, "extended_with_domain"),
            ("网站：测试\u3000ｗｅｂａｐｐ", True, "extended_with_domain"),
            ("", False, "no_trigger"),
        ]
        for text, expected, reason in cases:
            with self.subTest(text=text):
                result = match(text)
                self.assertIs(result["matched"], expected)
                self.assertEqual(result["reason"], reason)

    def test_normalization_is_idempotent_and_preserves_chinese_and_internal_spaces(self):
        samples = ["  设计网页\t ", "ＳＫＩＬＬＳ＜ＷＥＢ－ＤＥＳＩＧＮ＞", "React\n\t 页面性能"]
        for text in samples:
            self.assertEqual(normalize(normalize(text)), normalize(text))
        self.assertEqual(normalize("  设计 网页  "), "设计 网页")
        self.assertEqual(normalize("skills< Web-Design >"), "skills< web-design >")

    def test_same_context_output_can_be_consumed_by_next_step(self):
        result = match("Next.js 项目：优化 React 页面性能")
        self.assertEqual(result["context_domains"], ["Next.js"])
        self.assertEqual(result["matched_triggers"], ["优化 React 页面性能"])
        self.assertEqual(json.loads(json.dumps(result, ensure_ascii=False)), result)

    def test_native_cli_positive_and_negative_are_valid_json_with_zero_exit(self):
        script = Path(__file__).with_name("match_trigger.py")
        for text, expected in [("Skills<Web-Design>", True), ("优化 React 页面性能", False)]:
            process = subprocess.run([sys.executable, str(script), "--text", text],
                                     capture_output=True, encoding="utf-8", check=True)
            self.assertIs(json.loads(process.stdout)["matched"], expected)

    def test_registration_four_field_types(self):
        data = load_registration()
        self.assertEqual(list(data), ["name", "description", "triggers", "match_description"])
        self.assertEqual(len(data["triggers"]), 7)
        self.assertTrue(all(isinstance(term, str) for term in data["triggers"]))

    def test_utf8_stdin_matches_text_arguments_in_both_python_encoding_modes(self):
        script = Path(__file__).with_name("match_trigger.py")
        messages = ["设计网页", "网站：测试 webapp", "优化 React 页面性能", "ＳＫＩＬＬＳ＜ＷＥＢ－ＤＥＳＩＧＮ＞"]
        for mode in ("0", "1"):
            env = os.environ.copy()
            env["PYTHONUTF8"] = mode
            for text in messages:
                with self.subTest(mode=mode, text=text):
                    process = subprocess.run([sys.executable, "-B", str(script), "--stdin"],
                                             input=text, capture_output=True, encoding="utf-8",
                                             env=env, check=True)
                    self.assertEqual(json.loads(process.stdout), match(text))

    def test_invalid_utf8_stdin_fails_instead_of_returning_a_match(self):
        script = Path(__file__).with_name("match_trigger.py")
        process = subprocess.run([sys.executable, "-B", str(script), "--stdin"],
                                 input=b"\xff\xfe", capture_output=True)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(process.stdout, b"")


if __name__ == "__main__":
    unittest.main(verbosity=2)
