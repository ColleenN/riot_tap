#!/bin/bash

if [ -f "$MELTANO_YML_PATH" ]; then
    cp --force "$MELTANO_YML_PATH" /project/melt-project/meltano.yml
fi

STATE_ID_ARGS=()
if [ -n "$STATE_ID" ]; then
    STATE_ID_ARGS=(--state-id "$STATE_ID")
fi

meltano el tap-riotapi target-bigquery "${STATE_ID_ARGS[@]}"