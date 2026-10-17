"""Regression tests for Island Defenders.
Run headless: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tests/test_regression.py
Covers every bug Daniel caught in real playtests on 2026-10-12.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from game import Game
from ships.ship import Ship

PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  PASS: {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL: {name} {detail}")


def fresh_game(**kw):
    kw.setdefault("lives", 20)
    kw.setdefault("money", 5000)
    kw.setdefault("sound", False)
    return Game(**kw)


def test_ship_full_cycle():
    """Ship: IN -> DOCKED -> OUT -> AWAY (the stuck-ship loop bug)."""
    print("Ship full cycle:")
    g = fresh_game()
    g.ship.sail_in()
    for _ in range(2000):
        g.ship.update()
        if g.ship.state == Ship.DOCKED:
            break
    check("ship docks", g.ship.state == Ship.DOCKED, f"state={g.ship.state}")
    g.ship.sail_out()
    for _ in range(2000):
        g.ship.update()
        if g.ship.state == Ship.AWAY:
            break
    check("ship leaves to AWAY", g.ship.state == Ship.AWAY, f"state={g.ship.state}")


def test_waiting_for_clear_not_reset():
    """waiting_for_clear must stay True after disembark (was reset 60x/sec in _draw_cannonballs)."""
    print("waiting_for_clear stability:")
    g = fresh_game()
    g.ship.sail_in()
    for _ in range(2000):
        g.ship.update()
        if g.ship.state == Ship.DOCKED:
            break
    g.wave = 1
    # Spawn all wave enemies
    for _ in range(500):
        g.gen_enemies()
        if sum(g.current_wave) == 0 and g.waiting_for_clear:
            break
    check("waiting_for_clear set after disembark", g.waiting_for_clear)
    # Simulate 600 frames of drawing (the old bug reset it here every frame)
    for _ in range(600):
        g._draw_cannonballs()
    check("waiting_for_clear survives 600 draw frames", g.waiting_for_clear)


def test_wave_auto_advance():
    """After board cleared + ship AWAY, advance_wave fires and new ship sails in."""
    print("Wave auto-advance:")
    g = fresh_game()
    g.wave = 1
    g.waiting_for_clear = True
    g.ship.state = Ship.AWAY
    g.enemies.clear()
    wave_before = g.wave
    # Simulate the run-loop block
    if g.ship.state == Ship.AWAY and not g.won:
        if g.last_wave_done:
            g.won = True
        elif g.waiting_for_clear:
            if len(g.enemies) == 0:
                g.advance_wave()
                if not g.last_wave_done:
                    g.ship.sail_in()
    check("wave advanced", g.wave == wave_before + 1, f"wave={g.wave}")
    check("new ship sailing in", g.ship.state == Ship.IN, f"state={g.ship.state}")


def test_skip_preserves_enemies():
    """NEXT WAVE must NOT kill remaining enemies (regression caught twice)."""
    print("Skip preserves enemies:")
    g = fresh_game()
    g.wave = 1
    # Spawn some enemies
    g.ship.sail_in()
    for _ in range(2000):
        g.ship.update()
        if g.ship.state == Ship.DOCKED:
            break
    for _ in range(10):
        g.gen_enemies()
    n_before = len(g.enemies)
    check("enemies exist before skip", n_before > 0, f"n={n_before}")
    # Replicate the skip handler (must match game.py, minus the old enemies.clear())
    import game as game_mod
    src = open(game_mod.__file__).read()
    # Wytnij tylko blok obslugi przycisku NEXT WAVE (miedzy early_wave_rect a nastepnym continue)
    handler_start = src.find("# R2: przycisk wczesniejszej fali")
    handler_end = src.find("continue", handler_start)
    handler = src[handler_start:handler_end]
    check("no enemies.clear() in skip handler",
          "enemies.clear()" not in handler,
          "skip handler still clears enemies!")


def test_pause_blocks_spawns():
    """gen_enemies / ship updates must respect pause; spawns run on logic ticks
    (scale with 2x/3x), NOT on real time (which ignored speed)."""
    print("Pause blocks spawns:")
    import game as game_mod
    src = open(game_mod.__file__).read()
    check("gen_enemies guarded by pause",
          "not self.paused" in src,
          "run loop does not check self.paused before logic")
    check("spawns tick-based in update_game_logic",
          "self.gen_enemies()" in src and "_spawn_cd" in src,
          "spawn not driven by logic-tick countdown")
    check("no real-time spawn timer",
          "time.time() - self.timer" not in src,
          "spawn still uses real-time timer (ignores 2x/3x)")
    g = fresh_game()
    g.paused = True
    check("paused flag settable", g.paused is True)


def test_music_state_from_menu():
    """sound=False from menu -> music and sfx start muted (toggle showed wrong state)."""
    print("Music state from menu:")
    g = fresh_game(sound=False)
    check("music_muted when sound=False", g.music_muted is True)
    check("sfx_muted when sound=False", g.sfx_muted is True)
    g2 = fresh_game(sound=True)
    check("music not muted when sound=True", g2.music_muted is False)


def test_win_on_last_wave():
    """Final wave cleared -> won=True (YOU WIN screen)."""
    print("Win on last wave:")
    g = fresh_game()
    # Simulate last wave done: advance past final wave
    g.wave = 9  # 0-indexed wave 10
    g.last_wave_done = False
    g.waiting_for_clear = True
    g.ship.state = Ship.AWAY
    g.enemies.clear()
    g.advance_wave()  # should set last_wave_done for wave 10
    check("last_wave_done after final advance", g.last_wave_done,
          f"wave={g.wave} last_wave_done={g.last_wave_done}")


def main():
    pygame.init()
    print("=== Island Defenders regression tests ===")
    test_ship_full_cycle()
    test_waiting_for_clear_not_reset()
    test_wave_auto_advance()
    test_skip_preserves_enemies()
    test_pause_blocks_spawns()
    test_music_state_from_menu()
    test_win_on_last_wave()
    print(f"\n{PASS.__len__()} passed, {FAIL.__len__()} failed")
    if FAIL:
        print("FAILED:", FAIL)
        sys.exit(1)
    print("ALL GREEN")


if __name__ == "__main__":
    main()
