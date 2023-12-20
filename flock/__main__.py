import click
import tomli

from .simulation import Simulation


@click.argument(
    "config", default="config.toml", type=click.File("rb")
)
@click.command
def cli(config) -> None:
    """Boid flock simulator.
    
    The simulation is defined by a configuration file provided as an
    argument. If one is not provided, a default file of "config.toml" is
    used.
    
    To view a demo, run the program without arguments or use one of the
    demo configurations in the demos/ folder."""

    conf = tomli.load(config)

    simulation = Simulation.from_config(conf)
    simulation.run()

if __name__ == "__main__":
    cli()
