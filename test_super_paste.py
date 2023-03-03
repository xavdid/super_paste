from unittest.mock import patch

import pytest

from src.super_paste import _process_text, _process_url, find_go_link, find_issue_tag
from src.super_paste import main as main_func

github_tests = [
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
    # folder, trailing slash
    (
        "https://github.com/zapier/zapier-platform/blob/master/packages/core/src/checks/",
        "zapier/zapier-platform | /checks",
    ),
    # file w/o line
    (
        "https://github.com/zapier/zapier-platform/blob/master/packages/core/src/checks/trigger-has-id.js",
        "zapier/zapier-platform | trigger-has-id.js",
    ),
    # folder, tied to commit
    (
        "https://github.com/zapier/zapier-platform/blob/50ccdf5747468005f2ec48d2a33c0958528190f3/packages/core/src/checks",
        "zapier/zapier-platform | /checks",
    ),
    # folder, trailing slash, tied to commit
    (
        "https://github.com/zapier/zapier-platform/blob/50ccdf5747468005f2ec48d2a33c0958528190f3/packages/core/src/checks/",
        "zapier/zapier-platform | /checks",
    ),
    # file w/o line, tied to commit
    (
        "https://github.com/zapier/zapier-platform/blob/50ccdf5747468005f2ec48d2a33c0958528190f3/packages/core/src/checks/trigger-has-id.js",
        "zapier/zapier-platform | trigger-has-id.js",
    ),
    # file w/ line, tied to commit
    (
        "https://github.com/zapier/zapier-platform/blob/50ccdf5747468005f2ec48d2a33c0958528190f3/packages/core/src/checks/trigger-has-id.js#L16",
        "zapier/zapier-platform | trigger-has-id.js#L16",
    ),
    # file w/ lines, tied to commit
    (
        "https://github.com/zapier/zapier-platform/blob/50ccdf5747468005f2ec48d2a33c0958528190f3/packages/core/src/checks/trigger-has-id.js#L16-18",
        "zapier/zapier-platform | trigger-has-id.js#L16-18",
    ),
]


@pytest.mark.parametrize(
    ["text", "expected"],
    [
        ("", None),
        ("asdf", None),
        ("asdf-123", None),  # not caps
        ("ASDF-123", "ASDF-123"),
        ("RUN_DMC-456", "RUN_DMC-456"),
        ("DASHBOARD-789", "DASHBOARD-789"),
        ("A-123", None),  # too short
        ("https://test.atlassian.net/browse/PROJECT-3536", "PROJECT-3536"),
        ("https://test.atlassian.net/browse/PDE-2525", "PDE-2525"),
        (
            "https://test.atlassian.net/secure/RapidBoard.jspa?rapidView=13&projectKey=PDE&view=planning&selectedIssue=PDE-2572&issueLimit=100",
            "PDE-2572",
        ),
    ],
)
def test_find_issue_tag(text, expected):
    assert find_issue_tag(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "go/cool",
        "go/b",
        "go/do-the-thing",
        "go/api-v2-docs",
        "go/very_long_text_with-1234-numbers",
    ],
)
def test_find_go_link_found(text):
    assert find_go_link(text) == text


@pytest.mark.parametrize(
    "text",
    ["", "go", "go/", "this is go/cool", "go/???"],
)
def test_find_go_link_missing(text):
    assert find_go_link(text) is None


@pytest.mark.parametrize(
    ["text", "expected"],
    [
        ("asdf", "asdf"),  # non-issues untouched
        ("the issue was abc-123", "the issue was abc-123"),
        (
            "the issue was PDE-123",
            "[PDE-123](https://test.atlassian.net/browse/PDE-123)",
        ),  # issues become markdown urls
        ("more info at go/thing", "more info at go/thing"),
        ("go/thing", "[go/thing](http://go/thing)"),
    ],
)
def test_process_text(text, expected):
    assert _process_text(text) == expected


def tag_param(tag, tests):
    """
    wrap a series of `text, expected` tuples in a `pytest.param` w/ a nice id
    """
    return [pytest.param(*test, id=f"{tag}-{i}") for i, test in enumerate(tests)]


@pytest.mark.parametrize(
    ["text", "expected"],
    [
        *tag_param(
            "slack",
            [
                ("https://testing.slack.com/CABC123/p1625868226148700", "slack"),
                (
                    "https://testing.slack.com/CABC123/p1625868226148700?thread_ts=1625836374.142200&cid=CJJJKKHKJ",
                    "slack",
                ),
                (
                    "https://files.slack.com/files-tmb/T01CQK9PK7W/image_from_ios_720.png",
                    "slack",
                ),
            ],
        ),
        *tag_param(
            "zappy",
            [
                (
                    "https://cdn.zappy.app/e8ce0534c810f372effc10a1bdb87280.png",
                    "screenshot",
                )
            ],
        ),
        *tag_param("github", github_tests),
        *tag_param(
            "hosted_github",
            [
                (url.replace("https://github.com", "https://hosted.git.test.com"), tag)
                for url, tag in github_tests
            ],
        ),
        *tag_param(
            "gist",
            [
                (
                    "https://gist.github.com/xavdid/bb2ae92d7e13aa76738e0484a062ee5e",
                    "gist",
                ),
                # hosted gists have a slightly different path
                (
                    "https://hosted.git.test.com/gist/xavdid/bb2ae92d7e13aa76738e0484a062ee5e",
                    "gist",
                ),
            ],
        ),
        *tag_param(
            "gitlab",
            [
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
            ],
        ),
        *tag_param(
            "generic",
            [
                ("https://neat.com/cool/whoa?asdf=asdf", "neat.com"),
                ("https://blah.co.uk/cool/whoa?asdf=asdf", "blah.co.uk"),
                ("https://startup.io/cool/whoa?asdf=asdf", "startup.io"),
            ],
        ),
    ],
)
def test_process_url_no_change(text, expected):
    """
    handles most test cases, where the url should be unchanged
    this is most urls, like slack or github, which get a nice tag and leave the url as-is
    """

    tag, url = _process_url(text)
    assert tag == expected
    assert url == text


