#!/usr/bin/env bash
# Bash completion script for Taskra CLI

# Function to get project keys from taskra projects command
_taskra_get_projects() {
    # Use --json flag to get structured output
    local projects_json=$(taskra projects --json 2>/dev/null)
    if [[ -n "$projects_json" ]]; then
        # Extract just the project keys from the JSON output
        # This uses grep to find "key": patterns and extract what's inside the quotes
        echo "$projects_json" | grep -o '"key"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"key"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/'
    fi
}

# Cache project keys to avoid calling taskra projects repeatedly
_taskra_cache_projects() {
    local cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/taskra"
    local cache_file="$cache_dir/project_keys"
    local max_age=3600  # Cache expiration in seconds (1 hour)
    local debug_file="$cache_dir/completion_debug.log"
    
    # Debug mode - set to 1 to enable debugging
    local debug_mode=1
    
    # Debug function
    _debug_log() {
        if [[ $debug_mode -eq 1 ]]; then
            echo "$(date): $1" >> "$debug_file"
        fi
    }

    # Create cache directory if it doesn't exist
    mkdir -p "$cache_dir" 2>/dev/null || _debug_log "Failed to create cache directory"

    _debug_log "Starting project key retrieval"
    
    # First try to use the cache if it's valid
    if [[ -f "$cache_file" ]] && [[ $(($(date +%s) - $(stat -c %Y "$cache_file"))) -lt $max_age ]]; then
        _debug_log "Using cached project keys from $cache_file"
        cat "$cache_file"
        return 0
    fi
    
    _debug_log "Cache invalid or missing, calling taskra projects"
    
    # Cache is invalid or doesn't exist, refresh it
    local projects=$(_taskra_get_projects)
    
    _debug_log "Retrieved projects: ${projects:-none}"
    
    if [[ -n "$projects" ]]; then
        echo "$projects" > "$cache_file" || _debug_log "Failed to write to cache file"
        _debug_log "Updated cache with ${#projects} bytes"
        echo "$projects"
        return 0
    else
        _debug_log "No projects found or command failed"
        
        # As a fallback, if we have a cache file but it's just old, use it anyway
        if [[ -f "$cache_file" ]]; then
            _debug_log "Using outdated cache as fallback"
            cat "$cache_file"
            return 0
        fi
        
        # Don't use hardcoded fallback list
        return 1
    fi
}

