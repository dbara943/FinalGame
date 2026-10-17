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
- **Endless mode:** After victory, keep going — enemies scale +5% HP per wave, bigger gold bonuses per wave

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

## Clickable Buildings

**Glass Research Facility** (click it!) — 10 one-time upgrades per run, sorted by price:
War Treasury $1,200, Bounty Board $1,500, Lucky Charm $2,000, Reinforced Docks $2,500, Storm Caller $3,000, Reinforced Walls $3,500, Ammunition Depot $4,000, Repair Drones $5,000, Tesla Coil $6,500, and the secret **Call the Cavalry** $10,000 (endless only). Buying Repair Drones turns its slot into the **Drone Launch Facility** $8,000 (same slot, same icon — no locked/blacked-out entry).

**War Tent** (click it!) — 10 one-time upgrades per run, sorted by price:
Field Medic $1,500 (barrage destroy chance 50% → 25%), Scout Reports $2,000, Supply Lines $2,500 (towers 15% cheaper), War Drums $3,000, Signal Fire $3,500, Guerrilla Training $4,000, Honor Banner $4,000 (+10% damage, no flag visual), Spike Barricade $4,500, Recon Balloon $5,500, Sabotage $6,000.

---

## Enemies

Nine enemy types with full walk, hurt, and death animations:

- **Goblin, Swordman, Knight, Cyclop, Impostor, Ogre, Evil Villager, Forkman** — each with unique stats and behaviors
- **Golden (Elite) variants** — 8% spawn chance, 3× HP, 5× gold reward, 1.25× size, rendered in solid gold
- **Boss** — multi-phase final encounter with enrage mechanic and dedicated health bar

---

## Features

- **Animated pirate ship** — sails in from alternating sides with pirate fanfare, docks, disembarks enemies, and departs; lively animations (wave bobbing, rotation, wake trail, bow splashes, glowing demonic rune)
- **Cannon barrage** — on waves 4 and 8 (with enough lives), the ship sails to a bombardment position and fires cannonballs at your towers; during the barrage all menus close so the cinematic is visible (ESC still opens pause)
- **Call the Cavalry** — an allied ship intercepts the pirate ship, cripples it, then bombards enemies in endless mode; once the chase starts, input is no longer blocked
- **50 achievements** — tracked across runs with unlock popups, persistent save, and a gallery in the main menu
- **Resolution options** — 1124×720, 1280×720, 1600×900, 1920×1080, or native fullscreen
- **Dynamic day/night cycle** with smooth transitions
- **Weather system** — rain/storms with splash particles and ambient audio
- **Ambient life** — campfire with dancers; when Signal Fire is bought, the dancers walk to their guard posts along the road (2× mob speed on the road, half speed for the final stretch) and guard the facility with bows, firing visible arrows; one guard will charge a close enemy and trade their life for it
- **Recon Balloon** — a single balloon flies from the start; after the upgrade is bought it drops bombs every 3s straight down onto the player-drawn bomb line (no homing, no enemy targeting)
- **Spike Barricade** — spikes on the road deal 8 damage per second and can kill enemies on their own
- **Gold on coin landing** — kill gold is added only when the flying dollar bill lands in the counter, not the moment the enemy dies
- **Tesla Coil** — visible coil on the facility roof; lightning starts at the electrode ball, range 400 from the ball (300 damage + chain in storms)
- **Repair drone** — flies above the Tesla Coil (never clipped by it)
- **Drone Launch Facility** — flat rectangular dock on the building roof; launches a combat drone that zigzags across the map at a calmer speed, keeps its distance from enemies while strafing them with an animated minigun (8 dmg/shot, with sound), and fires a rocket launcher every ~20s (150 splash damage in 120px, with launch + explosion sounds). Then kamikazes into a random enemy (400 splash in 140px). Lifetime 2–4 min, then a 3-min rearm. The dock shows only the countdown: KAMIKAZE while the drone flies, NEXT DRONE while rearming. The drone model shows both weapons: minigun on the left, rocket launcher on the right
- **Tower upgrade menu** — vivid hologram buttons and brighter text (stronger fill, thicker borders, lightened tower colors)
- **Particle effects** — muzzle flashes, explosions, damage numbers, glass shards
- **Glass building destruction** — enemies shatter the facility's glass walls with sound and debris
- **Kill-streak announcements** and wave banners
- **Draggable shop panel** with semi-transparent modern UI
- **Click priority** — tower upgrade/sell buttons and tower selection always beat building/tent clicks underneath them
- **Performance optimized** — spatial targeting grid, 60 FPS rendering, 100 Hz logic

---

## Controls

| Key | Action |
|-----|--------|
| **Mouse** | Select, place, and upgrade towers |
| **ESC** | Cancel first (help → building/tent menu → placement refund → selected tower), then open pause menu; during the barrage it still opens pause (barrage freezes, second ESC resumes) |
| **1–5** | Quick-select tower type |
| **Q** | Activate selected tower's ability |
| **U** | Upgrade selected tower |
| **S** | Sell selected tower |
| **M** | Mute all audio |
| **F11** | Toggle fullscreen |
| **SPACE** | Pause/unpause |
| **Shift+click** | Quick-sell selected tower |
| **Ctrl+Z** | Undo last tower placement / upgrade |

### Pause Menu (ESC)
- Resume / Restart Game / How to Play
- Music and Sound Effects toggles (with checkmarks)
- Fullscreen toggle
- Game speed: 1× / 2× / 3×
- Quit to Desktop

---

## Installation

Requires **Python 3.15** and **pygame-ce 2.5.8**.

```bash
git clone https://github.com/dbara943/FinalGame.git
cd FinalGame
pip install -r requirements.txt
python game.py
```

---

## Project Structure

```
FinalGame/
├── game.py              # Main game loop, UI, wave management
├── achievements.py      # 50 achievements system
├── enemies/             # Enemy classes with animations
├── towers/              # Tower classes, projectiles, abilities
├── ships/               # Pirate ship and allied ship
├── menu/                # Start menu, pause menu, shop UI
├── effects/             # Particle system, floating text
├── images/              # Sprites, backgrounds, UI assets
│   ├── upgrades/        # Building/tent upgrade icons
│   └── achievements/    # Achievement category icons
└── sounds/              # Music and sound effects
```

---

## Author

**Daniel Baranowski** — Game design, direction, and playtesting.
