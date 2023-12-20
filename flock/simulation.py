import sys
import time
from typing import Any

from typing_extensions import Self

import pygame

from .boid import Boid
from .flock import Flock
from .color import ColorType


class Simulation:
    """A class to manage the Pygame interface and flocks of boids."""

    def __init__(
        self,
        flock_config: list[dict[str, Any]],
        window_size: tuple[int, int],
        background_color: ColorType,
        step_length: float,
    ) -> None:
        self.width, self.height = window_size
        self.background_color = background_color
        self.step_length = step_length

        self.window = pygame.display.set_mode(window_size, pygame.RESIZABLE)
        pygame.display.set_caption("Flock Simulator")

        # Initialize the list of flocks from a list of configuration dicts.
        self.flocks = [
            Flock.from_config(self, conf) for conf in flock_config
        ]

    @classmethod
    def from_config(cls, config: dict) -> Self:
        """Load the simulation from a configuration dict."""

        # Load the flock configuration settings but don't initialize the
        # flocks yet. This must happen in __init__() because each flock
        # must hold a reference to the initialized Simulation instance.
        flock_config = config["flocks"]

        window_size = config["window"]["dimensions"]
        background_color = config["window"]["background_color"]

        step_length = config["simulation"]["step_length"]

        return cls(flock_config, window_size, background_color, step_length)

    def absolute_coords(
        self, point: tuple[float, float]
    ) -> tuple[float, float]:
        """Convert the coordinate from relative to the center of the window
        to absolute, so that (0, 0) is at the center of the window."""

        return (point[0] + self.width / 2, point[1] + self.height / 2)

    def draw_tracer(self, boid: Boid) -> None:
        """Draw a tracer behind the boid on the window without updating the
        display."""

        # Convert the points in the boid's position history to their
        # absolute position.
        absolute_points = [
            self.absolute_coords(point) for point in boid.pos_history
        ]

        # Only draw the tracer if there are at least two points in the
        # history.
        if len(absolute_points) > 2:
            pygame.draw.lines(
                self.window,
                boid.flock.tracer_color,
                False,
                absolute_points,
            )

    def draw_entity(self, boid: Boid) -> None:
        """Draw the boid on the window without updating the display."""

        entity_size = 3
        # Convert the position of the entity to absolute.
        pos = self.absolute_coords((boid.x, boid.y))
        pygame.draw.circle(self.window, boid.flock.color, pos, entity_size)

    def run(self) -> None:
        """Run the simulation."""

        while True:
            # Keep track of the time at each tick for time normalization
            # purposes.
            current_time = time.time()

            self.window.fill(self.background_color)

            # Draw the tracers first so they appear beneath the boids.
            for flock in self.flocks:
                if not flock.tracer_enabled:
                    continue
                for boid in flock.boids:
                    self.draw_tracer(boid)

            # Draw the boids on top.
            for flock in self.flocks:
                for boid in flock.boids:
                    self.draw_entity(boid)
                    flock.update_boid(boid)

            # Only update the display after everything has been drawn.
            pygame.display.update()

            # After performing the calculations for the tick, sleep for the
            # rest of the tick. This ensures the simulation doesn't run
            # too fast in cases of low computational overhead.
            elapsed_time = time.time() - current_time
            remaining_sleep = self.step_length - elapsed_time
            if remaining_sleep > 0:
                time.sleep(remaining_sleep)

            # Handle the Pygame events for resizing the window and quitting.
            for event in pygame.event.get():
                match event.type:
                    case pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    case pygame.VIDEORESIZE:
                        self.width = event.w
                        self.height = event.h

    def get_flock(self, id: str) -> Flock:
        """Return the flock with the given id, or raise `KeyError` if
        one does not exist."""

        for flock in self.flocks:
            if flock.id is not None and flock.id == id:
                return flock

        raise KeyError(f'No flock exists with id "{id}".')
