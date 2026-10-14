"""System achievementow - 50 osiagniec."""
import os
import json
import pygame

# Definicje: (id, nazwa, opis, ikona_kategorii, warunek)
# Warunek: funkcja(stats) -> bool, gdzie stats to dict ze statystykami gry
ACHIEVEMENTS = [
    # Walka
    ("first_blood", "First Blood", "Kill your first enemy.", "combat",
     lambda s: s.get("kills", 0) >= 1),
    ("warming_up", "Warming Up", "Kill 50 enemies.", "combat",
     lambda s: s.get("kills", 0) >= 50),
    ("slayer", "Slayer", "Kill 250 enemies.", "combat",
     lambda s: s.get("kills", 0) >= 250),
    ("exterminator", "Exterminator", "Kill 1000 enemies.", "combat",
     lambda s: s.get("kills", 0) >= 1000),
    ("genocide", "Genocide", "Kill 5000 enemies.", "combat",
     lambda s: s.get("kills", 0) >= 5000),
    ("boss_hunter", "Boss Hunter", "Defeat a boss.", "boss",
     lambda s: s.get("boss_kills", 0) >= 1),
    ("boss_slayer", "Boss Slayer", "Defeat 3 bosses.", "boss",
     lambda s: s.get("boss_kills", 0) >= 3),
    ("elite_hunter", "Elite Hunter", "Defeat 10 elite enemies.", "boss",
     lambda s: s.get("elite_kills", 0) >= 10),
    # Fale
    ("survivor", "Survivor", "Reach wave 5.", "waves",
     lambda s: s.get("max_wave", 0) >= 5),
    ("veteran", "Veteran", "Reach wave 8.", "waves",
     lambda s: s.get("max_wave", 0) >= 8),
    ("champion", "Champion", "Win the game (wave 10).", "victory",
     lambda s: s.get("wins", 0) >= 1),
    ("flawless", "Flawless", "Complete a wave without losing lives.", "defense",
     lambda s: s.get("flawless_waves", 0) >= 1),
    ("perfect_game", "Perfect Game", "Win without losing any lives.", "victory",
     lambda s: s.get("perfect_wins", 0) >= 1),
    ("comeback", "Comeback", "Win with only 1 life left.", "special",
     lambda s: s.get("comeback_wins", 0) >= 1),
    # Endless
    ("beyond", "Beyond", "Enter endless mode.", "endless",
     lambda s: s.get("endless_entered", 0) >= 1),
    ("endless_5", "Endless Warrior", "Reach endless wave 5.", "endless",
     lambda s: s.get("max_endless_wave", 0) >= 5),
    ("endless_10", "Endless Veteran", "Reach endless wave 10.", "endless",
     lambda s: s.get("max_endless_wave", 0) >= 10),
    ("endless_20", "Endless Legend", "Reach endless wave 20.", "endless",
     lambda s: s.get("max_endless_wave", 0) >= 20),
    # Zloto
    ("first_gold", "First Gold", "Earn 1000 gold total.", "gold",
     lambda s: s.get("gold_earned", 0) >= 1000),
    ("merchant", "Merchant", "Earn 10000 gold total.", "gold",
     lambda s: s.get("gold_earned", 0) >= 10000),
    ("tycoon", "Tycoon", "Earn 50000 gold total.", "gold",
     lambda s: s.get("gold_earned", 0) >= 50000),
    ("hoarder", "Hoarder", "Hold 10000 gold at once.", "gold",
     lambda s: s.get("max_gold_held", 0) >= 10000),
    ("big_spender", "Big Spender", "Spend 20000 gold total.", "gold",
     lambda s: s.get("gold_spent", 0) >= 20000),
    # Wieze
    ("builder", "Builder", "Build 5 towers.", "tower",
     lambda s: s.get("towers_built", 0) >= 5),
    ("architect", "Architect", "Build 25 towers.", "tower",
     lambda s: s.get("towers_built", 0) >= 25),
    ("engineer", "Engineer", "Build 50 towers.", "tower",
     lambda s: s.get("towers_built", 0) >= 50),
    ("maxed_out", "Maxed Out", "Upgrade a tower to max level.", "tower",
     lambda s: s.get("max_level_towers", 0) >= 1),
    ("perfectionist", "Perfectionist", "Own 5 max-level towers at once.", "tower",
     lambda s: s.get("max_level_at_once", 0) >= 5),
    ("pyromaniac", "Pyromaniac", "Build 5 Fire towers in one game.", "tower",
     lambda s: s.get("fire_towers", 0) >= 5),
    ("golden_army", "Golden Army", "Build 5 Golden towers in one game.", "tower",
     lambda s: s.get("golden_towers", 0) >= 5),
    ("speed_demon", "Speed Demon", "Use 10 tower abilities.", "special",
     lambda s: s.get("abilities_used", 0) >= 10),
    # Ulepszenia budynku
    ("renovator", "Renovator", "Buy a building upgrade.", "upgrade",
     lambda s: s.get("building_upgrades", 0) >= 1),
    ("handyman", "Handyman", "Buy 5 building upgrades.", "upgrade",
     lambda s: s.get("building_upgrades", 0) >= 5),
    ("contractor", "Contractor", "Buy all building upgrades.", "upgrade",
     lambda s: s.get("building_upgrades", 0) >= 10),
    ("camper", "Camper", "Buy a tent upgrade.", "upgrade",
     lambda s: s.get("tent_upgrades", 0) >= 1),
    ("scout_master", "Scout Master", "Buy 5 tent upgrades.", "upgrade",
     lambda s: s.get("tent_upgrades", 0) >= 5),
    ("outfitter", "Outfitter", "Buy all tent upgrades.", "upgrade",
     lambda s: s.get("tent_upgrades", 0) >= 10),
    ("cavalry", "Cavalry", "Buy Call the Cavalry.", "special",
     lambda s: s.get("cavalry_bought", 0) >= 1),
    # Specjalne
    ("storm_chaser", "Storm Chaser", "Fight during a storm.", "special",
     lambda s: s.get("storm_fights", 0) >= 1),
    ("lucky", "Lucky", "Score a critical hit.", "special",
     lambda s: s.get("crits", 0) >= 1),
    ("shipwreck", "Shipwreck", "Cripple the pirate ship.", "special",
     lambda s: s.get("pirate_crippled", 0) >= 1),
    ("guardian", "Guardian", "Sacrifice both dancers.", "defense",
     lambda s: s.get("dancers_sacrificed", 0) >= 2),
    ("tesla_master", "Tesla Master", "Kill 25 enemies with Tesla Coil.", "combat",
     lambda s: s.get("tesla_kills", 0) >= 25),
    ("demolitionist", "Demolitionist", "Lose 5 towers to bombardment.", "defense",
     lambda s: s.get("towers_lost_bombard", 0) >= 5),
    ("untouchable", "Untouchable", "Reach wave 8 with full lives.", "defense",
     lambda s: s.get("full_lives_wave8", 0) >= 1),
    ("sharpshooter", "Sharpshooter", "Dancers kill 20 enemies.", "combat",
     lambda s: s.get("dancer_kills", 0) >= 20),
    ("saboteur", "Saboteur", "Buy Sabotage.", "upgrade",
     lambda s: s.get("sabotage_bought", 0) >= 1),
    ("balloonist", "Balloonist", "Buy Recon Balloon.", "upgrade",
     lambda s: s.get("balloon_bought", 0) >= 1),
    ("drummer", "Drummer", "Buy War Drums.", "upgrade",
     lambda s: s.get("drums_bought", 0) >= 1),
    ("medic", "Medic", "Buy Field Medic.", "upgrade",
     lambda s: s.get("medic_bought", 0) >= 1),
    ("legend", "Legend", "Unlock 25 achievements.", "victory",
     lambda s: s.get("achievements_unlocked", 0) >= 25),
]

