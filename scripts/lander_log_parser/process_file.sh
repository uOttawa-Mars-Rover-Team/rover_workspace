#!/bin/bash

declare -A processed_lines

function stringContain() { case $2 in *$1*) return 0 ;; *) return 1 ;; esac }

function process_line() {
    if stringContain Cell "$1"; then
        cell_number=$(echo "$1" | cut -d ' ' -f 4)
        status=$(echo "$1" | cut -d ' ' -f 6)

        if [ -v processed_lines[$cell_number] ]; then

            value="${processed_lines[$cell_number]}"
            current=$(echo "$value" | cut -d ',' -f 1)

            if [ $current != $status ]; then
                processed_lines[$cell_number]="${status}, ${value}"
            fi

        else
            processed_lines[$cell_number]="$status"
        fi
    fi
}

function read_lines() {
    while read LINE; do
        process_line "$LINE"
    done <$1
}

read_lines $1

for cell in "${!processed_lines[@]}"; do
    tmp=$(echo "${processed_lines[$cell]}" | cut -d ',' -f 1)
    echo "${cell}: ${tmp}"
done
