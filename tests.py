from typing import List, Tuple
from unittest import TestCase, main
from unittest.mock import patch

from src.super_paste import (
    _process_url,
    _process_text,
    find_issue_tag,
    main as main_func,
)


class IssueTagTest(TestCase):
    def test_find_issue_tag(self):
        tests = [
            ("", None),
            ("asdf", None),
            ("asdf-123", None),  # not caps
            ("ASDF-123", "ASDF-123"),
            ("A-123", None),  # too short
            ("https://test.atlassian.net/browse/PROJECT-3536", "PROJECT-3536"),
            ("https://test.atlassian.net/browse/PDE-2525", "PDE-2525"),
            (
                "https://test.atlassian.net/secure/RapidBoard.jspa?rapidView=13&projectKey=PDE&view=planning&selectedIssue=PDE-2572&issueLimit=100",
                "PDE-2572",
            ),
        ]
        for input_, expected in tests:
            self.assertEqual(find_issue_tag(input_), expected)


class ProcessTextTest(TestCase):
    def test_process_text(self):
        tests = [
            ("asdf", "asdf"),  # non-issues untouched
            ("the issue was abc-123", "the issue was abc-123"),
            (
                "the issue was PDE-123",
                "[PDE-123](https://test.atlassian.net/browse/PDE-123)",
            ),  # issues become markdown urls
        ]
        for input_, expected in tests:
            self.assertEqual(_process_text(input_), expected)


class ProcessUrlTest(TestCase):
    def default_test_run(self, tests: List[Tuple[str, str]]):
        """
        handles most test cases, where the url should be unchanged
        """
        for input_, expected in tests:
            tag, url = _process_url(input_)
            self.assertEqual(tag, expected, msg=f"failed on {input_}")
            self.assertEqual(url, input_, msg=f"failed on {input_}")

    def test_slack(self):
        tests = [
            ("https://testing.slack.com/CABC123/p1625868226148700", "slack"),
            (
                "https://testing.slack.com/CABC123/p1625868226148700?thread_ts=1625836374.142200&cid=CJJJKKHKJ",
                "slack",
            ),
            (
                "https://files.slack.com/files-tmb/T01CQK9PK7W/image_from_ios_720.png",
                "slack",
            ),
        ]
        self.default_test_run(tests)

    def test_zappy(self):
        tests = [
            ("https://cdn.zappy.app/e8ce0534c810f372effc10a1bdb87280.png", "screenshot")
        ]
        self.default_test_run(tests)

    def test_github(self):
        tests = [
            (
                "https://github.com/xavdid/typed-install/issues/1",
                "xavdid/typed-install#1",
            ),
            (
                "https://github.com/xavdid/typed-install/pull/3",
                "xavdid/typed-install#3",
            ),
            ("https://github.com/xavdid/typed-install", "github"),
            (
                "https://github.com/xavdid/typed-install/commit/c611f9b5c218814eff6c5631a585283bc039bab9",
                "commit",
            ),
            ("https://github.com/xavdid/typed-install/pulls", "github"),
        ]
        self.default_test_run(tests)

    def test_gitlab(self):
        tests = [
            (
                "https://gitlab.com/xavdid/some-project/-/issues/1",
                "xavdid/some-project#1",
            ),
            (
                "https://gitlab.com/xavdid/some-project/-/merge_requests/2",
                "xavdid/some-project!2",
            ),
            (
                "https://gitlab.com/xavdid/some-other-project/-/commit/11530b842858ccc0c915507b8f27af015a247fae",
                "xavdid/some-other-project@11530b84",
            ),
            (
                "https://gitlab.com/xavdid/team/some-other-project/-/merge_requests/50",
                "xavdid/team/some-other-project!50",
            ),
            (
                "https://gitlab.com/xavdid/team/some-other-project/-/commit/11530b842858ccc0c915507b8f27af015a247fae",
                "xavdid/team/some-other-project@11530b84",
            ),
            ("https://gitlab.com/xavdid/some-project/", "gitlab"),
            ("https://gitlab.com/-/profile/account", "gitlab"),
        ]
        self.default_test_run(tests)

        with self.assertRaises(ValueError):
            _process_url(
                "https://gitlab.com/some-other-project/-/issues/50"
            )  # too short

        with self.assertRaises(ValueError):
            _process_url(
                "https://gitlab.com/xavdid/subteam/thing/some-other-project/-/issues/50"
            )  # too long

    def test_hosted_jira(self):
        tests = [
            (
                "https://test.atlassian.net/browse/PROJECT-3536",
                ("PROJECT-3536", "https://test.atlassian.net/browse/PROJECT-3536"),
            ),
            (
                "https://test.atlassian.net/secure/RapidBoard.jspa?rapidView=13&projectKey=PDE&view=planning&selectedIssue=PDE-2572&issueLimit=100",
                ("PDE-2572", "https://test.atlassian.net/browse/PDE-2572"),
            ),
        ]

        for input_, expected in tests:
            self.assertEqual(_process_url(input_), expected)

    @patch("src.super_paste.JIRA_URL", "https://asdf.com")
    def test_custom_jira(self):
        tests = [
            (
                "https://asdf.com/browse/PROJECT-3536",
                ("PROJECT-3536", "https://asdf.com/browse/PROJECT-3536"),
            ),
            (
                "https://asdf.com/secure/RapidBoard.jspa?rapidView=13&projectKey=PDE&view=planning&selectedIssue=PDE-2572&issueLimit=100",
                ("PDE-2572", "https://asdf.com/browse/PDE-2572"),
            ),
            # normal jira still works, even with a custom url
            (
                "https://test.atlassian.net/browse/PROJECT-3536",
                ("PROJECT-3536", "https://test.atlassian.net/browse/PROJECT-3536"),
            ),
            (
                "https://test.atlassian.net/secure/RapidBoard.jspa?rapidView=13&projectKey=PDE&view=planning&selectedIssue=PDE-2572&issueLimit=100",
                ("PDE-2572", "https://test.atlassian.net/browse/PDE-2572"),
            ),
        ]

        for input_, expected in tests:
            self.assertEqual(_process_url(input_), expected)

    def test_takes_markdown_links(self):
        # special case so that you can re-paste existing markdown links
        tests = [
            "[LINK](https://neat.com)",
            "[PDE-123](https://test.atlassian.net/browse/PDE-123)",
        ]
        for test in tests:
            self.assertEqual(main_func(test), test)

    def test_errors_for_links_in_text(self):
        # special case so that you can re-paste existing markdown links
        tests = [
            "LINK](https://neat.com)",
            "see https://test.atlassian.net/browse/PDE-123",
        ]
        for test in tests:
            with self.assertRaises(ValueError):
                main_func(test)


