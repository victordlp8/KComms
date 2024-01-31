import asyncio
import shutil
import os
import time

from PIL import Image  # type: ignore

from kcomms import KComms, Entity, Team

"""
[X] Player PAM Puntos/Asesinatos/Muertes of all players
[X] Player life
[X] Blue and Red scoreboard
[X] Player being spectated

OPTIONAL:
    [] Time
    [] Camera being watched
"""


class KTeam(Team):
    def __init__(self, K: KComms, name: str):
        self.K = K
        self.name = name

    async def update(self):
        self.data = await Team.list(self.K, self.name)

        try:
            self.points = int(
                (await Entity.scoreboard(self.K, self.name))[self.name]["scores"]["Points"]
            )
        except KeyError:
            self.points = 0

        self.players: list[KPlayer] = []  # type: ignore
        for player in self.data[self.name]["teammates"]:
            if player != self.name:
                player = KPlayer(self.K, player)
                await player.update()

                player.team = self.name

                self.players.append(player)

    def __str__(self):
        r = f"Team {self.name} has {self.points} points;"
        for player in self.players:
            r += f"\n\t{player}"

        return r

    def health2image(self, hearts_path: str, save_path: str):
        for player in self.players:
            player.health2image(hearts_path, save_path)

    def save_pam(self, save_path: str):
        for player in self.players:
            player.save_pam(save_path)

    def save_points(self, save_path: str):
        save_path = os.path.join(save_path, self.name, f"{self.name}.points")
        with open(save_path, "w") as f:
            f.write(f"{self.points}")


class KPlayer(Entity):
    def __init__(self, K: KComms, name: str):
        self.K = K
        self.name = name

    async def update(self):
        self.data = await Entity.scoreboard(self.K, self.name)

    def __str__(self):
        return f"{self.team} {self.name} {self.health} | PAM {self.points}/{self.kills}/{self.deaths} | Spectated {self.beingSpectated}"

    @property
    def health(self):
        try:
            return int(self.data[self.name]["scores"]["Health"])
        except KeyError:
            return 0

    @property
    def points(self):
        try:
            return int(self.data[self.name]["scores"]["Player Points"])
        except KeyError:
            return 0

    @property
    def kills(self):
        try:
            return int(self.data[self.name]["scores"]["Kills"])
        except KeyError:
            return 0

    @property
    def deaths(self):
        try:
            return int(self.data[self.name]["scores"]["Deaths"])
        except KeyError:
            return 0

    @property
    def team(self):
        return self._team

    @team.setter
    def team(self, value):
        self._team = value

    @property
    def beingSpectated(self):
        try:
            return self.data[self.name]["scores"]["beingSpectated"] == 1
        except KeyError:
            return False

    def health2image(self, hearts_path: str, save_path: str):
        if self.team == "Red":
            hearts_path = os.path.join(hearts_path, "red")
        elif self.team == "Blue":
            hearts_path = os.path.join(hearts_path, "blue")

        if self.health > 20:
            hearts = 10
            half_hearts = 0

            golden_hearts = int((self.health - 20) / 2)
            golden_half_hearts = int((self.health - 20) % 2)

        else:
            hearts = int(self.health / 2)
            half_hearts = int(self.health % 2)

            golden_hearts = 0
            golden_half_hearts = 0

        pixel_space = 4

        with Image.open(os.path.join(hearts_path, "full_heart.png")) as heart:
            heart_width = heart.width
            heart_height = heart.height

            total_width = 10 * (heart_width + pixel_space)
            total_height = heart_height

            health_image = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))
            for i in range(hearts):
                health_image.paste(heart, (i * (heart_width + pixel_space), 0))

        if half_hearts == 1:
            half_heart = Image.open(os.path.join(hearts_path, "half_heart.png"))
            health_image.paste(half_heart, (hearts * (heart_width + pixel_space), 0))

        with Image.open(os.path.join(hearts_path, "empty_heart.png")) as empty_heart:
            for i in range(hearts + half_hearts, 10):
                health_image.paste(empty_heart, (i * (heart_width + pixel_space), 0))

        # GOLDEN HEARTS --------------------------------
        if golden_hearts > 0 or golden_half_hearts > 0:
            with Image.open(
                os.path.join(hearts_path, "golden_full_heart.png")
            ) as golden_heart:
                for i in range(golden_hearts):
                    health_image.paste(
                        golden_heart, (i * (heart_width + pixel_space), 0)
                    )

            if golden_half_hearts == 1:
                golden_half_heart = Image.open(
                    os.path.join(hearts_path, "golden_half_heart.png")
                )
                health_image.paste(
                    golden_half_heart, (golden_hearts * (heart_width + pixel_space), 0)
                )

        # FLIP IF BLUE --------------------------------
        if self.team == "Blue":
            health_image = health_image.transpose(Image.FLIP_LEFT_RIGHT)

        save_path = os.path.join(save_path, self.team, "health", f"{self.name}.png")

        if not os.path.exists(os.path.dirname(save_path)):
            os.makedirs(os.path.dirname(save_path))
        health_image.save(save_path)

    def save_pam(self, save_path: str):
        save_path = os.path.join(save_path, self.team, "pam", f"{self.name}.pam")

        if not os.path.exists(os.path.dirname(save_path)):
            os.makedirs(os.path.dirname(save_path))
            
        with open(save_path, "w") as f:
            f.write(f"{self.points}/{self.kills}/{self.deaths}")


class KTowers:
    def __init__(self, K: KComms, teams: list[str]):
        self.K = K
        self.team_names = teams

    async def update(self):
        self.teams: list[KTeam] = []  # type: ignore
        for team in self.team_names:
            team = KTeam(self.K, team)
            await team.update()

            self.teams.append(team)

    @staticmethod
    def purge_obs_files(save_path: str):
        try:
            shutil.rmtree(save_path)
            print(f"The folder {save_path} and all its contents have been deleted succesfully.")
        except OSError:
            pass

    @property
    def spectating(self):
        spectated = None

        for team in self.teams:
            for player in team.players:
                if player.beingSpectated:
                    spectated = player.name

        return spectated

    def health2image(self, hearts_path: str, save_path: str):
        for team in self.teams:
            team.health2image(hearts_path, save_path)

    def save_pam(self, save_path: str):
        for team in self.teams:
            team.save_pam(save_path)

    def save_points(self, save_path: str):
        for team in self.teams:
            team.save_points(save_path)

    def save_all(self, assets_path: str, save_path: str):
        hearts_path = os.path.join(assets_path, "hearts")

        self.health2image(hearts_path, save_path)
        self.save_pam(save_path)
        self.save_points(save_path)

        with open(os.path.join(save_path, "spectating.txt"), "w") as f:
            if self.spectating:
                f.write(self.spectating)
            else:
                f.write("")


async def main():
    secret_path = os.path.join("config", "secret.toml")
    K = KComms(secret_path)
    await K.connect()

    config_path = os.path.join("config", "config.toml")
    CONFIG = KComms.load_config(config_path)["KTOWERS"]

    KTowers.purge_obs_files(CONFIG["obs_path"])
    ktowers = KTowers(K, CONFIG["teams"])

    print("Updating KTowers information...")
    while True:
        await ktowers.update()

        ktowers.save_all(CONFIG["assets_path"], CONFIG["obs_path"])

        time.sleep(CONFIG["step_time"])


if __name__ == "__main__":
    asyncio.run(main())
