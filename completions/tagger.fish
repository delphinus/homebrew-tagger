# Fish completion for tagger
# This file is automatically installed by Homebrew

# Disable file completion by default
complete -c tagger -f

# Global options (work with all commands)
complete -c tagger -s e -l execute -d 'Execute changes (default is dry-run mode)'
complete -c tagger -s v -l version -d 'Display version information'
complete -c tagger -s h -l help -d 'Display help message'
complete -c tagger -l no-color -d 'Disable colored output'

# Tag mode specific options
complete -c tagger -n 'not __fish_seen_subcommand_from reminder' -l prefer-filename -d 'Prefer metadata from filenames over embedded tags'
complete -c tagger -n 'not __fish_seen_subcommand_from reminder' -l thumbnail-crop -d 'YouTube thumbnail cropping' -r -a 'auto square none'

# Output file option (YAML files) - tag mode only
complete -c tagger -n 'not __fish_seen_subcommand_from reminder' -s o -l output -d 'Output YAML file name' -r -F -a '(
    for file in *.{yaml,yml}
        test -f $file; and echo $file
    end
)'

# Positional argument: YAML files or subcommands
complete -c tagger -n '__fish_is_first_arg' -r -F -a '(
    for file in *.{yaml,yml}
        test -f $file; and echo $file
    end
)'

# Subcommand: reminder
complete -c tagger -n '__fish_is_first_arg' -a 'reminder' -d 'Manage macOS Reminders (macOS only)'

# Reminder sub-subcommand: add
complete -c tagger -n '__fish_seen_subcommand_from reminder; and not __fish_seen_subcommand_from add' -a 'add' -d 'Add URL to Reminders'

# Reminder options (only when in 'reminder add' mode)
complete -c tagger -n '__fish_seen_subcommand_from reminder; and __fish_seen_subcommand_from add' -s t -l title -d 'Custom reminder title' -r
complete -c tagger -n '__fish_seen_subcommand_from reminder; and __fish_seen_subcommand_from add' -s l -l list -d 'Reminder list name' -r
complete -c tagger -n '__fish_seen_subcommand_from reminder; and __fish_seen_subcommand_from add' -s n -l notes -d 'Additional notes' -r
complete -c tagger -n '__fish_seen_subcommand_from reminder; and __fish_seen_subcommand_from add' -l match-audio -d 'Match URL with audio files for title'