SAVE_FILE = "achievements.json"

class AchievementManager:
    def __init__(self):
        self.unlocked = set()
        self.icons = {}
        self._load()
        self._load_icons()
        self._pending_popup = []  # do wyswietlenia

    def _load(self):
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE) as f:
                    self.unlocked = set(json.load(f))
        except:
            self.unlocked = set()

    def _save(self):
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(list(self.unlocked), f)
        except:
            pass

    def _load_icons(self):
        for cat in ("combat", "waves", "gold", "tower", "upgrade", "special",
                    "boss", "endless", "defense", "victory"):
            try:
                img = pygame.image.load(os.path.join("images", "achievements", cat + ".webp"))
                self.icons[cat] = pygame.transform.smoothscale(img, (48, 48))
            except:
                self.icons[cat] = None

    def check(self, stats):
        """Sprawdza wszystkie achievementy, odblokowuje spelnione."""
        stats = dict(stats)
        stats["achievements_unlocked"] = len(self.unlocked)
        for aid, name, desc, icon, cond in ACHIEVEMENTS:
            if aid not in self.unlocked:
                try:
                    if cond(stats):
                        self.unlocked.add(aid)
                        self._pending_popup.append((name, desc, icon))
                        self._save()
                except:
                    pass

    def pop_popup(self):
        """Zwraca (name, desc, icon) do wyswietlenia lub None."""
        if self._pending_popup:
            return self._pending_popup.pop(0)
        return None

    def get_all(self):
        """Lista (id, name, desc, icon, unlocked)."""
        return [(aid, name, desc, icon, aid in self.unlocked)
                for aid, name, desc, icon, _ in ACHIEVEMENTS]
