FROM meltano/meltano:latest-python3.11

RUN meltano init melt-project
WORKDIR "/project/melt-project"

ARG MELTANO_LOADER_NAME=target-postgres
ENV MELTANO_LOADER=$MELTANO_LOADER_NAME

RUN meltano add loader $MELTANO_LOADER_NAME
RUN meltano add extractor tap-riotapi --from-ref https://raw.githubusercontent.com/ColleenN/riot_tap/refs/heads/main/plugin.yml

ENTRYPOINT meltano run tap-riotapi $MELTANO_LOADER