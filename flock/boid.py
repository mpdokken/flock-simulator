import math
import random

from typing_extensions import Self


class Boid:
    """A class to simulate a boid and keep track of its position and
    velocity."""

    def __init__(
        self,
        flock,
        x: float,
        y: float,
        vx: float,
        vy: float,
    ) -> None:
        self.flock = flock
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

        self.pos_history = []

    def update_position(self) -> None:
        self.pos_history.append((self.x, self.y))
        if len(self.pos_history) > self.flock.tracer_len:
            self.pos_history.pop(0)

        self.x += self.vx
        self.y += self.vy

    @classmethod
    def create_random(
        cls: type[Self],
        flock,
        min_position: tuple[float, float],
        max_position: tuple[float, float],
        min_velocity: float,
        max_velocity: float,
    ):
        """Create and return a boid with a random position and velocity."""

        x = random.uniform(min_position[0], max_position[0])
        y = random.uniform(min_position[1], max_position[1])

        vx = random.uniform(min_velocity, max_velocity)
        vy = random.uniform(min_velocity, max_velocity)

        return cls(flock, x, y, vx, vy)

    def in_range(self, other: "Boid") -> bool:
        """Return whether the other boid is within this boid's range of
        sight."""

        return (
            math.dist((self.x, self.y), (other.x, other.y))
            <= self.flock.sight_range
        )
