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
- **Endless mode:** After victory, keep going — enemies scale +5% HP per wave, bigger gold bonuses per wave. Wave composition shifts toward the strongest enemy types the deeper you go (and the golden-elite chance rises from 8% to up to 18%), so late endless is far more dangerous
- **Endless jump (main menu):** type a wave number in the bottom-left field and hit JUMP to start endless at that wave — or enter 10 for an Easter egg: a rematch against the final boss with 100× HP

---

## Towers

Five unique towers, each with 3 levels, distinct projectiles, and a special ability:

| Tower | Cost | Damage | Ability |
|-------|------|--------|---------|
| Wood Tower | $100 | 1 | **Rapid Fire** — temporary fire-rate boost |
| Metal Tower | $500 | 3 | **Frost Nova** — slows all enemies in range |
| Gold Tower | $750 | 5 | **Golden Touch** — marks enemies for double gold |
| Fire Tower | $1,000 | 9 | **Meteor** — devastating area strike |
| Blaze Tower | $2,000 | 12 | **Armageddon** — massive screen-wide damage |

Upgrades add damage per level by tier (Wood +2, Metal +3, Gold +4, Fire +6, Blaze +8) — pricier towers gain more from upgrades, so saving up for them pays off.

- **Free placement** — no grid snapping; place towers anywhere on valid grass zones
- **Tower links** — two towers of the same type within 100px link up (gold line between them), and each type gains a unique bonus instead of a flat damage boost: Wood +30% fire rate, Metal +25% range and much longer slows, Gold +50% gold from its kills, Fire +70% splash radius, Blaze chains 50% damage to a second nearby enemy. The active bonus is shown in the tower's menu
- **Sell back** towers you no longer need
- **Range preview** with green/red validity indicator while placing. The range circle always shows the tower's TRUE effective range (level, rain −10%, Metal link +25%) — towers engage exactly at the circle's edge, never beyond it
- **Prices in gold** — shop, tower menus and upgrade cards all show a gold coin icon next to the amount (no $ signs)
- **Full run summary** — victory, defeat and forfeit screens all show the complete stat set: wave reached, kills, damage, gold earned/spent, towers built/lost, abilities used, and kills by enemy type

---

## Clickable Buildings

**Glass Research Facility** (click it!) — 10 one-time upgrades per run, sorted by price:
War Treasury $1,200, Bounty Board $1,500, Lucky Charm $2,000, Reinforced Docks $2,500, Storm Caller $3,000, Reinforced Walls $3,500, Ammunition Depot $4,000, Repair Drones $5,000 (+1 max life right away, then heals +1 life every 2 waves, up to max), Tesla Coil $6,500, and the secret **Call the Cavalry** $10,000 (endless only). Buying Repair Drones turns its slot into the **Drone Launch Facility** $8,000 (same slot, same icon — no locked/blacked-out entry).

**War Tent** (click it!) — 10 one-time upgrades per run, sorted by price:
Field Medic $1,500 (barrage destroy chance 50% → 25%), Scout Reports $2,000, Supply Lines $2,500 (towers 15% cheaper), War Drums $3,000, Signal Fire $3,500 (campfire grows 2×, all Fire/Blaze towers shoot 12% faster, dancers guard with bows), Guerrilla Training $4,000, Honor Banner $4,000 (+10% damage, no flag visual), Spike Barricade $4,500, Recon Balloon $5,500, Sabotage $6,000.

---

## Difficulty

Three difficulties that actually change the game (shown in the main menu under the buttons):

| | EASY | NORMAL | HARD |
|---|------|--------|------|
| Prices (towers, tower upgrades, building/tent upgrades) | −20% | standard | +25% |
| Enemy HP (incl. bosses) | −20% | standard | +30% |
| Enemy speed | −15% | standard | +15% |
| Gold from kills | +25% | standard | −15% (every kill pays at least $1) |
| Spawn interval | +30% (slower) | standard | −30% (faster) |
| Ability cooldowns | −15% | standard | +25% |
| Sell-back value (buy + upgrades) | 80% | 70% | 60% |
| Starting lives / gold | 30 / 300 | 20 / 200 | 12 / 150 |
| Storm chance | 20% | 20% | 20% |

Tower upgrade costs scale with the tower tier (not a flat 250/500 for all): Wood 150/300, Metal 400/800, Gold 600/1200, Fire 800/1600, Blaze 1500/3000 (before difficulty multipliers).

---

## Languages

The full UI is available in **7 languages**: English, Polski (Polish), Deutsch (German), Español (Spanish), Français (French), Português (Brazilian Portuguese) and Русский (Russian).

