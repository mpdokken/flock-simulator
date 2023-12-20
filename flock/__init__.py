# Silence the advertisement text when importing Pygame and initialize it.
import contextlib

with contextlib.redirect_stdout(None):
    import pygame

pygame.init()
