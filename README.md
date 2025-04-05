# Taskra

Taskra is a powerful command-line tool for managing Jira projects, issues, worklogs, and generating reports directly from your terminal. It streamlines your workflow by providing fast, scriptable access to Jira, saving you time and reducing context switching.

---

## User's Guide

### Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/taskra.git
cd taskra
pip install -r requirements.txt
```

### Configuration

Before using Taskra, configure your Jira account:

```bash
taskra config add
```

You will be prompted for:

- **Jira URL** (e.g., `https://yourcompany.atlassian.net`)
- **Email address**
- **API token** (create at [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens))

Manage accounts:

```bash
taskra config list
taskra config remove <account-name>
taskra config set-default <account-name>
```

---

### Common Commands

#### Projects

List all accessible Jira projects:

```bash
taskra projects
```

#### Issues

Fetch details of a specific issue:

```bash
taskra issue <ISSUE-KEY>
```

Create a new issue interactively:

```bash
taskra issue create
```

Update an issue:

```bash
taskra issue update <ISSUE-KEY>
```

Add a comment to an issue:

```bash
taskra issue comment <ISSUE-KEY> --message "Your comment here"
```

#### Tickets Report

Generate a report of tickets in a project with filters:

```bash
taskra tickets <PROJECT-KEY> --start-date YYYY-MM-DD --end-date YYYY-MM-DD --status "In Progress" --assignee "john.doe"
```

Options:

- `--group-by status|assignee|none`
- `--sort-by created|updated|status|assignee|priority`
- `--format table|json|csv`
- `--reverse/--no-reverse` (sort order)

#### Worklogs

List your worklogs within a date range:

```bash
taskra worklogs list --start YYYY-MM-DD --end YYYY-MM-DD
```

Add a worklog to an issue:

```bash
taskra worklogs add <ISSUE-KEY> <time-spent> --comment "Worked on feature X"
```

Example:

```bash
taskra worklogs add PROJ-123 2h30m --comment "Bug fixes and testing"
```

#### Reports

Generate cross-project reports:

```bash
taskra report cross --projects PROJ1,PROJ2 --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

---

### Debugging & Verbose Output

Enable debug output to troubleshoot API calls:

```bash
taskra --debug verbose <command>
```

Debug levels:

- `none` (default)
- `error`
- `info`
- `verbose`

---

## Tips

- Use shell completion for faster command entry (see `scripts/taskra-completion.bash`).
- Combine filters to narrow down results.
- Use `--json` to get raw API data for scripting.

---

## License

MIT License

---

## Contributing

Contributions, bug reports, and feature requests are welcome! Please open an issue or submit a pull request.

---