- Pick your language in the **main menu** — click one of the small flags in the top-right corner. The menu switches instantly, and the choice is remembered for the next launch (saved in `language.json`).
- Everything is localized: menus, HUD, shop, tower and upgrade menus, wave banners, announcements, notifications, pause and help screens, end screens, and all 50 achievements — 303 strings per language.
- English is the source language and the automatic fallback. Translations live in `lang/*.json`; adding a language means adding one file there.

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
- **7 languages** — full UI localization (EN / PL / DE / ES / FR / PT-BR / RU) with a flag picker in the main menu; the choice persists between launches
- **Resolution options** — 1124×720, 1280×720, 1600×900, 1920×1080, or native fullscreen
- **Dynamic day/night cycle** with smooth transitions
- **Weather system** — rain/storms with splash particles and ambient audio; random storm chance per wave depends on difficulty: 20% on Easy, 15% on Normal, 10% on Hard, in campaign and endless alike (Storm Caller doubles the chance — never on boss waves)
- **Ambient life** — campfire with dancers; when Signal Fire is bought, the dancers walk to their guard posts along the road (2× mob speed on the road, half speed for the final stretch) and guard the facility with bows, firing visible arrows; one guard will charge a close enemy and trade their life for it
- **Recon Balloon** — the balloon appears only once the upgrade is bought (it flies in from the left edge) and drops bombs every 3s straight down onto the player-drawn bomb line (no homing, no enemy targeting)
- **Spike Barricade** — spikes on the road deal 8 damage per second and can kill enemies on their own (damage is checked against the enemy sprite's hitbox, and kills pay out a flying coin like tower kills); each of the 3 spike clusters is clickable like a tower, upgradeable by 2 levels (8/14/22 DPS, prices scaled by difficulty) and sellable
- **Gold on coin landing** — kill gold is added only when the flying gold coin lands in the counter, not the moment the enemy dies
- **Tesla Coil** — visible coil on the facility roof; zaps start at the electrode ball and never target enemies still on the pier. In clear weather it fires every 1.8s: 75 damage, range 400, single target. During a storm there is no timed fire — lightning strikes the coil (bolt from the sky, then the charge travels down the coil, roughly every 2.5s at random), and only then does it discharge: 100 damage, range 700, up to 3 targets (main + 2 chained). Buying the coil guarantees a storm next round (2 rounds if Storm Caller was bought earlier)
- **Repair drone** — flies above the Tesla Coil (never clipped by it)
- **Drone Launch Facility** — flat rectangular dock on the building roof; launches a combat drone that zigzags across the map at a calmer speed, keeps its distance from enemies while strafing them with an animated minigun (8 dmg/shot, with sound), and fires a rocket launcher every ~20s (150 splash damage in 120px, with launch + explosion sounds). The rocket launcher sits vertical when idle and swings to aim at the target while firing. Then kamikazes into a random enemy (400 splash in 140px). Lifetime 2–4 min, then a 3-min rearm. The dock shows only the countdown: KAMIKAZE while the drone flies, NEXT DRONE while rearming. The drone model shows both weapons: minigun on the left, rocket launcher on the right
- **Tower upgrade menu** — vivid hologram buttons and brighter text (stronger fill, thicker borders, lightened tower colors)
- **Particle effects** — muzzle flashes, explosions, damage numbers, glass shards
- **Glass building destruction** — enemies shatter the facility's glass walls with sound and debris
- **Kill-streak announcements** and wave banners
- **Draggable shop panel** with semi-transparent modern UI
- **Click priority** — tower upgrade/sell buttons and tower selection always beat building/tent clicks underneath them; clicking anywhere inside the tower menu panel (not just its buttons) consumes the click
- **Ability dock** — hidden until you own a tower; shows only the abilities of tower types you actually have on the board, growing/shrinking as types are bought or sold
- **Enemies panel** — sized exactly to its content (icons + counts), no extra empty space
- **Guards' tombstones** — Bonnie and Clyde's tombstones stand apart, with the name and kill count fitting inside each stone
- **Music / Sound Effects** — separate toggles (pause menu, M key = music only): Music covers the normal track and the boss (intense) track; everything else is SFX. The intense track plays only while a boss is alive
- **Speed** — 2×/3× speeds up everything, including enemy disembark from the ship (tick-based spawning)
- **Group disembark** — each spawn tick can land a whole group at once: 64% single, 20% two, 10% three, 5% four, 1% five enemies (types drawn randomly from the wave pool). Group members start spread out along the deck (~26px apart) instead of stacked on one spot
- **Damage dealt** — end-screen stats show rounded whole numbers
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
| **M** | Music on/off |
| **F11** | Toggle fullscreen |
| **SPACE** | Pause/unpause (pausing freezes ALL animation too — clouds, water, ships, drones, the balloon) |
| **Shift+click** | Quick-sell selected tower |
| **Ctrl+Z** | Undo last tower placement / upgrade |

### Pause Menu (ESC)
- Resume / Restart Game / Forfeit Run / How to Play
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
├── i18n.py              # Localization: loads lang/*.json, persists the choice
├── lang/                # Translation files (en, pl, de, es, fr, pt, ru)
├── enemies/             # Enemy classes with animations
├── towers/              # Tower classes, projectiles, abilities
├── ships/               # Pirate ship and allied ship
├── menu/                # Start menu, pause menu, shop UI
├── effects/             # Particle system, floating text
├── images/              # Sprites, backgrounds, UI assets
│   ├── upgrades/        # Building/tent upgrade icons
│   ├── achievements/    # Achievement category icons
│   └── flags/           # Language-picker flags
└── sounds/              # Music and sound effects
```

---

## Author

**Daniel Baranowski** — Game design, direction, and playtesting.
