import math
from typing import Any
from typing_extensions import Self


from .boid import Boid
from .color import ColorType, lighten


class Flock:
    """A class to manage a group of boids with common behavior.

    The boids follow movement rules for alignment, separation, cohesion,
    and affinity to pursue or flee other flocks."""

    def __init__(
        self,
        simulation,
        id: str | None,
        num_boids: int,
        affinity: list[tuple[str, float]],
        alignment: float,
        separation: float,
        cohesion: float,
        min_separation: float,
        max_speed: float,
        boundary_force: float,
        sight_range: float,
        color: ColorType,
        tracer_len: int,
        tracer_shade: float,
        tracer_enabled: bool,
    ) -> None:
        # A reference to the Simulation instance, so the flock may access
        # other flocks.
        self.simulation = simulation

        # The optional ID of the flock. This is only necessary if another
        # flock must reference this flock in its affinity list.
        self.id = id

        # The number of boids in the flock.
        self.num_boids = num_boids

        # A list of pairs consisting of a flock ID and an affinity value. A
        # positive affinity makes boids in this flock chase the target
        # flock, while a negative affinity makes them flee. This affinity
        # makes the "predator" flock chase the "prey" flock.
        self.affinity = affinity

        # How closely the boid's direction of movement should match its
        # neighbors.
        self.alignment = alignment

        # How strongly the boid should move away from its neighbors when they get
        # within the min_separation distance.
        self.separation = separation

        # How closely the boid should stay to the center of its neighbors.
        self.cohesion = cohesion

        # The minimum distance between the boid and its neighbors.
        self.min_separation = min_separation

        # The maximum possible velocity for the boid.
        self.max_speed = max_speed

        # The force applied opposite to the boid when it leaves the
        # boundaries of the window, to bring it back into view. If this
        # value is lower than forces pushing a boid out of the window, it
        # may not return.
        self.boundary_force = boundary_force

        # The boid only targets other boids within this distance to
        # determine its movement patterns, including pursuing/fleeing other
        # flocks.
        self.sight_range = sight_range

        # The RGB color value of the boid.
        self.color = color

        # The number of previous locations of the boid to be included in
        # the tracer.
        self.tracer_len = tracer_len

        # A modifier of the boid's color to determine the tracer color; a
        # value of 0.5 makes the tracer 50% lighter than the boid's color.
        self.tracer_color = lighten(self.color, tracer_shade)

        # Whether to display the tracer.
        self.tracer_enabled = tracer_enabled

        # Initialize a list of boids with random position and velocity.
        dimensions = (self.simulation.width / 2, self.simulation.height / 2)
        min_velocity = -1
        max_velocity = 1
        self.boids: list[Boid] = [
            Boid.create_random(
                self,
                (0, 0),
                dimensions,
                min_velocity,
                max_velocity,
            )
            for _ in range(num_boids)
        ]

    def update_boid(self, boid: Boid) -> None:
        """Apply the behavior rules to the boid then update its position."""

        # Calculate alignment first, because the other rules modify the
        # velocity which is used in these calculations.
        self.rule_alignment(boid)
        self.rule_cohesion(boid)
        self.rule_separation(boid)
        self.rule_affinity(boid)

        # Perform speed and bounds checks.
        self.limit_speed(boid)
        self.keep_in_bounds(boid)

        # Move the boid according to its new velocity.
        boid.update_position()

    @classmethod
    def from_config(cls, simulation, config: dict[str, Any]) -> Self:
        """Create and return a flock of boids from a configuration dict.

        The dict corresponds to one of the `[[flocks]]` array entries in
        the TOML config file."""

        return cls(
            simulation,
            config.get("id"),
            config["count"],
            config.get("affinity", []),
            config["alignment"],
            config["separation"],
            config["cohesion"],
            config["min_separation"],
            config["max_speed"],
            config["boundary_force"],
            config["sight_range"],
            config["color"],
            config["tracer"]["length"],
            config["tracer"]["shade"],
            config["tracer"]["enabled"],
        )

    def rule_affinity(self, boid: Boid) -> None:
        """If this flock has a positive or negative affinity toward another
        flock, move the boid toward or away from the closest boid in that
        flock."""

        for flock_id, affinity in self.affinity:
            # Lookup the flock by its ID.
            flock: Flock = self.simulation.get_flock(flock_id)

            # Find the closest boid in the other flock using the distance
            # as a comparison key.
            closest = min(
                flock.boids,
                key=lambda other: math.dist(
                    (boid.x, boid.y), (other.x, other.y)
                ),
            )

            # Only pursue/flee if the boid can see the other boid.
            if boid.in_range(closest):
                boid.vx += (closest.x - boid.x) * affinity
                boid.vy += (closest.y - boid.y) * affinity

    def rule_alignment(self, boid: Boid) -> None:
        """Align the boid's velocity with the other boids in the flock."""

        avg_vx = 0.0
        avg_vy = 0.0

        # Take the average of the neighboring boid's velocity.
        for other in self.boids:
            if boid is not other and boid.in_range(other):
                avg_vx += other.vx
                avg_vy += other.vy

        # Modify the boid's velocity based on the average neighbor velocity
        # and the flock's alignment value.
        avg_vx = (avg_vx - boid.vx) * self.alignment
        avg_vy = (avg_vy - boid.vy) * self.alignment
        boid.vx += avg_vx
        boid.vy += avg_vy

    def rule_separation(self, boid: Boid) -> None:
        """Make the boid avoid other boids in the flock that get too close."""

        vx = 0.0
        vy = 0.0

        # Steer the boid away from every neighboring boid that is too close.
        for other in self.boids:
            if other != boid:
                if (
                    math.dist((boid.x, boid.y), (other.x, other.y))
                    < self.min_separation
                ):
                    vx += boid.x - other.x
                    vy += boid.y - other.y

        # Modify the boid's velocity based on the calculated change and the
        # flock's alignment value.
        boid.vx += vx * self.separation
        boid.vy += vy * self.separation

    def rule_cohesion(self, boid: Boid) -> None:
        """Point the boid's velocity toward the center of the other boids
        in the flock within its line of sight."""

        center_x = 0.0
        center_y = 0.0
        # Count the number of neighbors to use in the average calculation.
        num_neighbors = 0

        # Calculate the average position of the neighboring boids.
        for other in self.boids:
            if boid is not other and boid.in_range(other):
                center_x += other.x
                center_y += other.y
                num_neighbors += 1

        # If there are no neighbors, no adjustment needs to be made.
        if num_neighbors == 0:
            return

        center_x /= num_neighbors
        center_y /= num_neighbors

        # Modify the boid's velocity to steer it towards the center of the
        # flock.
        boid.vx += (center_x - boid.x) * self.cohesion
        boid.vy += (center_y - boid.y) * self.cohesion

    def limit_speed(self, boid: Boid) -> None:
        """Limit the boid's speed to a maximum value."""

        # If the boid is too fast, set the speed to the max speed but
        # preserve the direction.
        speed = math.hypot(boid.vx, boid.vy)
        if speed > self.max_speed:
            boid.vx = (boid.vx / speed) * self.max_speed
            boid.vy = (boid.vy / speed) * self.max_speed

    def keep_in_bounds(self, boid: Boid) -> None:
        """Keep the boid within the window, turning it back if it strays
        outside."""

        # Convert the coordinates to absolute so they can be compared with
        # the window boundaries.
        x, y = self.simulation.absolute_coords((boid.x, boid.y))

        magnitude = math.hypot(boid.vx, boid.vy)

        if x < 0:
            boid.vx += self.boundary_force
        elif x > self.simulation.width:
            boid.vx -= self.boundary_force

        if y < 0:
            boid.vy += self.boundary_force
        elif y > self.simulation.height:
            boid.vy -= self.boundary_force

        # If the velocity correction made the boid speed up, set the speed
        # to the previous value while keeping the new direction.
        new_magnitude = math.hypot(boid.vx, boid.vy)
        if new_magnitude > magnitude:
            boid.vx, boid.vy = _set_magnitude((boid.vx, boid.vy), magnitude)

    def get_center(self) -> tuple[float, float]:
        """Return the (x, y) coordinates of the center of the flock."""

        x = sum(boid.x for boid in self.boids) / len(self.boids)
        y = sum(boid.y for boid in self.boids) / len(self.boids)
        return (x, y)


def _set_magnitude(
    v: tuple[float, float], magnitude: float
) -> tuple[float, float]:
    """Return a new vector with the same direction as `v`, but with the
    given magnitude."""

    x, y = v

    current_magnitude = math.sqrt(x**2 + y**2)
    if current_magnitude == 0:
        return (0, 0)
    else:
        scale_factor = magnitude / current_magnitude
        return (x * scale_factor, y * scale_factor)
