# Island Defenders

**Defend your island from monster-pirate invaders in this polished tower defense game.**

The year is 2048. The world has succumbed to chaos. As the chief engineer of the Vancouver Science Research Facility (VSRF), you must defend your home island — and the secret technology being developed there — from waves of monster-pirates landing on your shores.

Built with **Python** and **Pygame**. Cartoon-style graphics, dynamic gameplay, and a full suite of modern tower defense mechanics.

---

## Gameplay

Survive **10 waves** of increasingly dangerous enemies. Each wave arrives by ship — watch it sail in, dock, and disembark its crew of monsters. They follow the dirt path to your glass research facility. Stop them with towers, or lose lives with every breach.

- **Lives:** Enemies that reach the facility cost you a life and shatter its glass walls
- **Economy:** Earn gold for every kill. Golden (elite) enemies are tougher but worth 5× more
- **Victory:** Survive all 10 waves, including the final boss

---

## Towers

Five unique towers, each with 5 upgrade levels, distinct projectiles, and a special ability:

| Tower | Cost | Damage | Ability |
|-------|------|--------|---------|
| Wooden Tower | $100 | 1 | **Rapid Fire** — temporary fire-rate boost |
| Metal Tower | $500 | 3 | **Frost Nova** — slows all enemies in range |
| Golden Tower | $750 | 5 | **Golden Touch** — marks enemies for double gold |
| Fire Tower | $1,000 | 8 | **Meteor** — devastating area strike |
| Blaze Tower | $2,000 | 10 | **Armageddon** — massive screen-wide damage |

- **Free placement** — no grid snapping; place towers anywhere on valid grass zones
- **Tower synergy** — adjacent towers of the same type boost each other
- **Sell back** towers you no longer need
- **Range preview** with green/red validity indicator while placing

---

## Enemies

Nine enemy types with full walk, hurt, and death animations:

- **Goblin, Swordman, Knight, Cyclop, Impostor, Ogre, Evil Villager, Forkman** — each with unique stats and behaviors
- **Golden (Elite) variants** — 8% spawn chance, 3× HP, 5× gold reward, 1.25× size, rendered in solid gold
- **Boss** — multi-phase final encounter with enrage mechanic and dedicated health bar

---

## Features

- **Animated pirate ship** — sails in from alternating sides with pirate fanfare, docks, disembarks enemies, and departs; lively animations (wave bobbing, rotation, wake trail, bow splashes, glowing demonic rune)
- **Cannon barrage** — on waves 4 and 8 (with enough lives), the ship sails to a bombardment position and fires cannonballs at your towers (50% destroy chance)
- **Dynamic day/night cycle** with smooth transitions
- **Weather system** — rain with splash particles and ambient audio
- **Ambient life** — seagulls, butterflies, campfire with dancers
- **Particle effects** — muzzle flashes, explosions, damage numbers, glass shards
- **Glass building destruction** — enemies shatter the facility's glass walls with sound and debris
- **Kill-streak announcements** and wave banners
- **Draggable shop panel** with semi-transparent modern UI
- **Performance optimized** — spatial targeting grid, 60 FPS rendering, 100 Hz logic

---

## Controls

| Key | Action |
|-----|--------|
| **Mouse** | Select, place, and upgrade towers |
| **ESC** | Pause menu (pauses game, blocks tower interaction) |
| **1–5** | Quick-select tower type |
| **Q** | Activate selected tower's ability |
| **U** | Upgrade selected tower |
| **S** | Sell selected tower |
| **M** | Mute all audio |
| **F11** | Toggle fullscreen |
| **SPACE** | Pause/unpause |

### Pause Menu (ESC)
- Resume / Restart Game / How to Play
- Music and Sound Effects toggles (with checkmarks)
- Fullscreen toggle
- Game speed: 1× / 2× / 3×
- Quit to Desktop

---

## Installation

Requires **Python 3.12** and **Pygame 2.6+**.

```bash
git clone https://github.com/dbara943/FinalGame.git
cd FinalGame
pip install -r requirements.txt
py game.py
```

---

## Project Structure

```
FinalGame/
├── game.py              # Main game loop, UI, wave management
├── enemies/             # Enemy classes with animations
├── towers/              # Tower classes, projectiles, abilities
├── ships/               # Pirate ship animation and docking
├── menu/                # Start menu, pause menu, shop UI
├── effects/             # Particle system, floating text
├── images/              # Sprites, backgrounds, UI assets
└── sounds/              # Music and sound effects
```

---

## Author

**Daniel Baranowski** — Game design, direction, and playtesting.
