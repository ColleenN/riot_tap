FROM meltano/meltano:latest-python3.11

RUN meltano init melt-project
WORKDIR "/project/melt-project"

RUN meltano add --install target-bigquery
RUN meltano add extractor tap-riotapi --from-ref https://raw.githubusercontent.com/ColleenN/riot_tap/refs/heads/main/plugin.yml
RUN pip install psycopg2-binary

COPY --chmod=+x entrypoint.sh /project/melt-project
ENTRYPOINT ./entrypoint.sh