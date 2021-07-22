# Super Paste

An [Alfred](https://www.alfredapp.com/) workflow to paste beautiful markdown links. It works especially well when formatting Jira, GitHub, and GitLab links.

```
https://github.com/xavdid/typed-install/pull/3

becomes

[xavdid/typed-install#3](https://github.com/xavdid/typed-install/pull/3)
```

## Usage

With a link on your clipboard, type `;pr`. Your cursor will type a nice markdown link! The trigger shortcut is configurable in the workflow's settings:

![](https://cdn.zappy.app/c171760fba687fece58441bfba78ea46.png)

You can also have a Jira project tag on the clipboard. Super Paste-ing `ABC-123` results in `[ABC-123](https://test.atlassian.net/browse/ABC-123)`. The exact Jira url is [configurable](#configuration).

If your clipboard doesn't have a link on it, the text is pasted normally.

## Install

See [releases](https://github.com/xavdid/super_paste/releases) for the latest `.alfredworkflow` file. Download that, then double click on it to open the file in Alfred.

## Supported Sites

Pasting a link from the following sites results in "smart" behavior:

- [Slack](https://slack.com/)
- [Zappy](https://zapier.com/zappy)
- [GitHub](https://github.com)
- [GitLab](https://gitlab.com)
- [Jira](https://www.atlassian.com/software/jira)

## Configuration

Because `Super Paste` is a Python script under the hood, configuration also requires a writing a bit of Python. To edit that file:

1. Install the workflow (see [installation](#install))
2. Invoke Alfred and type `?super`; this will bring you to the workflow's settings
3. Right-click on the workflow and click `Open in Finder` ([screenshot](https://cdn.zappy.app/dae5e34c023c15eeb18b983e5780ef89.png))
4. Open the `config.py` file in an editor of your choice.
5. Read through that file - it tells you exactly how to alter it and what the functions expect you to return.
6. :exclamation: **IMPORTANT**: after saving your edits to the file, copy the entire thing and save it somewhere else (Dropbox, a [Gist](https://gist.github.com), etc). Every time you update the workflow, that file gets overwritten with the default. Saving the edited `config.py` file means you'll be able to easily repeat these steps to restore your configuration after updates.

## Contributing

### Development & Releases

1. Update the `version` key in the `plist` (towards the bottom)
2. Update code w/ changes
3. Once done, update the `CHANGELOG.md`
4. run `./bin/release`
5. push!