@pytest.mark.parametrize(
    ["text", "expected"],
    [
        (
            "https://test.atlassian.net/browse/PROJECT-3536",
            ("PROJECT-3536", "https://test.atlassian.net/browse/PROJECT-3536"),
        ),
        (
            "https://test.atlassian.net/secure/RapidBoard.jspa?rapidView=13&projectKey=PDE&view=planning&selectedIssue=PDE-2572&issueLimit=100",
            ("PDE-2572", "https://test.atlassian.net/browse/PDE-2572"),
        ),
    ],
)
def test_hosted_jira(text, expected):
    """
    this covers cases like jira, where a tag is extracted from a url _and_ the url is modified
    """
    assert _process_url(text) == expected


@patch("src.super_paste.JIRA_URL", "https://asdf.com")
@pytest.mark.parametrize(
    ["text", "expected"],
    [
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
    ],
)
def test_custom_jira(text, expected):
    assert _process_url(text) == expected


@patch("src.super_paste.GHE_URL", "https://asdf.com")
@pytest.mark.parametrize(
    ["text", "expected"],
    [
        (
            "https://asdf.com/xavdid/typed-install/pull/3",
            ("xavdid/typed-install#3", "https://asdf.com/xavdid/typed-install/pull/3"),
        ),
        (
            "https://asdf.com/zapier/zapier-platform/blob/master/packages/core/src/checks/",
            (
                "zapier/zapier-platform | /checks",
                "https://asdf.com/zapier/zapier-platform/blob/master/packages/core/src/checks/",
            ),
        ),
        # normal gh still works, even with a custom url
        (
            "https://github.com/xavdid/typed-install/pull/3",
            (
                "xavdid/typed-install#3",
                "https://github.com/xavdid/typed-install/pull/3",
            ),
        ),
        (
            "https://github.com/zapier/zapier-platform/blob/master/packages/core/src/checks/",
            (
                "zapier/zapier-platform | /checks",
                "https://github.com/zapier/zapier-platform/blob/master/packages/core/src/checks/",
            ),
        ),
    ],
)
def test_custom_ghe(text, expected):
    assert _process_url(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        # too few segments
        "https://gitlab.com/some-other-project/-/issues/50",
        # too many segments
        "https://gitlab.com/xavdid/subteam/thing/some-other-project/-/issues/50",
    ],
)
def test_ivalid_gitlab_raises(text):
    with pytest.raises(ValueError):
        _process_url(text)


@pytest.mark.parametrize(
    "text",
    [
        "[LINK](https://neat.com)",
        "[PDE-123](https://test.atlassian.net/browse/PDE-123)",
    ],
)
def test_re_paste_markdown_links(text):
    assert main_func(text) == text


@pytest.mark.parametrize(
    "text",
    [
        "LINK](https://neat.com)",
        "see https://test.atlassian.net/browse/PDE-123",
    ],
)
def test_invalid_markdown_raises(text):
    with pytest.raises(ValueError):
        main_func(text)


@pytest.mark.parametrize(
    ["url", "target"],
    [
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
    ],
)
def test_main_with_urls(url, target):
    assert main_func(url) == f"[{target}]({url})"


@pytest.mark.parametrize(
    "text",
    ["asdf", "the issue was abc-123"],
)
def test_main_with_text_no_jira(text):
    assert main_func(text) == text


@pytest.mark.parametrize(
    ["text", "expected"],
    [("it is PDE-123", ("PDE-123", "https://test.atlassian.net/browse/PDE-123"))],
)
def test_main_with_jira_tag_in_text(text, expected):
    text, target = expected
    assert main_func(text) == f"[{text}]({target})"


@patch("src.super_paste._process_url")
@patch("src.super_paste.custom_url", return_value=("neat", "https://website.com"))
def test_main_with_url_config(mocked_custom_url, mocked_process_url):
    assert main_func("https://neat.com") == "[neat](https://website.com)"

    assert mocked_custom_url.called
    assert not mocked_process_url.called


@patch("src.super_paste._process_text")
@patch("src.super_paste.custom_text", return_value="asdf")
def test_main_with_text_config(mocked_custom_text, mocked_process_text):
    assert main_func("something") == "asdf"

    assert mocked_custom_text.called
    assert not mocked_process_text.called


@patch("src.super_paste._process_url")
@patch("src.super_paste.custom_url")
@patch("src.super_paste._process_text", wraps=lambda x: _process_text(x))
@patch("src.super_paste.custom_text", return_value=None)
def test_main_calling_pattern_text(
    mocked_custom_text,
    mocked_process_text,
    mocked_custom_url,
    mocked_process_url,
):
    assert main_func("something") == "something"

    assert mocked_custom_text.called
    assert mocked_process_text.called

    # non-relevant functions aren't called
    assert not mocked_custom_url.called
    assert not mocked_process_url.called


@patch("src.super_paste._process_text")
@patch("src.super_paste.custom_text")
@patch("src.super_paste._process_url", wraps=lambda x: _process_url(x))
@patch("src.super_paste.custom_url", return_value=None)
def test_main_calling_pattern_url(
    mocked_custom_url,
    mocked_process_url,
    mocked_custom_text,
    mocked_process_text,
):
    assert main_func("https://neat.com") == "[neat.com](https://neat.com)"

    assert mocked_custom_url.called
    assert mocked_process_url.called

    # non-relevant functions aren't called
    assert not mocked_custom_text.called
    assert not mocked_process_text.called
