# Bash completion for tagger
# Source this file to enable completion:
#   source completions/tagger.bash
# Or install to your completion directory:
#   cp completions/tagger.bash /usr/local/etc/bash_completion.d/

_tagger() {
    local cur prev opts subcommands reminder_opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Global options (work with all commands)
    opts="-e --execute -v --version -h --help --no-color"

    # Tag mode specific options
    tag_opts="-o --output --prefer-filename --thumbnail-crop"

    # Reminder mode specific options
    reminder_opts="-t --title -l --list -n --notes --match-audio"

    # Subcommands
    subcommands="reminder"

    # Options that require a value
    case "$prev" in
        -o|--output)
            # Complete with .yaml files
            COMPREPLY=( $(compgen -f -X '!*.@(yaml|yml)' -- "$cur") )
            return 0
            ;;
        --thumbnail-crop)
            # Complete with cropping options
            COMPREPLY=( $(compgen -W "auto square none" -- "$cur") )
            return 0
            ;;
        -t|--title|-l|--list|-n|--notes)
            # These options require string arguments, no completion
            return 0
            ;;
        *)
            ;;
    esac

    # Check if we're in reminder mode
    local in_reminder_mode=0
    local reminder_subcommand=""
    for ((i=1; i<COMP_CWORD; i++)); do
        if [[ "${COMP_WORDS[i]}" == "reminder" ]]; then
            in_reminder_mode=1
            # Check for reminder subcommand
            if [[ $((i+1)) -lt ${COMP_CWORD} ]]; then
                reminder_subcommand="${COMP_WORDS[i+1]}"
            fi
            break
        fi
    done

    # If in reminder mode
    if [[ $in_reminder_mode -eq 1 ]]; then
        # If we're right after 'reminder', complete with reminder subcommands
        if [[ "${COMP_WORDS[COMP_CWORD-1]}" == "reminder" ]]; then
            COMPREPLY=( $(compgen -W "add" -- "$cur") )
            return 0
        fi

        # If we're in 'reminder add', complete with reminder options
        if [[ "$reminder_subcommand" == "add" ]]; then
            if [[ "$cur" == -* ]]; then
                COMPREPLY=( $(compgen -W "$opts $reminder_opts" -- "$cur") )
                return 0
            fi
            # For URL argument, no completion
            return 0
        fi

        return 0
    fi

    # First positional argument: can be subcommand or YAML file
    if [[ $COMP_CWORD -eq 1 ]] || ([[ $COMP_CWORD -gt 1 ]] && [[ "${COMP_WORDS[COMP_CWORD-1]}" == -* ]]); then
        # If it starts with -, complete with options
        if [[ "$cur" == -* ]]; then
            COMPREPLY=( $(compgen -W "$opts $tag_opts" -- "$cur") )
            return 0
        fi

        # Otherwise, complete with subcommands and YAML files
        local completions="$subcommands $(compgen -f -X '!*.@(yaml|yml)' -- "$cur")"
        COMPREPLY=( $(compgen -W "$completions" -- "$cur") )
        return 0
    fi

    # Complete options for tag mode
    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "$opts $tag_opts" -- "$cur") )
        return 0
    fi

    # Complete with YAML files for tag mode
    COMPREPLY=( $(compgen -f -X '!*.@(yaml|yml)' -- "$cur") )
}

complete -F _tagger tagger
