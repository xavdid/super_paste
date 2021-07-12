#!/usr/local/bin/python3

import re
import sys
from typing import Optional, Tuple
from urllib.parse import urlparse

try:
    # deployed setup, everything is top-level
    from config import JIRA_URL, custom_text, custom_url
except ImportError:
    # testing setup, everything in a subdir
    from .config import JIRA_URL, custom_text, custom_url


def find_issue_tag(text: str) -> Optional[str]:
    """
    Looks for jira tags in text. They're a few capital letters, followed by a
    dash and a number.
    """
    match = re.search(r"[A-Z]{2,}-\d+", text)
    if match:
        return match.group()
    return None


def markdown_link(link_text, href):
    return f"[{link_text}]({href})"


def _process_text(text: str) -> str:
    """
    Function called for non-url strings. Primary used to pull issue tags out
    of text. If it doesn't find a tag, it returns the text, unaltered.
    """
    maybe_jira = find_issue_tag(text)
    if maybe_jira:
        return markdown_link(maybe_jira, f"{JIRA_URL}/browse/{maybe_jira}")

    else:
        return text


def _process_url(url: str) -> Tuple[str, str]:
    """
    given a url, return a 2-tuple of the link text and target
    """

    def link_titled(text) -> Tuple[str, str]:
        """
        almost every return statement uses this except for cleaning up jira urls
        """
        return text, url

    parsed_url = urlparse(url)
    # rough approximation, but it's probably fine
    if not bool(parsed_url.scheme and parsed_url.netloc):
        # todo: walrus?
        markdown_link = re.match(r"\[(.*)\]\((.*)\)", url)
        # might be a markdown link already?
        if markdown_link:
            return markdown_link.groups()  # type: ignore - it's a 2-tuple if it matched

        raise ValueError(f"can't format non-url string: `{url}`")

    domain = parsed_url.netloc

    if domain.endswith(".slack.com"):
        # todo: check for thread?
        return link_titled("slack")

    if domain == "cdn.zappy.app":
        return link_titled("screenshot")

    if domain.endswith(".atlassian.net") or url.startswith(JIRA_URL):
        issue_tag = find_issue_tag(url)
        if issue_tag:
            # don't transform links that don't match the custom url even if it's defined
            if url.startswith(JIRA_URL):
                return (issue_tag, f"{JIRA_URL}/browse/{issue_tag}")
            return (issue_tag, f"{parsed_url.scheme}://{domain}/browse/{issue_tag}")

        return link_titled("JIRA")

    if domain == "github.com":
        if "/pull/" in url or "/issues/" in url:
            # pull out the repo name nicely
            _, _, _, user, repo, _, number = url.split("/")

            return link_titled(f"{user}/{repo}#{number}")

        if "/commit/" in url:
            return link_titled("commit")

        return link_titled("github")

    # should handle hosted
    if "gitlab.com" in domain:
        # if it's not a url we can nicely format, just bail
        if not any(
            [x in url for x in ["/-/issues/", "/-/merge_requests/", "/-/commit/"]]
        ):
            return link_titled("gitlab")

        separators = {"issues": "#", "merge_requests": "!", "commit": "@"}

        # https://gitlab.com/xavdid/some-project/-/issues/1
        # https://gitlab.com/xavdid/some-project/-/merge_requests/2
        # https://gitlab.com/xavdid/team/some-other-project/-/merge_requests/50
        # https://gitlab.com/xavdid/team/some-other-project/-/commit/11530b842858ccc0c915507b8f27af015a247fae

        # pull out the repo name nicely; may have a subteam
        parts = url.split("/")
        if len(parts) == 8:
            # no subteam
            _, _, _, user, repo, _, resource, id_ = parts
            subteam = ""
        elif len(parts) == 9:
            # has subteam
            _, _, _, user, subteam, repo, _, resource, id_ = parts
        else:
            raise ValueError(f"unable to parse Gitlab URL: {url}")

        if "/-/commit/" in url:
            id_ = id_[:8]

        link_with_subteam = (
            f"{f'{subteam}/' if subteam else ''}{repo}{separators[resource]}{id_}"
        )

        return link_titled(f"{user}/{link_with_subteam}")

    # default to pulling the root domain out, if we can
    return link_titled(domain)


def main(input_: str) -> str:
    # we'll almost always have urls, but we could also have plain jira tags
    # if we do, turn them into nice jira urls
    if "https:" in input_ or "http:" in input_:
        custom_result = custom_url(input_)
        if custom_result:
            return markdown_link(*custom_result)
        return markdown_link(*_process_url(input_))

    else:
        custom_result = custom_text(input_)
        if custom_result:
            return custom_result
        return _process_text(input_)


if __name__ == "__main__":
    try:
        res = main(sys.argv[1])
    except Exception as e:
        res = f"! Alfred ERR ! {e}"
    sys.stdout.write(res)
