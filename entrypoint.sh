#!/bin/bash

while [[ $# -gt 0 ]]; do
    case "$1" in
        --extra-meltano-args)
            MELTANO_EXTRA_ARGS="$2"
            shift # Shift past --extra-meltano-args
            shift # Shift past the value
            ;;
        --extra-tap-args)
            TAP_EXTRA_ARGS="$2"
            shift # Shift past --extra-tap-args
            shift # Shift past the value
            ;;
        --extra-loader-args)
            LOADER_EXTRA_ARGS="$2"
            shift # Shift past --extra-loader-args
            shift # Shift past the value
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done



if [ -f "$MELTANO_YML_PATH" ]; then
    cp --force "$MELTANO_YML_PATH" /project/melt-project/meltano.yml
fi
meltano run "${MELTANO_EXTRA_ARGS:-''}" tap-riotapi "${TAP_EXTRA_ARGS:-''}" target-bigquery "${LOADER_EXTRA_ARGS:-''}"