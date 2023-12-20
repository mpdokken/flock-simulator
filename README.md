# Flock Simulator

![flock gif](https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzR2bGFsazJqY28wM2ZqcWFwejQyeTJkcnh3M2o5aHVqdWkxbnBmOSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/55pW0cL1wTTsIErkl7/giphy.gif)

## Overview

Pygame application for simulating flocks of boids.

The boids follow several movement rules:

- Don't get too close to other boids (separation)
- Don't stray too far from the flock (cohesion)
- Fly the same direction as the flock (alignment)
- Pursue or flee from other flocks (affinity)

## Usage

To run the program, create a virtual environment and install the dependencies:

```
python3 -m virtualenv .venv
./.venv/bin/activate
pip install -r requirements.txt
```

Run the program with `python3 -m flock` or `python3 -m flock some_config_file.toml `.

The simulation is defined by a TOML configuration file which may be provided as an argument. If an argument is not provided, `config.toml `is used. Demo simulations are included in the `demos/`folder. The default `config.toml` file includes documentation comments explaining each configuration setting.
