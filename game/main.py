"""
Main game loop and interface for AI Text Adventure Game
Handles user input, game state, and high-level game flow
"""

import os
import sys
import time
import random
from typing import Optional, Dict, Any
from datetime import datetime

# Import game modules
from .utils import TextFormatter, Colors, Dice, GameLogger
from .world import WorldGenerator, WorldManager
from .ai_engine import AIEngine
from .combat import CombatSystem
from .quests import QuestManager
from .npc import NPCSystem
from .inventory import InventorySystem
from .save_system import SaveSystem

class Game:
    """
    Main game class that orchestrates all game systems
    """
    
    def __init__(self, new_game: bool = True, save_file: Optional[str] = None):
        """Initialize a new game or load from save"""
        
        # Initialize systems
        self.logger = GameLogger(enabled=True)
        self.save_system = SaveSystem()
        
        # Game state
        self.running = True
        self.game_over = False
        self.turn_count = 0
        self.start_time = datetime.now()
        
        # Player stats
        self.player = {
            'name': '',
            'health': 100,
            'max_health': 100,
            'mana': 50,
            'max_mana': 50,
            'level': 1,
            'xp': 0,
            'xp_to_next': 100,
            'gold': 50,
            'strength': 10,
            'defense': 10,
            'intelligence': 10,
            'skills': [],
            'status_effects': [],
            'difficulty': 'normal'
        }
        
        # Game flags
        self.flags = {
            'first_visit_tavern': True,
            'met_guild_master': False,
            'completed_tutorial': False,
            'discovered_magic': False,
            'reputation': {
                'townsfolk': 0,
                'guild': 0,
                'thieves': 0
            }
        }
        
        # Load or create game
        if new_game:
            self.setup_new_game()
        else:
            self.load_game(save_file)
        
        # Initialize systems that depend on player/world
        self.ai_engine = AIEngine(self.player, self.flags)
        self.combat = CombatSystem(self.player)
        self.quest_manager = QuestManager(self.player, self.flags)
        self.npc_system = NPCSystem(self.player, self.flags)
        self.inventory = InventorySystem(self.player)
        
        # Command history for undo
        self.command_history = []
        self.max_history = 50
        
        self.logger.log('game_init', {'new_game': new_game})
    
    def setup_new_game(self):
        """Setup a brand new game"""
        self.clear_screen()
        
        # Welcome screen
        self.display_title()
        
        # Character creation
        self.create_character()
        
        # Generate world
        print(f"\n{TextFormatter.info('Generating your adventure world...')}")
        time.sleep(1)
        
        generator = WorldGenerator(seed=random.randint(1, 1000000))
        self.world_data = generator.generate_world(size='medium')
        self.world = WorldManager(self.world_data)
        
        # Initial tutorial
        self.show_tutorial()
        
        # Log game start
        self.logger.log('new_game', {
            'player': self.player,
            'world_size': len(self.world_data)
        })
    
    def display_title(self):
        """Display game title screen"""
        title = f"""
{Colors.HEADER}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   █████╗ ██╗    ████████╗███████╗██╗  ██╗████████╗       ║
║  ██╔══██╗██║    ╚══██╔══╝██╔════╝╚██╗██╔╝╚══██╔══╝       ║
║  ███████║██║       ██║   █████╗   ╚███╔╝    ██║          ║
║  ██╔══██║██║       ██║   ██╔══╝   ██╔██╗    ██║          ║
║  ██║  ██║██║       ██║   ███████╗██╔╝ ██╗   ██║          ║
║  ╚═╝  ╚═╝╚═╝       ╚═╝   ╚══════╝╚═╝  ╚═╝   ╚═╝          ║
║                                                           ║
║              ██████╗ ██████╗ ███╗   ███╗                 ║
║             ██╔════╝ ██╔══██╗████╗ ████║                 ║
║             ██║  ███╗██████╔╝██╔████╔██║                 ║
║             ██║   ██║██╔══██╗██║╚██╔╝██║                 ║
║             ╚██████╔╝██║  ██║██║ ╚═╝ ██║                 ║
║              ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝                 ║
║                                                           ║
║                 A I   T E X T   A D V E N T U R E        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
{Colors.RESET}

{TextFormatter.info('Version 1.0.0')}                     {TextFormatter.info('Created with 🎮 in Python')}

{TextFormatter.warning('Type "help" at any time for commands.')}
"""
        print(title)
        time.sleep(2)
    
    def create_character(self):
        """Character creation screen"""
        print(f"\n{TextFormatter.header('👤 CHARACTER CREATION')}")
        print(TextFormatter.divider())
        
        # Get player name
        while True:
            name = input(f"\n{TextFormatter.info('What is your name, adventurer?')}\n> ").strip()
            if name and len(name) <= 20:
                self.player['name'] = name
                break
            print(TextFormatter.error("Please enter a valid name (1-20 characters)"))
        
        # Choose class
        print(f"\n{TextFormatter.info('Choose your class:')}")
        classes = {
            '1': {
                'name': 'Warrior',
                'strength': 15,
                'defense': 12,
                'intelligence': 8,
                'health': 120,
                'desc': 'Mighty fighters who excel in combat'
            },
            '2': {
                'name': 'Mage',
                'strength': 8,
                'defense': 10,
                'intelligence': 15,
                'health': 80,
                'mana': 100,
                'desc': 'Masters of arcane magic'
            },
            '3': {
                'name': 'Rogue',
                'strength': 12,
                'defense': 8,
                'intelligence': 12,
                'health': 90,
                'desc': 'Stealthy and cunning adventurers'
            },
            '4': {
                'name': 'Cleric',
                'strength': 10,
                'defense': 12,
                'intelligence': 12,
                'health': 100,
                'mana': 80,
                'desc': 'Divine healers and protectors'
            }
        }
        
        for key, cls in classes.items():
            print(f"\n  {Colors.BOLD}{key}. {cls['name']}{Colors.RESET}")
            print(f"     {cls['desc']}")
            print(f"     Str: {cls['strength']} | Def: {cls['defense']} | Int: {cls['intelligence']}")
        
        while True:
            choice = input(f"\n{TextFormatter.info('Enter your choice (1-4):')}\n> ").strip()
            if choice in classes:
                selected = classes[choice]
                self.player.update({
                    'class': selected['name'],
                    'strength': selected['strength'],
                    'defense': selected['defense'],
                    'intelligence': selected['intelligence'],
                    'health': selected.get('health', 100),
                    'max_health': selected.get('health', 100),
                    'mana': selected.get('mana', 50),
                    'max_mana': selected.get('mana', 50)
                })
                break
            print(TextFormatter.error("Invalid choice. Please enter 1-4."))
        
        # Choose difficulty
        print(f"\n{TextFormatter.info('Select difficulty:')}")
        print(f"  {Colors.BOLD}1. Easy{Colors.RESET}     - For story-focused players")
        print(f"  {Colors.BOLD}2. Normal{Colors.RESET}   - Balanced experience")
        print(f"  {Colors.BOLD}3. Hard{Colors.RESET}     - For experienced adventurers")
        print(f"  {Colors.BOLD}4. Legendary{Colors.RESET} - Only for the brave")
        
        difficulties = {
            '1': {'name': 'easy', 'mult': 0.7},
            '2': {'name': 'normal', 'mult': 1.0},
            '3': {'name': 'hard', 'mult': 1.5},
            '4': {'name': 'legendary', 'mult': 2.0}
        }
        
        choice = input(f"\n{TextFormatter.info('Enter your choice (1-4):')}\n> ").strip()
        if choice in difficulties:
            self.player['difficulty'] = difficulties[choice]['name']
            self.player['damage_mult'] = difficulties[choice]['mult']
        
        # Starting items based on class
        starting_items = {
            'Warrior': ['Iron Sword', 'Leather Armor', 'Health Potion'],
            'Mage': ['Wooden Staff', 'Spellbook', 'Mana Potion'],
            'Rogue': ['Dagger', 'Thieves Tools', 'Smoke Bomb'],
            'Cleric': ['Mace', 'Holy Symbol', 'Healing Potion']
        }
        
        self.player['inventory'] = starting_items.get(self.player['class'], [])
        
        print(f"\n{TextFormatter.success('✅ Character created successfully!')}")
        print(f"\n{TextFormatter.info('Welcome,')} {Colors.BOLD}{self.player['name']}{Colors.RESET} the {self.player['class']}!")
        time.sleep(2)
    
    def show_tutorial(self):
        """Show tutorial for new players"""
        print(f"\n{TextFormatter.header('📖 QUICK TUTORIAL')}")
        print(TextFormatter.divider())
        
        tutorial_text = [
            "Welcome to your adventure! Here's how to play:",
            "",
            f"{Colors.BOLD}Basic Commands:{Colors.RESET}",
            "  • look / l     - Examine your surroundings",
            "  • go [dir]     - Move north/south/east/west",
            "  • talk [name]  - Talk to NPCs",
            "  • take [item]  - Pick up items",
            "  • inventory / i - Check your items",
            "  • stats / st   - View character stats",
            "  • map          - See discovered locations",
            "  • help / ?     - Show all commands",
            "  • quit         - Exit game",
            "",
            f"{Colors.BOLD}Combat Commands:{Colors.RESET}",
            "  • attack       - Fight current enemy",
            "  • defend       - Increase defense for a turn",
            "  • use [item]   - Use item in combat",
            "  • run          - Attempt to flee",
            "",
            f"{Colors.BOLD}Tips:{Colors.RESET}",
            "  • Talk to everyone - they might have quests!",
            "  • Check your surroundings carefully",
            "  • Save often with 'save' command",
            "  • Rest in safe places to heal"
        ]
        
        for line in tutorial_text:
            print(line)
            time.sleep(0.3)
        
        input(f"\n{TextFormatter.info('Press Enter to begin your journey...')}")
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_help(self):
        """Display help screen"""
        print(f"\n{TextFormatter.header('📚 COMMAND REFERENCE')}")
        print(TextFormatter.divider())
        
        help_categories = {
            'Movement': [
                ('go [dir]', 'Move in direction (n/s/e/w)'),
                ('map', 'Show discovered locations'),
                ('return', 'Go back to previous location')
            ],
            'Interaction': [
                ('look / l', 'Examine current location'),
                ('talk [name]', 'Talk to an NPC'),
                ('take [item]', 'Pick up an item'),
                ('use [item]', 'Use an item'),
                ('drop [item]', 'Drop an item'),
                ('examine [item]', 'Look at item closely')
            ],
            'Character': [
                ('stats / st', 'View character stats'),
                ('inventory / i', 'View inventory'),
                ('rest', 'Rest and recover'),
                ('skills', 'View learned skills')
            ],
            'Quests': [
                ('quests / q', 'View active quests'),
                ('journal / j', 'Read quest journal'),
                ('complete [quest]', 'Complete a quest objective')
            ],
            'System': [
                ('save [name]', 'Save game'),
                ('load [name]', 'Load saved game'),
                ('saves', 'List saved games'),
                ('help / ?', 'Show this help'),
                ('quit / exit', 'Exit game')
            ]
        }
        
        for category, commands in help_categories.items():
            print(f"\n{Colors.BOLD}{category}:{Colors.RESET}")
            for cmd, desc in commands:
                print(f"  {TextFormatter.info(f'{cmd:15}')} - {desc}")
        
        print(f"\n{TextFormatter.warning('💡 Tip:')} Commands are not case-sensitive!")
    
    def process_command(self, command: str) -> str:
        """Process and execute player commands"""
        
        if not command.strip():
            return ""
        
        # Add to history
        self.command_history.append(command)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
        
        # Parse command
        parts = command.lower().split()
        base_cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Log command
        self.logger.log('command', {'cmd': command})
        
        # Help command
        if base_cmd in ['help', '?', 'h']:
            self.display_help()
            return ""
        
        # Movement commands
        if base_cmd == 'go' and args:
            direction = args[0]
            success, message = self.world.move(direction)
            if success:
                # Check for random encounters
                encounter = self.check_random_encounter()
                if encounter:
                    return message + "\n\n" + encounter
                return message
            return TextFormatter.error(message)
        
        # Look command
        if base_cmd in ['look', 'l']:
            return self.world.get_location_description()
        
        # Map command
        if base_cmd == 'map':
            return self.world.get_map()
        
        # Stats command
        if base_cmd in ['stats', 'st']:
            return self.display_stats()
        
        # Inventory command
        if base_cmd in ['inventory', 'i']:
            return self.inventory.display()
        
        # Take command
        if base_cmd == 'take' and args:
            item_name = ' '.join(args)
            return self.take_item(item_name)
        
        # Drop command
        if base_cmd == 'drop' and args:
            item_name = ' '.join(args)
            return self.drop_item(item_name)
        
        # Use command
        if base_cmd == 'use' and args:
            item_name = ' '.join(args)
            return self.use_item(item_name)
        
        # Examine command
        if base_cmd == 'examine' and args:
            target = ' '.join(args)
            return self.examine(target)
        
        # Talk command
        if base_cmd == 'talk' and args:
            npc_name = ' '.join(args)
            return self.talk_to_npc(npc_name)
        
        # Rest command
        if base_cmd == 'rest':
            return self.rest()
        
        # Quests command
        if base_cmd in ['quests', 'q']:
            return self.quest_manager.display_quests()
        
        # Journal command
        if base_cmd in ['journal', 'j']:
            return self.quest_manager.display_journal()
        
        # Skills command
        if base_cmd == 'skills':
            return self.display_skills()
        
        # Save command
        if base_cmd == 'save':
            save_name = args[0] if args else None
            return self.save_game(save_name)
        
        # Load command
        if base_cmd == 'load' and args:
            save_name = args[0]
            return self.load_game(save_name)
        
        # Saves command
        if base_cmd == 'saves':
            return self.list_saves()
        
        # Return to previous location
        if base_cmd == 'return':
            return self.return_to_previous()
        
        # Time command
        if base_cmd == 'time':
            return self.display_time()
        
        # Difficulty command
        if base_cmd == 'difficulty':
            return self.display_difficulty()
        
        # If we get here, use AI engine to interpret command
        return self.ai_engine.interpret_command(command, self.get_context())
    
    def get_context(self) -> Dict:
        """Get current game context for AI"""
        location = self.world.get_current_location()
        
        return {
            'location': location['name'],
            'location_type': location['type'],
            'npcs': [npc['name'] for npc in location['npcs']],
            'items': [item['name'] for item in location['items']],
            'player_health': f"{self.player['health']}/{self.player['max_health']}",
            'player_level': self.player['level'],
            'player_gold': self.player['gold'],
            'has_quests': len(self.quest_manager.active_quests) > 0,
            'in_combat': False  # Will be updated by combat system
        }
    
    def check_random_encounter(self) -> Optional[str]:
        """Check if player encounters an enemy"""
        location = self.world.get_current_location()
        
        # Base encounter chance
        encounter_chance = 0.1 + (location['danger_level'] * 0.02)
        
        # Adjust for difficulty
        if self.player['difficulty'] == 'hard':
            encounter_chance *= 1.5
        elif self.player['difficulty'] == 'legendary':
            encounter_chance *= 2.0
        
        if random.random() < encounter_chance:
            # Select enemy
            enemy_type = random.choice(location['enemies'])
            enemy_level = location['enemy_level']
            
            # Scale enemy to player level
            if self.player['level'] > 5:
                enemy_level += random.randint(1, 3)
            
            # Start combat
            self.combat.start_combat(enemy_type, enemy_level)
            
            return self.combat.get_combat_status()
        
        return None
    
    def take_item(self, item_name: str) -> str:
        """Take an item from current location"""
        location = self.world.get_current_location()
        
        # Find item (case-insensitive partial match)
        found_item = None
        for item in location['items']:
            if item_name.lower() in item['name'].lower():
                found_item = item
                break
        
        if found_item:
            # Add to inventory
            self.inventory.add_item(found_item)
            
            # Remove from location
            location['items'].remove(found_item)
            
            # Check if item is valuable for quests
            self.quest_manager.check_item_quests(found_item)
            
            return TextFormatter.success(f"You take the {found_item['name']}.")
        
        return TextFormatter.error(f"There's no '{item_name}' here.")
    
    def drop_item(self, item_name: str) -> str:
        """Drop an item at current location"""
        # Find item in inventory
        item = self.inventory.get_item(item_name)
        
        if item:
            # Remove from inventory
            self.inventory.remove_item(item)
            
            # Add to location
            location = self.world.get_current_location()
            location['items'].append(item)
            
            return TextFormatter.info(f"You drop the {item['name']}.")
        
        return TextFormatter.error(f"You don't have '{item_name}'.")
    
    def use_item(self, item_name: str) -> str:
        """Use an item"""
        result = self.inventory.use_item(item_name)
        
        # Check if combat relevant
        if self.combat.in_combat:
            self.combat.process_item_use(result)
        
        return result
    
    def examine(self, target: str) -> str:
        """Examine something closely"""
        location = self.world.get_current_location()
        
        # Check items in location
        for item in location['items']:
            if target.lower() in item['name'].lower():
                return self.examine_item(item)
        
        # Check NPCs
        for npc in location['npcs']:
            if target.lower() in npc['name'].lower():
                return self.examine_npc(npc)
        
        # Check inventory
        item = self.inventory.get_item(target)
        if item:
            return self.examine_item(item)
        
        # Default examine
        return f"You look closely at {target}, but don't notice anything special."
    
    def examine_item(self, item: Dict) -> str:
        """Get detailed item description"""
        desc = f"\n{TextFormatter.item(f'📦 {item["name"]}')}\n"
        desc += TextFormatter.divider('-', 30) + "\n"
        desc += f"Type: {item['type'].title()}\n"
        desc += f"Value: {item['value']} gold\n"
        
        if 'damage' in item:
            desc += f"Damage: {item['damage']}\n"
        if 'defense' in item:
            desc += f"Defense: {item['defense']}\n"
        
        return desc
    
    def examine_npc(self, npc: Dict) -> str:
        """Get detailed NPC description"""
        desc = f"\n{TextFormatter.dialogue('', npc['name'])}\n"
        desc += TextFormatter.divider('-', 30) + "\n"
        desc += f"A {npc['personality']} {npc['race']} {npc['profession']}.\n"
        
        if npc.get('quest_giver', False):
            desc += f"{TextFormatter.info('They might have a quest for you.')}\n"
        
        return desc
    
    def talk_to_npc(self, npc_name: str) -> str:
        """Talk to an NPC"""
        location = self.world.get_current_location()
        
        # Find NPC
        found_npc = None
        for npc in location['npcs']:
            if npc_name.lower() in npc['name'].lower():
                found_npc = npc
                break
        
        if not found_npc:
            return TextFormatter.error(f"You don't see {npc_name} here.")
        
        # Get dialogue from NPC system
        dialogue = self.npc_system.talk_to(found_npc)
        
        # Check for quests
        if found_npc.get('quest_giver', False):
            quest = self.quest_manager.check_for_quest(found_npc)
            if quest:
                dialogue += f"\n\n{TextFormatter.info('They have a quest for you!')}\n"
                dialogue += f"Type 'quests' to view it."
        
        return dialogue
    
    def rest(self) -> str:
        """Rest and recover"""
        location = self.world.get_current_location()
        
        # Can't rest in dangerous places
        if location['danger_level'] > 5 or 'enemies' in location:
            return TextFormatter.error("It's too dangerous to rest here!")
        
        # Check if location is safe for resting
        safe_places = ['civilization', 'town']
        if location['type'] in safe_places or 'inn' in location['name'].lower():
            # Full rest in safe places
            heal_amount = self.player['max_health'] - self.player['health']
            self.player['health'] = self.player['max_health']
            self.player['mana'] = self.player['max_mana']
            
            # Time passes
            self.turn_count += 8
            
            return TextFormatter.success(f"You rest peacefully. Health and mana fully restored! ({heal_amount} HP)")
        
        # Quick rest in wilderness
        heal_amount = min(20, self.player['max_health'] - self.player['health'])
        self.player['health'] += heal_amount
        
        # Small chance of encounter while resting
        if random.random() < 0.3:
            encounter = self.check_random_encounter()
            if encounter:
                return f"You rest for a while, recovering {heal_amount} health.\n\nBUT YOU'RE INTERRUPTED!\n\n{encounter}"
        
        self.turn_count += 2
        return TextFormatter.info(f"You rest briefly, recovering {heal_amount} health.")
    
    def display_stats(self) -> str:
        """Display detailed player stats"""
        stats = f"""
{TextFormatter.header('📊 CHARACTER STATS')}
{TextFormatter.divider()}

{Colors.BOLD}{self.player['name']}{Colors.RESET} the {self.player['class']}
Level {self.player['level']} {self.player['class']}

{TextFormatter.info('Attributes:')}
  ❤️  Health: {self.player['health']}/{self.player['max_health']}
  💙 Mana:   {self.player['mana']}/{self.player['max_mana']}
  ⚔️  Strength: {self.player['strength']}
  🛡️  Defense:  {self.player['defense']}
  📚 Intelligence: {self.player['intelligence']}

{TextFormatter.info('Progress:')}
  ✨ XP: {self.player['xp']}/{self.player['xp_to_next']}
  🪙 Gold: {self.player['gold']}
  🎮 Difficulty: {self.player['difficulty'].title()}

{TextFormatter.info('Adventure Stats:')}
  🗺️  Locations Discovered: {len(self.world.discovered_locations)}
  📜 Active Quests: {len(self.quest_manager.active_quests)}
  ⚔️  Turns Taken: {self.turn_count}
  ⏱️  Play Time: {self.get_play_time()}
"""
        return stats
    
    def display_skills(self) -> str:
        """Display learned skills"""
        if not self.player['skills']:
            return "You haven't learned any skills yet."
        
        skills = f"\n{TextFormatter.header('✨ LEARNED SKILLS')}\n"
        skills += TextFormatter.divider() + "\n"
        
        for skill in self.player['skills']:
            skills += f"\n{Colors.BOLD}{skill['name']}{Colors.RESET}\n"
            skills += f"  {skill['description']}\n"
            skills += f"  Cost: {skill.get('cost', 0)} mana\n"
        
        return skills
    
    def get_play_time(self) -> str:
        """Get formatted play time"""
        elapsed = datetime.now() - self.start_time
        hours = elapsed.seconds // 3600
        minutes = (elapsed.seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    def display_time(self) -> str:
        """Display in-game time"""
        time_of_day = self.turn_count % 24
        day = self.turn_count // 24 + 1
        
        if time_of_day < 6:
            period = "night"
        elif time_of_day < 12:
            period = "morning"
        elif time_of_day < 18:
            period = "afternoon"
        else:
            period = "evening"
        
        return f"Day {day}, {time_of_day}:00 ({period})"
    
    def display_difficulty(self) -> str:
        """Display current difficulty settings"""
        difficulties = {
            'easy': "Enemies deal less damage, better loot",
            'normal': "Balanced experience",
            'hard': "Enemies are tougher, less loot",
            'legendary': "Extreme challenge, permadeath recommended"
        }
        
        desc = difficulties.get(self.player['difficulty'], "Unknown")
        return f"Current difficulty: {self.player['difficulty'].title()}\n{desc}"
    
    def return_to_previous(self) -> str:
        """Return to previous location"""
        if self.world.location_history:
            previous = self.world.location_history[-1]
            self.world.current_location = previous
            self.world.location_history.pop()
            return self.world.get_location_description()
        return "No previous location to return to."
    
    def save_game(self, save_name: Optional[str] = None) -> str:
        """Save current game state"""
        if not save_name:
            save_name = f"{self.player['name']}_Day{self.turn_count//24+1}"
        
        game_state = {
            'player': self.player,
            'world': self.world_data,
            'current_location': self.world.current_location,
            'discovered_locations': list(self.world.discovered_locations),
            'location_history': self.world.location_history,
            'flags': self.flags,
            'turn_count': self.turn_count,
            'quests': self.quest_manager.get_state(),
            'inventory': self.inventory.get_state(),
            'timestamp': datetime.now().isoformat()
        }
        
        if self.save_system.save_game(game_state, save_name):
            return TextFormatter.success(f"✅ Game saved as '{save_name}'")
        return TextFormatter.error("❌ Failed to save game")
    
    def load_game(self, save_name: Optional[str] = None) -> str:
        """Load a saved game"""
        if not save_name:
            saves = self.save_system.list_saves()
            if not saves:
                return "No saved games found."
            
            print(f"\n{TextFormatter.info('Available saves:')}")
            for i, save in enumerate(saves, 1):
                print(f"  {i}. {save}")
            
            choice = input(f"\n{TextFormatter.info('Enter save number:')}\n> ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(saves):
                    save_name = saves[idx]
                else:
                    return "Invalid choice."
            except ValueError:
                return "Invalid choice."
        
        game_state = self.save_system.load_game(save_name)
        if not game_state:
            return TextFormatter.error(f"Could not load '{save_name}'")
        
        # Restore game state
        self.player = game_state['player']
        self.world_data = game_state['world']
        self.world = WorldManager(self.world_data)
        self.world.current_location = game_state['current_location']
        self.world.discovered_locations = set(game_state['discovered_locations'])
        self.world.location_history = game_state['location_history']
        self.flags = game_state['flags']
        self.turn_count = game_state['turn_count']
        
        # Reinitialize systems
        self.quest_manager.load_state(game_state['quests'])
        self.inventory.load_state(game_state['inventory'])
        
        return TextFormatter.success(f"✅ Loaded game: {save_name}")
    
    def list_saves(self) -> str:
        """List all saved games"""
        saves = self.save_system.list_saves()
        
        if not saves:
            return "No saved games found."
        
        result = f"\n{TextFormatter.header('💾 SAVED GAMES')}\n"
        result += TextFormatter.divider() + "\n"
        
        for save in saves:
            info = self.save_system.get_save_info(save)
            if info:
                result += f"\n{Colors.BOLD}{save}{Colors.RESET}\n"
                result += f"  Player: {info.get('player', 'Unknown')}\n"
                result += f"  Day: {info.get('day', 1)}\n"
                result += f"  Saved: {info.get('timestamp', 'Unknown')}\n"
        
        return result
    
    def handle_death(self):
        """Handle player death"""
        self.clear_screen()
        
        death_messages = [
            f"{Colors.ERROR}{Colors.BOLD}💀 YOU HAVE DIED 💀{Colors.RESET}",
            "",
            f"{self.player['name']} the {self.player['class']} has fallen in battle.",
            "Your adventure has come to an end...",
            "",
            f"Final Stats:",
            f"  • Level: {self.player['level']}",
            f"  • Turns Survived: {self.turn_count}",
            f"  • Locations Discovered: {len(self.world.discovered_locations)}",
            f"  • Quests Completed: {self.quest_manager.completed_quests}"
        ]
        
        for line in death_messages:
            print(line)
            time.sleep(1)
        
        print(f"\n{TextFormatter.info('Would you like to:')}")
        print(f"  1. Load a saved game")
        print(f"  2. Start a new game")
        print(f"  3. Quit")
        
        while True:
            choice = input(f"\n{TextFormatter.info('Enter your choice (1-3):')}\n> ").strip()
            
            if choice == '1':
                self.load_game()
                self.running = True
                self.game_over = False
                break
            elif choice == '2':
                self.__init__(new_game=True)
                break
            elif choice == '3':
                self.running = False
                sys.exit(0)
    
    def game_loop(self):
        """Main game loop"""
        
        # Show initial location
        print(self.world.get_location_description())
        
        while self.running:
            try:
                # Check if player is dead
                if self.player['health'] <= 0:
                    self.game_over = True
                    self.handle_death()
                    continue
                
                # Get player input
                if self.combat.in_combat:
                    prompt = f"\n{Colors.COMBAT}⚔️ COMBAT [{self.combat.get_enemy_status()}] >{Colors.RESET} "
                else:
                    location = self.world.get_current_location()
                    prompt = f"\n{Colors.LOCATION}📍 [{location['name']}] >{Colors.RESET} "
                
                command = input(prompt).strip()
                
                # Quit command
                if command.lower() in ['quit', 'exit', 'q']:
                    print(f"\n{TextFormatter.info('Thanks for playing!')}")
                    print(f"Final stats: Level {self.player['level']}, {self.turn_count} turns")
                    
                    # Auto-save on quit
                    if self.player['health'] > 0:
                        self.save_game("autosave")
                    
                    self.running = False
                    break
                
                # Empty command
                if not command:
                    continue
                
                # Process command
                if self.combat.in_combat:
                    # Combat commands go through combat system first
                    if command.lower() in ['attack', 'fight']:
                        result = self.combat.process_turn('attack')
                    elif command.lower() == 'defend':
                        result = self.combat.process_turn('defend')
                    elif command.lower() == 'run':
                        result = self.combat.process_turn('flee')
                        if 'fled' in result.lower():
                            self.combat.in_combat = False
                    elif command.lower().startswith('use '):
                        item = command[4:].strip()
                        result = self.use_item(item)
                    else:
                        result = self.process_command(command)
                    
                    print(result)
                    
                    # Check if combat ended
                    if not self.combat.in_combat:
                        print(self.world.get_location_description())
                
                else:
                    # Normal commands
                    result = self.process_command(command)
                    if result:
                        print(result)
                    
                    # Auto-save every 10 turns
                    self.turn_count += 1
                    if self.turn_count % 10 == 0:
                        self.save_game("autosave")
                
            except KeyboardInterrupt:
                print(f"\n\n{TextFormatter.warning('Use "quit" to exit gracefully.')}")
            except Exception as e:
                print(TextFormatter.error(f"An error occurred: {e}"))
                self.logger.log('error', {'error': str(e)})

def main():
    """Main entry point"""
    try:
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description='AI Text Adventure Game')
        parser.add_argument('--load', '-l', help='Load a saved game')
        parser.add_argument('--new', '-n', action='store_true', help='Start new game')
        args = parser.parse_args()
        
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Start game
        if args.load:
            game = Game(new_game=False, save_file=args.load)
        else:
            game = Game(new_game=not args.new)
        
        # Run game
        game.game_loop()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()