_taskra_completion() {
    local cur prev opts cmd
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Define all top-level commands
    opts="projects issue worklogs config tickets"
    
    # Get the current command - if there's one already entered
    for ((i=1; i < COMP_CWORD; i++)); do
        if [[ ${COMP_WORDS[i]} == projects || ${COMP_WORDS[i]} == issue || 
              ${COMP_WORDS[i]} == worklogs || ${COMP_WORDS[i]} == config ||
              ${COMP_WORDS[i]} == tickets ]]; then
            cmd=${COMP_WORDS[i]}
            break
        fi
    done

    # Complete options based on the command
    case "${cmd}" in
        projects)
            if [[ ${cur} == -* ]]; then
                COMPREPLY=( $(compgen -W "--json -j --debug -d" -- ${cur}) )
            fi
            ;;
        issue)
            # When we need an issue key
            if [[ ${prev} == "issue" ]]; then
                # Get project keys from cache or command
                local project_keys=$(_taskra_cache_projects)
                
                if [[ -n "$project_keys" ]]; then
                    # If user has started typing, filter completions
                    if [[ ${cur} == *-* ]]; then
                        # User has entered part of the issue key with a dash
                        local project_prefix="${cur%%-*}"
                        # Check if we match a specific project
                        if echo "$project_keys" | grep -q "^$project_prefix$"; then
                            # If we have an exact match and user typed the dash, offer numbered completions
                            if [[ ${cur} == *-* ]]; then
                                # Generate some common issue numbers (1-20)
                                local issue_nums=$(seq -f "$project_prefix-%g" 1 20)
                                COMPREPLY=( $(compgen -W "$issue_nums" -- ${cur}) )
                            fi
                        else
                            # Find any project key that matches what user has typed
                            COMPREPLY=( $(compgen -W "$(echo "$project_keys" | grep "^$project_prefix" | sed 's/$/-/')" -- ${cur}) )
                        fi
                    else
                        # User is just starting to type - offer all project keys with dash
                        local project_suggestions=""
                        while read -r project; do
                            if [[ -n "$project" ]]; then
                                project_suggestions+="$project- "
                            fi
                        done <<< "$project_keys"
                        
                        if [[ -n "$project_suggestions" ]]; then
                            COMPREPLY=( $(compgen -W "$project_suggestions" -- ${cur}) )
                        else
                            # If no project keys are available after filtering
                            COMPREPLY=( $(compgen -W "<Type-Issue-Key>" -- ${cur}) )
                        fi
                    fi
                else
                    # User-friendly hint if no projects found
                    COMPREPLY=( $(compgen -W "<Type-Issue-Key>" -- ${cur}) )
                fi
                return 0
            fi
            # Handle options for the issue command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=( $(compgen -W "--json -j --debug -d --worklogs -w --start-date -s --end-date -e --all-time -a" -- ${cur}) )
            fi
            # Handle option arguments
            case "${prev}" in
                --start-date|-s|--end-date|-e)
                    # Date format suggestion
                    COMPREPLY=( $(compgen -W "$(date +%Y-%m-%d)" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        tickets)
            # When we need a project key
            if [[ ${prev} == "tickets" ]]; then
                # Get project keys from cache or command
                local project_keys=$(_taskra_cache_projects)
                
                if [[ -n "$project_keys" ]]; then
                    # Filter out empty lines and build suggestion list
                    local project_list=""
                    while read -r project; do
                        if [[ -n "$project" ]]; then
                            project_list+="$project "
                        fi
                    done <<< "$project_keys"
                    
                    if [[ -n "$project_list" ]]; then
                        COMPREPLY=( $(compgen -W "$project_list" -- ${cur}) )
                    else
                        # If no project keys are available after filtering
                        COMPREPLY=( $(compgen -W "<Project-Key>" -- ${cur}) )
                    fi
                else
                    # User-friendly hint if no projects found
                    COMPREPLY=( $(compgen -W "<Project-Key>" -- ${cur}) )
                fi
                return 0
            fi
            # Handle options for the tickets command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=( $(compgen -W "--start-date -s --end-date -e --status --assignee --reporter --worklog-user --num-tickets -n --group-by -g --sort-by -b --format -f --debug -d --sort-order -o" -- ${cur}) )
            fi
            # Handle option arguments
            case "${prev}" in
                --start-date|-s|--end-date|-e)
                    # Date format suggestion
                    COMPREPLY=( $(compgen -W "$(date +%Y-%m-%d)" -- ${cur}) )
                    return 0
                    ;;
                --group-by|-g)
                    COMPREPLY=( $(compgen -W "status assignee none" -- ${cur}) )
                    return 0
                    ;;
                --sort-by|-b)
                    COMPREPLY=( $(compgen -W "created updated status assignee priority" -- ${cur}) )
                    return 0
                    ;;
                --format|-f)
                    COMPREPLY=( $(compgen -W "table json csv" -- ${cur}) )
                    return 0
                    ;;
                --sort-order|-o)
                    COMPREPLY=( $(compgen -W "asc desc" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        worklogs)
            if [[ ${cur} == -* ]]; then
                COMPREPLY=( $(compgen -W "--username -u --start -s --end -e --json -j --debug -d" -- ${cur}) )
            fi
            # Handle option arguments
            case "${prev}" in
                --username|-u)
                    # Could potentially fetch users from cache
                    return 0
                    ;;
                --start|-s|--end|-e)
                    # Date format suggestion
                    COMPREPLY=( $(compgen -W "$(date +%Y-%m-%d)" -- ${cur}) )
                    return 0
                    ;;
                --debug|-d)
                    COMPREPLY=( $(compgen -W "none error info verbose" -- ${cur}) )
                    return 0
                    ;;
            esac
            ;;
        config)
            # Subcommands for config
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "list add remove set-default current debug" -- ${cur}) )
                return 0
            fi
            
            # Options for each subcommand
            local subcmd=${COMP_WORDS[2]}
            case "${subcmd}" in
                add)
                    if [[ ${cur} == -* ]]; then
                        COMPREPLY=( $(compgen -W "--name -n --url -u --email -e" -- ${cur}) )
                    fi
                    ;;
                remove|set-default)
                    # Get account names from config if available
                    COMPREPLY=( $(compgen -W "$(taskra config list 2>/dev/null | grep -oE '[a-zA-Z0-9_-]+')" -- ${cur}) )
                    ;;
            esac
            ;;
        *)
            # Complete top-level commands
            if [[ ${cur} == -* ]]; then
                COMPREPLY=( $(compgen -W "--help --version" -- ${cur}) )
            else
                COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            fi
            ;;
    esac
}

# Register the completion function
complete -F _taskra_completion taskra
