FROM meltano/meltano:latest-python3.11

RUN meltano init melt-project
WORKDIR "/project/melt-project"

RUN meltano add --install target-bigquery

COPY . /opt/riot_tap
RUN meltano add extractor tap-riotapi --from-ref /opt/riot_tap/plugin.yml
# Replace the GitHub install with this checkout, keeping pip_url so Meltano won't reinstall at runtime.
RUN python -m uv pip install --python .meltano/extractors/tap-riotapi/venv/bin/python \
    --no-deps --reinstall /opt/riot_tap

RUN pip install psycopg2-binary

COPY --chmod=755 entrypoint.sh /project/melt-project
ENTRYPOINT ./entrypoint.sh
