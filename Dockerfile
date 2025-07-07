FROM meltano/meltano:latest-python3.12

RUN meltano init melt-project
WORKDIR "/project/melt-project"

ENV MELTANO_LOADER=target-postgres

RUN meltano add loader $MELTANO_LOADER
RUN meltano add extractor tap-riotapi --from-ref https://raw.githubusercontent.com/ColleenN/riot_tap/refs/heads/main/plugin.yml

ENTRYPOINT meltano run tap-riotapi $MELTANO_LOADER