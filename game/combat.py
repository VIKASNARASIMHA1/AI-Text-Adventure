"""
Combat system for AI Text Adventure Game
Handles turn-based combat, enemy AI, special abilities, and battle mechanics
"""

import random
import time
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from collections import defaultdict

from .utils import TextFormatter, Colors, Dice

class CombatState(Enum):
    """Combat state enumeration"""
    ACTIVE = "active"
    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn"
    VICTORY = "victory"
    DEFEAT = "defeat"
    FLEE = "flee"

class DamageType(Enum):
    """Damage types for attacks"""
    PHYSICAL = "physical"
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    POISON = "poison"
    HOLY = "holy"
    DARK = "dark"
    TRUE = "true"  # Ignores resistances

class CombatSystem:
    """
    Main combat system handling all battle mechanics
    """
    
    def __init__(self, player: Dict):
        self.player = player
        self.enemy = None
        self.state = CombatState.ACTIVE
        self.turn_count = 0
        self.combat_log = []
        self.battle_flags = {}
        
        # Combat modifiers
        self.player_buffs = []
        self.enemy_buffs = []
        self.player_debuffs = []
        self.enemy_debuffs = []
        
        # Initialize combat data
        self.setup_enemy_types()
        self.setup_combat_abilities()
        self.setup_status_effects()
        
    def setup_enemy_types(self):
        """Define all possible enemy types and their stats"""
        
        self.enemy_types = {
            # Tier 1 enemies (level 1-3)
            'goblin': {
                'name': 'Goblin',
                'level': 1,
                'base_health': 25,
                'base_damage': 5,
                'base_defense': 3,
                'speed': 12,
                'xp_reward': 15,
                'gold_reward': (3, 8),
                'abilities': ['scratch', 'dodge'],
                'resistances': {},
                'weaknesses': {'physical': 1.2},
                'description': 'A small, green, cowardly creature with sharp teeth.',
                'attack_patterns': ['basic', 'basic', 'dodge'],
                'loot_table': ['goblin_ear', 'rusty_dagger', 'copper_coin']
            },
            
            'wolf': {
                'name': 'Wolf',
                'level': 2,
                'base_health': 35,
                'base_damage': 8,
                'base_defense': 4,
                'speed': 15,
                'xp_reward': 25,
                'gold_reward': (5, 12),
                'abilities': ['bite', 'howl', 'pack_tactics'],
                'resistances': {},
                'weaknesses': {'fire': 1.2},
                'description': 'A lean, gray wolf with yellow eyes. Hunts in packs.',
                'attack_patterns': ['basic', 'bite', 'howl'],
                'loot_table': ['wolf_pelt', 'wolf_tooth', 'raw_meat']
            },
            
            'bandit': {
                'name': 'Bandit',
                'level': 2,
                'base_health': 40,
                'base_damage': 7,
                'base_defense': 5,
                'speed': 10,
                'xp_reward': 30,
                'gold_reward': (10, 25),
                'abilities': ['stab', 'intimidate', 'flee'],
                'resistances': {},
                'weaknesses': {},
                'description': 'A rough-looking outlaw wearing tattered leather armor.',
                'attack_patterns': ['basic', 'stab', 'basic', 'intimidate'],
                'loot_table': ['leather_armor', 'short_sword', 'gold_coins']
            },
            
            'giant_spider': {
                'name': 'Giant Spider',
                'level': 3,
                'base_health': 45,
                'base_damage': 10,
                'base_defense': 6,
                'speed': 14,
                'xp_reward': 40,
                'gold_reward': (8, 15),
                'abilities': ['bite', 'web', 'poison'],
                'resistances': {'poison': 0.5},
                'weaknesses': {'fire': 1.5},
                'description': 'A massive spider with glowing red eyes. Venom drips from its fangs.',
                'attack_patterns': ['basic', 'bite', 'web', 'poison'],
                'loot_table': ['spider_silk', 'venom_sac', 'chitin']
            },
            
            # Tier 2 enemies (level 4-6)
            'orc': {
                'name': 'Orc',
                'level': 4,
                'base_health': 65,
                'base_damage': 15,
                'base_defense': 10,
                'speed': 8,
                'xp_reward': 60,
                'gold_reward': (15, 30),
                'abilities': ['cleave', 'charge', 'berserk'],
                'resistances': {'physical': 0.8},
                'weaknesses': {'holy': 1.3},
                'description': 'A hulking green brute wielding a massive axe.',
                'attack_patterns': ['basic', 'cleave', 'charge', 'berserk'],
                'loot_table': ['orc_axe', 'tusks', 'coarse_fur']
            },
            
            'skeleton': {
                'name': 'Skeleton Warrior',
                'level': 4,
                'base_health': 50,
                'base_damage': 12,
                'base_defense': 8,
                'speed': 11,
                'xp_reward': 55,
                'gold_reward': (10, 20),
                'abilities': ['slash', 'shield_block', 'bone_shield'],
                'resistances': {'physical': 0.7, 'poison': 0.0},
                'weaknesses': {'holy': 2.0, 'bludgeoning': 1.3},
                'description': 'An animated skeleton in rusted chainmail. Its eye sockets glow with blue light.',
                'attack_patterns': ['basic', 'slash', 'shield_block', 'bone_shield'],
                'loot_table': ['bone_fragments', 'rusted_sword', 'skull']
            },
            
            'dark_cultist': {
                'name': 'Dark Cultist',
                'level': 5,
                'base_health': 55,
                'base_damage': 10,
                'base_defense': 7,
                'speed': 12,
                'xp_reward': 75,
                'gold_reward': (20, 40),
                'abilities': ['shadow_bolt', 'life_drain', 'summon', 'curse'],
                'resistances': {'dark': 0.5},
                'weaknesses': {'holy': 1.8, 'fire': 1.2},
                'description': 'A robed figure chanting in an ancient tongue. Shadows writhe around them.',
                'attack_patterns': ['shadow_bolt', 'basic', 'life_drain', 'curse'],
                'loot_table': ['cultist_robes', 'dark_tome', 'ritual_dagger']
            },
            
            # Tier 3 enemies (level 7-9)
            'troll': {
                'name': 'Troll',
                'level': 7,
                'base_health': 120,
                'base_damage': 20,
                'base_defense': 12,
                'speed': 6,
                'xp_reward': 120,
                'gold_reward': (30, 60),
                'abilities': ['club_smash', 'regeneration', 'throw_rock', 'rage'],
                'resistances': {'physical': 0.6, 'fire': 0.5},
                'weaknesses': {'acid': 1.5, 'fire': 0.8},  # Fire stops regen
                'description': 'A massive, ugly creature with warty green skin and a foul odor.',
                'attack_patterns': ['club_smash', 'basic', 'regeneration', 'rage'],
                'loot_table': ['troll_hide', 'giant_club', 'troll_blood']
            },
            
            'wraith': {
                'name': 'Wraith',
                'level': 8,
                'base_health': 85,
                'base_damage': 18,
                'base_defense': 15,
                'speed': 14,
                'xp_reward': 150,
                'gold_reward': (40, 80),
                'abilities': ['life_drain', 'possess', 'invisibility', 'scream'],
                'resistances': {'physical': 0.3, 'fire': 0.5, 'ice': 0.5},
                'weaknesses': {'holy': 2.5, 'lightning': 1.3},
                'description': 'A ghostly figure that radiates intense cold. It seems to phase in and out of reality.',
                'attack_patterns': ['life_drain', 'invisibility', 'scream', 'life_drain'],
                'loot_table': ['ectoplasm', 'soul_shard', 'ethereal_dust']
            },
            
            # Boss enemies
            'troll_king': {
                'name': 'Troll King',
                'level': 10,
                'base_health': 250,
                'base_damage': 30,
                'base_defense': 18,
                'speed': 8,
                'xp_reward': 500,
                'gold_reward': (200, 500),
                'abilities': ['mighty_smash', 'regeneration', 'earth_shake', 'roar', 'enrage'],
                'resistances': {'physical': 0.5, 'fire': 0.4},
                'weaknesses': {'acid': 1.3},
                'description': 'A colossal troll wearing a crown of bones. The ground shakes with each step.',
                'attack_patterns': ['mighty_smash', 'roar', 'earth_shake', 'regeneration', 'enrage'],
                'loot_table': ['troll_crown', 'giant_tooth', 'kingly_trophy']
            },
            
            'dragon': {
                'name': 'Young Dragon',
                'level': 12,
                'base_health': 400,
                'base_damage': 40,
                'base_defense': 25,
                'speed': 12,
                'xp_reward': 1000,
                'gold_reward': (500, 1000),
                'abilities': ['fire_breath', 'claw', 'tail_whip', 'fly', 'fear'],
                'resistances': {'physical': 0.6, 'fire': 0.2, 'ice': 0.5},
                'weaknesses': {'lightning': 1.3, 'holy': 1.2},
                'description': 'A majestic dragon with gleaming scales. Its eyes burn with ancient intelligence.',
                'attack_patterns': ['fire_breath', 'claw', 'fly', 'fire_breath', 'fear'],
                'loot_table': ['dragon_scale', 'dragon_heart', 'golden_hoard']
            }
        }
        
    def setup_combat_abilities(self):
        """Define all combat abilities for enemies and players"""
        
        self.abilities = {
            # Basic abilities
            'scratch': {
                'name': 'Scratch',
                'damage_mult': 0.8,
                'accuracy': 90,
                'description': 'A quick, weak attack.',
                'effect': None
            },
            
            'bite': {
                'name': 'Bite',
                'damage_mult': 1.2,
                'accuracy': 85,
                'description': 'A powerful bite with sharp teeth.',
                'effect': 'bleed'  # Causes bleeding over time
            },
            
            'stab': {
                'name': 'Stab',
                'damage_mult': 1.3,
                'accuracy': 80,
                'description': 'A precise thrust with a blade.',
                'effect': 'wound'  # Reduces healing
            },
            
            # Special abilities
            'howl': {
                'name': 'Howl',
                'damage_mult': 0,
                'accuracy': 100,
                'description': 'A terrifying howl that reduces enemy defense.',
                'effect': 'reduce_defense',
                'effect_power': 0.8,  # 20% defense reduction
                'duration': 3
            },
            
            'pack_tactics': {
                'name': 'Pack Tactics',
                'damage_mult': 1.5,
                'accuracy': 90,
                'description': 'Coordinate attack for extra damage.',
                'condition': 'has_ally',
                'effect': None
            },
            
            'web': {
                'name': 'Web Shot',
                'damage_mult': 0.5,
                'accuracy': 75,
                'description': 'Shoots sticky webbing to slow the target.',
                'effect': 'slow',
                'duration': 2
            },
            
            'poison': {
                'name': 'Poison Bite',
                'damage_mult': 0.9,
                'accuracy': 70,
                'description': 'A venomous attack that poisons the target.',
                'effect': 'poison',
                'effect_power': 3,  # Damage per turn
                'duration': 4
            },
            
            'cleave': {
                'name': 'Cleave',
                'damage_mult': 1.4,
                'accuracy': 80,
                'description': 'A sweeping attack that hits multiple targets.',
                'aoe': True,
                'effect': None
            },
            
            'charge': {
                'name': 'Charge',
                'damage_mult': 1.8,
                'accuracy': 70,
                'description': 'A powerful charging attack.',
                'effect': 'stun',
                'duration': 1
            },
            
            'berserk': {
                'name': 'Berserk',
                'damage_mult': 1.3,
                'accuracy': 90,
                'description': 'Attacks wildly, trading defense for damage.',
                'self_effect': 'increase_damage',
                'self_damage': 0.1,  # Takes 10% damage
                'duration': 3
            },
            
            'shield_block': {
                'name': 'Shield Block',
                'damage_mult': 0,
                'accuracy': 100,
                'description': 'Raise shield to block incoming damage.',
                'self_effect': 'increase_defense',
                'effect_power': 1.5,  # 50% defense increase
                'duration': 2
            },
            
            'bone_shield': {
                'name': 'Bone Shield',
                'damage_mult': 0,
                'accuracy': 100,
                'description': 'Summon floating bones to protect yourself.',
                'self_effect': 'damage_shield',
                'effect_power': 20,  # Absorbs 20 damage
                'duration': 3
            },
            
            'shadow_bolt': {
                'name': 'Shadow Bolt',
                'damage_mult': 1.5,
                'accuracy': 85,
                'description': 'A bolt of dark magic.',
                'damage_type': 'dark',
                'effect': None
            },
            
            'life_drain': {
                'name': 'Life Drain',
                'damage_mult': 1.1,
                'accuracy': 80,
                'description': 'Drains life from the target.',
                'damage_type': 'dark',
                'lifesteal': 0.5,  # Heals for 50% of damage
                'effect': None
            },
            
            'curse': {
                'name': 'Curse',
                'damage_mult': 0,
                'accuracy': 70,
                'description': 'Curses the target, reducing all stats.',
                'effect': 'reduce_all',
                'effect_power': 0.7,  # 30% reduction
                'duration': 3
            },
            
            'regeneration': {
                'name': 'Regeneration',
                'damage_mult': 0,
                'accuracy': 100,
                'description': 'Rapidly regenerate health.',
                'self_effect': 'heal_over_time',
                'effect_power': 10,  # Heal 10 per turn
                'duration': 3
            },
            
            'rage': {
                'name': 'Rage',
                'damage_mult': 1.0,
                'accuracy': 100,
                'description': 'Enter a rage, increasing damage but decreasing defense.',
                'self_effect': 'berserk_mode',
                'effect_power': 1.3,  # 30% damage increase
                'self_damage_effect': 'reduce_defense',
                'duration': 4
            },
            
            'fire_breath': {
                'name': 'Fire Breath',
                'damage_mult': 2.0,
                'accuracy': 80,
                'description': 'Breathes a cone of searing flame.',
                'damage_type': 'fire',
                'aoe': True,
                'effect': 'burn',
                'effect_power': 8,  # Burn damage per turn
                'duration': 3
            },
            
            'fear': {
                'name': 'Fearsome Presence',
                'damage_mult': 0,
                'accuracy': 60,
                'description': 'Instills fear in the target.',
                'effect': 'fear',  # Chance to skip turn
                'duration': 2
            }
        }
        
    def setup_status_effects(self):
        """Define all status effects and their mechanics"""
        
        self.status_effects = {
            'bleed': {
                'name': 'Bleeding',
                'description': 'Taking damage over time',
                'on_turn': lambda target: target.take_damage(5, DamageType.TRUE),
                'on_end': None,
                'stack': True,
                'max_stacks': 3
            },
            
            'poison': {
                'name': 'Poisoned',
                'description': 'Taking poison damage over time',
                'on_turn': lambda target: target.take_damage(4, DamageType.POISON),
                'on_end': None,
                'stack': True,
                'max_stacks': 5
            },
            
            'burn': {
                'name': 'Burning',
                'description': 'Consumed by flames',
                'on_turn': lambda target: target.take_damage(8, DamageType.FIRE),
                'on_end': None,
                'stack': False
            },
            
            'slow': {
                'name': 'Slowed',
                'description': 'Movement and attacks are sluggish',
                'modifier': {'speed': 0.5, 'accuracy': 0.8},
                'stack': False
            },
            
            'stun': {
                'name': 'Stunned',
                'description': 'Unable to act',
                'on_turn': lambda target: target.skip_turn(),
                'stack': False
            },
            
            'fear': {
                'name': 'Frightened',
                'description': 'Chance to skip turn',
                'modifier': {'accuracy': 0.7},
                'on_turn_roll': 0.3,  # 30% chance to skip
                'stack': False
            },
            
            'wound': {
                'name': 'Wounded',
                'description': 'Healing is less effective',
                'modifier': {'healing_received': 0.5},
                'stack': False
            },
            
            'bless': {
                'name': 'Blessed',
                'description': 'Holy power increases all stats',
                'modifier': {'damage': 1.2, 'defense': 1.2, 'accuracy': 1.1},
                'stack': False
            },
            
            'fortify': {
                'name': 'Fortified',
                'description': 'Increased defenses',
                'modifier': {'defense': 1.5},
                'stack': False
            },
            
            'haste': {
                'name': 'Hasted',
                'description': 'Increased speed and reflexes',
                'modifier': {'speed': 1.5, 'accuracy': 1.2},
                'stack': False
            }
        }
    
    class Enemy:
        """Enemy class for combat instances"""
        
        def __init__(self, enemy_type: str, level_mult: float = 1.0, enemy_data: Dict = None):
            self.type = enemy_type
            self.data = enemy_data[enemy_type]
            
            # Scale stats based on level
            level = self.data['level'] * level_mult
            
            self.max_health = int(self.data['base_health'] * level_mult)
            self.health = self.max_health
            self.damage = int(self.data['base_damage'] * level_mult)
            self.defense = int(self.data['base_defense'] * level_mult)
            self.speed = self.data['speed']
            
            self.name = self.data['name']
            self.abilities = self.data['abilities']
            self.attack_patterns = self.data['attack_patterns']
            self.pattern_index = 0
            
            self.status_effects = []
            self.buffs = []
            self.debuffs = []
            
            self.xp_reward = int(self.data['xp_reward'] * level_mult)
            self.gold_min, self.gold_max = self.data['gold_reward']
            self.gold_reward = random.randint(self.gold_min, int(self.gold_max * level_mult))
            
            self.description = self.data['description']
            self.resistances = self.data.get('resistances', {})
            self.weaknesses = self.data.get('weaknesses', {})
            
            self.stunned = False
            self.fleeing = False
            self.taunted = False
            self.taunt_target = None
            
        def take_damage(self, amount: int, damage_type: DamageType = DamageType.PHYSICAL) -> int:
            """Calculate damage taken with resistances/weaknesses"""
            
            # Apply resistances
            resist_mult = 1.0
            if damage_type.value in self.resistances:
                resist_mult *= self.resistances[damage_type.value]
            
            # Apply weaknesses
            if damage_type.value in self.weaknesses:
                resist_mult *= self.weaknesses[damage_type.value]
            
            final_damage = int(amount * resist_mult)
            
            # Apply defense
            if damage_type == DamageType.PHYSICAL:
                final_damage = max(1, final_damage - self.defense)
            
            self.health -= final_damage
            return final_damage
        
        def heal(self, amount: int) -> int:
            """Heal the enemy"""
            old_health = self.health
            self.health = min(self.max_health, self.health + amount)
            return self.health - old_health
        
        def is_alive(self) -> bool:
            return self.health > 0
        
        def get_next_ability(self) -> str:
            """Get next ability based on attack pattern"""
            ability = self.attack_patterns[self.pattern_index % len(self.attack_patterns)]
            self.pattern_index += 1
            return ability
        
        def apply_status(self, effect: str, duration: int):
            """Apply status effect"""
            self.status_effects.append({
                'name': effect,
                'duration': duration,
                'stacks': 1
            })
        
        def process_status_effects(self):
            """Process status effects at turn start"""
            for effect in self.status_effects[:]:
                if effect['name'] in combat_system.status_effects:
                    effect_data = combat_system.status_effects[effect['name']]
                    if 'on_turn' in effect_data:
                        effect_data['on_turn'](self)
                    
                    effect['duration'] -= 1
                    if effect['duration'] <= 0:
                        if 'on_end' in effect_data:
                            effect_data['on_end'](self)
                        self.status_effects.remove(effect)
        
        def skip_turn(self):
            """Skip current turn (for stun)"""
            self.stunned = True
        
        def get_status_string(self) -> str:
            """Get formatted status effect string"""
            if not self.status_effects:
                return ""
            
            effects = []
            for effect in self.status_effects:
                name = combat_system.status_effects[effect['name']]['name']
                effects.append(f"{name}({effect['duration']})")
            
            return f" [{', '.join(effects)}]"
        
        def __str__(self) -> str:
            return f"{self.name} (HP: {self.health}/{self.max_health}){self.get_status_string()}"
    
    def start_combat(self, enemy_type: str, level_mult: float = 1.0):
        """Start combat with an enemy"""
        
        self.enemy = self.Enemy(enemy_type, level_mult, self.enemy_types)
        self.state = CombatState.PLAYER_TURN
        self.turn_count = 0
        self.combat_log = []
        
        # Initialize battle flags
        self.battle_flags = {
            'enemy_initial_health': self.enemy.health,
            'player_initial_health': self.player['health'],
            'rounds_survived': 0,
            'special_abilities_used': []
        }
        
        # Log combat start
        self.add_to_log(f"⚔️ Combat started with {self.enemy.name}!")
        self.add_to_log(self.enemy.description)
        
    def add_to_log(self, message: str):
        """Add message to combat log"""
        self.combat_log.append(message)
        if len(self.combat_log) > 10:
            self.combat_log.pop(0)
    
    def process_player_turn(self, action: str, target: str = None, item: str = None) -> str:
        """Process player's turn in combat"""
        
        if self.state != CombatState.PLAYER_TURN:
            return "It's not your turn!"
        
        result = []
        
        # Process action
        if action == 'attack':
            result.append(self.player_attack())
        elif action == 'defend':
            result.append(self.player_defend())
        elif action == 'ability':
            result.append(self.player_ability(target))
        elif action == 'use_item':
            result.append(self.player_use_item(item))
        elif action == 'flee':
            result.append(self.player_flee())
        else:
            return "Invalid combat action!"
        
        # Check if enemy died
        if not self.enemy.is_alive():
            self.state = CombatState.VICTORY
            victory_result = self.process_victory()
            result.append(victory_result)
            return "\n".join(result)
        
        # Switch to enemy turn
        self.state = CombatState.ENEMY_TURN
        self.turn_count += 1
        
        # Process enemy turn
        enemy_result = self.process_enemy_turn()
        result.append(enemy_result)
        
        # Check if player died
        if self.player['health'] <= 0:
            self.state = CombatState.DEFEAT
            result.append(self.process_defeat())
        
        # Switch back to player turn if combat continues
        if self.state == CombatState.ACTIVE:
            self.state = CombatState.PLAYER_TURN
        
        return "\n".join(result)
    
    def player_attack(self) -> str:
        """Process player basic attack"""
        
        # Calculate hit chance
        base_hit = 85  # Base 85% chance
        if 'accuracy_mod' in self.player:
            base_hit *= self.player['accuracy_mod']
        
        if random.randint(1, 100) > base_hit:
            self.add_to_log("Your attack misses!")
            return "Your attack misses!"
        
        # Calculate damage
        base_damage = random.randint(
            self.player['strength'] - 2,
            self.player['strength'] + 2
        )
        
        # Apply damage modifiers
        damage = base_damage
        for buff in self.player_buffs:
            if 'damage_mult' in buff:
                damage *= buff['damage_mult']
        
        # Apply to enemy
        actual_damage = self.enemy.take_damage(damage)
        
        result = f"You attack for {actual_damage} damage!"
        self.add_to_log(result)
        
        # Check for critical hit
        if random.randint(1, 20) == 20:  # 5% crit chance
            crit_damage = self.enemy.take_damage(damage // 2)
            result += f" Critical hit for additional {crit_damage} damage!"
        
        return result
    
    def player_defend(self) -> str:
        """Process player defend action"""
        
        # Add defense buff
        self.player_buffs.append({
            'name': 'defending',
            'defense_mult': 1.5,
            'duration': 2
        })
        
        result = "You take a defensive stance. Your defense is increased for 2 turns!"
        self.add_to_log(result)
        return result
    
    def player_ability(self, ability_name: str) -> str:
        """Process player using a special ability"""
        
        # Check if player has ability
        if ability_name not in self.player.get('abilities', []):
            return f"You don't have the ability '{ability_name}'!"
        
        # Check mana cost
        ability_data = self.get_player_ability(ability_name)
        if ability_data.get('mana_cost', 0) > self.player.get('mana', 0):
            return "Not enough mana!"
        
        # Use ability
        result = self.use_ability(self.player, ability_name, self.enemy)
        
        # Deduct mana
        if 'mana_cost' in ability_data:
            self.player['mana'] -= ability_data['mana_cost']
        
        self.add_to_log(result)
        return result
    
    def player_use_item(self, item_name: str) -> str:
        """Process player using an item"""
        
        # Check if player has item
        if item_name not in self.player.get('inventory', []):
            return f"You don't have {item_name}!"
        
        # Process item effects
        item_effects = self.get_item_effects(item_name)
        result = []
        
        for effect in item_effects:
            if effect['type'] == 'heal':
                heal_amount = min(
                    effect['amount'],
                    self.player['max_health'] - self.player['health']
                )
                self.player['health'] += heal_amount
                result.append(f"Healed for {heal_amount} health!")
            
            elif effect['type'] == 'damage':
                damage = self.enemy.take_damage(effect['amount'], effect.get('damage_type'))
                result.append(f"Dealt {damage} damage to {self.enemy.name}!")
            
            elif effect['type'] == 'buff':
                self.player_buffs.append(effect['buff'])
                result.append(f"Gained {effect['buff']['name']}!")
        
        # Remove item from inventory
        self.player['inventory'].remove(item_name)
        
        result_str = "\n".join(result)
        self.add_to_log(f"Used {item_name}: {result_str}")
        return f"You use {item_name}!\n{result_str}"
    
    def player_flee(self) -> str:
        """Attempt to flee from combat"""
        
        # Calculate flee chance
        player_speed = self.player.get('speed', 10)
        enemy_speed = self.enemy.speed
        
        flee_chance = 0.3 + (player_speed - enemy_speed) * 0.05
        flee_chance = max(0.1, min(0.7, flee_chance))  # Cap between 10% and 70%
        
        if random.random() < flee_chance:
            self.state = CombatState.FLEE
            result = "You successfully flee from combat!"
            self.add_to_log(result)
            return result
        else:
            result = "You failed to flee!"
            self.add_to_log(result)
            return result
    
    def process_enemy_turn(self) -> str:
        """Process enemy's turn"""
        
        if not self.enemy.is_alive():
            return ""
        
        # Check if enemy is stunned
        if self.enemy.stunned:
            self.enemy.stunned = False
            return f"{self.enemy.name} is stunned and cannot act!"
        
        # Process status effects
        self.enemy.process_status_effects()
        
        # Get enemy action
        ability_name = self.enemy.get_next_ability()
        ability_data = self.abilities.get(ability_name, self.abilities['scratch'])
        
        # Use ability
        result = self.use_ability(self.enemy, ability_name, self.player)
        self.add_to_log(result)
        
        return result
    
    def use_ability(self, user, ability_name: str, target) -> str:
        """Use a combat ability"""
        
        ability = self.abilities.get(ability_name, self.abilities['scratch'])
        
        # Check accuracy
        if random.randint(1, 100) > ability.get('accuracy', 85):
            return f"{user.name if hasattr(user, 'name') else 'You'} tries to use {ability['name']} but misses!"
        
        # Calculate damage
        damage_mult = ability.get('damage_mult', 1.0)
        
        if hasattr(user, 'damage'):  # Enemy
            base_damage = user.damage
            user_name = user.name
        else:  # Player
            base_damage = user['strength']
            user_name = "You"
        
        damage = int(base_damage * damage_mult)
        
        # Apply damage type
        damage_type = DamageType[ability.get('damage_type', 'PHYSICAL').upper()]
        
        # Deal damage if applicable
        damage_dealt = 0
        if damage > 0:
            damage_dealt = target.take_damage(damage, damage_type)
        
        # Build result message
        result_parts = []
        
        if damage_dealt > 0:
            if hasattr(target, 'name'):
                target_name = target.name
            else:
                target_name = "you"
            
            result_parts.append(f"{user_name} uses {ability['name']} on {target_name} for {damage_dealt} damage!")
        else:
            result_parts.append(f"{user_name} uses {ability['name']}!")
        
        # Apply effects
        if ability.get('effect'):
            effect_result = self.apply_effect(
                ability['effect'],
                target,
                ability.get('duration', 2),
                ability.get('effect_power')
            )
            if effect_result:
                result_parts.append(effect_result)
        
        # Apply self effects
        if ability.get('self_effect'):
            self_effect_result = self.apply_effect(
                ability['self_effect'],
                user,
                ability.get('duration', 2),
                ability.get('effect_power')
            )
            if self_effect_result:
                result_parts.append(self_effect_result)
        
        # Apply lifesteal
        if ability.get('lifesteal') and damage_dealt > 0:
            if hasattr(user, 'heal'):  # Enemy
                heal_amount = int(damage_dealt * ability['lifesteal'])
                actual_heal = user.heal(heal_amount)
                result_parts.append(f"{user_name} drains {actual_heal} health!")
            else:  # Player
                heal_amount = int(damage_dealt * ability['lifesteal'])
                self.player['health'] = min(
                    self.player['max_health'],
                    self.player['health'] + heal_amount
                )
                result_parts.append(f"You drain {heal_amount} health!")
        
        return " ".join(result_parts)
    
    def apply_effect(self, effect_name: str, target, duration: int, power=None) -> Optional[str]:
        """Apply a status effect to target"""
        
        if effect_name in self.status_effects:
            if hasattr(target, 'apply_status'):
                target.apply_status(effect_name, duration)
            elif isinstance(target, dict):  # Player
                # Apply player status effect
                self.player_debuffs.append({
                    'name': effect_name,
                    'duration': duration,
                    'power': power
                })
            
            effect_data = self.status_effects[effect_name]
            return f"{target.name if hasattr(target, 'name') else 'You'} is now {effect_data['name']}!"
        
        return None
    
    def process_victory(self) -> str:
        """Process victory in combat"""
        
        result = []
        result.append(f"\n{Colors.SUCCESS}🎉 VICTORY! You defeated the {self.enemy.name}!{Colors.RESET}")
        
        # Award XP
        xp_gained = self.enemy.xp_reward
        self.player['xp'] += xp_gained
        result.append(f"✨ Gained {xp_gained} experience!")
        
        # Award gold
        gold_gained = self.enemy.gold_reward
        self.player['gold'] += gold_gained
        result.append(f"🪙 Found {gold_gained} gold!")
        
        # Check for level up
        if self.player['xp'] >= self.player['xp_to_next']:
            level_up_result = self.level_up()
            result.append(level_up_result)
        
        # Get loot
        loot = self.get_loot()
        if loot:
            result.append(f"📦 Loot: {', '.join(loot)}")
        
        self.add_to_log("Victory!")
        return "\n".join(result)
    
    def process_defeat(self) -> str:
        """Process defeat in combat"""
        
        result = f"\n{Colors.ERROR}💀 DEFEAT! You were slain by the {self.enemy.name}!{Colors.RESET}"
        self.add_to_log("Defeat!")
        return result
    
    def get_loot(self) -> List[str]:
        """Generate loot from defeated enemy"""
        
        loot = []
        loot_table = self.enemy.data.get('loot_table', [])
        
        # Roll for each possible loot item
        for item in loot_table:
            if random.random() < 0.3:  # 30% chance per item
                loot.append(item)
                self.player['inventory'].append(item)
        
        return loot
    
    def level_up(self) -> str:
        """Process player level up"""
        
        self.player['level'] += 1
        self.player['xp'] -= self.player['xp_to_next']
        self.player['xp_to_next'] = int(self.player['xp_to_next'] * 1.5)
        
        # Increase stats
        self.player['max_health'] += 10
        self.player['health'] = self.player['max_health']
        self.player['strength'] += 2
        self.player['defense'] += 1
        
        return f"\n{Colors.INFO}🌟 LEVEL UP! You are now level {self.player['level']}!{Colors.RESET}"
    
    def get_player_ability(self, ability_name: str) -> Dict:
        """Get player ability data"""
        
        # Define player abilities
        player_abilities = {
            'power_attack': {
                'name': 'Power Attack',
                'damage_mult': 1.5,
                'mana_cost': 5,
                'accuracy': 75,
                'description': 'A powerful but slower attack'
            },
            'quick_strike': {
                'name': 'Quick Strike',
                'damage_mult': 0.8,
                'mana_cost': 3,
                'accuracy': 95,
                'description': 'A fast attack that\'s hard to dodge'
            },
            'shield_bash': {
                'name': 'Shield Bash',
                'damage_mult': 1.0,
                'mana_cost': 4,
                'accuracy': 80,
                'effect': 'stun',
                'description': 'Bash with your shield to stun the enemy'
            },
            'healing_light': {
                'name': 'Healing Light',
                'damage_mult': 0,
                'mana_cost': 10,
                'heal': 25,
                'description': 'Heal yourself with holy light'
            },
            'fireball': {
                'name': 'Fireball',
                'damage_mult': 1.8,
                'mana_cost': 15,
                'damage_type': 'fire',
                'accuracy': 70,
                'description': 'Hurl a ball of fire at your enemy'
            }
        }
        
        return player_abilities.get(ability_name, {})
    
    def get_item_effects(self, item_name: str) -> List[Dict]:
        """Get item effects"""
        
        item_effects = {
            'health_potion': [
                {'type': 'heal', 'amount': 30}
            ],
            'mana_potion': [
                {'type': 'mana', 'amount': 20}
            ],
            'bomb': [
                {'type': 'damage', 'amount': 25, 'damage_type': 'fire'}
            ],
            'poison_dagger': [
                {'type': 'damage', 'amount': 15},
                {'type': 'effect', 'effect': 'poison', 'duration': 3}
            ]
        }
        
        return item_effects.get(item_name.lower(), [])
    
    def get_combat_status(self) -> str:
        """Get current combat status display"""
        
        if not self.enemy:
            return "Not in combat"
        
        status = f"\n{Colors.COMBAT}⚔️ COMBAT STATUS{Colors.RESET}\n"
        status += TextFormatter.divider('-', 40) + "\n"
        
        # Player status
        player_hp_pct = (self.player['health'] / self.player['max_health']) * 100
        player_bar = self.get_health_bar(player_hp_pct)
        status += f"❤️ You:     {player_bar} {self.player['health']}/{self.player['max_health']}\n"
        
        # Enemy status
        enemy_hp_pct = (self.enemy.health / self.enemy.max_health) * 100
        enemy_bar = self.get_health_bar(enemy_hp_pct)
        enemy_name = self.enemy.name
        if self.enemy.status_effects:
            enemy_name += self.enemy.get_status_string()
        status += f"💀 Enemy:   {enemy_bar} {self.enemy.health}/{self.enemy.max_health}\n"
        
        # Turn info
        status += f"\nTurn: {self.turn_count + 1} | "
        if self.state == CombatState.PLAYER_TURN:
            status += f"{Colors.SUCCESS}Your turn!{Colors.RESET}"
        elif self.state == CombatState.ENEMY_TURN:
            status += f"{Colors.COMBAT}Enemy turn...{Colors.RESET}"
        
        return status
    
    def get_health_bar(self, percentage: float, length: int = 20) -> str:
        """Generate a health bar"""
        
        filled = int(percentage / 100 * length)
        bar = "█" * filled + "░" * (length - filled)
        
        if percentage > 60:
            color = Colors.SUCCESS
        elif percentage > 30:
            color = Colors.WARNING
        else:
            color = Colors.ERROR
        
        return f"{color}{bar}{Colors.RESET}"
    
    def get_combat_log(self) -> str:
        """Get recent combat log"""
        
        if not self.combat_log:
            return ""
        
        log = f"\n{Colors.INFO}📜 Combat Log:{Colors.RESET}\n"
        for entry in self.combat_log[-5:]:  # Last 5 entries
            log += f"  • {entry}\n"
        
        return log
    
    def get_available_actions(self) -> str:
        """Get available combat actions"""
        
        actions = f"\n{Colors.INFO}⚡ Available Actions:{Colors.RESET}\n"
        actions += "  attack  - Perform a basic attack\n"
        actions += "  defend  - Take defensive stance\n"
        actions += "  ability - Use special ability\n"
        actions += "  use     - Use an item\n"
        actions += "  flee    - Attempt to run away\n"
        
        return actions
    
    def process_turn(self, action: str) -> str:
        """Process a full turn (wrapper for main combat loop)"""
        
        if not self.in_combat():
            return "Not in combat!"
        
        # Process based on current state
        if self.state == CombatState.PLAYER_TURN:
            return self.process_player_turn(action)
        else:
            return "Wait for your turn!"
    
    def in_combat(self) -> bool:
        """Check if currently in combat"""
        return self.state not in [CombatState.VICTORY, CombatState.DEFEAT, CombatState.FLEE]
    
    def get_enemy_status(self) -> str:
        """Get enemy status for prompt"""
        if not self.enemy:
            return ""
        
        return f"{self.enemy.name} [{self.enemy.health}/{self.enemy.max_health} HP]"

# Global instance for status effect callbacks
combat_system = None