class MainTestCase(TestCase):
    def test_main_with_urls(self):
        # some simple tests to make sure it's wired up correctly
        tests = [
            (
                "https://github.com/xavdid/typed-install/issues/1",
                "xavdid/typed-install#1",
            ),
            (
                "https://cdn.zappy.app/e8ce0534c810f372effc10a1bdb87280.png",
                "screenshot",
            ),
            ("https://testing.slack.com/CABC123/p1625868226148700", "slack"),
            ("https://test.atlassian.net/browse/PROJECT-3536", "PROJECT-3536"),
        ]
        for url, target in tests:
            self.assertEqual(main_func(url), f"[{target}]({url})")

    def test_main_with_text_no_jira(self):
        # some simple tests to make sure it's wired up correctly
        tests = ["asdf", "the issue was abc-123"]
        for target in tests:
            self.assertEqual(main_func(target), target)

    def test_main_with_jira_tag_in_text(self):
        # some simple tests to make sure it's wired up correctly
        tests = [
            ("it is PDE-123", ("PDE-123", "https://test.atlassian.net/browse/PDE-123"))
        ]
        for input_, (text, target) in tests:
            self.assertEqual(main_func(input_), f"[{text}]({target})")

    @patch("src.super_paste._process_url")
    @patch("src.super_paste.custom_url", return_value=("neat", "https://website.com"))
    def test_main_with_url_config(self, mocked_custom_url, mocked_process_url):
        self.assertEqual(main_func("https://neat.com"), "[neat](https://website.com)")

        self.assertTrue(mocked_custom_url.called)
        self.assertFalse(mocked_process_url.called)

    @patch("src.super_paste._process_text")
    @patch("src.super_paste.custom_text", return_value="asdf")
    def test_main_with_text_config(self, mocked_custom_text, mocked_process_text):
        self.assertEqual(main_func("something"), "asdf")

        self.assertTrue(mocked_custom_text.called)
        self.assertFalse(mocked_process_text.called)

    @patch("src.super_paste._process_url")
    @patch("src.super_paste.custom_url")
    @patch("src.super_paste._process_text", wraps=lambda x: _process_text(x))
    @patch("src.super_paste.custom_text", return_value=None)
    def test_main_calling_pattern_text(
        self,
        mocked_custom_text,
        mocked_process_text,
        mocked_custom_url,
        mocked_process_url,
    ):
        self.assertEqual(main_func("something"), "something")

        self.assertTrue(mocked_custom_text.called)
        self.assertTrue(mocked_process_text.called)

        # non-relevant functions aren't called
        self.assertFalse(mocked_custom_url.called)
        self.assertFalse(mocked_process_url.called)

    @patch("src.super_paste._process_text")
    @patch("src.super_paste.custom_text")
    @patch("src.super_paste._process_url", wraps=lambda x: _process_url(x))
    @patch("src.super_paste.custom_url", return_value=None)
    def test_main_calling_pattern_url(
        self,
        mocked_custom_url,
        mocked_process_url,
        mocked_custom_text,
        mocked_process_text,
    ):
        self.assertEqual(main_func("https://neat.com"), "[LINK](https://neat.com)")

        self.assertTrue(mocked_custom_url.called)
        self.assertTrue(mocked_process_url.called)

        # non-relevant functions aren't called
        self.assertFalse(mocked_custom_text.called)
        self.assertFalse(mocked_process_text.called)


if __name__ == "__main__":
    main()
