# Taskra Completion Troubleshooting

If you're experiencing issues with the bash completion for `taskra`, follow these steps to diagnose and fix the problems.

## Common Issues and Solutions

### 1. No Project Keys are Showing Up

When you type `taskra issue` and press tab, you should see available project keys. If you only see "<Type-Issue-Key>" instead, try the following:

#### Check if the Projects Command Works

First, verify that the projects command works correctly:

```bash
taskra projects --json
```

If this command returns valid JSON data with project keys, then the issue is with the completion script's parsing.

#### View Debug Logs

The completion script creates debug logs at:

