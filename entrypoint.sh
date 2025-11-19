#!/bin/bash

if [ -f "$MELTANO_YML_PATH" ]; then
    cp --force "$MELTANO_YML_PATH" /project/melt-project/meltano.yml
fi
meltano run tap-riotapi target-bigquery