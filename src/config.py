"""
This file holds custom configuration for an otherwise generic super-paste

At this time, it recognizes the following variables:

- JIRA_URL
- GHE_URL
- process_url
- process_text

See their docs below for more info about how you can customize super_paste behavior.

!! It is HIGHLY RECOMMENDED !! to keep any modifications to this file saved separately
When you download an update to the workflow, any changes to this file will be lost.
"""

from typing import Optional, Tuple

# The full url (without the trailing slash) of a Jira instance
# it'll be slotted into urls like "{JIRA_URL}/browse/ABC-123"
# see this list for urls where your Jira instance might live:
# https://confluence.atlassian.com/jirakb/how-to-find-your-site-url-to-set-up-the-jira-data-center-and-server-mobile-app-954244798.html
JIRA_URL = "https://test.atlassian.net"

# If you use a hosted GitHub enterprise server, add its homepage here:
GHE_URL = "https://hosted.git.test.com"


def custom_url(url: str) -> Optional[Tuple[str, str]]:
    """
    If you want to create nice links to non-public resources, this function is
    the place to customize that behavior. If you aren't adding a case for the
    incoming url, then return `None` and the default super_paste will take over.

    If you are returning a custom link, return a 2-tuple of: (link_text, target).
    That will result in a url like `[link_text](target)`.
    You are unlikely to want to modify the incoming url when it's returned in the tuple.
    """
    # if my.internal.url in url:
    #     return 'internal thing', url
    return None


def custom_text(text: str) -> Optional[str]:
    """
    This function is used to turn non-links into links, such as a Jira tag
    becoming a full link.

    If you're not transforming the text, return `None` and default behavior will take over.

    Make sure to return the created link in markdown format if it's becoming a link.
    """
    return None
