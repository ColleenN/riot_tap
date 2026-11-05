FROM meltano/meltano:latest-python3.11

RUN meltano init melt-project
WORKDIR "/project/melt-project"

RUN meltano add --install target-bigquery

COPY . /opt/riot_tap
RUN meltano add extractor tap-riotapi --from-ref /opt/riot_tap/plugin.yml
# Meltano installs the tap from plugin.yml's pip_url (GitHub main). Reinstall it
# from this checkout in the same venv instead. The pip_url, and so Meltano's
# install fingerprint, stays the same, so runs don't reinstall it from GitHub.
RUN python -m uv pip install --python .meltano/extractors/tap-riotapi/venv/bin/python \
    --no-deps --reinstall /opt/riot_tap

RUN pip install psycopg2-binary

COPY --chmod=755 entrypoint.sh /project/melt-project
ENTRYPOINT ./entrypoint.sh
