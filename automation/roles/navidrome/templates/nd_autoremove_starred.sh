#!/bin/bash

SQL="select path from annotation a JOIN media_file m on a.item_id = m.id where starred is TRUE;"
MUSIC_DIR="{{ MUSIC_DIR }}"
DB_PATH="{{ DATABASE_PATH }}"
LOG_FILE="{{ AUTOREMOVE_LOG_FILE }}"

# Ensure the log file is writable
touch "$LOG_FILE" || { echo "Error: Cannot create log file $LOG_FILE" >&2; exit 1; }

# Execute the SQL query and check for errors
output=$(sqlite3 "$DB_PATH" "$SQL")
if [ $? -ne 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') Error executing SQL query" >> "$LOG_FILE" >&2
    exit 1
fi

# Check if there are any files to delete
if [ -z "$output" ]; then
    # echo "$(date '+%Y-%m-%d %H:%M:%S') No files to delete" >> "$LOG_FILE"
    exit 0
fi

# Process each file path and delete
echo "$output" | while IFS= read -r path; do
    # Skip empty lines
    [ -z "$path" ] && continue

    full_path="${MUSIC_DIR%/}/$path"  # Properly join paths

    if [ -e "$full_path" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') Deleting: $full_path" >> "$LOG_FILE"
        rm -v "$full_path" >> "$LOG_FILE" 2>&1
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') File not found: $full_path" | tee -a "$LOG_FILE" >&2
    fi
done
