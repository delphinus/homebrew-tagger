# Bash completion for tagger
# Source this file to enable completion:
#   source completions/tagger.bash
# Or install to your completion directory:
#   cp completions/tagger.bash /usr/local/etc/bash_completion.d/

_tagger() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # All options
    opts="-e --execute -o --output -v --version -h --help --no-color --prefer-filename"

    # Options that require a value
    case "$prev" in
        -o|--output)
            # Complete with .yaml files
            COMPREPLY=( $(compgen -f -X '!*.@(yaml|yml)' -- "$cur") )
            return 0
            ;;
        *)
            ;;
    esac

    # Complete options
    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
        return 0
    fi

    # Complete with YAML files for positional argument
    COMPREPLY=( $(compgen -f -X '!*.@(yaml|yml)' -- "$cur") )
}

complete -F _tagger tagger
