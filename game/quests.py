"""
Quest system for AI Text Adventure Game
Handles quest generation, tracking, rewards, and progression
"""

import random
import json
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime
from collections import defaultdict

from .utils import TextFormatter, Colors

class QuestType(Enum):
    """Types of quests available"""
    KILL = "kill"           # Defeat specific enemies
    COLLECT = "collect"     # Gather items
    DELIVERY = "delivery"   # Deliver items to NPCs
    EXPLORE = "explore"     # Discover locations
    ESCORT = "escort"       # Protect NPCs
    BOSS = "boss"           # Defeat boss enemies
    MYSTERY = "mystery"     # Solve puzzles/find clues
    CHAIN = "chain"         # Multi-part quests
    RANDOM = "random"       # Procedurally generated
    DAILY = "daily"         # Repeatable daily quests

class QuestDifficulty(Enum):
    """Quest difficulty levels"""
    TRIVIAL = "trivial"     # Very easy, low rewards
    EASY = "easy"           # Easy, suitable for beginners
    MEDIUM = "medium"       # Standard difficulty
    HARD = "hard"           # Challenging, good rewards
    EPIC = "epic"           # Very difficult, great rewards
    LEGENDARY = "legendary" # Extremely hard, best rewards

class QuestStatus(Enum):
    """Quest status states"""
    UNAVAILABLE = "unavailable"  # Not yet available
    AVAILABLE = "available"      # Can be accepted
    ACTIVE = "active"            # Currently in progress
    COMPLETED = "completed"      # Finished successfully
    FAILED = "failed"            # Failed to complete
    TURNED_IN = "turned_in"      # Rewards claimed

