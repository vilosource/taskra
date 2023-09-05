# Bash Completion for Taskra

Taskra includes a bash completion script to make it easier to use the command line interface.

## Installation

### Temporary Use
To use the completion script in your current shell session:

```bash
source /path/to/taskra/scripts/taskra-completion.bash
```

### Permanent Installation

#### Option 1: Source in .bashrc
Add this line to your `~/.bashrc` file:

```bash
source /path/to/taskra/scripts/taskra-completion.bash
```

#### Option 2: Add to bash_completion.d
Copy or symlink the completion script to your bash completion directory:

```bash
# For system-wide installation (requires sudo)
sudo ln -s /path/to/taskra/scripts/taskra-completion.bash /etc/bash_completion.d/taskra

# OR for user-specific installation
mkdir -p ~/.local/share/bash-completion/completions
ln -s /path/to/taskra/scripts/taskra-completion.bash ~/.local/share/bash-completion/completions/taskra
```

## Features

The completion script provides:

- Completion for all Taskra commands (projects, issue, worklogs, config, tickets)
- Completion for command options (like --json, --debug, etc.)
- **Smart issue key completion based on available project keys**
- Project key autocompletion for ticket and issue commands
- Context-sensitive completion for option values:
  - Date format suggestions
  - Debug level options
  - Sort and group by fields
  - Output formats

## Example Usage
