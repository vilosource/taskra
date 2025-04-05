# Taskra

Taskra is a command-line tool for managing Jira projects, issues, worklogs, and reports efficiently from your terminal. It aims to streamline your workflow by providing quick access to common Jira operations without leaving the command line.

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

Before using Taskra, add your Jira account credentials:

```bash
taskra config add
```

You will be prompted for:

- Jira URL (e.g., `https://yourcompany.atlassian.net`)
- Email address
- API token (create at https://id.atlassian.com/manage-profile/security/api-tokens)

You can list, remove, or set default accounts with:

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

Create a new issue (interactive prompt):

```bash
taskra issue create
```

#### Tickets Report

Generate a report of tickets in a project with filters:

```bash
taskra tickets <PROJECT-KEY> --start-date YYYY-MM-DD --end-date YYYY-MM-DD --status "In Progress" --assignee "john.doe"
```

Options include grouping, sorting, and output format (table, JSON, CSV).

#### Worklogs

List your worklogs within a date range:

```bash
taskra worklogs list --start YYYY-MM-DD --end YYYY-MM-DD
```

Add a worklog to an issue:

```bash
taskra worklogs add <ISSUE-KEY> <time-spent> --comment "Worked on feature X"
```

#### Reports

Generate cross-project reports:

```bash
taskra report cross --projects PROJ1,PROJ2 --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

---

### Debugging

Enable debug output with:

```bash
taskra --debug verbose <command>
```

---

## License

MIT License

---

## Contributing

Contributions are welcome! Please open issues or pull requests.

