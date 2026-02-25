"""
NPC system for AI Text Adventure Game
Handles NPC generation, personalities, relationships, schedules, and dynamic interactions
"""

import random
import math
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, time
from collections import defaultdict

from .utils import TextFormatter, Colors, Dice
from .ai_engine import AIEngine

class NPCRole(Enum):
    """NPC roles in the game world"""
    VILLAGER = "villager"
    MERCHANT = "merchant"
    GUARD = "guard"
    BLACKSMITH = "blacksmith"
    INNKEEPER = "innkeeper"
    FARMER = "farmer"
    PRIEST = "priest"
    SCHOLAR = "scholar"
    THIEF = "thief"
    ADVENTURER = "adventurer"
    NOBLE = "noble"
    BEGGAR = "beggar"
    ALCHEMIST = "alchemist"
    BARD = "bard"
    HUNTER = "hunter"
    HERMIT = "hermit"
    QUEST_GIVER = "quest_giver"
    TRAINER = "trainer"

class NPCStatus(Enum):
    """Current status of NPC"""
    AVAILABLE = "available"      # Can be interacted with
    BUSY = "busy"                # Currently occupied
    SLEEPING = "sleeping"        # Asleep
    WORKING = "working"          # At work
    TRAVELING = "traveling"      # Moving between locations
    DEAD = "dead"                # Permanently unavailable

class RelationshipLevel(Enum):
    """Relationship levels with NPC"""
    HOSTILE = "hostile"           # Will attack on sight
    UNFRIENDLY = "unfriendly"     # Dislikes player
    NEUTRAL = "neutral"           # No strong feelings
    FRIENDLY = "friendly"         # Likes player
    TRUSTING = "trusting"         # Close relationship
    ALLY = "ally"                 # Will fight for player
    LOVER = "lover"               # Romantic relationship
    FAMILY = "family"             # Blood relation

