# Fish completion for tagger
# This file is automatically installed by Homebrew

# Disable file completion by default
complete -c tagger -f

# Basic options
complete -c tagger -s e -l execute -d 'Execute changes (default is dry-run mode)'
complete -c tagger -s v -l version -d 'Display version information'
complete -c tagger -s h -l help -d 'Display help message'
complete -c tagger -l no-color -d 'Disable colored output'
complete -c tagger -l prefer-filename -d 'Prefer metadata from filenames over embedded tags'

# Output file option (YAML files)
complete -c tagger -s o -l output -d 'Output YAML file name' -r -F -a '(
    for file in *.{yaml,yml}
        test -f $file; and echo $file
    end
)'

# Positional argument: YAML files
complete -c tagger -n '__fish_is_first_arg' -r -F -a '(
    for file in *.{yaml,yml}
        test -f $file; and echo $file
    end
)'
