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

# Output file option (YAML or CUE files)
complete -c tagger -s o -l output -d 'Output YAML file name' -r -F -a '(
    for file in *.{yaml,yml,cue}
        test -f $file; and echo $file
    end
)'

# Segment option (audio files)
complete -c tagger -l segment -d 'Segment a DJ mix and generate CUE sheet' -r -F -a '(
    for file in *.{mp3,m4a,aac,wav,flac,ogg}
        test -f $file; and echo $file
    end
)'

# Sensitivity option
complete -c tagger -l sensitivity -d 'Detection sensitivity (0.0-1.0)' -r

# Tracklist options
complete -c tagger -l tracklist -d 'Tracklist source (clipboard/file/URL)' -r -F -a '(
    echo clipboard
    for file in *.{txt,md}
        test -f $file; and echo $file
    end
)'

complete -c tagger -l tracklist-file -d 'Read tracklist from text file' -r -F -a '(
    for file in *.{txt,md}
        test -f $file; and echo $file
    end
)'

complete -c tagger -l tracklist-clipboard -d 'Read tracklist from clipboard'

# Recognition options
complete -c tagger -l recognize -d 'Use music recognition to identify tracks'
complete -c tagger -l verify-boundaries -d 'Verify detected boundaries using music recognition'

# Positional argument: YAML files
complete -c tagger -n '__fish_is_first_arg' -r -F -a '(
    for file in *.{yaml,yml}
        test -f $file; and echo $file
    end
)'
