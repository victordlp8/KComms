from aiomcrcon import Client  # type: ignore
from enum import Enum
import asyncio
import toml  # type: ignore
import os
import re


class KComms(Client):
    def __new__(self, path: str):
        SECRET = KComms.load_config(path)["SERVER"]

        return Client(SECRET["ip"], SECRET["port"], SECRET["password"])

    @staticmethod
    def load_config(path: str):
        with open(path, "r") as c:
            config = toml.load(c)

        return config


class Minecraft:
    class Type(Enum):
        SCORE = "score"
        TEAM = "team"

    class Parser:
        def __new__(self, type: "Minecraft.Type", data):
            match type:
                case Minecraft.Type.SCORE:
                    return Minecraft.Parser.parse_scores(data)

                case Minecraft.Type.TEAM:
                    return Minecraft.Parser.parse_team(data)

        @staticmethod
        def parse_scores(data) -> dict:
            r = data[0]

            r = r.split(":")
            r[0] = r[0].split(" ")

            entity = r[0][0]

            if r[0][2] == "no":
                n_scores = 0
                scores: dict = {}

                d = {entity: {"n_scores": n_scores, "scores": scores}}

            else:
                n_scores = int(r[0][2])

                r = "".join(r[1:])
                r = r.split("[")

                scores = {}
                for r in r[1:]:
                    r = r.split("]")
                    score = r[0]
                    value = r[1]

                    try:
                        value = float(value)
                    except ValueError:
                        pass

                    scores[score] = value

                d = {entity: {"n_scores": n_scores, "scores": scores}}

            return d

        @staticmethod
        def parse_team(data) -> dict:
            r = data[0].split(":")

            team = re.findall(r"\[(.*?)\]", r[0])[0]

            n_teammates = int(r[0].split(" ")[3])
            teammates = r[1].strip().split(", ")

            d = {team: {"n_teammates": n_teammates, "teammates": teammates}}

            return d


class Entity:
    def __init__(self, entity_name: str):
        self.entity_name = entity_name

    @staticmethod
    async def scoreboard(*args) -> dict | bool:
        if len(args) == 2 and isinstance(args[1], Client):
            self: Entity = args[0]  # type: ignore
            K: KComms = args[1]  # type: ignore

            return await Entity.scoreboard(K, self.entity_name)

        elif len(args) == 2 and isinstance(args[0], Client):
            K: KComms = args[0]  # type: ignore
            entity: str = args[1]  # type: ignore

            cmd = f"scoreboard players list {entity}"

            r = await K.send_cmd(cmd)
            r = Minecraft.Parser(Minecraft.Type.SCORE, r)

            return r

        return False


class Team:
    def __init__(self, team_id: str):
        self.team_id = team_id

    @staticmethod
    async def list(*args) -> dict | bool:
        if len(args) == 2 and isinstance(args[1], Client):
            self: Team = args[0]  # type: ignore
            K: KComms = args[1]  # type: ignore

            return await Team.list(K, self.team_id)

        elif len(args) == 2 and isinstance(args[0], Client):
            K: KComms = args[0]  # type: ignore
            team_id: str = args[1]  # type: ignore

            cmd = f"team list {team_id}"

            r = await K.send_cmd(cmd)
            r = Minecraft.Parser(Minecraft.Type.TEAM, r)

            return r

        return False


async def main():
    secret_path = os.path.join("config", "secret.toml")
    K = KComms(secret_path)
    await K.connect()

    cmd = "scoreboard players list victordlp8"

    r = await K.send_cmd(cmd)
    print(r)


if __name__ == "__main__":
    asyncio.run(main())