class QuestManager:
    """
    Main quest management system
    Handles quest creation, tracking, and rewards
    """
    
    def __init__(self, player: Dict, game_flags: Dict):
        self.player = player
        self.game_flags = game_flags
        
        # Quest storage
        self.available_quests = []      # Quests that can be accepted
        self.active_quests = []          # Quests in progress
        self.completed_quests = []       # Completed quests
        self.failed_quests = []           # Failed quests
        
        # Quest tracking
        self.quest_log = []               # History of quest events
        self.daily_quests_completed = 0   # Daily quests done today
        self.last_daily_reset = datetime.now().date()
        
        # Quest chains
        self.quest_chains = {}             # Multi-part quest sequences
        
        # Initialize quest templates
        self.setup_quest_templates()
        self.setup_quest_rewards()
        self.setup_quest_dialogue()
        self.setup_quest_generators()
        
    def setup_quest_templates(self):
        """Define all possible quest templates"""
        
        self.quest_templates = {
            # KILL quests
            'kill_basic': {
                'type': QuestType.KILL,
                'difficulty': QuestDifficulty.EASY,
                'name_template': "Threat in the {location}",
                'description_template': "{giver_name} needs you to eliminate {target_count} {target_name} that have been terrorizing the {location}.",
                'objectives': [
                    {'type': 'kill', 'target': '{target_name}', 'count': '{target_count}', 'current': 0}
                ],
                'reward_mult': 1.0,
                'time_limit': None,  # No time limit
                'repeatable': False,
                'tags': ['combat', 'monster_hunting']
            },
            
            'kill_boss': {
                'type': QuestType.BOSS,
                'difficulty': QuestDifficulty.HARD,
                'name_template': "The {boss_name} Menace",
                'description_template': "A powerful {boss_name} threatens the {location}. {giver_name} offers a great reward for its defeat.",
                'objectives': [
                    {'type': 'kill', 'target': '{boss_name}', 'count': 1, 'current': 0, 'boss': True}
                ],
                'reward_mult': 3.0,
                'time_limit': 7,  # 7 days
                'repeatable': False,
                'tags': ['combat', 'boss', 'challenge']
            },
            
            # COLLECT quests
            'collect_basic': {
                'type': QuestType.COLLECT,
                'difficulty': QuestDifficulty.EASY,
                'name_template': "Materials Needed",
                'description_template': "{giver_name} needs {item_count} {item_name} for {purpose}. Bring them to {giver_name} for a reward.",
                'objectives': [
                    {'type': 'collect', 'item': '{item_name}', 'count': '{item_count}', 'current': 0}
                ],
                'reward_mult': 1.2,
                'time_limit': None,
                'repeatable': True,
                'tags': ['gathering', 'crafting']
            },
            
            'collect_rare': {
                'type': QuestType.COLLECT,
                'difficulty': QuestDifficulty.HARD,
                'name_template': "Rare {item_name} Hunt",
                'description_template': "{giver_name} seeks the rare {item_name}. They're willing to pay handsomely for even one.",
                'objectives': [
                    {'type': 'collect', 'item': '{item_name}', 'count': 1, 'current': 0, 'rare': True}
                ],
                'reward_mult': 2.5,
                'time_limit': None,
                'repeatable': False,
                'tags': ['rare', 'treasure_hunt']
            },
            
            # DELIVERY quests
            'delivery_basic': {
                'type': QuestType.DELIVERY,
                'difficulty': QuestDifficulty.TRIVIAL,
                'name_template': "Package for {recipient}",
                'description_template': "{giver_name} needs you to deliver {item_name} to {recipient} in {target_location}.",
                'objectives': [
                    {'type': 'deliver', 'item': '{item_name}', 'target': '{recipient}', 'location': '{target_location}'}
                ],
                'reward_mult': 0.8,
                'time_limit': 3,  # 3 days
                'repeatable': True,
                'tags': ['travel', 'errand']
            },
            
            'delivery_urgent': {
                'type': QuestType.DELIVERY,
                'difficulty': QuestDifficulty.MEDIUM,
                'name_template': "Urgent Delivery",
                'description_template': "Time is critical! {giver_name} needs {item_name} delivered to {recipient} in {target_location} within {time_limit} days.",
                'objectives': [
                    {'type': 'deliver', 'item': '{item_name}', 'target': '{recipient}', 'location': '{target_location}', 'urgent': True}
                ],
                'reward_mult': 1.5,
                'time_limit': 1,  # 1 day
                'repeatable': True,
                'tags': ['urgent', 'time_critical']
            },
            
            # EXPLORE quests
            'explore_basic': {
                'type': QuestType.EXPLORE,
                'difficulty': QuestDifficulty.EASY,
                'name_template': "Scout the {location}",
                'description_template': "{giver_name} wants you to explore {location} and report back on what you find.",
                'objectives': [
                    {'type': 'explore', 'location': '{location}', 'discover': True}
                ],
                'reward_mult': 1.0,
                'time_limit': None,
                'repeatable': False,
                'tags': ['exploration', 'scouting']
            },
            
            'explore_dungeon': {
                'type': QuestType.EXPLORE,
                'difficulty': QuestDifficulty.HARD,
                'name_template': "Into the {dungeon_name}",
                'description_template': "The {dungeon_name} has claimed many lives. {giver_name} wants you to explore it and discover its secrets.",
                'objectives': [
                    {'type': 'explore', 'location': '{dungeon_name}', 'discover': True},
                    {'type': 'explore', 'location': '{dungeon_depth}', 'reach': True}
                ],
                'reward_mult': 2.0,
                'time_limit': None,
                'repeatable': False,
                'tags': ['dungeon', 'dangerous']
            },
            
            # ESCORT quests
            'escort_basic': {
                'type': QuestType.ESCORT,
                'difficulty': QuestDifficulty.MEDIUM,
                'name_template': "Escort {npc_name}",
                'description_template': "{npc_name} needs to reach {destination} safely. Protect them from dangers along the way.",
                'objectives': [
                    {'type': 'escort', 'target': '{npc_name}', 'destination': '{destination}', 'protect': True}
                ],
                'reward_mult': 1.8,
                'time_limit': 5,
                'repeatable': False,
                'tags': ['protection', 'travel']
            },
            
            # MYSTERY quests
            'mystery_basic': {
                'type': QuestType.MYSTERY,
                'difficulty': QuestDifficulty.MEDIUM,
                'name_template': "The {mystery_name} Mystery",
                'description_template': "Something strange is happening in {location}. {giver_name} wants you to investigate and solve the mystery.",
                'objectives': [
                    {'type': 'investigate', 'location': '{location}', 'clues': 3},
                    {'type': 'solve', 'mystery': '{mystery_name}'}
                ],
                'reward_mult': 2.2,
                'time_limit': None,
                'repeatable': False,
                'tags': ['investigation', 'puzzle']
            },
            
            # CHAIN quests (multi-part)
            'chain_start': {
                'type': QuestType.CHAIN,
                'difficulty': QuestDifficulty.EASY,
                'name_template': "A Humble Beginning",
                'description_template': "{giver_name} has a small task for you. Complete it to prove yourself.",
                'next_quest': 'chain_part1',
                'objectives': [
                    {'type': 'simple_task'}
                ],
                'reward_mult': 1.0,
                'time_limit': None,
                'repeatable': False,
                'tags': ['chain', 'prologue']
            },
            
            # DAILY quests
            'daily_kill': {
                'type': QuestType.DAILY,
                'difficulty': QuestDifficulty.MEDIUM,
                'name_template': "Daily: Cull the {enemy_type}",
                'description_template': "The {location} needs help thinning the {enemy_type} population. Kill {kill_count} today.",
                'objectives': [
                    {'type': 'kill', 'target': '{enemy_type}', 'count': '{kill_count}', 'current': 0}
                ],
                'reward_mult': 1.5,
                'time_limit': 1,  # Must complete today
                'repeatable': True,
                'daily': True,
                'tags': ['daily', 'combat']
            },
            
            'daily_collect': {
                'type': QuestType.DAILY,
                'difficulty': QuestDifficulty.EASY,
                'name_template': "Daily: Gather {item_name}",
                'description_template': "The market needs {item_count} {item_name} today. Collect them for a reward.",
                'objectives': [
                    {'type': 'collect', 'item': '{item_name}', 'count': '{item_count}', 'current': 0}
                ],
                'reward_mult': 1.2,
                'time_limit': 1,
                'repeatable': True,
                'daily': True,
                'tags': ['daily', 'gathering']
            }
        }
    
    def setup_quest_rewards(self):
        """Define reward templates for quests"""
        
        self.reward_templates = {
            'gold': {
                'trivial': (10, 30),
                'easy': (30, 80),
                'medium': (80, 200),
                'hard': (200, 500),
                'epic': (500, 1000),
                'legendary': (1000, 3000)
            },
            
            'xp': {
                'trivial': (20, 40),
                'easy': (40, 100),
                'medium': (100, 250),
                'hard': (250, 600),
                'epic': (600, 1500),
                'legendary': (1500, 3000)
            },
            
            'items': {
                'trivial': ['health_potion', 'bread', 'torch'],
                'easy': ['health_potion', 'mana_potion', 'leather_armor'],
                'medium': ['steel_sword', 'chainmail', 'magic_scroll'],
                'hard': ['enchanted_weapon', 'rare_gem', 'magic_ring'],
                'epic': ['legendary_armor', 'ancient_artifact', 'dragon_scale'],
                'legendary': ['mythical_weapon', 'crown_of_kings', 'philosophers_stone']
            },
            
            'reputation': {
                'trivial': 5,
                'easy': 10,
                'medium': 20,
                'hard': 35,
                'epic': 50,
                'legendary': 100
            },
            
            'special': {
                'trivial': [],
                'easy': ['skill_point'],
                'medium': ['attribute_point', 'new_ability'],
                'hard': ['title', 'unique_item'],
                'epic': ['companion', 'base_upgrade'],
                'legendary': ['immortality_fragment', 'divine_blessing']
            }
        }
    
    def setup_quest_dialogue(self):
        """Setup quest-related dialogue templates"""
        
        self.quest_dialogue = {
            'offer': {
                'greeting': [
                    "Ah, {player_name}! I have a task for someone of your talents.",
                    "Just the person I wanted to see! I have a quest for you.",
                    "You look capable. Care to earn some gold?",
                    "I've been waiting for someone like you. I need help with something.",
                    "Fortune favors the bold! And I have a proposition for you."
                ],
                
                'details': [
                    "Here's what needs to be done: {quest_description}",
                    "The task is simple: {quest_description}",
                    "I need you to {quest_description}",
                    "This is what I'm asking: {quest_description}"
                ],
                
                'reward': [
                    "Complete this, and I'll reward you with {reward_description}.",
                    "Your payment will be {reward_description}.",
                    "I can offer {reward_description} for your trouble.",
                    "The reward is {reward_description}. Worth your while, I'd say."
                ],
                
                'accept': [
                    "Excellent! I knew I could count on you.",
                    "Wonderful! The details are in your journal.",
                    "Great! Be careful out there.",
                    "Perfect! Report back when you're done."
                ],
                
                'decline': [
                    "I understand. Come back if you change your mind.",
                    "No problem. I'll find someone else.",
                    "Perhaps another time then.",
                    "Suit yourself. The offer stands if you reconsider."
                ]
            },
            
            'progress': {
                'check': [
                    "How goes the {quest_name}? Any progress?",
                    "Have you made headway on that task I gave you?",
                    "Any news about {quest_objective}?",
                    "I've been wondering about your progress. How goes it?"
                ],
                
                'partial': [
                    "Good work so far! Keep it up.",
                    "You're making progress. Don't give up now!",
                    "Almost there. I have faith in you.",
                    "You're getting closer. The reward will be worth it."
                ],
                
                'encouragement': [
                    "Don't get discouraged. These things take time.",
                    "I know you can do this. You're the right person for the job.",
                    "Stay focused. The reward awaits!",
                    "Remember why you started. You've got this!"
                ],
                
                'warning': [
                    "Time is running out! Please hurry.",
                    "If you can't complete this, I'll have to find someone else.",
                    "Others have tried and failed. Don't be like them.",
                    "This is your last chance. Make it count!"
                ]
            },
            
            'completion': {
                'success': [
                    "You did it! I knew you would!",
                    "Incredible work! Here's your reward.",
                    "I never doubted you for a moment. Well done!",
                    "Amazing! You've earned every piece of this reward."
                ],
                
                'praise': [
                    "You're even more capable than you look!",
                    "The bards will sing of your deeds!",
                    "You've done what many thought impossible!",
                    "Truly impressive. I'm glad I chose you."
                ],
                
                'extra': [
                    "And here's a little extra for going above and beyond.",
                    "Take this as well. It belonged to someone special.",
                    "I've told others about your deeds. You'll find more work.",
                    "Consider this a bonus. You've earned it."
                ],
                
                'repeat': [
                    "Back so soon? Ready for another task?",
                    "Excellent work last time. I have something else for you.",
                    "You proved yourself before. Care to try something harder?"
                ]
            },
            
            'failure': {
                'too_late': [
                    "You're too late. I had to find someone else.",
                    "The opportunity has passed. Maybe next time.",
                    "I waited as long as I could. Sorry.",
                    "Time ran out. I can't accept this now."
                ],
                
                'incomplete': [
                    "This isn't what I asked for. I can't pay for this.",
                    "You didn't complete the task. No reward.",
                    "I'm disappointed. This won't do.",
                    "Maybe questing isn't for you. Try something easier."
                ],
                
                'forgive': [
                    "It happens. At least you tried.",
                    "Don't be discouraged. Failure is part of learning.",
                    "The important thing is that you're still alive.",
                    "There will be other opportunities."
                ]
            }
        }
    
    def setup_quest_generators(self):
        """Setup procedural quest generation components"""
        
        self.quest_components = {
            'locations': [
                'Dark Forest', 'Crystal Caves', 'Abandoned Mine', 'Ancient Ruins',
                'Dragon\'s Peak', 'Whispering Woods', 'Sunken Temple', 'Frozen Wastes',
                'Burning Sands', 'Thunder Plateau', 'Misty Valley', 'Goblin Warrens',
                'Orc Camp', 'Bandit Hideout', 'Haunted Cemetery', 'Wizard\'s Tower'
            ],
            
            'enemies': [
                ('Goblins', 3, 8), ('Wolves', 2, 6), ('Bandits', 3, 5),
                ('Orcs', 4, 7), ('Skeletons', 3, 6), ('Spiders', 2, 5),
                ('Cultists', 3, 4), ('Trolls', 5, 8), ('Dark Elves', 4, 6),
                ('Elementals', 5, 7), ('Demons', 6, 9), ('Dragons', 8, 12)
            ],
            
            'bosses': [
                ('Troll King', 10), ('Dragon Lord', 15), ('Lich', 12),
                ('Demon Prince', 14), ('Giant Spider Queen', 8), ('Orc Warlord', 9),
                ('Ancient Treant', 11), ('Sea Serpent', 13), ('Griffon', 7)
            ],
            
            'items': [
                ('Healing Herbs', 5, 15), ('Magic Crystals', 3, 8), ('Ancient Coins', 10, 30),
                ('Dragon Scales', 1, 3), ('Fairy Dust', 2, 6), ('Troll Blood', 2, 4),
                ('Phoenix Feathers', 1, 2), ('Mermaid Tears', 3, 7), ('Griffon Eggs', 1, 2)
            ],
            
            'rare_items': [
                ('Amulet of Kings', 1), ('Crystal of Eternity', 1), ('Heart of the Forest', 1),
                ('Eye of the Dragon', 1), ('Staff of Ages', 1), ('Crown of Shadows', 1),
                ('Orb of Prophecy', 1), ('Blade of Legends', 1), ('Tome of Secrets', 1)
            ],
            
            'npcs': [
                'Elder Marcus', 'Merchant Greta', 'Captain Vane', 'Wizard Orin',
                'Priestess Luna', 'Blacksmith Thorin', 'Hunter William', 'Mage Celeste',
                'Bard Melody', 'Guard Commander Rex', 'Thief Shadow', 'Healer Sarah'
            ],
            
            'recipients': [
                'the Mayor', 'the Guild Master', 'the Village Elder', 'the King\'s Courier',
                'the Temple Priest', 'the Academy Dean', 'the General', 'the Ambassador'
            ],
            
            'purposes': [
                'an important ritual', 'crafting a magical item', 'feeding the village',
                'a celebration feast', 'research', 'healing the sick', 'fortifying defenses'
            ],
            
            'mysteries': [
                'Vanishing Villagers', 'Haunted Lighthouse', 'Missing Heirloom',
                'Strange Noises at Night', 'The Cursed Painting', 'Whispers in the Walls',
                'The Phantom Thief', 'The Alchemist\'s Secret', 'The Forgotten Ritual'
            ]
        }
    
    def generate_quest(self, giver_name: str, location: str, 
                      difficulty: QuestDifficulty = QuestDifficulty.MEDIUM,
                      quest_type: Optional[QuestType] = None) -> Dict:
        """
        Procedurally generate a new quest
        """
        
        # Select quest type if not specified
        if not quest_type:
            quest_type = random.choice([
                QuestType.KILL, QuestType.COLLECT, QuestType.DELIVERY,
                QuestType.EXPLORE, QuestType.MYSTERY
            ])
        
        # Get template based on type and difficulty
        template = self.select_template(quest_type, difficulty)
        
        # Generate quest components
        components = self.generate_quest_components(quest_type, location)
        
        # Build quest data
        quest = {
            'id': self.generate_quest_id(),
            'type': quest_type,
            'difficulty': difficulty,
            'giver': giver_name,
            'location': location,
            'name': self.format_template(template['name_template'], components),
            'description': self.format_template(template['description_template'], components),
            'objectives': self.generate_objectives(template['objectives'], components),
            'rewards': self.generate_rewards(difficulty, quest_type, components),
            'time_limit': template.get('time_limit'),
            'repeatable': template.get('repeatable', False),
            'tags': template.get('tags', []),
            'status': QuestStatus.AVAILABLE,
            'accepted_time': None,
            'completed_time': None,
            'progress': {},
            'story_flags': self.generate_story_flags(components)
        }
        
        # Add special flags
        if template.get('daily'):
            quest['daily'] = True
            quest['daily_reset'] = datetime.now().date()
        
        if template.get('next_quest'):
            quest['next_quest'] = template['next_quest']
            quest['chain_position'] = 1
        
        return quest
    
    def select_template(self, quest_type: QuestType, difficulty: QuestDifficulty) -> Dict:
        """Select appropriate template based on type and difficulty"""
        
        # Filter templates by type
        candidates = [
            t for t in self.quest_templates.values()
            if t['type'] == quest_type and t['difficulty'] == difficulty
        ]
        
        if candidates:
            return random.choice(candidates)
        
        # Fallback to basic template
        for t in self.quest_templates.values():
            if t['type'] == quest_type:
                return t
        
        # Ultimate fallback
        return self.quest_templates['kill_basic']
    
    def generate_quest_components(self, quest_type: QuestType, location: str) -> Dict:
        """Generate random components for quest"""
        
        components = {
            'location': location,
            'giver_name': 'Quest Giver'  # Will be replaced
        }
        
        if quest_type in [QuestType.KILL, QuestType.BOSS]:
            if quest_type == QuestType.BOSS:
                boss = random.choice(self.quest_components['bosses'])
                components['boss_name'] = boss[0]
                components['target_name'] = boss[0]
                components['target_count'] = 1
                components['boss_level'] = boss[1]
            else:
                enemy = random.choice(self.quest_components['enemies'])
                components['target_name'] = enemy[0]
                components['target_count'] = random.randint(enemy[1], enemy[2])
        
        elif quest_type in [QuestType.COLLECT, QuestType.DELIVERY]:
            if random.random() < 0.3:  # 30% chance for rare items
                rare = random.choice(self.quest_components['rare_items'])
                components['item_name'] = rare[0]
                components['item_count'] = rare[1]
                components['rare'] = True
            else:
                item = random.choice(self.quest_components['items'])
                components['item_name'] = item[0]
                components['item_count'] = random.randint(item[1], item[2])
            
            components['purpose'] = random.choice(self.quest_components['purposes'])
            components['recipient'] = random.choice(self.quest_components['recipients'])
            components['target_location'] = random.choice(self.quest_components['locations'])
        
        elif quest_type == QuestType.EXPLORE:
            components['dungeon_name'] = random.choice(self.quest_components['locations'])
            components['dungeon_depth'] = f"Level {random.randint(2, 5)}"
        
        elif quest_type == QuestType.ESCORT:
            components['npc_name'] = random.choice(self.quest_components['npcs'])
            components['destination'] = random.choice(self.quest_components['locations'])
        
        elif quest_type == QuestType.MYSTERY:
            components['mystery_name'] = random.choice(self.quest_components['mysteries'])
            components['clue_count'] = random.randint(2, 5)
        
        return components
    
    def generate_objectives(self, objective_templates: List[Dict], components: Dict) -> List[Dict]:
        """Generate quest objectives from templates"""
        
        objectives = []
        
        for template in objective_templates:
            objective = template.copy()
            
            # Format strings with components
            for key, value in objective.items():
                if isinstance(value, str) and '{' in value:
                    objective[key] = self.format_template(value, components)
            
            # Add tracking fields
            if objective['type'] == 'kill':
                objective['current'] = 0
            elif objective['type'] == 'collect':
                objective['current'] = 0
            elif objective['type'] == 'explore':
                objective['discovered'] = False
            elif objective['type'] == 'deliver':
                objective['delivered'] = False
            elif objective['type'] == 'escort':
                objective['completed'] = False
                objective['npc_health'] = 100
            elif objective['type'] == 'investigate':
                objective['clues_found'] = 0
                objective['clues'] = []
            
            objectives.append(objective)
        
        return objectives
    
    def generate_rewards(self, difficulty: QuestDifficulty, quest_type: QuestType, 
                        components: Dict) -> Dict:
        """Generate quest rewards based on difficulty"""
        
        diff_str = difficulty.value
        
        # Gold reward
        gold_range = self.reward_templates['gold'][diff_str]
        gold = random.randint(gold_range[0], gold_range[1])
        
        # XP reward
        xp_range = self.reward_templates['xp'][diff_str]
        xp = random.randint(xp_range[0], xp_range[1])
        
        # Item rewards
        num_items = random.randint(0, 2) if difficulty != QuestDifficulty.TRIVIAL else 0
        items = []
        
        for _ in range(num_items):
            item_pool = self.reward_templates['items'][diff_str]
            items.append(random.choice(item_pool))
        
        # Special rewards for higher difficulties
        special = []
        if difficulty.value in ['hard', 'epic', 'legendary']:
            special_pool = self.reward_templates['special'][diff_str]
            if special_pool and random.random() < 0.3:
                special.append(random.choice(special_pool))
        
        # Reputation reward
        reputation = self.reward_templates['reputation'][diff_str]
        
        # Apply quest type multiplier
        type_multipliers = {
            QuestType.BOSS: 2.0,
            QuestType.CHAIN: 1.3,
            QuestType.MYSTERY: 1.2,
            QuestType.ESCORT: 1.1
        }
        
        mult = type_multipliers.get(quest_type, 1.0)
        gold = int(gold * mult)
        xp = int(xp * mult)
        
        return {
            'gold': gold,
            'xp': xp,
            'items': items,
            'special': special,
            'reputation': {
                'townsfolk': reputation if 'town' in str(quest_type) else reputation // 2,
                'guild': reputation if 'guild' in str(quest_type) else reputation // 2
            }
        }
    
    def generate_quest_id(self) -> str:
        """Generate unique quest ID"""
        import hashlib
        import time
        
        unique = f"{time.time()}{random.random()}"
        return hashlib.md5(unique.encode()).hexdigest()[:8]
    
    def generate_story_flags(self, components: Dict) -> Dict:
        """Generate story-related flags for quest"""
        
        return {
            'important_npc': random.choice([True, False]) if random.random() < 0.2 else False,
            'world_changing': random.choice([True, False]) if random.random() < 0.1 else False,
            'secret_outcome': random.choice([True, False]) if random.random() < 0.15 else False,
            'related_to_main': random.choice([True, False]) if random.random() < 0.05 else False
        }
    
    def format_template(self, template: str, components: Dict) -> str:
        """Format template string with components"""
        
        result = template
        for key, value in components.items():
            placeholder = '{' + key + '}'
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        return result
    
    def offer_quest(self, quest: Dict, npc_name: str) -> str:
        """Generate dialogue for offering a quest"""
        
        dialogue = []
        
        # Greeting
        dialogue.append(random.choice(self.quest_dialogue['offer']['greeting']).format(
            player_name=self.player['name']
        ))
        
        # Quest details
        dialogue.append(random.choice(self.quest_dialogue['offer']['details']).format(
            quest_description=quest['description']
        ))
        
        # Reward
        reward_desc = self.format_reward_description(quest['rewards'])
        dialogue.append(random.choice(self.quest_dialogue['offer']['reward']).format(
            reward_description=reward_desc
        ))
        
        # Store quest reference
        quest['giver'] = npc_name
        quest['status'] = QuestStatus.AVAILABLE
        
        if quest not in self.available_quests:
            self.available_quests.append(quest)
        
        return "\n\n".join(dialogue)
    
    def format_reward_description(self, rewards: Dict) -> str:
        """Format rewards into readable description"""
        
        parts = []
        
        if rewards['gold'] > 0:
            parts.append(f"{rewards['gold']} gold")
        
        if rewards['xp'] > 0:
            parts.append(f"{rewards['xp']} experience")
        
        if rewards['items']:
            items = ', '.join(rewards['items'])
            parts.append(f"the following items: {items}")
        
        if rewards['special']:
            special = ', '.join(rewards['special'])
            parts.append(f"special rewards: {special}")
        
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return f"{', '.join(parts[:-1])}, and {parts[-1]}"
    
    def accept_quest(self, quest_id: str) -> bool:
        """Accept a quest"""
        
        # Find quest in available list
        for quest in self.available_quests[:]:
            if quest['id'] == quest_id:
                # Move to active
                self.available_quests.remove(quest)
                quest['status'] = QuestStatus.ACTIVE
                quest['accepted_time'] = datetime.now()
                self.active_quests.append(quest)
                
                # Log acceptance
                self.log_quest_event('accept', quest)
                
                return True
        
        return False
    
    def update_quest_progress(self, event_type: str, target: str, count: int = 1) -> List[str]:
        """
        Update quest progress based on player actions
        Returns list of completion messages
        """
        
        completions = []
        
        for quest in self.active_quests[:]:
            progress_made = False
            
            for objective in quest['objectives']:
                if objective['type'] == event_type:
                    if event_type == 'kill' and objective['target'] == target:
                        objective['current'] += count
                        progress_made = True
                        
                        # Check if boss kill
                        if objective.get('boss', False) and objective['current'] >= objective['count']:
                            completions.append(self.complete_quest(quest['id']))
                    
                    elif event_type == 'collect' and objective['item'] == target:
                        # Check if player has the item
                        if target in self.player.get('inventory', []):
                            objective['current'] += count
                            progress_made = True
                            
                            if objective['current'] >= objective['count']:
                                completions.append(self.complete_quest(quest['id']))
                    
                    elif event_type == 'explore' and objective['location'] == target:
                        objective['discovered'] = True
                        progress_made = True
                        
                        # Check if all exploration objectives complete
                        if all(o.get('discovered', False) for o in quest['objectives'] if o['type'] == 'explore'):
                            completions.append(self.complete_quest(quest['id']))
            
            if progress_made:
                self.log_quest_event('progress', quest, {'target': target, 'count': count})
        
        return completions
    
    def complete_quest(self, quest_id: str) -> str:
        """Mark a quest as completed (waiting for turn-in)"""
        
        for quest in self.active_quests:
            if quest['id'] == quest_id:
                quest['status'] = QuestStatus.COMPLETED
                quest['completed_time'] = datetime.now()
                
                return f"\n{Colors.SUCCESS}✓ Quest Complete: {quest['name']}{Colors.RESET}\nReturn to {quest['giver']} for your reward!"
        
        return ""
    
    def turn_in_quest(self, quest_id: str, npc_name: str) -> str:
        """Turn in a completed quest and receive rewards"""
        
        for quest in self.active_quests[:]:
            if quest['id'] == quest_id and quest['giver'] == npc_name:
                if quest['status'] == QuestStatus.COMPLETED:
                    # Give rewards
                    reward_messages = self.give_rewards(quest['rewards'])
                    
                    # Move to completed
                    self.active_quests.remove(quest)
                    quest['status'] = QuestStatus.TURNED_IN
                    self.completed_quests.append(quest)
                    
                    # Generate completion dialogue
                    dialogue = self.generate_completion_dialogue(quest)
                    
                    # Log completion
                    self.log_quest_event('turn_in', quest)
                    
                    # Check for chain quests
                    if quest.get('next_quest'):
                        next_quest = self.generate_next_chain_quest(quest)
                        if next_quest:
                            self.available_quests.append(next_quest)
                            dialogue += f"\n\n{TextFormatter.info('A new quest is available from ' + npc_name + '!')}"
                    
                    return f"{dialogue}\n\n{reward_messages}"
                
                elif quest['status'] == QuestStatus.ACTIVE:
                    return f"You haven't completed {quest['name']} yet! Check your journal for objectives."
        
        return "I don't have any quest to turn in from you."
    
    def give_rewards(self, rewards: Dict) -> str:
        """Give quest rewards to player"""
        
        messages = [f"\n{Colors.SUCCESS}✨ Rewards Received:{Colors.RESET}"]
        
        # Gold
        if rewards['gold'] > 0:
            self.player['gold'] += rewards['gold']
            messages.append(f"  🪙 {rewards['gold']} gold")
        
        # XP
        if rewards['xp'] > 0:
            self.player['xp'] += rewards['xp']
            messages.append(f"  ✨ {rewards['xp']} experience")
        
        # Items
        if rewards['items']:
            for item in rewards['items']:
                self.player['inventory'].append(item)
                messages.append(f"  📦 {item}")
        
        # Reputation
        for faction, amount in rewards.get('reputation', {}).items():
            if amount > 0:
                if faction not in self.game_flags['reputation']:
                    self.game_flags['reputation'][faction] = 0
                self.game_flags['reputation'][faction] += amount
                messages.append(f"  💬 +{amount} reputation with {faction}")
        
        # Special rewards
        if rewards.get('special'):
            for special in rewards['special']:
                if special == 'skill_point':
                    self.player['skill_points'] = self.player.get('skill_points', 0) + 1
                    messages.append(f"  ⭐ Gained a skill point!")
                elif special == 'title':
                    new_title = self.generate_title()
                    self.player['titles'] = self.player.get('titles', []) + [new_title]
                    messages.append(f"  👑 Gained title: {new_title}")
                # Add more special reward types as needed
        
        # Check for level up
        if self.player['xp'] >= self.player.get('xp_to_next', 100):
            level_up = self.level_up()
            messages.append(level_up)
        
        return "\n".join(messages)
    
    def generate_completion_dialogue(self, quest: Dict) -> str:
        """Generate NPC dialogue for quest completion"""
        
        dialogue = []
        
        # Success message
        dialogue.append(random.choice(self.quest_dialogue['completion']['success']))
        
        # Praise
        if random.random() < 0.5:
            dialogue.append(random.choice(self.quest_dialogue['completion']['praise']))
        
        # Extra reward chance
        if random.random() < 0.2:  # 20% chance for extra
            extra = random.choice(self.quest_dialogue['completion']['extra'])
            
            # Give a small bonus
            bonus_gold = random.randint(5, 20)
            self.player['gold'] += bonus_gold
            extra += f" Here's an extra {bonus_gold} gold."
            
            dialogue.append(extra)
        
        return " ".join(dialogue)
    
    def generate_title(self) -> str:
        """Generate a random title for player"""
        
        titles = [
            'the Brave', 'the Wise', 'the Swift', 'the Strong',
            'Dragon Slayer', 'Shadow Walker', 'Light Bearer',
            'Hero of the Realm', 'Legend in the Making', 'Fate Breaker',
            'Storm Caller', 'Peace Keeper', 'Star Gazer'
        ]
        
        return random.choice(titles)
    
    def generate_next_chain_quest(self, previous_quest: Dict) -> Optional[Dict]:
        """Generate next quest in a chain"""
        
        if not previous_quest.get('next_quest'):
            return None
        
        # Find next template
        next_template = None
        for template in self.quest_templates.values():
            if template.get('name_template') == previous_quest['next_quest']:
                next_template = template
                break
        
        if not next_template:
            return None
        
        # Generate next quest
        components = self.generate_quest_components(
            next_template['type'],
            previous_quest.get('location', 'Unknown')
        )
        
        quest = {
            'id': self.generate_quest_id(),
            'type': next_template['type'],
            'difficulty': self.increase_difficulty(previous_quest['difficulty']),
            'giver': previous_quest['giver'],
            'location': previous_quest.get('location', 'Unknown'),
            'name': self.format_template(next_template['name_template'], components),
            'description': self.format_template(next_template['description_template'], components),
            'objectives': self.generate_objectives(next_template['objectives'], components),
            'rewards': self.generate_rewards(
                self.increase_difficulty(previous_quest['difficulty']),
                next_template['type'],
                components
            ),
            'time_limit': next_template.get('time_limit'),
            'repeatable': next_template.get('repeatable', False),
            'tags': next_template.get('tags', []),
            'status': QuestStatus.AVAILABLE,
            'previous_quest': previous_quest['id'],
            'chain_position': previous_quest.get('chain_position', 1) + 1
        }
        
        if next_template.get('next_quest'):
            quest['next_quest'] = next_template['next_quest']
        
        return quest
    
    def increase_difficulty(self, difficulty: QuestDifficulty) -> QuestDifficulty:
        """Increase difficulty for chain quests"""
        
        difficulties = [
            QuestDifficulty.TRIVIAL,
            QuestDifficulty.EASY,
            QuestDifficulty.MEDIUM,
            QuestDifficulty.HARD,
            QuestDifficulty.EPIC,
            QuestDifficulty.LEGENDARY
        ]
        
        try:
            current_idx = difficulties.index(difficulty)
            next_idx = min(current_idx + 1, len(difficulties) - 1)
            return difficulties[next_idx]
        except ValueError:
            return QuestDifficulty.MEDIUM
    
    def fail_quest(self, quest_id: str, reason: str = "timeout") -> Optional[str]:
        """Mark a quest as failed"""
        
        for quest in self.active_quests[:]:
            if quest['id'] == quest_id:
                self.active_quests.remove(quest)
                quest['status'] = QuestStatus.FAILED
                quest['failure_reason'] = reason
                self.failed_quests.append(quest)
                
                # Log failure
                self.log_quest_event('fail', quest, {'reason': reason})
                
                # Generate failure message
                if reason == "timeout":
                    return random.choice(self.quest_dialogue['failure']['too_late'])
                else:
                    return random.choice(self.quest_dialogue['failure']['incomplete'])
        
        return None
    
    def check_time_limits(self, days_passed: int):
        """Check all active quests for time limit expiry"""
        
        for quest in self.active_quests[:]:
            if quest.get('time_limit') and quest.get('accepted_time'):
                time_passed = (datetime.now() - quest['accepted_time']).days
                if time_passed > quest['time_limit']:
                    self.fail_quest(quest['id'], "timeout")
    
    def get_quests_by_giver(self, npc_name: str) -> List[Dict]:
        """Get all quests associated with an NPC"""
        
        quests = []
        
        # Available quests
        for quest in self.available_quests:
            if quest.get('giver') == npc_name:
                quests.append(quest)
        
        # Active quests (for progress checking)
        for quest in self.active_quests:
            if quest.get('giver') == npc_name:
                quests.append(quest)
        
        # Completed quests ready to turn in
        for quest in self.active_quests:
            if quest.get('giver') == npc_name and quest['status'] == QuestStatus.COMPLETED:
                quests.append(quest)
        
        return quests
    
    def get_quest_dialogue(self, npc_name: str) -> Optional[str]:
        """Get appropriate quest dialogue for an NPC"""
        
        quests = self.get_quests_by_giver(npc_name)
        
        if not quests:
            return None
        
        # Check for completed quests first
        for quest in quests:
            if quest['status'] == QuestStatus.COMPLETED:
                return f"You have completed '{quest['name']}'! Ready to claim your reward?"
        
        # Then check for active quests
        for quest in quests:
            if quest['status'] == QuestStatus.ACTIVE:
                progress = self.get_quest_progress_string(quest)
                return f"How goes '{quest['name']}'? {progress}"
        
        # Finally, offer available quests
        available = [q for q in quests if q['status'] == QuestStatus.AVAILABLE]
        if available:
            return self.offer_quest(available[0], npc_name)
        
        return None
    
    def get_quest_progress_string(self, quest: Dict) -> str:
        """Get formatted quest progress"""
        
        progress = []
        
        for objective in quest['objectives']:
            if objective['type'] == 'kill':
                progress.append(f"{objective['current']}/{objective['count']} {objective['target']} killed")
            elif objective['type'] == 'collect':
                progress.append(f"{objective['current']}/{objective['count']} {objective['item']} collected")
            elif objective['type'] == 'explore':
                status = "✓" if objective.get('discovered') else "✗"
                progress.append(f"{objective['location']} {status}")
            elif objective['type'] == 'deliver':
                status = "✓" if objective.get('delivered') else "✗"
                progress.append(f"Delivery to {objective['target']} {status}")
        
        return " | ".join(progress)
    
    def display_quests(self) -> str:
        """Display all active quests"""
        
        if not self.active_quests:
            return f"\n{TextFormatter.info('You have no active quests.')}\nVisit the guild or talk to NPCs to find work!"
        
        display = f"\n{TextFormatter.header('📜 ACTIVE QUESTS')}\n"
        display += TextFormatter.divider()
        
        for i, quest in enumerate(self.active_quests, 1):
            status_icon = "✓" if quest['status'] == QuestStatus.COMPLETED else "⚔️"
            display += f"\n{Colors.BOLD}{i}. {status_icon} {quest['name']}{Colors.RESET}\n"
            display += f"   {quest['description']}\n"
            display += f"   {TextFormatter.info('Progress:')} {self.get_quest_progress_string(quest)}\n"
            
            if quest.get('time_limit'):
                days_left = self.get_days_left(quest)
                if days_left is not None:
                    display += f"   {TextFormatter.warning(f'⏰ Time left: {days_left} days')}\n"
        
        return display
    
    def display_journal(self) -> str:
        """Display quest journal with history"""
        
        display = f"\n{TextFormatter.header('📔 QUEST JOURNAL')}\n"
        display += TextFormatter.divider()
        
        # Completed quests
        if self.completed_quests:
            display += f"\n{Colors.SUCCESS}✅ Completed Quests:{Colors.RESET}\n"
            for quest in self.completed_quests[-5:]:  # Last 5 completed
                display += f"  • {quest['name']}\n"
        
        # Failed quests
        if self.failed_quests:
            display += f"\n{Colors.ERROR}❌ Failed Quests:{Colors.RESET}\n"
            for quest in self.failed_quests[-3:]:  # Last 3 failed
                display += f"  • {quest['name']} - {quest.get('failure_reason', 'unknown')}\n"
        
        # Available quests
        if self.available_quests:
            display += f"\n{Colors.INFO}📋 Available Quests:{Colors.RESET}\n"
            for quest in self.available_quests[:3]:  # Show up to 3 available
                display += f"  • {quest['name']} (from {quest['giver']})\n"
        
        # Stats
        display += f"\n{TextFormatter.info('📊 Quest Statistics:')}\n"
        display += f"  Completed: {len(self.completed_quests)}\n"
        display += f"  Active: {len(self.active_quests)}\n"
        display += f"  Available: {len(self.available_quests)}\n"
        
        return display
    
    def get_days_left(self, quest: Dict) -> Optional[int]:
        """Get days remaining on time-limited quest"""
        
        if quest.get('time_limit') and quest.get('accepted_time'):
            time_passed = (datetime.now() - quest['accepted_time']).days
            return max(0, quest['time_limit'] - time_passed)
        
        return None
    
    def log_quest_event(self, event_type: str, quest: Dict, data: Dict = None):
        """Log quest event for history"""
        
        self.quest_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'quest_id': quest['id'],
            'quest_name': quest['name'],
            'data': data or {}
        })
        
        # Keep log manageable
        if len(self.quest_log) > 100:
            self.quest_log = self.quest_log[-100:]
    
    def level_up(self) -> str:
        """Process player level up (called from rewards)"""
        
        self.player['level'] += 1
        self.player['xp'] -= self.player.get('xp_to_next', 100)
        self.player['xp_to_next'] = int(self.player.get('xp_to_next', 100) * 1.5)
        
        # Increase stats
        self.player['max_health'] += 10
        self.player['health'] = self.player['max_health']
        self.player['strength'] += 2
        self.player['defense'] += 1
        
        return f"\n{Colors.INFO}🌟 LEVEL UP! You are now level {self.player['level']}!{Colors.RESET}"
    
    def get_state(self) -> Dict:
        """Get quest system state for saving"""
        
        return {
            'available_quests': self.available_quests,
            'active_quests': self.active_quests,
            'completed_quests': self.completed_quests,
            'failed_quests': self.failed_quests,
            'quest_log': self.quest_log[-50:],  # Last 50 events
            'daily_quests_completed': self.daily_quests_completed,
            'last_daily_reset': self.last_daily_reset.isoformat() if self.last_daily_reset else None
        }
    
    def load_state(self, state: Dict):
        """Load quest system state from save"""
        
        self.available_quests = state.get('available_quests', [])
        self.active_quests = state.get('active_quests', [])
        self.completed_quests = state.get('completed_quests', [])
        self.failed_quests = state.get('failed_quests', [])
        self.quest_log = state.get('quest_log', [])
        self.daily_quests_completed = state.get('daily_quests_completed', 0)
        
        if state.get('last_daily_reset'):
            self.last_daily_reset = datetime.fromisoformat(state['last_daily_reset'])