class NPCSystem:
    """
    Main NPC management system
    Handles NPC generation, relationships, schedules, and interactions
    """
    
    def __init__(self, player: Dict, game_flags: Dict):
        self.player = player
        self.game_flags = game_flags
        
        # NPC storage
        self.npcs = {}              # All NPCs in game (key: npc_id)
        self.npcs_by_location = defaultdict(list)  # NPCs by location
        self.npcs_by_role = defaultdict(list)      # NPCs by role
        
        # Relationship tracking
        self.relationships = defaultdict(dict)     # npc_id -> relationship data
        self.conversation_history = defaultdict(list)  # npc_id -> past conversations
        
        # World state
        self.current_time = datetime.now()
        self.world_events = []
        
        # Initialize NPC templates
        self.setup_npc_templates()
        self.setup_name_generators()
        self.setup_personalities()
        self.setup_dialogue_templates()
        self.setup_relationship_thresholds()
        self.setup_schedule_templates()
        self.setup_trade_tables()
        
    def setup_npc_templates(self):
        """Define base templates for different NPC roles"""
        
        self.npc_templates = {
            NPCRole.VILLAGER: {
                'name_prefixes': ['Farmer', 'Miller', 'Baker', 'Carpenter', 'Fisher'],
                'health_range': (50, 80),
                'gold_range': (10, 50),
                'inventory_size': (2, 4),
                'base_friendliness': 0.5,
                'gossip_chance': 0.7,
                'rumor_knowledge': 0.3,
                'combat_skill': (1, 3),
                'schedule_type': 'villager'
            },
            
            NPCRole.MERCHANT: {
                'name_prefixes': ['Trader', 'Merchant', 'Shopkeeper', 'Vendor'],
                'health_range': (40, 60),
                'gold_range': (100, 500),
                'inventory_size': (8, 15),
                'base_friendliness': 0.4,
                'gossip_chance': 0.5,
                'rumor_knowledge': 0.4,
                'combat_skill': (1, 2),
                'schedule_type': 'merchant',
                'trade_multiplier': 1.2  # Sell high, buy low
            },
            
            NPCRole.GUARD: {
                'name_prefixes': ['Guard', 'Watchman', 'Sentinel', 'Patrol'],
                'health_range': (80, 120),
                'gold_range': (20, 80),
                'inventory_size': (3, 6),
                'base_friendliness': 0.3,
                'gossip_chance': 0.4,
                'rumor_knowledge': 0.5,
                'combat_skill': (5, 8),
                'schedule_type': 'guard',
                'suspicion_threshold': 0.6
            },
            
            NPCRole.BLACKSMITH: {
                'name_prefixes': ['Smith', 'Forger', 'Ironworker'],
                'health_range': (70, 100),
                'gold_range': (50, 200),
                'inventory_size': (5, 10),
                'base_friendliness': 0.4,
                'gossip_chance': 0.3,
                'rumor_knowledge': 0.2,
                'combat_skill': (4, 6),
                'schedule_type': 'artisan',
                'services': ['repair', 'craft', 'upgrade']
            },
            
            NPCRole.INNKEEPER: {
                'name_prefixes': ['Innkeeper', 'Tavernkeep', 'Barkeep'],
                'health_range': (50, 70),
                'gold_range': (50, 150),
                'inventory_size': (10, 20),
                'base_friendliness': 0.8,
                'gossip_chance': 0.9,
                'rumor_knowledge': 0.8,
                'combat_skill': (2, 4),
                'schedule_type': 'innkeeper',
                'services': ['lodging', 'food', 'drink', 'information']
            },
            
            NPCRole.PRIEST: {
                'name_prefixes': ['Priest', 'Cleric', 'Healer', 'Friar'],
                'health_range': (45, 65),
                'gold_range': (20, 100),
                'inventory_size': (3, 7),
                'base_friendliness': 0.9,
                'gossip_chance': 0.5,
                'rumor_knowledge': 0.3,
                'combat_skill': (2, 4),
                'schedule_type': 'priest',
                'services': ['heal', 'bless', 'confess', 'marry']
            },
            
            NPCRole.SCHOLAR: {
                'name_prefixes': ['Scholar', 'Sage', 'Lorekeeper', 'Historian'],
                'health_range': (30, 50),
                'gold_range': (30, 120),
                'inventory_size': (4, 8),
                'base_friendliness': 0.5,
                'gossip_chance': 0.6,
                'rumor_knowledge': 0.9,
                'combat_skill': (1, 2),
                'schedule_type': 'scholar',
                'services': ['identify', 'research', 'translate']
            },
            
            NPCRole.THIEF: {
                'name_prefixes': ['Shadow', 'Rogue', 'Cutpurse', 'Thief'],
                'health_range': (40, 70),
                'gold_range': (20, 300),
                'inventory_size': (3, 8),
                'base_friendliness': 0.1,
                'gossip_chance': 0.3,
                'rumor_knowledge': 0.6,
                'combat_skill': (4, 7),
                'schedule_type': 'thief',
                'steal_chance': 0.3,
                'fence_multiplier': 0.5
            },
            
            NPCRole.ADVENTURER: {
                'name_prefixes': ['Brave', 'Bold', 'Fearless', 'Veteran'],
                'health_range': (70, 130),
                'gold_range': (30, 200),
                'inventory_size': (5, 12),
                'base_friendliness': 0.5,
                'gossip_chance': 0.7,
                'rumor_knowledge': 0.7,
                'combat_skill': (6, 10),
                'schedule_type': 'adventurer',
                'can_join_party': True
            },
            
            NPCRole.QUEST_GIVER: {
                'name_prefixes': ['Elder', 'Master', 'Chief', 'Leader'],
                'health_range': (40, 80),
                'gold_range': (100, 500),
                'inventory_size': (2, 5),
                'base_friendliness': 0.6,
                'gossip_chance': 0.8,
                'rumor_knowledge': 0.8,
                'combat_skill': (2, 5),
                'schedule_type': 'leader',
                'quests_available': (1, 3)
            }
        }
    
    def setup_name_generators(self):
        """Setup name generation components for different cultures/races"""
        
        self.name_data = {
            'first_names': {
                'human': [
                    'John', 'Emma', 'William', 'Olivia', 'James', 'Sophia',
                    'Robert', 'Isabella', 'Michael', 'Mia', 'David', 'Charlotte',
                    'Richard', 'Amelia', 'Joseph', 'Harper', 'Thomas', 'Evelyn'
                ],
                'elf': [
                    'Aelar', 'Lyra', 'Erion', 'Caelia', 'Faelan', 'Sylph',
                    'Thalanil', 'Elara', 'Kaelen', 'Lúthien', 'Orophin', 'Celebrían'
                ],
                'dwarf': [
                    'Thorin', 'Borin', 'Gimli', 'Hildi', 'Bofur', 'Dís',
                    'Durin', 'Helga', 'Balin', 'Frida', 'Nori', 'Sigrid'
                ],
                'halfling': [
                    'Bilbo', 'Rosie', 'Frodo', 'Daisy', 'Samwise', 'Poppy',
                    'Meriadoc', 'Lily', 'Peregrin', 'Marigold', 'Hamfast', 'Primula'
                ]
            },
            
            'last_names': {
                'human': [
                    'Smith', 'Baker', 'Miller', 'Cooper', 'Fletcher', 'Thatcher',
                    'Weaver', 'Tanner', 'Mason', 'Carter', 'Harper', 'Fisher'
                ],
                'elf': [
                    'Starweaver', 'Moonshadow', 'Greenleaf', 'Nightbreeze',
                    'Dawnweaver', 'Silverstream', 'Goldenhair', 'Swiftarrow'
                ],
                'dwarf': [
                    'Ironfoot', 'Stonehelm', 'Goldbeard', 'Oakenheart',
                    'Bronzebelt', 'Copperhand', 'Ironforge', 'Deepdelver'
                ],
                'halfling': [
                    'Underhill', 'Goodbarrel', 'Tealeaf', 'Took', 'Brandybuck',
                    'Hornblower', 'Proudfoot', 'Baggins', 'Gamgee'
                ]
            },
            
            'titles': {
                'merchant': ['the Trader', 'the Merchant', 'of the Bazaar'],
                'guard': ['the Guardian', 'the Watchful', 'Shieldbearer'],
                'priest': ['the Holy', 'the Devout', 'Lightbringer'],
                'scholar': ['the Learned', 'the Wise', 'Sage'],
                'thief': ['the Shadow', 'the Silent', 'Nightwalker'],
                'adventurer': ['the Brave', 'the Bold', 'Dragonslayer']
            },
            
            'nicknames': [
                'the Red', 'the Grey', 'the Young', 'the Old', 'the Tall',
                'the Short', 'the Quick', 'the Kind', 'the Stern', 'the Jolly',
                'One-Eye', 'Gold-Tooth', 'Swift-Hand', 'Iron-Heart'
            ]
        }
    
    def setup_personalities(self):
        """Define personality traits and their effects"""
        
        self.personality_traits = {
            'friendly': {
                'modifiers': {'friendliness': +0.3, 'patience': +0.2, 'helpfulness': +0.3},
                'dialogue_prefix': ['Hello there!', 'Good to see you!', 'Welcome!'],
                'topics': ['weather', 'family', 'celebration']
            },
            
            'grumpy': {
                'modifiers': {'friendliness': -0.2, 'patience': -0.3, 'helpfulness': -0.2},
                'dialogue_prefix': ['What do you want?', 'Make it quick.', 'Ugh, another visitor.'],
                'topics': ['complaints', 'work', 'money']
            },
            
            'mysterious': {
                'modifiers': {'friendliness': 0, 'patience': +0.1, 'helpfulness': -0.1},
                'dialogue_prefix': ['The stars align...', 'I sense something about you...', 'Curious timing.'],
                'topics': ['fate', 'dreams', 'secrets']
            },
            
            'wise': {
                'modifiers': {'friendliness': +0.1, 'patience': +0.4, 'helpfulness': +0.2},
                'dialogue_prefix': ['Ah, a seeker of wisdom.', 'I have seen much in my years.', 'Listen closely.'],
                'topics': ['history', 'advice', 'philosophy']
            },
            
            'greedy': {
                'modifiers': {'friendliness': -0.1, 'patience': -0.1, 'helpfulness': -0.3},
                'dialogue_prefix': ['Got any coin?', 'Nothing is free.', 'What\'s in it for me?'],
                'topics': ['prices', 'treasure', 'deals']
            },
            
            'curious': {
                'modifiers': {'friendliness': +0.2, 'patience': +0.3, 'helpfulness': +0.1},
                'dialogue_prefix': ['Oh! A visitor!', 'Tell me everything!', 'How fascinating!'],
                'topics': ['questions', 'stories', 'news']
            },
            
            'proud': {
                'modifiers': {'friendliness': -0.1, 'patience': -0.2, 'helpfulness': -0.1},
                'dialogue_prefix': ['You speak to me?', 'I am quite important here.', 'Show some respect.'],
                'topics': ['achievements', 'status', 'honor']
            },
            
            'cowardly': {
                'modifiers': {'friendliness': +0.1, 'patience': -0.2, 'helpfulness': -0.2},
                'dialogue_prefix': ['Please don\'t hurt me!', 'I\'m just a simple...', 'Nothing to see here!'],
                'topics': ['safety', 'escape', 'fear']
            }
        }
        
        # Generate combinations
        self.personality_combinations = []
        for i in range(3):  # 3 traits per NPC
            self.personality_combinations.append(
                random.sample(list(self.personality_traits.keys()), 3)
            )
    
    def setup_dialogue_templates(self):
        """Setup dialogue templates for various situations"""
        
        self.dialogue_templates = {
            'greeting': {
                'first_meeting': [
                    "Hello there, stranger! I don't think we've met.",
                    "Greetings, traveler! What brings you to {location}?",
                    "Ah, a new face! Welcome to {location}.",
                    "Well met! I am {name}.",
                    "Hello! Can I help you with something?"
                ],
                
                'friendly': [
                    "{name} the {role}! Good to see you again!",
                    "Welcome back, friend!",
                    "Ah, it's you! How have you been?",
                    "Good to see your face again!",
                    "Hello there, always a pleasure!"
                ],
                
                'neutral': [
                    "Oh, it's you again.",
                    "Back so soon?",
                    "Hello.",
                    "You're here.",
                    "What is it now?"
                ],
                
                'unfriendly': [
                    "You again. Great.",
                    "I don't have time for this.",
                    "What do you want?",
                    "Leave me alone.",
                    "Not you again."
                ],
                
                'hostile': [
                    "I should kill you where you stand.",
                    "You have no business here.",
                    "Get out of my sight.",
                    "You're not welcome here.",
                    "I'll give you one chance to leave."
                ]
            },
            
            'farewell': {
                'friendly': [
                    "Safe travels, friend!",
                    "Come back anytime!",
                    "Take care out there!",
                    "Until next time!",
                    "Farewell, and good luck!"
                ],
                
                'neutral': [
                    "Goodbye.",
                    "See you around.",
                    "Farewell.",
                    "Take care.",
                    "Later."
                ],
                
                'unfriendly': [
                    "Finally.",
                    "Good riddance.",
                    "Don't come back.",
                    "Leave already.",
                    "About time."
                ]
            },
            
            'rumors': [
                "I heard that {rumor} in {location}.",
                "They say {rumor}.",
                "Word is that {rumor}.",
                "A traveler told me {rumor}.",
                "Everyone's talking about {rumor}.",
                "I shouldn't say this, but {rumor}.",
                "If you're interested, {rumor}."
            ],
            
            'gossip': [
                "Did you hear about {npc1} and {npc2}? Apparently {gossip}.",
                "Between us, {npc} is {gossip}.",
                "I probably shouldn't say, but {gossip}.",
                "You didn't hear this from me, but {gossip}.",
                "The whole town knows that {gossip}."
            ],
            
            'services': {
                'merchant': [
                    "Take a look at my wares!",
                    "Best prices in town!",
                    "I've got exactly what you need.",
                    "Buy something, please!",
                    "Quality goods, fair prices!"
                ],
                
                'innkeeper': [
                    "Welcome to the {inn_name}!",
                    "Need a room for the night?",
                    "We've got the best ale in town!",
                    "Food and lodging, finest around!",
                    "Come in, come in! What'll it be?"
                ],
                
                'blacksmith': [
                    "Need a weapon? Armor?",
                    "I can fix that for you.",
                    "Quality craftsmanship, I promise.",
                    "This steel is the best you'll find.",
                    "What can I forge for you?"
                ],
                
                'priest': [
                    "The Light welcomes you.",
                    "Need healing or blessing?",
                    "How can I serve you today?",
                    "The gods watch over us all.",
                    "Come, seek solace here."
                ],
                
                'trainer': [
                    "Looking to improve your skills?",
                    "I can teach you a thing or two.",
                    "Training is the path to mastery.",
                    "Ready to learn?",
                    "I'll make you stronger, for a price."
                ]
            },
            
            'refusal': [
                "I can't help you with that.",
                "Not interested.",
                "Sorry, I'm busy.",
                "Ask someone else.",
                "That's not something I do.",
                "No. Just no.",
                "Maybe another time.",
                "I don't know anything about that."
            ],
            
            'thanks': [
                "Thank you! I appreciate it.",
                "You're too kind!",
                "Thanks, friend!",
                "I owe you one.",
                "Much obliged!",
                "You have my gratitude."
            ],
            
            'insult': [
                "You're not very bright, are you?",
                "Is that the best you can do?",
                "What a fool.",
                "You must be joking.",
                "Are you serious?",
                "That's the dumbest thing I've heard."
            ],
            
            'combat': {
                'start': [
                    "You'll regret this!",
                    "Time to die!",
                    "I'll teach you a lesson!",
                    "Have at you!",
                    "You asked for this!"
                ],
                
                'hit': [
                    "Take that!",
                    "How do you like that?!",
                    "Not so tough now, are you?",
                    "Ha! Got you!",
                    "Feel that?"
                ],
                
                'miss': [
                    "Missed me!",
                    "Can't hit what you can't see!",
                    "Too slow!",
                    "Is that all you've got?",
                    "Ha! Over here!"
                ],
                
                'low_hp': [
                    "This isn't over!",
                    "I can still fight!",
                    "You'll pay for that!",
                    "Just a scratch!",
                    "I've had worse!"
                ],
                
                'defeated': [
                    "I yield! I yield!",
                    "Mercy! Please!",
                    "You win...",
                    "How... how did you...",
                    "I... I failed..."
                ]
            }
        }
    
    def setup_relationship_thresholds(self):
        """Setup thresholds for relationship levels"""
        
        self.relationship_thresholds = {
            RelationshipLevel.HOSTILE: -50,
            RelationshipLevel.UNFRIENDLY: -10,
            RelationshipLevel.NEUTRAL: 0,
            RelationshipLevel.FRIENDLY: 25,
            RelationshipLevel.TRUSTING: 50,
            RelationshipLevel.ALLY: 80,
            RelationshipLevel.LOVER: 95,
            RelationshipLevel.FAMILY: 100
        }
        
        self.relationship_actions = {
            'greet': 1,
            'help': 5,
            'gift_small': 3,
            'gift_medium': 8,
            'gift_large': 15,
            'quest_complete': 20,
            'save_life': 50,
            'insult': -5,
            'threaten': -10,
            'steal': -30,
            'attack': -50,
            'kill_friend': -100
        }
    
    def setup_schedule_templates(self):
        """Setup daily schedules for different NPC roles"""
        
        self.schedule_templates = {
            'villager': {
                6: {'activity': 'wake_up', 'location': 'home'},
                7: {'activity': 'breakfast', 'location': 'home'},
                8: {'activity': 'work', 'location': 'fields'},
                12: {'activity': 'lunch', 'location': 'home'},
                13: {'activity': 'work', 'location': 'fields'},
                17: {'activity': 'return_home', 'location': 'home'},
                18: {'activity': 'dinner', 'location': 'home'},
                19: {'activity': 'socialize', 'location': 'tavern'},
                21: {'activity': 'home', 'location': 'home'},
                22: {'activity': 'sleep', 'location': 'home'}
            },
            
            'merchant': {
                7: {'activity': 'wake_up', 'location': 'home'},
                8: {'activity': 'open_shop', 'location': 'shop'},
                12: {'activity': 'lunch', 'location': 'shop'},
                13: {'activity': 'work', 'location': 'shop'},
                18: {'activity': 'close_shop', 'location': 'shop'},
                19: {'activity': 'dinner', 'location': 'tavern'},
                21: {'activity': 'home', 'location': 'home'},
                22: {'activity': 'sleep', 'location': 'home'}
            },
            
            'guard': {
                6: {'activity': 'wake_up', 'location': 'barracks'},
                7: {'activity': 'breakfast', 'location': 'barracks'},
                8: {'activity': 'patrol', 'location': 'walls'},
                12: {'activity': 'lunch', 'location': 'barracks'},
                13: {'activity': 'patrol', 'location': 'gates'},
                20: {'activity': 'dinner', 'location': 'barracks'},
                21: {'activity': 'socialize', 'location': 'tavern'},
                23: {'activity': 'sleep', 'location': 'barracks'}
            },
            
            'innkeeper': {
                5: {'activity': 'wake_up', 'location': 'inn'},
                6: {'activity': 'prepare', 'location': 'inn'},
                7: {'activity': 'serve_breakfast', 'location': 'inn'},
                12: {'activity': 'serve_lunch', 'location': 'inn'},
                18: {'activity': 'serve_dinner', 'location': 'inn'},
                22: {'activity': 'clean', 'location': 'inn'},
                23: {'activity': 'sleep', 'location': 'inn'}
            },
            
            'priest': {
                5: {'activity': 'prayer', 'location': 'temple'},
                6: {'activity': 'prepare', 'location': 'temple'},
                8: {'activity': 'morning_service', 'location': 'temple'},
                12: {'activity': 'lunch', 'location': 'temple'},
                13: {'activity': 'counsel', 'location': 'temple'},
                17: {'activity': 'evening_service', 'location': 'temple'},
                19: {'activity': 'dinner', 'location': 'temple'},
                20: {'activity': 'study', 'location': 'temple'},
                22: {'activity': 'sleep', 'location': 'temple'}
            },
            
            'thief': {
                10: {'activity': 'wake_up', 'location': 'hideout'},
                11: {'activity': 'plan', 'location': 'hideout'},
                13: {'activity': 'scout', 'location': 'market'},
                17: {'activity': 'steal', 'location': 'rich_houses'},
                21: {'activity': 'fence_goods', 'location': 'underworld'},
                23: {'activity': 'hideout', 'location': 'hideout'},
                1: {'activity': 'sleep', 'location': 'hideout'}
            }
        }
    
    def setup_trade_tables(self):
        """Setup trade prices and items for different merchant types"""
        
        self.trade_tables = {
            'general': {
                'buys': ['junk', 'common_goods', 'produce'],
                'sells': [
                    {'name': 'Bread', 'price': 5, 'type': 'food'},
                    {'name': 'Torch', 'price': 2, 'type': 'tool'},
                    {'name': 'Rope', 'price': 10, 'type': 'tool'},
                    {'name': 'Backpack', 'price': 25, 'type': 'container'},
                    {'name': 'Waterskin', 'price': 5, 'type': 'container'}
                ]
            },
            
            'weapons': {
                'buys': ['weapons', 'scrap_metal'],
                'sells': [
                    {'name': 'Dagger', 'price': 20, 'type': 'weapon', 'damage': 4},
                    {'name': 'Short Sword', 'price': 50, 'type': 'weapon', 'damage': 6},
                    {'name': 'Long Sword', 'price': 100, 'type': 'weapon', 'damage': 8},
                    {'name': 'Bow', 'price': 75, 'type': 'weapon', 'damage': 5},
                    {'name': 'Arrows (20)', 'price': 10, 'type': 'ammo'}
                ]
            },
            
            'armor': {
                'buys': ['armor', 'leather', 'metal'],
                'sells': [
                    {'name': 'Leather Armor', 'price': 50, 'type': 'armor', 'defense': 3},
                    {'name': 'Chain Mail', 'price': 150, 'type': 'armor', 'defense': 5},
                    {'name': 'Plate Armor', 'price': 300, 'type': 'armor', 'defense': 8},
                    {'name': 'Shield', 'price': 40, 'type': 'armor', 'defense': 2},
                    {'name': 'Helmet', 'price': 30, 'type': 'armor', 'defense': 1}
                ]
            },
            
            'magic': {
                'buys': ['magic_items', 'rare_components'],
                'sells': [
                    {'name': 'Health Potion', 'price': 30, 'type': 'potion', 'effect': 'heal 30'},
                    {'name': 'Mana Potion', 'price': 25, 'type': 'potion', 'effect': 'restore 20 mana'},
                    {'name': 'Scroll of Fire', 'price': 100, 'type': 'scroll', 'spell': 'fireball'},
                    {'name': 'Magic Ring', 'price': 200, 'type': 'jewelry', 'effect': '+1 defense'},
                    {'name': 'Enchanted Gem', 'price': 150, 'type': 'component'}
                ]
            },
            
            'food': {
                'buys': ['food', 'ingredients'],
                'sells': [
                    {'name': 'Bread', 'price': 3, 'type': 'food', 'heal': 5},
                    {'name': 'Cheese', 'price': 5, 'type': 'food', 'heal': 8},
                    {'name': 'Apple', 'price': 2, 'type': 'food', 'heal': 3},
                    {'name': 'Cooked Meat', 'price': 8, 'type': 'food', 'heal': 12},
                    {'name': 'Ale', 'price': 4, 'type': 'drink'}
                ]
            }
        }
    
    def generate_npc(self, role: NPCRole, location: str, race: str = None) -> Dict:
        """
        Generate a new NPC with specified role and location
        """
        
        # Get template for role
        template = self.npc_templates.get(role, self.npc_templates[NPCRole.VILLAGER])
        
        # Select race if not specified
        if not race:
            race = random.choice(['human', 'elf', 'dwarf', 'halfling'])
        
        # Generate basic info
        npc = {
            'id': self.generate_npc_id(),
            'role': role,
            'race': race,
            'name': self.generate_name(race, role),
            'title': self.generate_title(role),
            'location': location,
            'status': NPCStatus.AVAILABLE,
            'created_time': datetime.now(),
            'last_interaction': None
        }
        
        # Generate stats
        npc.update({
            'health': random.randint(*template['health_range']),
            'max_health': random.randint(*template['health_range']),
            'gold': random.randint(*template['gold_range']),
            'inventory': self.generate_inventory(role, template['inventory_size']),
            'combat_skill': random.randint(*template['combat_skill'])
        })
        
        # Generate personality
        npc['personality'] = self.generate_personality()
        
        # Generate schedule
        npc['schedule'] = self.generate_schedule(template['schedule_type'])
        
        # Generate dialogue data
        npc['dialogue'] = {
            'greetings': [],
            'rumors': [],
            'gossip': [],
            'known_facts': []
        }
        
        # Role-specific data
        if role == NPCRole.MERCHANT:
            npc['trade_table'] = random.choice(['general', 'weapons', 'armor', 'magic', 'food'])
            npc['trade_multiplier'] = template.get('trade_multiplier', 1.0)
        
        elif role == NPCRole.QUEST_GIVER:
            npc['quest_count'] = random.randint(*template['quests_available'])
            npc['quests_given'] = []
        
        elif role == NPCRole.TRAINER:
            npc['trainable_skills'] = self.generate_trainable_skills()
        
        # Generate secrets
        npc['secrets'] = self.generate_secrets()
        
        # Generate relationships with other NPCs
        npc['relationships'] = {}
        
        return npc
    
    def generate_name(self, race: str, role: NPCRole) -> str:
        """Generate a name for an NPC"""
        
        first = random.choice(self.name_data['first_names'].get(race, ['Unknown']))
        last = random.choice(self.name_data['last_names'].get(race, ['Unknown']))
        
        # 30% chance to add a nickname
        if random.random() < 0.3:
            nickname = random.choice(self.name_data['nicknames'])
            return f"{first} {nickname} {last}"
        
        return f"{first} {last}"
    
    def generate_title(self, role: NPCRole) -> str:
        """Generate a title for an NPC"""
        
        role_str = role.value
        if role_str in self.name_data['titles']:
            return random.choice(self.name_data['titles'][role_str])
        
        return ""
    
    def generate_npc_id(self) -> str:
        """Generate unique NPC ID"""
        import hashlib
        import time
        
        unique = f"npc_{time.time()}_{random.random()}"
        return hashlib.md5(unique.encode()).hexdigest()[:8]
    
    def generate_personality(self) -> Dict:
        """Generate personality traits for NPC"""
        
        # Select 2-3 traits
        num_traits = random.randint(2, 3)
        traits = random.sample(list(self.personality_traits.keys()), num_traits)
        
        personality = {
            'traits': traits,
            'modifiers': {}
        }
        
        # Combine modifiers
        for trait in traits:
            trait_data = self.personality_traits[trait]
            for key, value in trait_data['modifiers'].items():
                if key not in personality['modifiers']:
                    personality['modifiers'][key] = 0
                personality['modifiers'][key] += value
        
        # Generate dialogue prefixes
        personality['dialogue_prefix'] = []
        for trait in traits[:2]:  # Use first 2 traits for prefixes
            personality['dialogue_prefix'].extend(
                self.personality_traits[trait]['dialogue_prefix']
            )
        
        # Generate topics of interest
        personality['topics'] = set()
        for trait in traits:
            personality['topics'].update(self.personality_traits[trait]['topics'])
        
        return personality
    
    def generate_inventory(self, role: NPCRole, size_range: Tuple[int, int]) -> List[Dict]:
        """Generate initial inventory for NPC"""
        
        size = random.randint(*size_range)
        inventory = []
        
        # Add role-specific items
        if role == NPCRole.MERCHANT:
            # Will be populated from trade table
            pass
        elif role == NPCRole.GUARD:
            inventory.append({'name': 'Sword', 'type': 'weapon'})
            inventory.append({'name': 'Uniform', 'type': 'clothing'})
        elif role == NPCRole.BLACKSMITH:
            inventory.append({'name': 'Hammer', 'type': 'tool'})
            inventory.append({'name': 'Tongs', 'type': 'tool'})
        elif role == NPCRole.INNKEEPER:
            inventory.append({'name': 'Ale', 'type': 'drink', 'count': random.randint(5, 20)})
            inventory.append({'name': 'Food', 'type': 'food', 'count': random.randint(10, 30)})
        
        return inventory
    
    def generate_schedule(self, schedule_type: str) -> Dict:
        """Generate daily schedule for NPC"""
        
        base_schedule = self.schedule_templates.get(schedule_type, self.schedule_templates['villager'])
        
        # Add randomness to times (±1 hour)
        schedule = {}
        for hour, activity in base_schedule.items():
            # Add variation
            if random.random() < 0.3:
                hour += random.randint(-1, 1)
                hour = max(0, min(23, hour))
            
            schedule[hour] = activity
        
        return schedule
    
    def generate_secrets(self) -> List[Dict]:
        """Generate secrets for NPC"""
        
        secrets = []
        num_secrets = random.randint(0, 2)
        
        secret_templates = [
            {'type': 'fear', 'content': 'afraid of the dark', 'revealed': False},
            {'type': 'desire', 'content': 'wants to leave this town', 'revealed': False},
            {'type': 'past', 'content': 'was once a criminal', 'revealed': False},
            {'type': 'relationship', 'content': 'secretly loves someone', 'revealed': False},
            {'type': 'knowledge', 'content': 'knows where treasure is', 'revealed': False},
            {'type': 'debt', 'content': 'owes money to someone', 'revealed': False},
            {'type': 'crime', 'content': 'committed a crime', 'revealed': False},
            {'type': 'identity', 'content': 'is not who they seem', 'revealed': False}
        ]
        
        for _ in range(num_secrets):
            secret = random.choice(secret_templates).copy()
            secret['id'] = len(secrets)
            secrets.append(secret)
        
        return secrets
    
    def generate_trainable_skills(self) -> List[Dict]:
        """Generate skills that NPC can train"""
        
        skills = [
            {'name': 'Swordsmanship', 'cost': 100, 'req_level': 1, 'improves': 'strength'},
            {'name': 'Archery', 'cost': 100, 'req_level': 1, 'improves': 'dexterity'},
            {'name': 'Shield Defense', 'cost': 150, 'req_level': 2, 'improves': 'defense'},
            {'name': 'Critical Strike', 'cost': 200, 'req_level': 3, 'improves': 'critical_chance'},
            {'name': 'Dodge', 'cost': 150, 'req_level': 2, 'improves': 'evasion'},
            {'name': 'Meditation', 'cost': 120, 'req_level': 1, 'improves': 'mana_regen'}
        ]
        
        return random.sample(skills, k=random.randint(1, 3))
    
    def add_npc_to_world(self, npc: Dict):
        """Add NPC to world tracking"""
        
        npc_id = npc['id']
        self.npcs[npc_id] = npc
        self.npcs_by_location[npc['location']].append(npc_id)
        self.npcs_by_role[npc['role'].value].append(npc_id)
        
        # Initialize relationships
        self.relationships[npc_id] = {
            'player': {
                'value': 0,
                'level': RelationshipLevel.NEUTRAL,
                'history': []
            }
        }
    
    def get_npcs_at_location(self, location: str) -> List[Dict]:
        """Get all NPCs at a specific location"""
        
        npc_ids = self.npcs_by_location.get(location, [])
        return [self.npcs[npc_id] for npc_id in npc_ids if npc_id in self.npcs]
    
    def get_npc_by_name(self, name: str, location: str = None) -> Optional[Dict]:
        """Find NPC by name (partial match)"""
        
        candidates = []
        
        if location:
            npc_ids = self.npcs_by_location.get(location, [])
            candidates = [self.npcs[npc_id] for npc_id in npc_ids]
        else:
            candidates = list(self.npcs.values())
        
        # Try exact match first
        for npc in candidates:
            if npc['name'].lower() == name.lower():
                return npc
        
        # Then partial match
        for npc in candidates:
            if name.lower() in npc['name'].lower():
                return npc
        
        return None
    
    def interact(self, npc_id: str, player_action: str, context: Dict) -> str:
        """
        Main interaction function with NPC
        """
        
        if npc_id not in self.npcs:
            return "That person isn't here."
        
        npc = self.npcs[npc_id]
        
        # Check if NPC is available
        if npc['status'] != NPCStatus.AVAILABLE:
            return self.get_unavailable_message(npc)
        
        # Update last interaction
        npc['last_interaction'] = datetime.now()
        
        # Get relationship level
        rel_data = self.relationships[npc_id]['player']
        rel_level = rel_data['level']
        
        # Get personality modifiers
        personality = npc['personality']
        
        # Generate response based on action
        if 'greet' in player_action.lower() or 'hello' in player_action.lower():
            response = self.greet(npc, rel_level, personality)
        elif 'bye' in player_action.lower() or 'farewell' in player_action.lower():
            response = self.farewell(npc, rel_level, personality)
        elif 'trade' in player_action.lower() or 'buy' in player_action.lower() or 'sell' in player_action.lower():
            response = self.trade(npc, rel_level, personality)
        elif 'quest' in player_action.lower() or 'task' in player_action.lower():
            response = self.quest_interaction(npc, rel_level, personality)
        elif 'gossip' in player_action.lower() or 'rumor' in player_action.lower():
            response = self.gossip(npc, rel_level, personality)
        elif 'help' in player_action.lower():
            response = self.help_request(npc, rel_level, personality)
        elif 'gift' in player_action.lower() or 'give' in player_action.lower():
            response = self.give_gift(npc, player_action, rel_level, personality)
        elif 'train' in player_action.lower():
            response = self.train(npc, rel_level, personality)
        elif 'service' in player_action.lower():
            response = self.service(npc, rel_level, personality)
        else:
            # Default conversation
            response = self.converse(npc, player_action, rel_level, personality)
        
        # Log conversation
        self.log_conversation(npc_id, player_action, response)
        
        return response
    
    def greet(self, npc: Dict, rel_level: RelationshipLevel, personality: Dict) -> str:
        """Generate greeting based on relationship"""
        
        # Get appropriate greeting template
        if rel_level == RelationshipLevel.HOSTILE:
            template = random.choice(self.dialogue_templates['greeting']['hostile'])
        elif rel_level in [RelationshipLevel.UNFRIENDLY, RelationshipLevel.NEUTRAL]:
            if random.random() < 0.3:
                template = random.choice(self.dialogue_templates['greeting']['first_meeting'])
            else:
                template = random.choice(self.dialogue_templates['greeting']['neutral'])
        elif rel_level in [RelationshipLevel.FRIENDLY, RelationshipLevel.TRUSTING]:
            template = random.choice(self.dialogue_templates['greeting']['friendly'])
        else:
            template = random.choice(self.dialogue_templates['greeting']['friendly'])
        
        # Format template
        greeting = template.format(
            name=npc['name'],
            role=npc['role'].value,
            location=npc['location']
        )
        
        # Add personality prefix
        if personality['dialogue_prefix'] and random.random() < 0.5:
            prefix = random.choice(personality['dialogue_prefix'])
            greeting = f"{prefix} {greeting}"
        
        # Update relationship (slightly)
        self.modify_relationship(npc['id'], 'greet')
        
        return greeting
    
    def farewell(self, npc: Dict, rel_level: RelationshipLevel, personality: Dict) -> str:
        """Generate farewell based on relationship"""
        
        if rel_level in [RelationshipLevel.HOSTILE, RelationshipLevel.UNFRIENDLY]:
            template = random.choice(self.dialogue_templates['farewell']['unfriendly'])
        elif rel_level == RelationshipLevel.NEUTRAL:
            template = random.choice(self.dialogue_templates['farewell']['neutral'])
        else:
            template = random.choice(self.dialogue_templates['farewell']['friendly'])
        
        return template
    
    def trade(self, npc: Dict, rel_level: RelationshipLevel, personality: Dict) -> str:
        """Handle trading interaction"""
        
        if npc['role'] not in [NPCRole.MERCHANT, NPCRole.BLACKSMITH, NPCRole.INNKEEPER]:
            return "I don't have anything to trade."
        
        # Check if NPC has trade table
        if 'trade_table' not in npc:
            # Generate random trade goods
            npc['trade_table'] = random.choice(['general', 'weapons', 'armor', 'food'])
        
        # Get trade items
        trade_data = self.trade_tables[npc['trade_table']]
        
        # Apply relationship multiplier to prices
        price_mult = self.get_price_multiplier(rel_level)
        
        # Build trade menu
        menu = f"\n{Colors.INFO}🛒 {npc['name']}'s Wares:{Colors.RESET}\n"
        menu += TextFormatter.divider('-', 40) + "\n"
        
        for i, item in enumerate(trade_data['sells'][:6], 1):  # Show first 6 items
            price = int(item['price'] * price_mult * npc.get('trade_multiplier', 1.0))
            menu += f"{i}. {item['name']} - {price} gold\n"
        
        menu += f"\n{TextFormatter.info('Type "buy [number]" to purchase.')}"
        menu += f"\n{TextFormatter.info('Your gold:')} {self.player['gold']}"
        
        return menu
    
    def quest_interaction(self, npc: Dict, rel_level: RelationshipLevel, personality: Dict) -> str:
        """Handle quest-related interaction"""
        
        # Check if NPC is quest giver
        if npc['role'] != NPCRole.QUEST_GIVER:
            return "I don't have any quests for you."
        
        # This will be handled by quest system
        return "QUEST_INTERACTION"  # Flag for quest system
    
    def gossip(self, npc: Dict, rel_level: RelationshipLevel, personality: Dict) -> str:
        """Share gossip and rumors"""
        
        # Check if NPC will share gossip
        gossip_chance = 0.5
        
        # Adjust based on relationship
        if rel_level in [RelationshipLevel.FRIENDLY, RelationshipLevel.TRUSTING]:
            gossip_chance += 0.3
        elif rel_level in [RelationshipLevel.UNFRIENDLY, RelationshipLevel.HOSTILE]:
            gossip_chance -= 0.3
        
        if random.random() > gossip_chance:
            return "I don't have any gossip for you."
        
        # Generate random gossip
        gossip_type = random.choice(['rumor', 'gossip'])
        
        if gossip_type == 'rumor':
            rumor = self.generate_rumor(npc['location'])
            template = random.choice(self.dialogue_templates['rumors'])
            return template.format(rumor=rumor, location=npc['location'])
        else:
            gossip = self.generate_gossip()
            npcs = list(self.npcs.values())
            if len(npcs) > 1:
                npc1 = random.choice(npcs)['name']
                npc2 = random.choice([n for n in npcs if n['name'] != npc1])['name']
                template = random.choice(self.dialogue_templates['gossip'])
                return template.format(npc1=npc1, npc2=npc2, npc=npc1, gossip=gossip)
            else:
                return "The town is quiet lately. Nothing interesting happening."
    
    def help_request(self, npc: Dict, rel_level: RelationshipLevel, personality: Dict) -> str:
        """Handle help requests"""
        
        # Calculate helpfulness
        helpfulness = 0.5
        helpfulness += personality['modifiers'].get('helpfulness', 0)
        
        if rel_level in [RelationshipLevel.FRIENDLY, RelationshipLevel.TRUSTING]:
            helpfulness += 0.2
        elif rel_level in [RelationshipLevel.UNFRIENDLY, RelationshipLevel.HOSTILE]:
            helpfulness -= 0.3
        
        if random.random() < helpfulness:
            # Generate random help response
            help_options = [
                f"You could try asking {random.choice(list(self.npcs.values()))['name']}.",
                f"I think there's {random.choice(['trouble', 'a problem', 'something strange'])} at the {random.choice(['forest', 'caves', 'old ruins'])}.",
                f"If you're looking for work, check the guild.",
                f"The {random.choice(['tavern', 'market', 'temple'])} might have what you need."
            ]
            return random.choice(help_options)
        else:
            return random.choice(self.dialogue_templates['refusal'])
    
    def give_gift(self, npc: Dict, action: str, rel_level: RelationshipLevel, personality: Dict) -> str:
        """Handle gift giving"""
        
        # Extract gift name from action
        gift_name = action.replace('give', '').replace('gift', '').strip()
        
        # Check if player has the gift
        if gift_name not in self.player.get('inventory', []):
            return f"You don't have {gift_name} to give."
        
        # Determine gift value
        gift_value = self.get_gift_value(gift_name)
        
        # Calculate relationship change
        rel_change = self.relationship_actions.get('gift_small', 3)
        if gift_value > 50:
            rel_change = self.relationship_actions.get('gift_large', 15)
        elif gift_value > 20:
            rel_change = self.relationship_actions.get('gift_medium', 8)
        
        # Apply personality modifiers
        if 'greedy' in npc['personality']['traits']:
            rel_change *= 1.5
        elif 'proud' in npc['personality']['traits']:
            rel_change *= 0.7
        
        # Update relationship
        self.modify_relationship(npc['id'], 'gift', rel_change)
        
        # Remove from inventory
        self.player['inventory'].remove(gift_name)
        
        # Generate response
        responses = [
            f"Thank you! This {gift_name} is wonderful!",
            f"A gift? For me? Thank you!",
            f"How thoughtful! I'll treasure this {gift_name}.",
            f"You shouldn't have! Thank you so much!"
        ]
        
        return random.choice(responses)
    
    def train(self, npc: Dict, rel_level: RelationshipLevel, personality: Dict) -> str:
        """Handle training interaction"""
        
        if npc['role'] != NPCRole.TRAINER:
            return "I can't train you."
        
        if 'trainable_skills' not in npc:
            return "I have nothing to teach you right now."
        
        # Build training menu
        menu = f"\n{Colors.INFO}⚔️ {npc['name']}'s Training:{Colors.RESET}\n"
        menu += TextFormatter.divider('-', 40) + "\n"
        
        for i, skill in enumerate(npc['trainable_skills'], 1):
            menu += f"{i}. {skill['name']} - {skill['cost']} gold"
            if skill.get('req_level', 1) > self.player['level']:
                menu += f" (Requires level {skill['req_level']})"
            menu += "\n"
        
        menu += f"\n{TextFormatter.info('Type "train [number]" to learn.')}"
        menu += f"\n{TextFormatter.info('Your gold:')} {self.player['gold']}"
        
        return menu
    
    def service(self, npc: Dict, rel_level: RelationshipLevel, personality: Dict) -> str:
        """Handle service requests (healing, repairs, etc.)"""
        
        if 'services' not in npc:
            return "I don't offer any services."
        
        services = npc.get('services', [])
        
        if npc['role'] == NPCRole.PRIEST and 'heal' in services:
            # Offer healing
            heal_cost = 10 * (self.player['max_health'] - self.player['health'])
            if heal_cost == 0:
                return "You're already at full health!"
            
            return f"I can heal you for {heal_cost} gold. Type 'heal' to accept."
        
        elif npc['role'] == NPCRole.BLACKSMITH and 'repair' in services:
            return "I can repair your equipment. Show me what needs fixing."
        
        elif npc['role'] == NPCRole.INNKEEPER and 'lodging' in services:
            return f"A room for the night is 10 gold. Type 'rest' to stay."
        
        return "I don't have any services for you right now."
    
    def converse(self, npc: Dict, player_input: str, rel_level: RelationshipLevel, personality: Dict) -> str:
        """Handle general conversation"""
        
        # Check if player input matches any known topics
        topics = personality.get('topics', set())
        
        for topic in topics:
            if topic.lower() in player_input.lower():
                return self.topic_response(npc, topic, rel_level)
        
        # Check for emotional content
        if any(word in player_input.lower() for word in ['sad', 'happy', 'angry', 'scared']):
            return self.empathetic_response(npc, player_input, rel_level)
        
        # Random conversation
        conversation_pool = [
            "Interesting weather we're having.",
            f"I've lived in {npc['location']} my whole life.",
            "Do you travel often?",
            "Be careful out there. It's dangerous.",
            "Have you tried the food at the tavern?",
            "I hope the monsters stay away from here.",
            "The guards do their best, but it's never enough.",
            "I miss the old days. Simpler times."
        ]
        
        return random.choice(conversation_pool)
    
    def topic_response(self, npc: Dict, topic: str, rel_level: RelationshipLevel) -> str:
        """Generate response about specific topic"""
        
        topic_responses = {
            'weather': [
                "The weather's been strange lately.",
                "I hope it doesn't rain. Bad for business.",
                "Perfect day for a journey!",
                "Storm coming, I can feel it in my bones."
            ],
            'family': [
                "My family's been here for generations.",
                "I have a cousin in the next town over.",
                "Family is everything, you know?",
                "I don't see my children enough."
            ],
            'work': [
                "Work never ends around here.",
                "It's honest work. Pays the bills.",
                "I love what I do, most days.",
                "Could always use more customers."
            ],
            'money': [
                "Gold makes the world go round.",
                "Never enough coin, is there?",
                "I'm saving up for something special.",
                "Money comes and goes."
            ],
            'adventure': [
                "I used to adventure when I was young.",
                "The old ruins are supposed to be haunted.",
                "I hear there's treasure in the caves.",
                "Adventuring is a young person's game."
            ],
            'danger': [
                "The roads aren't safe anymore.",
                "Something's changed in the forest.",
                "I lock my doors at night now.",
                "We need more guards."
            ]
        }
        
        responses = topic_responses.get(topic, ["Interesting topic."])
        return random.choice(responses)
    
    def empathetic_response(self, npc: Dict, player_input: str, rel_level: RelationshipLevel) -> str:
        """Generate empathetic response to player's emotional state"""
        
        if 'sad' in player_input.lower():
            responses = [
                "I'm sorry to hear that. Things will get better.",
                "Everyone has bad days. Tomorrow's another chance.",
                "Would you like to talk about it?",
                "I understand. Life can be hard."
            ]
        elif 'happy' in player_input.lower():
            responses = [
                "That's wonderful! I'm happy for you!",
                "Good news is always welcome!",
                "Wonderful! Tell me more!",
                "Happiness is worth celebrating!"
            ]
        elif 'angry' in player_input.lower():
            responses = [
                "Take a deep breath. Anger solves nothing.",
                "I understand being upset, but stay calm.",
                "Maybe you should rest and think things through.",
                "Violence isn't the answer."
            ]
        elif 'scared' in player_input.lower():
            responses = [
                "Fear keeps us alive. It's natural.",
                "You're brave for facing your fears.",
                "Is there anything I can do to help?",
                "Stay strong. You'll get through this."
            ]
        else:
            return "I hope you're doing well."
        
        return random.choice(responses)
    
    def get_unavailable_message(self, npc: Dict) -> str:
        """Get message when NPC is unavailable"""
        
        status_messages = {
            NPCStatus.SLEEPING: f"{npc['name']} is asleep right now.",
            NPCStatus.BUSY: f"{npc['name']} is busy at the moment.",
            NPCStatus.WORKING: f"{npc['name']} is working and can't talk.",
            NPCStatus.TRAVELING: f"{npc['name']} isn't here right now."
        }
        
        return status_messages.get(npc['status'], f"{npc['name']} is unavailable.")
    
    def modify_relationship(self, npc_id: str, action: str, custom_value: int = None):
        """Modify relationship with NPC"""
        
        if npc_id not in self.relationships:
            return
        
        rel_data = self.relationships[npc_id]['player']
        
        # Get base value change
        if custom_value is not None:
            change = custom_value
        else:
            change = self.relationship_actions.get(action, 0)
        
        # Apply personality modifiers
        npc = self.npcs.get(npc_id)
        if npc:
            personality = npc['personality']
            if 'friendly' in personality['traits'] and change > 0:
                change = int(change * 1.2)
            elif 'grumpy' in personality['traits'] and change > 0:
                change = int(change * 0.8)
        
        # Update value
        rel_data['value'] += change
        rel_data['value'] = max(-100, min(100, rel_data['value']))
        
        # Update level
        rel_data['level'] = self.get_relationship_level(rel_data['value'])
        
        # Log change
        rel_data['history'].append({
            'action': action,
            'change': change,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_relationship_level(self, value: int) -> RelationshipLevel:
        """Get relationship level based on value"""
        
        for level, threshold in sorted(self.relationship_thresholds.items(), 
                                      key=lambda x: x[1], reverse=True):
            if value >= threshold:
                return level
        
        return RelationshipLevel.HOSTILE
    
    def get_price_multiplier(self, rel_level: RelationshipLevel) -> float:
        """Get price multiplier based on relationship"""
        
        multipliers = {
            RelationshipLevel.HOSTILE: 1.5,
            RelationshipLevel.UNFRIENDLY: 1.3,
            RelationshipLevel.NEUTRAL: 1.0,
            RelationshipLevel.FRIENDLY: 0.9,
            RelationshipLevel.TRUSTING: 0.8,
            RelationshipLevel.ALLY: 0.7,
            RelationshipLevel.LOVER: 0.6,
            RelationshipLevel.FAMILY: 0.5
        }
        
        return multipliers.get(rel_level, 1.0)
    
    def get_gift_value(self, gift_name: str) -> int:
        """Calculate approximate value of gift"""
        
        # Simple value estimation
        if any(word in gift_name.lower() for word in ['gold', 'gem', 'jewel']):
            return 100
        elif any(word in gift_name.lower() for word in ['silver', 'magic', 'rare']):
            return 50
        elif any(word in gift_name.lower() for word in ['weapon', 'armor', 'potion']):
            return 25
        else:
            return 10
    
    def generate_rumor(self, location: str) -> str:
        """Generate a random rumor"""
        
        rumors = [
            f"a {random.choice(['dragon', 'troll', 'giant'])} was spotted near {location}",
            f"treasure was found in the {random.choice(['caves', 'ruins', 'forest'])}",
            f"the {random.choice(['king', 'queen', 'mayor'])} is offering a reward",
            f"strange lights appear at night in {location}",
            f"someone went missing in {location} last week",
            f"a famous hero is visiting the area",
            f"bandits are gathering in the {random.choice(['hills', 'mountains', 'forest'])}",
            f"an ancient artifact was discovered nearby"
        ]
        
        return random.choice(rumors)
    
    def generate_gossip(self) -> str:
        """Generate random gossip"""
        
        gossip = [
            "is secretly in love with",
            "owes money to",
            "had a big argument with",
            "is planning to leave town with",
            "stole something from",
            "has been sneaking around with",
            "is related to",
            "made a bet with"
        ]
        
        return random.choice(gossip)
    
    def log_conversation(self, npc_id: str, player_input: str, response: str):
        """Log conversation for history"""
        
        self.conversation_history[npc_id].append({
            'timestamp': datetime.now().isoformat(),
            'player_input': player_input,
            'npc_response': response
        })
        
        # Keep only last 20 conversations
        if len(self.conversation_history[npc_id]) > 20:
            self.conversation_history[npc_id] = self.conversation_history[npc_id][-20:]
    
    def update_schedules(self, current_hour: int):
        """Update NPC schedules based on time"""
        
        for npc_id, npc in self.npcs.items():
            if npc['status'] == NPCStatus.DEAD:
                continue
            
            # Get current activity based on hour
            schedule = npc.get('schedule', {})
            activity = schedule.get(current_hour, {'activity': 'idle', 'location': npc['location']})
            
            # Update status based on activity
            if 'sleep' in activity['activity']:
                npc['status'] = NPCStatus.SLEEPING
            elif 'work' in activity['activity'] or 'serve' in activity['activity']:
                npc['status'] = NPCStatus.WORKING
            elif 'patrol' in activity['activity'] or 'travel' in activity['activity']:
                npc['status'] = NPCStatus.TRAVELING
            else:
                npc['status'] = NPCStatus.AVAILABLE
            
            # Update location if changed
            if activity['location'] != npc['location']:
                # Remove from old location
                if npc_id in self.npcs_by_location[npc['location']]:
                    self.npcs_by_location[npc['location']].remove(npc_id)
                
                # Add to new location
                npc['location'] = activity['location']
                self.npcs_by_location[npc['location']].append(npc_id)
    
    def get_npc_info(self, npc_id: str) -> str:
        """Get detailed information about an NPC"""
        
        if npc_id not in self.npcs:
            return "NPC not found."
        
        npc = self.npcs[npc_id]
        rel_data = self.relationships[npc_id]['player']
        
        info = f"\n{Colors.INFO}👤 NPC Information{Colors.RESET}\n"
        info += TextFormatter.divider() + "\n"
        
        # Basic info
        info += f"Name: {Colors.BOLD}{npc['name']}{Colors.RESET}"
        if npc.get('title'):
            info += f" {npc['title']}"
        info += f"\nRole: {npc['role'].value.title()}"
        info += f"\nRace: {npc['race'].title()}"
        info += f"\nLocation: {npc['location']}"
        info += f"\nStatus: {npc['status'].value.title()}"
        
        # Relationship
        info += f"\n\n{Colors.INFO}Relationship:{Colors.RESET}"
        info += f"\nLevel: {rel_data['level'].value.title()}"
        info += f"\nValue: {rel_data['value']}"
        
        # Personality
        info += f"\n\n{Colors.INFO}Personality:{Colors.RESET}"
        info += f"\nTraits: {', '.join(npc['personality']['traits'])}"
        
        # Services
        if npc.get('services'):
            info += f"\n\n{Colors.INFO}Services:{Colors.RESET}"
            info += f"\n{', '.join(npc['services'])}"
        
        # Health
        info += f"\n\n{Colors.INFO}Combat Stats:{Colors.RESET}"
        info += f"\nHealth: {npc['health']}/{npc['max_health']}"
        info += f"\nCombat Skill: {npc['combat_skill']}"
        
        return info
    
    def save_state(self) -> Dict:
        """Save NPC system state"""
        
        return {
            'npcs': self.npcs,
            'relationships': self.relationships,
            'conversation_history': self.conversation_history,
            'npcs_by_location': dict(self.npcs_by_location),
            'npcs_by_role': dict(self.npcs_by_role)
        }
    
    def load_state(self, state: Dict):
        """Load NPC system state"""
        
        self.npcs = state.get('npcs', {})
        self.relationships = state.get('relationships', defaultdict(dict))
        self.conversation_history = state.get('conversation_history', defaultdict(list))
        
        # Rebuild location index
        self.npcs_by_location = defaultdict(list)
        for npc_id, npc in self.npcs.items():
            self.npcs_by_location[npc['location']].append(npc_id)
        
        # Rebuild role index
        self.npcs_by_role = defaultdict(list)
        for npc_id, npc in self.npcs.items():
            self.npcs_by_role[npc['role'].value].append(npc_id)