"""
Inventory system for AI Text Adventure Game
Handles item management, equipment, crafting, and inventory operations
"""

import random
import json
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from collections import defaultdict

from .utils import TextFormatter, Colors

class ItemType(Enum):
    """Types of items in the game"""
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    FOOD = "food"
    SCROLL = "scroll"
    QUEST = "quest"
    TREASURE = "treasure"
    CRAFTING = "crafting"
    TOOL = "tool"
    BOOK = "book"
    KEY = "key"
    MISC = "miscellaneous"

class ItemRarity(Enum):
    """Rarity levels for items"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"

class EquipmentSlot(Enum):
    """Equipment slots for items"""
    HEAD = "head"
    CHEST = "chest"
    LEGS = "legs"
    FEET = "feet"
    HANDS = "hands"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    TWO_HAND = "two_hand"
    NECK = "neck"
    FINGER = "finger"
    BACK = "back"

class InventorySystem:
    """
    Main inventory management system
    Handles item storage, equipment, crafting, and item interactions
    """
    
    def __init__(self, player: Dict):
        self.player = player
        
        # Initialize player inventory if not exists
        if 'inventory' not in self.player:
            self.player['inventory'] = []
        if 'equipment' not in self.player:
            self.player['equipment'] = {}
        if 'gold' not in self.player:
            self.player['gold'] = 0
        
        # Inventory settings
        self.max_inventory_size = 20
        self.max_item_stack = 99
        
        # Initialize item database
        self.setup_item_database()
        self.setup_crafting_recipes()
        self.setup_item_effects()
        
    def setup_item_database(self):
        """Define all possible items in the game"""
        
        self.item_database = {
            # Weapons
            'dagger': {
                'name': 'Dagger',
                'type': ItemType.WEAPON,
                'rarity': ItemRarity.COMMON,
                'value': 10,
                'weight': 1,
                'damage': 4,
                'damage_type': 'piercing',
                'slot': EquipmentSlot.MAIN_HAND,
                'requirements': {'strength': 5},
                'description': 'A small, sharp blade. Good for stabbing.',
                'tags': ['light', 'quick']
            },
            
            'short_sword': {
                'name': 'Short Sword',
                'type': ItemType.WEAPON,
                'rarity': ItemRarity.COMMON,
                'value': 25,
                'weight': 3,
                'damage': 6,
                'damage_type': 'slashing',
                'slot': EquipmentSlot.MAIN_HAND,
                'requirements': {'strength': 8},
                'description': 'A standard short sword, well-balanced and reliable.',
                'tags': ['versatile']
            },
            
            'long_sword': {
                'name': 'Long Sword',
                'type': ItemType.WEAPON,
                'rarity': ItemRarity.UNCOMMON,
                'value': 50,
                'weight': 5,
                'damage': 8,
                'damage_type': 'slashing',
                'slot': EquipmentSlot.MAIN_HAND,
                'requirements': {'strength': 12},
                'description': 'A classic longsword. Deadly in skilled hands.',
                'tags': ['heavy', 'two_handed']
            },
            
            'battle_axe': {
                'name': 'Battle Axe',
                'type': ItemType.WEAPON,
                'rarity': ItemRarity.UNCOMMON,
                'value': 60,
                'weight': 7,
                'damage': 10,
                'damage_type': 'slashing',
                'slot': EquipmentSlot.TWO_HAND,
                'requirements': {'strength': 14},
                'description': 'A massive axe that can cleave through armor.',
                'tags': ['heavy', 'two_handed', 'brutal']
            },
            
            'bow': {
                'name': 'Bow',
                'type': ItemType.WEAPON,
                'rarity': ItemRarity.COMMON,
                'value': 35,
                'weight': 3,
                'damage': 6,
                'damage_type': 'piercing',
                'slot': EquipmentSlot.TWO_HAND,
                'requirements': {'dexterity': 10},
                'description': 'A simple wooden bow. Requires arrows.',
                'tags': ['ranged', 'two_handed']
            },
            
            'magic_staff': {
                'name': 'Magic Staff',
                'type': ItemType.WEAPON,
                'rarity': ItemRarity.RARE,
                'value': 120,
                'weight': 4,
                'damage': 6,
                'damage_type': 'magic',
                'slot': EquipmentSlot.TWO_HAND,
                'requirements': {'intelligence': 14},
                'description': 'A staff imbued with magical power.',
                'tags': ['magic', 'focus'],
                'spell_power': 10
            },
            
            # Armor
            'leather_armor': {
                'name': 'Leather Armor',
                'type': ItemType.ARMOR,
                'rarity': ItemRarity.COMMON,
                'value': 30,
                'weight': 10,
                'defense': 3,
                'slot': EquipmentSlot.CHEST,
                'requirements': {'strength': 5},
                'description': 'Tough leather that offers basic protection.',
                'tags': ['light']
            },
            
            'chainmail': {
                'name': 'Chainmail',
                'type': ItemType.ARMOR,
                'rarity': ItemRarity.UNCOMMON,
                'value': 75,
                'weight': 20,
                'defense': 5,
                'slot': EquipmentSlot.CHEST,
                'requirements': {'strength': 10},
                'description': 'Interlocking rings provide good protection.',
                'tags': ['medium']
            },
            
            'plate_armor': {
                'name': 'Plate Armor',
                'type': ItemType.ARMOR,
                'rarity': ItemRarity.RARE,
                'value': 200,
                'weight': 35,
                'defense': 8,
                'slot': EquipmentSlot.CHEST,
                'requirements': {'strength': 15},
                'description': 'Solid steel plates offering maximum protection.',
                'tags': ['heavy']
            },
            
            'shield': {
                'name': 'Shield',
                'type': ItemType.ARMOR,
                'rarity': ItemRarity.COMMON,
                'value': 25,
                'weight': 8,
                'defense': 2,
                'block_chance': 15,
                'slot': EquipmentSlot.OFF_HAND,
                'requirements': {'strength': 8},
                'description': 'A wooden shield with metal reinforcement.',
                'tags': ['defensive']
            },
            
            'helmet': {
                'name': 'Helmet',
                'type': ItemType.ARMOR,
                'rarity': ItemRarity.COMMON,
                'value': 20,
                'weight': 4,
                'defense': 2,
                'slot': EquipmentSlot.HEAD,
                'requirements': {'strength': 5},
                'description': 'Protects your head. Very important.',
                'tags': ['light']
            },
            
            'boots': {
                'name': 'Leather Boots',
                'type': ItemType.ARMOR,
                'rarity': ItemRarity.COMMON,
                'value': 15,
                'weight': 3,
                'defense': 1,
                'slot': EquipmentSlot.FEET,
                'description': 'Sturdy boots for long journeys.',
                'tags': ['light']
            },
            
            # Potions
            'health_potion': {
                'name': 'Health Potion',
                'type': ItemType.POTION,
                'rarity': ItemRarity.COMMON,
                'value': 20,
                'weight': 1,
                'effects': [{'type': 'heal', 'value': 30}],
                'description': 'A red potion that restores health.',
                'tags': ['consumable', 'healing'],
                'stackable': True
            },
            
            'mana_potion': {
                'name': 'Mana Potion',
                'type': ItemType.POTION,
                'rarity': ItemRarity.COMMON,
                'value': 18,
                'weight': 1,
                'effects': [{'type': 'mana', 'value': 20}],
                'description': 'A blue potion that restores mana.',
                'tags': ['consumable', 'mana'],
                'stackable': True
            },
            
            'strength_potion': {
                'name': 'Strength Potion',
                'type': ItemType.POTION,
                'rarity': ItemRarity.UNCOMMON,
                'value': 35,
                'weight': 1,
                'effects': [{'type': 'buff', 'stat': 'strength', 'value': 3, 'duration': 5}],
                'description': 'Grants temporary strength.',
                'tags': ['consumable', 'buff'],
                'stackable': True
            },
            
            'invisibility_potion': {
                'name': 'Invisibility Potion',
                'type': ItemType.POTION,
                'rarity': ItemRarity.RARE,
                'value': 80,
                'weight': 1,
                'effects': [{'type': 'buff', 'effect': 'invisibility', 'duration': 3}],
                'description': 'Makes you invisible for a short time.',
                'tags': ['consumable', 'utility'],
                'stackable': True
            },
            
            # Food
            'bread': {
                'name': 'Bread',
                'type': ItemType.FOOD,
                'rarity': ItemRarity.COMMON,
                'value': 3,
                'weight': 1,
                'effects': [{'type': 'heal', 'value': 5}],
                'description': 'A fresh loaf of bread.',
                'tags': ['consumable', 'food'],
                'stackable': True
            },
            
            'cheese': {
                'name': 'Cheese',
                'type': ItemType.FOOD,
                'rarity': ItemRarity.COMMON,
                'value': 4,
                'weight': 1,
                'effects': [{'type': 'heal', 'value': 8}],
                'description': 'A wedge of aged cheese.',
                'tags': ['consumable', 'food'],
                'stackable': True
            },
            
            'cooked_meat': {
                'name': 'Cooked Meat',
                'type': ItemType.FOOD,
                'rarity': ItemRarity.COMMON,
                'value': 6,
                'weight': 2,
                'effects': [{'type': 'heal', 'value': 12}],
                'description': 'Savory cooked meat, still warm.',
                'tags': ['consumable', 'food'],
                'stackable': True
            },
            
            # Scrolls
            'scroll_fireball': {
                'name': 'Scroll of Fireball',
                'type': ItemType.SCROLL,
                'rarity': ItemRarity.UNCOMMON,
                'value': 45,
                'weight': 1,
                'spell': 'fireball',
                'effects': [{'type': 'damage', 'value': 25, 'damage_type': 'fire', 'aoe': True}],
                'description': 'A scroll inscribed with the Fireball spell.',
                'tags': ['consumable', 'magic', 'aoe']
            },
            
            'scroll_healing': {
                'name': 'Scroll of Healing',
                'type': ItemType.SCROLL,
                'rarity': ItemRarity.UNCOMMON,
                'value': 40,
                'weight': 1,
                'spell': 'heal',
                'effects': [{'type': 'heal', 'value': 40}],
                'description': 'A scroll inscribed with a powerful healing spell.',
                'tags': ['consumable', 'magic', 'healing']
            },
            
            'scroll_identify': {
                'name': 'Scroll of Identify',
                'type': ItemType.SCROLL,
                'rarity': ItemRarity.COMMON,
                'value': 25,
                'weight': 1,
                'spell': 'identify',
                'description': 'Reveals the magical properties of an item.',
                'tags': ['consumable', 'magic', 'utility']
            },
            
            # Quest items
            'goblin_ear': {
                'name': 'Goblin Ear',
                'type': ItemType.QUEST,
                'rarity': ItemRarity.COMMON,
                'value': 5,
                'weight': 0.1,
                'description': 'Proof of a goblin kill.',
                'tags': ['quest', 'trophy'],
                'stackable': True
            },
            
            'ancient_key': {
                'name': 'Ancient Key',
                'type': ItemType.KEY,
                'rarity': ItemRarity.RARE,
                'value': 0,
                'weight': 0.5,
                'description': 'An old rusty key. It looks important.',
                'tags': ['quest', 'key']
            },
            
            'magic_crystal': {
                'name': 'Magic Crystal',
                'type': ItemType.QUEST,
                'rarity': ItemRarity.EPIC,
                'value': 200,
                'weight': 2,
                'description': 'A pulsing crystal radiating magical energy.',
                'tags': ['quest', 'artifact']
            },
            
            # Crafting materials
            'iron_ore': {
                'name': 'Iron Ore',
                'type': ItemType.CRAFTING,
                'rarity': ItemRarity.COMMON,
                'value': 5,
                'weight': 3,
                'description': 'Raw iron ore. Needs smelting.',
                'tags': ['crafting', 'ore'],
                'stackable': True
            },
            
            'leather': {
                'name': 'Leather',
                'type': ItemType.CRAFTING,
                'rarity': ItemRarity.COMMON,
                'value': 8,
                'weight': 2,
                'description': 'Treated animal hide.',
                'tags': ['crafting', 'material'],
                'stackable': True
            },
            
            'herbs': {
                'name': 'Herbs',
                'type': ItemType.CRAFTING,
                'rarity': ItemRarity.COMMON,
                'value': 3,
                'weight': 0.5,
                'description': 'A bundle of medicinal herbs.',
                'tags': ['crafting', 'alchemy'],
                'stackable': True
            },
            
            # Tools
            'pickaxe': {
                'name': 'Pickaxe',
                'type': ItemType.TOOL,
                'rarity': ItemRarity.COMMON,
                'value': 15,
                'weight': 5,
                'description': 'Used for mining ore.',
                'tags': ['tool', 'mining'],
                'durability': 100
            },
            
            'fishing_rod': {
                'name': 'Fishing Rod',
                'type': ItemType.TOOL,
                'rarity': ItemRarity.COMMON,
                'value': 12,
                'weight': 3,
                'description': 'Used for catching fish.',
                'tags': ['tool', 'fishing'],
                'durability': 50
            },
            
            'lockpicks': {
                'name': 'Lockpicks',
                'type': ItemType.TOOL,
                'rarity': ItemRarity.UNCOMMON,
                'value': 25,
                'weight': 0.2,
                'description': 'Used for picking locks.',
                'tags': ['tool', 'thieving'],
                'durability': 30
            },
            
            # Books
            'bestiary': {
                'name': 'Monster Bestiary',
                'type': ItemType.BOOK,
                'rarity': ItemRarity.UNCOMMON,
                'value': 30,
                'weight': 2,
                'description': 'Contains information about various monsters.',
                'tags': ['book', 'knowledge'],
                'pages': 50
            },
            
            'spellbook': {
                'name': 'Spellbook',
                'type': ItemType.BOOK,
                'rarity': ItemRarity.RARE,
                'value': 100,
                'weight': 3,
                'description': 'Contains magical formulas and spells.',
                'tags': ['book', 'magic'],
                'spells': ['magic_missile', 'shield', 'light']
            },
            
            # Treasure
            'gold_coins': {
                'name': 'Gold Coins',
                'type': ItemType.TREASURE,
                'rarity': ItemRarity.COMMON,
                'value': 1,
                'weight': 0.01,
                'description': 'Shiny gold coins.',
                'tags': ['treasure', 'currency'],
                'stackable': True
            },
            
            'gemstone': {
                'name': 'Gemstone',
                'type': ItemType.TREASURE,
                'rarity': ItemRarity.UNCOMMON,
                'value': 50,
                'weight': 0.1,
                'description': 'A precious cut gemstone.',
                'tags': ['treasure', 'valuable']
            },
            
            'gold_bar': {
                'name': 'Gold Bar',
                'type': ItemType.TREASURE,
                'rarity': ItemRarity.RARE,
                'value': 100,
                'weight': 5,
                'description': 'A bar of pure gold.',
                'tags': ['treasure', 'valuable']
            }
        }
    
    def setup_crafting_recipes(self):
        """Define crafting recipes"""
        
        self.crafting_recipes = {
            'iron_sword': {
                'name': 'Iron Sword',
                'result': 'short_sword',  # Using short_sword as base
                'ingredients': {
                    'iron_ore': 3,
                    'coal': 2
                },
                'skill': 'smithing',
                'skill_level': 1,
                'time': 10
            },
            
            'health_potion': {
                'name': 'Health Potion',
                'result': 'health_potion',
                'ingredients': {
                    'herbs': 2,
                    'water_flask': 1
                },
                'skill': 'alchemy',
                'skill_level': 1,
                'time': 5
            },
            
            'leather_armor': {
                'name': 'Leather Armor',
                'result': 'leather_armor',
                'ingredients': {
                    'leather': 4,
                    'thread': 1
                },
                'skill': 'leatherworking',
                'skill_level': 2,
                'time': 15
            },
            
            'strength_potion': {
                'name': 'Strength Potion',
                'result': 'strength_potion',
                'ingredients': {
                    'herbs': 3,
                    'wolf_tooth': 1,
                    'water_flask': 1
                },
                'skill': 'alchemy',
                'skill_level': 3,
                'time': 8
            },
            
            'chainmail': {
                'name': 'Chainmail',
                'result': 'chainmail',
                'ingredients': {
                    'iron_ore': 6,
                    'coal': 4
                },
                'skill': 'smithing',
                'skill_level': 3,
                'time': 20
            }
        }
    
    def setup_item_effects(self):
        """Define special item effects"""
        
        self.item_effects = {
            'heal': self.effect_heal,
            'mana': self.effect_mana,
            'damage': self.effect_damage,
            'buff': self.effect_buff,
            'debuff': self.effect_debuff,
            'teleport': self.effect_teleport,
            'identify': self.effect_identify,
            'repair': self.effect_repair
        }
    
    def add_item(self, item_name: str, count: int = 1) -> bool:
        """
        Add item(s) to inventory
        Returns True if successful, False if inventory full
        """
        
        # Check if item exists in database
        if item_name not in self.item_database:
            # Try to find by name (case-insensitive)
            found = False
            for key, item in self.item_database.items():
                if item['name'].lower() == item_name.lower():
                    item_name = key
                    found = True
                    break
            
            if not found:
                print(f"Item '{item_name}' not found in database")
                return False
        
        item_template = self.item_database[item_name]
        
        # Check if item is stackable
        if item_template.get('stackable', False):
            return self.add_stackable_item(item_name, count)
        else:
            return self.add_single_item(item_name, count)
    
    def add_stackable_item(self, item_name: str, count: int) -> bool:
        """Add stackable items to inventory"""
        
        # Find existing stack
        for item in self.player['inventory']:
            if item.get('name') == item_name and item.get('count', 1) < self.max_item_stack:
                # Add to existing stack
                space = self.max_item_stack - item['count']
                add_amount = min(count, space)
                item['count'] += add_amount
                count -= add_amount
                
                if count == 0:
                    return True
        
        # Create new stacks if needed
        while count > 0:
            if len(self.player['inventory']) >= self.max_inventory_size:
                return False
            
            stack_size = min(count, self.max_item_stack)
            new_item = self.create_item(item_name)
            new_item['count'] = stack_size
            self.player['inventory'].append(new_item)
            count -= stack_size
        
        return True
    
    def add_single_item(self, item_name: str, count: int) -> bool:
        """Add non-stackable items to inventory"""
        
        for _ in range(count):
            if len(self.player['inventory']) >= self.max_inventory_size:
                return False
            
            new_item = self.create_item(item_name)
            self.player['inventory'].append(new_item)
        
        return True
    
    def create_item(self, item_name: str) -> Dict:
        """Create a new item instance from template"""
        
        template = self.item_database[item_name].copy()
        
        # Create item instance
        item = {
            'id': self.generate_item_id(),
            'name': template['name'],
            'type': template['type'],
            'rarity': template['rarity'],
            'value': template['value'],
            'weight': template['weight'],
            'description': template['description'],
            'tags': template.get('tags', []),
            'equipped': False
        }
        
        # Copy specific attributes
        for attr in ['damage', 'defense', 'slot', 'requirements', 'effects', 
                    'spell', 'durability', 'pages', 'spells']:
            if attr in template:
                item[attr] = template[attr]
        
        return item
    
    def generate_item_id(self) -> str:
        """Generate unique item ID"""
        import hashlib
        import time
        
        unique = f"item_{time.time()}_{random.random()}"
        return hashlib.md5(unique.encode()).hexdigest()[:8]
    
    def remove_item(self, item_name: str, count: int = 1) -> bool:
        """
        Remove item(s) from inventory
        Returns True if successful, False if not enough items
        """
        
        items_removed = 0
        
        for i in range(len(self.player['inventory']) - 1, -1, -1):
            item = self.player['inventory'][i]
            
            if item['name'].lower() == item_name.lower():
                if item.get('count', 1) > 1:
                    # Stackable item
                    remove_count = min(item['count'], count - items_removed)
                    item['count'] -= remove_count
                    items_removed += remove_count
                    
                    if item['count'] == 0:
                        self.player['inventory'].pop(i)
                else:
                    # Single item
                    self.player['inventory'].pop(i)
                    items_removed += 1
                
                if items_removed >= count:
                    return True
        
        return items_removed == count
    
    def get_item(self, item_name: str) -> Optional[Dict]:
        """Get item from inventory by name (partial match)"""
        
        # Try exact match first
        for item in self.player['inventory']:
            if item['name'].lower() == item_name.lower():
                return item
        
        # Then partial match
        for item in self.player['inventory']:
            if item_name.lower() in item['name'].lower():
                return item
        
        return None
    
    def get_all_items(self, item_name: str) -> List[Dict]:
        """Get all items matching name"""
        
        matches = []
        for item in self.player['inventory']:
            if item_name.lower() in item['name'].lower():
                matches.append(item)
        
        return matches
    
    def use_item(self, item_name: str) -> str:
        """Use an item from inventory"""
        
        item = self.get_item(item_name)
        
        if not item:
            return f"You don't have {item_name}."
        
        # Process based on item type
        if item['type'] == ItemType.POTION or item['type'] == ItemType.FOOD:
            return self.use_consumable(item)
        
        elif item['type'] == ItemType.SCROLL:
            return self.use_scroll(item)
        
        elif item['type'] == ItemType.BOOK:
            return self.use_book(item)
        
        elif item['type'] == ItemType.TOOL:
            return self.use_tool(item)
        
        elif item['type'] == ItemType.WEAPON or item['type'] == ItemType.ARMOR:
            return self.equip_item(item)
        
        else:
            return f"You can't use the {item['name']} right now."
    
    def use_consumable(self, item: Dict) -> str:
        """Use a consumable item (potion/food)"""
        
        messages = []
        
        # Apply effects
        for effect in item.get('effects', []):
            effect_type = effect['type']
            if effect_type in self.item_effects:
                result = self.item_effects[effect_type](effect)
                if result:
                    messages.append(result)
        
        # Remove used item
        if item.get('count', 1) > 1:
            item['count'] -= 1
        else:
            self.player['inventory'].remove(item)
        
        return "\n".join(messages) if messages else f"You use the {item['name']}."
    
    def use_scroll(self, item: Dict) -> str:
        """Use a magic scroll"""
        
        spell = item.get('spell', 'unknown')
        
        messages = [f"You read the {item['name']}..."]
        
        # Apply spell effects
        for effect in item.get('effects', []):
            effect_type = effect['type']
            if effect_type in self.item_effects:
                result = self.item_effects[effect_type](effect)
                if result:
                    messages.append(result)
        
        # Remove scroll after use
        self.player['inventory'].remove(item)
        
        return "\n".join(messages)
    
    def use_book(self, item: Dict) -> str:
        """Read a book"""
        
        if 'spells' in item:
            # Spellbook - learn spells
            learned = []
            for spell in item['spells']:
                if spell not in self.player.get('spells', []):
                    if 'spells' not in self.player:
                        self.player['spells'] = []
                    self.player['spells'].append(spell)
                    learned.append(spell)
            
            if learned:
                return f"You study the {item['name']} and learn: {', '.join(learned)}"
            else:
                return f"You already know the spells in this book."
        
        elif 'pages' in item:
            # Regular book
            return f"You read the {item['name']}. It's quite informative."
        
        return f"You flip through the {item['name']}."
    
    def use_tool(self, item: Dict) -> str:
        """Use a tool"""
        
        # Check durability
        if 'durability' in item:
            if item['durability'] <= 0:
                return f"The {item['name']} is broken and needs repair."
        
        # Tool-specific messages
        if 'pickaxe' in item['name'].lower():
            return "You swing your pickaxe. (Use 'mine' command in mining areas)"
        elif 'fishing' in item['name'].lower():
            return "You cast your line. (Use 'fish' command near water)"
        elif 'lockpick' in item['name'].lower():
            return "You ready your lockpicks. (Use 'pick' command on locked objects)"
        
        return f"You examine your {item['name']}."
    
    def equip_item(self, item: Dict) -> str:
        """Equip a weapon or armor"""
        
        # Check requirements
        requirements = item.get('requirements', {})
        for stat, value in requirements.items():
            if self.player.get(stat, 0) < value:
                return f"You don't meet the {stat} requirement ({value}) to equip this."
        
        # Check if already equipped
        if item.get('equipped', False):
            return self.unequip_item(item)
        
        # Get slot
        slot = item.get('slot')
        if not slot:
            return "This item cannot be equipped."
        
        # Check if slot is occupied
        if slot.value in self.player.get('equipment', {}):
            # Unequip current item
            current = self.player['equipment'][slot.value]
            current['equipped'] = False
            del self.player['equipment'][slot.value]
        
        # Equip new item
        item['equipped'] = True
        if 'equipment' not in self.player:
            self.player['equipment'] = {}
        self.player['equipment'][slot.value] = item
        
        return f"You equip the {item['name']}."
    
    def unequip_item(self, item: Dict) -> str:
        """Unequip an item"""
        
        slot = item.get('slot')
        if slot and slot.value in self.player.get('equipment', {}):
            item['equipped'] = False
            del self.player['equipment'][slot.value]
            return f"You unequip the {item['name']}."
        
        return f"The {item['name']} is not equipped."
    
    def effect_heal(self, effect: Dict) -> str:
        """Healing effect"""
        heal_amount = effect.get('value', 10)
        old_health = self.player['health']
        self.player['health'] = min(self.player['max_health'], self.player['health'] + heal_amount)
        actual_heal = self.player['health'] - old_health
        return f"❤️ Healed for {actual_heal} health."
    
    def effect_mana(self, effect: Dict) -> str:
        """Mana restoration effect"""
        mana_amount = effect.get('value', 10)
        old_mana = self.player.get('mana', 0)
        self.player['mana'] = min(self.player.get('max_mana', 100), self.player.get('mana', 0) + mana_amount)
        actual_mana = self.player['mana'] - old_mana
        return f"💙 Restored {actual_mana} mana."
    
    def effect_damage(self, effect: Dict) -> str:
        """Damage effect (for combat items)"""
        # This will be handled by combat system
        return f"⚔️ Deals {effect.get('value', 0)} {effect.get('damage_type', 'physical')} damage."
    
    def effect_buff(self, effect: Dict) -> str:
        """Buff effect"""
        stat = effect.get('stat', 'strength')
        value = effect.get('value', 1)
        duration = effect.get('duration', 3)
        
        # Add to player buffs
        if 'buffs' not in self.player:
            self.player['buffs'] = []
        
        self.player['buffs'].append({
            'stat': stat,
            'value': value,
            'duration': duration,
            'source': 'item'
        })
        
        return f"✨ Gained +{value} {stat} for {duration} turns."
    
    def effect_debuff(self, effect: Dict) -> str:
        """Debuff effect (for enemy use)"""
        return f"😨 Enemy affected by {effect.get('effect', 'debuff')}."
    
    def effect_teleport(self, effect: Dict) -> str:
        """Teleport effect"""
        # This will be handled by world system
        return "🌀 You feel a strange pulling sensation..."
    
    def effect_identify(self, effect: Dict) -> str:
        """Identify item effect"""
        return "🔍 You can now identify magical properties of items."
    
    def effect_repair(self, effect: Dict) -> str:
        """Repair item effect"""
        return "🔧 Your equipment feels restored."
    
    def get_item_value(self, item: Dict) -> int:
        """Calculate item value (with modifiers)"""
        
        base_value = item.get('value', 0)
        
        # Rarity multiplier
        rarity_mult = {
            ItemRarity.COMMON: 1,
            ItemRarity.UNCOMMON: 1.5,
            ItemRarity.RARE: 3,
            ItemRarity.EPIC: 6,
            ItemRarity.LEGENDARY: 10,
            ItemRarity.MYTHIC: 20
        }
        
        mult = rarity_mult.get(item['rarity'], 1)
        
        # Condition multiplier (for durability)
        if 'durability' in item:
            max_durability = item.get('max_durability', item['durability'])
            condition = item['durability'] / max_durability
            mult *= condition
        
        return int(base_value * mult)
    
    def get_total_weight(self) -> float:
        """Calculate total inventory weight"""
        
        total = 0
        for item in self.player['inventory']:
            weight = item.get('weight', 0)
            if item.get('count', 1) > 1:
                weight *= item['count']
            total += weight
        
        return total
    
    def is_inventory_full(self) -> bool:
        """Check if inventory is full"""
        return len(self.player['inventory']) >= self.max_inventory_size
    
    def get_free_slots(self) -> int:
        """Get number of free inventory slots"""
        return max(0, self.max_inventory_size - len(self.player['inventory']))
    
    def display(self) -> str:
        """Display inventory contents"""
        
        if not self.player['inventory']:
            return f"\n{TextFormatter.info('Your inventory is empty.')}"
        
        # Group stackable items
        display_items = []
        stackable_groups = defaultdict(list)
        
        for item in self.player['inventory']:
            if item.get('stackable', False):
                stackable_groups[item['name']].append(item)
            else:
                display_items.append(item)
        
        # Format display
        display = f"\n{TextFormatter.header('🎒 INVENTORY')}\n"
        display += TextFormatter.divider()
        
        # Show equipment first
        if self.player.get('equipment'):
            display += f"\n{Colors.INFO}⚔️ Equipped:{Colors.RESET}\n"
            for slot, item in self.player['equipment'].items():
                display += f"  {slot}: {item['name']}\n"
            display += "\n"
        
        # Show regular items
        if display_items:
            display += f"{Colors.INFO}📦 Items:{Colors.RESET}\n"
            for item in display_items:
                equipped = " (equipped)" if item.get('equipped') else ""
                display += f"  • {item['name']}{equipped}\n"
        
        # Show stackable items
        if stackable_groups:
            display += f"\n{Colors.INFO}📚 Stacked:{Colors.RESET}\n"
            for name, items in stackable_groups.items():
                total = sum(item.get('count', 1) for item in items)
                display += f"  • {name} x{total}\n"
        
        # Show stats
        display += f"\n{TextFormatter.info('Stats:')}\n"
        display += f"  Slots: {len(self.player['inventory'])}/{self.max_inventory_size}\n"
        display += f"  Weight: {self.get_total_weight():.1f} kg\n"
        display += f"  Gold: {self.player.get('gold', 0)} 🪙\n"
        
        return display
    
    def display_equipment(self) -> str:
        """Display currently equipped items"""
        
        if not self.player.get('equipment'):
            return f"\n{TextFormatter.info('You have nothing equipped.')}"
        
        display = f"\n{TextFormatter.header('⚔️ EQUIPMENT')}\n"
        display += TextFormatter.divider() + "\n"
        
        equipment = self.player['equipment']
        
        # Calculate total stats
        total_damage = 0
        total_defense = 0
        
        for slot, item in equipment.items():
            display += f"{slot}: {item['name']}\n"
            if 'damage' in item:
                total_damage += item['damage']
            if 'defense' in item:
                total_defense += item['defense']
        
        display += f"\n{TextFormatter.info('Total Stats:')}\n"
        if total_damage > 0:
            display += f"  Damage: {total_damage}\n"
        if total_defense > 0:
            display += f"  Defense: {total_defense}\n"
        
        return display
    
    def display_crafting(self) -> str:
        """Display available crafting recipes"""
        
        display = f"\n{TextFormatter.header('🔨 CRAFTING')}\n"
        display += TextFormatter.divider() + "\n"
        
        # Check player's crafting skills
        smithing_level = self.player.get('skills', {}).get('smithing', 0)
        alchemy_level = self.player.get('skills', {}).get('alchemy', 0)
        
        available_recipes = []
        
        for recipe_id, recipe in self.crafting_recipes.items():
            skill = recipe['skill']
            skill_level = recipe['skill_level']
            
            # Check if player meets skill requirement
            player_skill = self.player.get('skills', {}).get(skill, 0)
            if player_skill >= skill_level:
                available_recipes.append(recipe)
        
        if not available_recipes:
            display += "You don't know any crafting recipes yet.\n"
            display += "Visit a trainer to learn crafting skills."
        else:
            for i, recipe in enumerate(available_recipes, 1):
                display += f"\n{i}. {recipe['name']}\n"
                display += f"   Requires: {recipe['skill']} level {recipe['skill_level']}\n"
                display += f"   Ingredients:\n"
                
                for ingredient, amount in recipe['ingredients'].items():
                    # Check if player has ingredients
                    has_ingredient = self.has_item(ingredient, amount)
                    status = "✅" if has_ingredient else "❌"
                    display += f"     {status} {ingredient} x{amount}\n"
        
        return display
    
    def has_item(self, item_name: str, count: int = 1) -> bool:
        """Check if player has at least count of item"""
        
        total = 0
        for item in self.player['inventory']:
            if item['name'].lower() == item_name.lower():
                if item.get('count', 1) > 1:
                    total += item['count']
                else:
                    total += 1
                
                if total >= count:
                    return True
        
        return False
    
    def craft_item(self, recipe_name: str) -> str:
        """Craft an item from a recipe"""
        
        # Find recipe
        recipe = None
        for rid, r in self.crafting_recipes.items():
            if recipe_name.lower() in r['name'].lower():
                recipe = r
                break
        
        if not recipe:
            return f"No recipe found for '{recipe_name}'."
        
        # Check if player has ingredients
        missing = []
        for ingredient, amount in recipe['ingredients'].items():
            if not self.has_item(ingredient, amount):
                missing.append(f"{ingredient} x{amount}")
        
        if missing:
            return f"Missing ingredients: {', '.join(missing)}"
        
        # Remove ingredients
        for ingredient, amount in recipe['ingredients'].items():
            self.remove_item(ingredient, amount)
        
        # Add crafted item
        self.add_item(recipe['result'])
        
        return f"✅ Successfully crafted {recipe['name']}!"
    
    def sort_inventory(self, method: str = 'name'):
        """Sort inventory by various methods"""
        
        if method == 'name':
            self.player['inventory'].sort(key=lambda x: x['name'])
        elif method == 'value':
            self.player['inventory'].sort(key=lambda x: x.get('value', 0), reverse=True)
        elif method == 'type':
            self.player['inventory'].sort(key=lambda x: x['type'].value)
        elif method == 'weight':
            self.player['inventory'].sort(key=lambda x: x.get('weight', 0))
    
    def drop_all(self, item_name: str) -> List[Dict]:
        """Drop all of a specific item type"""
        
        dropped = []
        
        for item in self.player['inventory'][:]:
            if item_name.lower() in item['name'].lower():
                self.player['inventory'].remove(item)
                dropped.append(item)
        
        return dropped
    
    def get_state(self) -> Dict:
        """Get inventory state for saving"""
        
        return {
            'inventory': self.player['inventory'],
            'equipment': self.player.get('equipment', {}),
            'gold': self.player.get('gold', 0),
            'max_inventory_size': self.max_inventory_size
        }
    
    def load_state(self, state: Dict):
        """Load inventory state from save"""
        
        self.player['inventory'] = state.get('inventory', [])
        self.player['equipment'] = state.get('equipment', {})
        self.player['gold'] = state.get('gold', 0)
        self.max_inventory_size = state.get('max_inventory_size', 20)

# Global item database instance
item_database = None