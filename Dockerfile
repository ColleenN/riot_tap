FROM meltano/meltano:latest-python3.12

RUN meltano init melt-project
WORKDIR "/project/melt-project"

RUN meltano add loader target-postgres
RUN meltano add extractor tap-riotapi --from-ref https://raw.githubusercontent.com/ColleenN/riot_tap/refs/heads/main/plugin.yml

CMD ["run", "tap-riotapi", "target-postgres"]