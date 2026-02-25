"""
AI Engine for Text Adventure Game
Handles natural language processing, response generation, and dynamic dialogue
"""

import re
import random
import json
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from difflib import SequenceMatcher
from datetime import datetime

from .utils import TextFormatter, Colors

class AIEngine:
    """
    Main AI engine that processes player input and generates intelligent responses
    Uses pattern matching, context awareness, and dynamic response generation
    """
    
    def __init__(self, player: Dict, game_flags: Dict):
        self.player = player
        self.game_flags = game_flags
        
        # Conversation memory
        self.memory = {
            'recent_topics': [],
            'known_facts': set(),
            'player_reputation': defaultdict(int),
            'npc_relationships': defaultdict(lambda: {'favor': 0, 'times_talked': 0}),
            'last_interaction': {},
            'emotional_state': 'neutral'
        }
        
        # Response patterns by category
        self.setup_patterns()
        
        # Knowledge base
        self.setup_knowledge_base()
        
        # Dynamic response templates
        self.setup_response_templates()
        
        # Personality profiles
        self.setup_personalities()
        
        # Quest-related dialogue
        self.setup_quest_dialogue()
        
        # Emotion responses
        self.setup_emotions()
        
    def setup_patterns(self):
        """Setup advanced pattern matching for command interpretation"""
        
        self.patterns = {
            # Greetings
            'greeting': {
                'patterns': [
                    r'hello', r'hi', r'hey', r'greetings', r'howdy',
                    r'good (morning|afternoon|evening)', r'what\'s up'
                ],
                'priority': 1
            },
            
            # Farewells
            'farewell': {
                'patterns': [
                    r'bye', r'goodbye', r'farewell', r'see you',
                    r'take care', r'until next time'
                ],
                'priority': 1
            },
            
            # Questions about self
            'about_self': {
                'patterns': [
                    r'who are you', r'what are you', r'tell me about yourself',
                    r'your name', r'what do you do'
                ],
                'priority': 2
            },
            
            # Questions about player
            'about_player': {
                'patterns': [
                    r'who am i', r'what am i', r'my purpose',
                    r'why am i here', r'what should i do'
                ],
                'priority': 2
            },
            
            # Help requests
            'help_request': {
                'patterns': [
                    r'help me', r'i need help', r'can you help',
                    r' assist ', r'guidance', r'advice'
                ],
                'priority': 2
            },
            
            # Quest-related
            'quest_related': {
                'patterns': [
                    r'quest', r'mission', r'task', r'job',
                    r'favor', r' errand', r'chore'
                ],
                'priority': 3
            },
            
            # Location inquiries
            'location_questions': {
                'patterns': [
                    r'where am i', r'what is this place', r'where are we',
                    r'describe (the|this) (area|place|location)',
                    r'what\'s around here'
                ],
                'priority': 2
            },
            
            # Time inquiries
            'time_questions': {
                'patterns': [
                    r'what time', r'what day', r'how long',
                    r'when is', r'what hour'
                ],
                'priority': 2
            },
            
            # Combat-related
            'combat_related': {
                'patterns': [
                    r'fight', r'battle', r'combat', r'enemy',
                    r'monster', r'danger', r'threat'
                ],
                'priority': 3
            },
            
            # Item-related
            'item_related': {
                'patterns': [
                    r'item', r'object', r'thing', r'loot',
                    r'treasure', r'equipment', r'weapon', r'armor'
                ],
                'priority': 2
            },
            
            # NPC-related
            'npc_related': {
                'patterns': [
                    r'npc', r'person', r'people', r'character',
                    r'villager', r'guard', r'merchant'
                ],
                'priority': 2
            },
            
            # Emotional expressions
            'emotion': {
                'patterns': [
                    r'happy', r'sad', r'angry', r'scared',
                    r'excited', r'tired', r'confused', r'grateful'
                ],
                'priority': 1
            },
            
            # Opinion requests
            'ask_opinion': {
                'patterns': [
                    r'what do you think', r'your opinion', r'do you think',
                    r'how do you feel', r'what\'s your take'
                ],
                'priority': 2
            },
            
            # Story/lore
            'ask_story': {
                'patterns': [
                    r'tell me a story', r'history', r'lore',
                    r'legend', r'tale', r'myth', r'rumor'
                ],
                'priority': 3
            },
            
            # Trading
            'trading': {
                'patterns': [
                    r'trade', r'buy', r'sell', r'price',
                    r'cost', r'how much', r'merchant'
                ],
                'priority': 3
            },
            
            # Jokes/humor
            'joke': {
                'patterns': [
                    r'joke', r'funny', r'make me laugh',
                    r'humor', r'comedy'
                ],
                'priority': 2
            },
            
            # Compliments
            'compliment': {
                'patterns': [
                    r'nice', r'great', r'amazing', r'wonderful',
                    r'you\'re (good|kind|helpful)', r'i like you'
                ],
                'priority': 2
            },
            
            # Insults
            'insult': {
                'patterns': [
                    r'stupid', r'dumb', r'idiot', r'fool',
                    r'you\'re (bad|terrible|awful)', r'i hate you'
                ],
                'priority': 2
            }
        }
        
        # Compile regex patterns
        for category, data in self.patterns.items():
            compiled = []
            for pattern in data['patterns']:
                try:
                    compiled.append(re.compile(pattern, re.IGNORECASE))
                except re.error:
                    continue
            self.patterns[category]['compiled'] = compiled
    
    def setup_knowledge_base(self):
        """Setup game world knowledge for AI responses"""
        
        self.knowledge_base = {
            'world_facts': {
                'age': 'ancient',
                'magic_level': 'high',
                'main_threat': 'darkness spreading from the east',
                'recent_events': [
                    'The old king passed away',
                    'Strange creatures have been seen in the forest',
                    'Trade routes have become dangerous',
                    'A mysterious comet appeared in the sky'
                ]
            },
            
            'locations': {
                'town_square': {
                    'facts': [
                        'Built over 500 years ago',
                        'Center of local trade and politics',
                        'Fountain said to grant wishes'
                    ],
                    'rumors': [
                        'Secret tunnels run beneath the square',
                        'The fountain water has healing properties',
                        'Merchants gather here from distant lands'
                    ]
                },
                'tavern': {
                    'facts': [
                        'Run by the cheerful innkeeper Greta',
                        'Famous for its honeyed mead',
                        'Gathering place for adventurers'
                    ],
                    'rumors': [
                        'Secret meetings happen in the back room',
                        'A treasure map is hidden under the bar',
                        'Ghost of a former patron haunts the cellar'
                    ]
                },
                'forest': {
                    'facts': [
                        'Ancient woodland older than the town',
                        'Home to many mystical creatures',
                        'Contains ruins of old civilization'
                    ],
                    'rumors': [
                        'A druid circle meets at the full moon',
                        'Talking animals live deep within',
                        'Portal to the feywild hidden somewhere'
                    ]
                }
            },
            
            'npcs': {
                'generic_knowledge': {
                    'traits': [
                        'People here are generally friendly',
                        'Most fear the increasing monster attacks',
                        'They respect brave adventurers'
                    ]
                }
            },
            
            'quest_knowledge': {
                'common_needs': [
                    'protection from monsters',
                    'rare ingredients',
                    'lost family heirlooms',
                    'information from distant lands',
                    'help with local disputes'
                ]
            }
        }
    
    def setup_response_templates(self):
        """Setup dynamic response templates for various situations"""
        
        self.response_templates = {
            'greeting': [
                "Hello there, {player_name}! How can I help you today?",
                "Greetings, traveler! What brings you to {location}?",
                "Well met, {player_name}! It's good to see a friendly face.",
                "Ah, a visitor! Welcome to {location}.",
                "Hey there! Looking for something specific?"
            ],
            
            'farewell': [
                "Safe travels, {player_name}! May your path be clear.",
                "Farewell! Come back anytime.",
                "Take care out there. It's dangerous these days.",
                "Until we meet again, adventurer!",
                "Goodbye! Remember to visit the tavern for a drink!"
            ],
            
            'about_self': [
                "I'm just a simple {npc_profession} in {location}. Nothing special about me.",
                "Me? I've lived here my whole life. Seen many adventurers come and go.",
                "I'm {npc_name}, the {npc_profession}. If you need {profession_service}, I'm your {npc_race}.",
                "Just another face in the crowd. But I know these parts well."
            ],
            
            'about_player': [
                "You're {player_name}, the {player_class}. I've heard tales of your kind.",
                "An adventurer seeking glory and gold, I presume?",
                "You look like someone who's seen their share of danger.",
                "A {player_class}? We don't get many of those around here."
            ],
            
            'help_request': {
                'friendly': [
                    "I'd be happy to help! What do you need?",
                    "Of course! What seems to be the trouble?",
                    "I'll do what I can. What's the matter?"
                ],
                'neutral': [
                    "I might be able to assist. What is it?",
                    "Depends on what you need. Tell me more.",
                    "I'm listening. What's your problem?"
                ],
                'grumpy': [
                    "What now? Make it quick.",
                    "I'm busy, but fine. What is it?",
                    "You adventurers are always needing something."
                ]
            },
            
            'quest_related': {
                'has_quest': [
                    "Actually, I do have a task for someone brave enough...",
                    "Now that you mention it, there IS something you could help with.",
                    "Funny you should ask. I need {quest_item} from {quest_location}.",
                    "Yes! I've been looking for someone to {quest_task}."
                ],
                'no_quest': [
                    "Sorry, no tasks at the moment. Check back later.",
                    "Nothing right now, but things change fast around here.",
                    "I wish I had work for you, but all is quiet for now."
                ],
                'progress': [
                    "How goes the {quest_name}? Any luck?",
                    "Have you made progress on that task I gave you?",
                    "Find that {quest_item} yet? I'm counting on you!"
                ]
            },
            
            'location_info': {
                'town': [
                    "This town has stood for generations. Safe place, mostly.",
                    "The heart of our community. You'll find everything you need here.",
                    "We take care of our own here. Outsiders are welcome if they're friendly."
                ],
                'wilderness': [
                    "Dangerous lands, these. Many have ventured in and never returned.",
                    "The wild places hold both beauty and terror. Stay alert.",
                    "Nature here is untamed. Respect it, or it'll swallow you whole."
                ],
                'dungeon': [
                    "Dark places hold dark things. Are you sure you want to go in?",
                    "Legends say great treasure lies within. Also great danger.",
                    "I wouldn't go in there without proper preparation."
                ]
            },
            
            'combat_advice': [
                "Watch their movements. Every enemy has a pattern.",
                "Aim for weak points! Even monsters have them.",
                "Sometimes running away is the smart choice.",
                "Use the environment to your advantage.",
                "Don't forget to use items in battle!"
            ],
            
            'item_advice': [
                "That {item_name} could be useful for {item_purpose}.",
                "Be careful with that! It's more valuable than it looks.",
                "Where did you find that? I haven't seen one in years.",
                "That belongs in a museum! Or maybe your pocket..."
            ],
            
            'rumor': [
                "I heard that {rumor_content}. Can't say if it's true or not.",
                "There's talk that {rumor_content}. Make of that what you will.",
                "The strangest thing... {rumor_content}. Weird, right?",
                "Word around town is {rumor_content}. Interesting times."
            ],
            
            'joke': [
                "Why don't adventurers play cards in the forest? Too many cheetahs!",
                "What's a goblin's favorite drink? Goblin-ade!",
                "Why did the dragon hoard so much gold? It had a burning desire!",
                "How do you organize a space party? You planet!",
                "What do you call a dwarf who just escaped prison? A fugitive!"
            ],
            
            'compliment_response': {
                'friendly': [
                    "You're too kind! Just doing my job.",
                    "Aw shucks, you're making me blush!",
                    "Well thank you! You're not so bad yourself."
                ],
                'neutral': [
                    "Thanks, I suppose.",
                    "Appreciate that.",
                    "Good to know."
                ],
                'grumpy': [
                    "Flattery won't get you better prices.",
                    "Save your compliments for someone who cares.",
                    "Yeah, yeah. Everyone says that."
                ]
            },
            
            'insult_response': {
                'friendly': [
                    "Ouch! That hurts. What did I do to deserve that?",
                    "That's not very nice. I was trying to help.",
                    "I'm sorry you feel that way. Maybe you're just having a bad day?"
                ],
                'neutral': [
                    "No need for insults. I'm just trying to help.",
                    "Rude. But I'll ignore that.",
                    "If you're going to be mean, I won't help you."
                ],
                'grumpy': [
                    "Get lost then! See how far you get without help.",
                    "Right back at you, friend. Some 'adventurer' you are.",
                    "Oh, you're one of THOSE types. Guards! We have a troublemaker!"
                ]
            },
            
            'unknown': [
                "I'm not sure I understand. Could you rephrase that?",
                "Hmm, I don't know about that. Anything else?",
                "That's beyond my knowledge. Try asking someone else.",
                "Interesting question. I'll have to think about that one.",
                "Not something I can help with, sorry."
            ]
        }
    
    def setup_personalities(self):
        """Setup different NPC personality profiles"""
        
        self.personalities = {
            'friendly': {
                'greeting_boost': 2,
                'help_chance': 0.9,
                'patience': 10,
                'topics': ['weather', 'family', 'food', 'celebration'],
                'speech_pattern': 'warm and welcoming',
                'response_modifiers': {
                    'formality': 0.3,
                    'enthusiasm': 0.9,
                    'detail': 0.7
                }
            },
            
            'grumpy': {
                'greeting_boost': -1,
                'help_chance': 0.3,
                'patience': 3,
                'topics': ['complaints', 'work', 'money', 'trouble'],
                'speech_pattern': 'curt and dismissive',
                'response_modifiers': {
                    'formality': 0.5,
                    'enthusiasm': 0.2,
                    'detail': 0.4
                }
            },
            
            'mysterious': {
                'greeting_boost': 0,
                'help_chance': 0.6,
                'patience': 7,
                'topics': ['secrets', 'magic', 'dreams', 'fate'],
                'speech_pattern': 'enigmatic and vague',
                'response_modifiers': {
                    'formality': 0.8,
                    'enthusiasm': 0.4,
                    'detail': 0.3
                }
            },
            
            'wise': {
                'greeting_boost': 1,
                'help_chance': 0.8,
                'patience': 12,
                'topics': ['history', 'advice', 'philosophy', 'nature'],
                'speech_pattern': 'thoughtful and measured',
                'response_modifiers': {
                    'formality': 0.9,
                    'enthusiasm': 0.5,
                    'detail': 0.9
                }
            },
            
            'eager': {
                'greeting_boost': 3,
                'help_chance': 0.95,
                'patience': 8,
                'topics': ['adventure', 'stories', 'dreams', 'travel'],
                'speech_pattern': 'excited and enthusiastic',
                'response_modifiers': {
                    'formality': 0.2,
                    'enthusiasm': 1.0,
                    'detail': 0.8
                }
            },
            
            'merchant': {
                'greeting_boost': 2,
                'help_chance': 0.7,
                'patience': 6,
                'topics': ['prices', 'goods', 'trade', 'economy'],
                'speech_pattern': 'business-like and persuasive',
                'response_modifiers': {
                    'formality': 0.7,
                    'enthusiasm': 0.6,
                    'detail': 0.8
                }
            }
        }
    
    def setup_quest_dialogue(self):
        """Setup quest-specific dialogue templates"""
        
        self.quest_dialogue = {
            'offer': {
                'simple': [
                    "I need {quest_item} from {quest_location}. Bring it to me and I'll pay {reward} gold.",
                    "Could you {quest_task}? I'd be very grateful.",
                    "There's a {monster_type} causing trouble near {quest_location}. Can you deal with it?"
                ],
                'story': [
                    "Long ago, {backstory_stub}. Now, I need someone to {quest_task}.",
                    "The {ancient_artifact} has been lost for generations. Find it and claim your reward!",
                    "My {family_member} disappeared in {quest_location}. Please find them!"
                ],
                'urgent': [
                    "Quickly! {urgent_situation}! You're the only one who can help!",
                    "No time to explain! {quest_task} before it's too late!",
                    "This is a matter of life and death! {quest_objective}!"
                ]
            },
            
            'progress': {
                'checking': [
                    "Made any progress on {quest_name}?",
                    "How goes the search for {quest_item}?",
                    "Any news about {quest_location}?"
                ],
                'encouragement': [
                    "I have faith in you. You can do this!",
                    "Be careful out there, but don't give up!",
                    "The reward is waiting when you succeed!"
                ],
                'warning': [
                    "Time is running out! Please hurry!",
                    "Others have tried and failed. Don't be like them.",
                    "If you can't do this, I'll have to find someone else."
                ]
            },
            
            'completion': {
                'success': [
                    "You did it! I can't thank you enough! Here's your reward: {reward} gold.",
                    "Amazing! You're a true hero! Take this gold and my eternal gratitude.",
                    "I never doubted you for a moment! Here's what I promised."
                ],
                'praise': [
                    "Incredible work! You're even more capable than you look.",
                    "The bards will sing of your deeds!",
                    "You've done what many thought impossible!"
                ],
                'reward_extra': [
                    "And here's a little extra for going above and beyond.",
                    "Take this as well. It belonged to {previous_owner}. May it serve you well.",
                    "I've also told the guild about your deeds. You'll find more work there."
                ]
            }
        }
    
    def setup_emotions(self):
        """Setup emotional response system"""
        
        self.emotions = {
            'happy': {
                'triggers': ['compliment', 'success', 'gift', 'joke'],
                'responses': [
                    "*smiles warmly*",
                    "*laughs cheerfully*",
                    "*beams with joy*",
                    "*hums a happy tune*"
                ],
                'modifiers': {
                    'friendliness': +2,
                    'patience': +3,
                    'helpfulness': +2
                }
            },
            
            'sad': {
                'triggers': ['bad_news', 'loss', 'memory'],
                'responses': [
                    "*sighs heavily*",
                    "*looks downcast*",
                    "*wipes away a tear*",
                    "*voice cracks with emotion*"
                ],
                'modifiers': {
                    'friendliness': -1,
                    'patience': +2,
                    'helpfulness': +1
                }
            },
            
            'angry': {
                'triggers': ['insult', 'betrayal', 'threat'],
                'responses': [
                    "*glares angrily*",
                    "*clenches fists*",
                    "*raises voice*",
                    "*stomps foot*"
                ],
                'modifiers': {
                    'friendliness': -3,
                    'patience': -4,
                    'helpfulness': -2
                }
            },
            
            'scared': {
                'triggers': ['danger', 'monster', 'dark'],
                'responses': [
                    "*trembles slightly*",
                    "*looks around nervously*",
                    "*voice quivers*",
                    "*jumps at every sound*"
                ],
                'modifiers': {
                    'friendliness': +1,
                    'patience': -2,
                    'helpfulness': -1
                }
            },
            
            'curious': {
                'triggers': ['question', 'mystery', 'new_item'],
                'responses': [
                    "*tilts head curiously*",
                    "*leans in with interest*",
                    "*eyes widen*",
                    "*scratches chin thoughtfully*"
                ],
                'modifiers': {
                    'friendliness': +1,
                    'patience': +2,
                    'helpfulness': +1
                }
            }
        }
    
    def interpret_command(self, command: str, context: Dict) -> str:
        """
        Main entry point for AI command interpretation
        Returns appropriate response based on input and context
        """
        
        # Analyze command
        category, confidence = self.analyze_command(command)
        
        # Get NPC personality if in conversation
        npc_personality = context.get('npc_personality', 'neutral')
        
        # Generate response based on category
        if category == 'greeting':
            return self.generate_greeting(context, npc_personality)
        
        elif category == 'farewell':
            return self.generate_farewell(context, npc_personality)
        
        elif category == 'about_self':
            return self.generate_self_introduction(context, npc_personality)
        
        elif category == 'about_player':
            return self.generate_player_reflection(context, npc_personality)
        
        elif category == 'help_request':
            return self.generate_help_response(context, npc_personality)
        
        elif category == 'quest_related':
            return self.generate_quest_response(context, npc_personality)
        
        elif category == 'location_questions':
            return self.generate_location_info(context, npc_personality)
        
        elif category == 'time_questions':
            return self.generate_time_response(context)
        
        elif category == 'combat_related':
            return self.generate_combat_advice(context, npc_personality)
        
        elif category == 'item_related':
            return self.generate_item_response(context, npc_personality)
        
        elif category == 'npc_related':
            return self.generate_npc_info(context, npc_personality)
        
        elif category == 'emotion':
            return self.generate_emotional_response(command, context, npc_personality)
        
        elif category == 'ask_opinion':
            return self.generate_opinion(context, npc_personality)
        
        elif category == 'ask_story':
            return self.generate_story(context, npc_personality)
        
        elif category == 'trading':
            return self.generate_trade_response(context, npc_personality)
        
        elif category == 'joke':
            return self.generate_joke(context, npc_personality)
        
        elif category == 'compliment':
            return self.generate_compliment_response(context, npc_personality)
        
        elif category == 'insult':
            return self.generate_insult_response(context, npc_personality)
        
        else:
            # Try to generate contextual response
            return self.generate_contextual_response(command, context, npc_personality)
    
    def analyze_command(self, command: str) -> Tuple[str, float]:
        """
        Analyze command to determine intent and confidence
        Returns (category, confidence_score)
        """
        best_category = 'unknown'
        best_confidence = 0.0
        
        for category, data in self.patterns.items():
            matches = 0
            total_patterns = len(data['compiled'])
            
            if total_patterns == 0:
                continue
            
            for pattern in data['compiled']:
                if pattern.search(command):
                    matches += 1
            
            # Calculate confidence based on matches and priority
            confidence = (matches / total_patterns) * (data['priority'] / 3.0)
            
            # Boost confidence for exact matches
            if matches > 0 and len(command.split()) <= 3:
                confidence *= 1.5
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_category = category
        
        # Store in memory
        if best_confidence > 0.3:
            self.memory['recent_topics'].append({
                'category': best_category,
                'timestamp': datetime.now().isoformat(),
                'command': command
            })
            if len(self.memory['recent_topics']) > 10:
                self.memory['recent_topics'].pop(0)
        
        return best_category, best_confidence
    
    def generate_greeting(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate a greeting response"""
        
        template = random.choice(self.response_templates['greeting'])
        
        # Check if we've met before
        npc_name = context.get('npc_name', 'stranger')
        if npc_name in self.memory['npc_relationships']:
            rel = self.memory['npc_relationships'][npc_name]
            if rel['times_talked'] > 1:
                # Return greeting
                greeting = random.choice([
                    f"Welcome back, {self.player['name']}!",
                    f"Good to see you again!",
                    f"Back so soon? What can I do for you?"
                ])
                return greeting
        
        # Format template
        response = template.format(
            player_name=self.player['name'],
            location=context.get('location', 'this place'),
            npc_name=context.get('npc_name', 'I'),
            npc_profession=context.get('npc_profession', 'local'),
            player_class=self.player.get('class', 'adventurer')
        )
        
        # Add emotional modifier
        response = self.add_emotional_flourish(response, personality)
        
        # Update memory
        if context.get('npc_name'):
            self.memory['npc_relationships'][context['npc_name']]['times_talked'] += 1
        
        return response
    
    def generate_farewell(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate a farewell response"""
        
        template = random.choice(self.response_templates['farewell'])
        
        response = template.format(
            player_name=self.player['name'],
            location=context.get('location', '')
        )
        
        return self.add_emotional_flourish(response, personality)
    
    def generate_self_introduction(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate self-introduction"""
        
        template = random.choice(self.response_templates['about_self'])
        
        response = template.format(
            npc_name=context.get('npc_name', 'I'),
            npc_profession=context.get('npc_profession', 'resident'),
            npc_race=context.get('npc_race', 'person'),
            location=context.get('location', 'here'),
            profession_service=self.get_profession_service(context.get('npc_profession', ''))
        )
        
        # Add random fact if personality is talkative
        if personality in ['friendly', 'eager', 'wise'] and random.random() < 0.4:
            fact = self.get_random_fact(context.get('location', ''))
            if fact:
                response += f" {fact}"
        
        return self.add_emotional_flourish(response, personality)
    
    def generate_player_reflection(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate reflection about the player"""
        
        template = random.choice(self.response_templates['about_player'])
        
        response = template.format(
            player_name=self.player['name'],
            player_class=self.player.get('class', 'adventurer')
        )
        
        # Add comment based on player stats
        if self.player['level'] > 5:
            response += " You look quite experienced!"
        elif self.player['level'] < 3:
            response += " New to adventuring, I take it?"
        
        return self.add_emotional_flourish(response, personality)
    
    def generate_help_response(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate help response"""
        
        # Get personality-specific templates
        help_templates = self.response_templates['help_request']
        
        # Choose based on personality or fallback to neutral
        if personality in help_templates:
            template = random.choice(help_templates[personality])
        else:
            template = random.choice(help_templates['neutral'])
        
        return self.add_emotional_flourish(template, personality)
    
    def generate_quest_response(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate quest-related response"""
        
        # Check if NPC has quest
        has_quest = context.get('has_quest', False)
        quest_context = context.get('quest_context', {})
        
        if has_quest:
            template = random.choice(self.response_templates['quest_related']['has_quest'])
            
            # Check if quest is already active
            if quest_context.get('active'):
                template = random.choice(self.response_templates['quest_related']['progress'])
            
            response = template.format(
                quest_name=quest_context.get('name', 'task'),
                quest_item=quest_context.get('item', 'something'),
                quest_location=quest_context.get('location', 'somewhere'),
                quest_task=quest_context.get('task', 'help out')
            )
        else:
            template = random.choice(self.response_templates['quest_related']['no_quest'])
            response = template
        
        return self.add_emotional_flourish(response, personality)
    
    def generate_location_info(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate information about current location"""
        
        location_type = context.get('location_type', 'town')
        location_name = context.get('location', '')
        
        # Get location-specific templates
        if location_type in self.response_templates['location_info']:
            template = random.choice(self.response_templates['location_info'][location_type])
        else:
            template = random.choice(self.response_templates['location_info']['town'])
        
        response = template
        
        # Add rumor if NPC is talkative
        if personality in ['friendly', 'eager'] and random.random() < 0.5:
            rumor = self.generate_rumor(location_name)
            if rumor:
                response += f"\n\n{rumor}"
        
        return self.add_emotional_flourish(response, personality)
    
    def generate_time_response(self, context: Dict) -> str:
        """Generate response about time"""
        
        hour = context.get('hour', 12)
        day = context.get('day', 1)
        
        time_phrases = {
            (0, 5): "dead of night",
            (5, 8): "early morning",
            (8, 12): "morning",
            (12, 17): "afternoon",
            (17, 20): "evening",
            (20, 24): "night"
        }
        
        time_of_day = "day"
        for (start, end), phrase in time_phrases.items():
            if start <= hour < end:
                time_of_day = phrase
                break
        
        responses = [
            f"It's the {time_of_day} of day {day}.",
            f"The {time_of_day} sun casts long shadows. Day {day} of your journey.",
            f"Day {day}, in the {time_of_day}. Time flies when you're adventuring!",
            f"The {time_of_day} air feels {random.choice(['fresh', 'heavy', 'cool', 'warm'])}."
        ]
        
        return random.choice(responses)
    
    def generate_combat_advice(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate combat advice"""
        
        template = random.choice(self.response_templates['combat_advice'])
        
        # Add specific advice based on player class
        player_class = self.player.get('class', '').lower()
        if 'warrior' in player_class:
            template += " As a warrior, your strength is your greatest asset!"
        elif 'mage' in player_class:
            template += " A mage should keep their distance and use spells wisely."
        elif 'rogue' in player_class:
            template += " Rogues excel at striking first and striking hard!"
        elif 'cleric' in player_class:
            template += " Don't forget your healing abilities in the heat of battle!"
        
        return self.add_emotional_flourish(template, personality)
    
    def generate_item_response(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate response about items"""
        
        item_name = context.get('item_name', 'that item')
        
        template = random.choice(self.response_templates['item_advice'])
        
        response = template.format(
            item_name=item_name,
            item_purpose=random.choice([
                'crafting', 'trading', 'quests', 'survival', 'combat'
            ])
        )
        
        return self.add_emotional_flourish(response, personality)
    
    def generate_npc_info(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate information about other NPCs"""
        
        target_npc = context.get('target_npc', '')
        
        if target_npc and target_npc in context.get('known_npcs', []):
            responses = [
                f"Oh, {target_npc}? They're {random.choice(['nice', 'helpful', 'strange', 'quiet'])}.",
                f"{target_npc} lives over by the {random.choice(['market', 'temple', 'gates'])}.",
                f"You can usually find {target_npc} at the {random.choice(['tavern', 'their shop', 'town square'])}."
            ]
        else:
            responses = [
                "I don't know much about them, sorry.",
                "Can't say I've heard of that person.",
                "You'd have to ask someone else about them."
            ]
        
        return random.choice(responses)
    
    def generate_emotional_response(self, command: str, context: Dict, personality: str = 'neutral') -> str:
        """Generate emotional response"""
        
        # Detect emotion from command
        detected_emotion = self.detect_emotion(command)
        
        if detected_emotion and detected_emotion in self.emotions:
            emotion_data = self.emotions[detected_emotion]
            
            # Add emotional flourish
            flourish = random.choice(emotion_data['responses'])
            
            # Generate appropriate response
            if detected_emotion == 'happy':
                response = f"{flourish} That's wonderful to hear!"
            elif detected_emotion == 'sad':
                response = f"{flourish} I'm sorry you're feeling that way."
            elif detected_emotion == 'angry':
                response = f"{flourish} Let's calm down and talk about this."
            elif detected_emotion == 'scared':
                response = f"{flourish} Don't worry, you're safe here."
            else:
                response = flourish
            
            return response
        
        return self.generate_contextual_response(command, context, personality)
    
    def generate_opinion(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate opinion on a topic"""
        
        topics = [
            ('adventuring', "It's a dangerous life, but someone has to do it."),
            ('the town', "Quiet place. I like it that way."),
            ('the king', "He does his best, I suppose."),
            ('magic', "Powerful stuff. Should be respected."),
            ('monsters', "They're getting bolder lately. Worrying."),
            ('treasure', "Shiny things attract trouble."),
            ('the weather', random.choice(["Could be worse.", "Beautiful day!", "Rain again..."]))
        ]
        
        topic, opinion = random.choice(topics)
        return f"{topic.title()}? {opinion}"
    
    def generate_story(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate a short story or legend"""
        
        story_elements = {
            'hero': ['The Brave Warrior', 'The Wise Mage', 'The Cunning Rogue', 'The Pious Cleric'],
            'villain': ['a terrible dragon', 'an evil sorcerer', 'a dark cult', 'an ancient curse'],
            'treasure': ['golden treasure', 'magical artifact', 'sacred relic', 'hidden knowledge'],
            'twist': ['betrayal', 'sacrifice', 'unexpected ally', 'forgotten truth']
        }
        
        hero = random.choice(story_elements['hero'])
        villain = random.choice(story_elements['villain'])
        treasure = random.choice(story_elements['treasure'])
        twist = random.choice(story_elements['twist'])
        
        story = f"Long ago, {hero} ventured forth to defeat {villain} and claim the {treasure}. "
        story += f"But in a shocking {twist}, they discovered that {random.choice(['nothing is as it seems', 'the real enemy was within', 'the treasure was a trap', 'the villain was misunderstood'])}. "
        story += f"To this day, {random.choice(['the treasure remains unfound', 'the battle echoes in legend', 'few dare to follow that path', 'the truth is buried with time'])}."
        
        return story
    
    def generate_trade_response(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate trading-related response"""
        
        if context.get('is_merchant', False):
            responses = [
                f"Everything has a price. What catches your eye?",
                f"Best prices in town! Take a look at my wares.",
                f"I've got {random.choice(['rare', 'exotic', 'fine', 'practical'])} goods for sale."
            ]
        else:
            responses = [
                "I'm not a merchant, sorry.",
                "Don't have anything to trade, but thanks for asking.",
                "If you need supplies, try the market."
            ]
        
        return random.choice(responses)
    
    def generate_joke(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate a joke"""
        
        return random.choice(self.response_templates['joke'])
    
    def generate_compliment_response(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate response to a compliment"""
        
        comp_templates = self.response_templates['compliment_response']
        
        if personality in comp_templates:
            template = random.choice(comp_templates[personality])
        else:
            template = random.choice(comp_templates['neutral'])
        
        # Update relationship
        if context.get('npc_name'):
            self.memory['npc_relationships'][context['npc_name']]['favor'] += 1
        
        return template
    
    def generate_insult_response(self, context: Dict, personality: str = 'neutral') -> str:
        """Generate response to an insult"""
        
        insult_templates = self.response_templates['insult_response']
        
        if personality in insult_templates:
            template = random.choice(insult_templates[personality])
        else:
            template = random.choice(insult_templates['neutral'])
        
        # Update relationship negatively
        if context.get('npc_name'):
            self.memory['npc_relationships'][context['npc_name']]['favor'] -= 2
        
        return template
    
    def generate_contextual_response(self, command: str, context: Dict, personality: str = 'neutral') -> str:
        """Generate contextual response for unknown commands"""
        
        # Try to extract keywords
        keywords = self.extract_keywords(command)
        
        # Check if we have any relevant responses
        for keyword in keywords:
            if keyword in self.knowledge_base.get('world_facts', {}):
                return f"Ah, {keyword}? {random.choice(self.knowledge_base['world_facts']['recent_events'])}"
        
        # Check for location-specific knowledge
        location = context.get('location', '')
        if location in self.knowledge_base.get('locations', {}):
            loc_data = self.knowledge_base['locations'][location]
            if random.random() < 0.5 and loc_data.get('rumors'):
                return random.choice(loc_data['rumors'])
        
        # Default responses
        return random.choice(self.response_templates['unknown'])
    
    def generate_rumor(self, location: str) -> str:
        """Generate a random rumor"""
        
        rumors = [
            f"{location} is haunted by the ghost of a {random.choice(['king', 'thief', 'lover', 'hero'])}.",
            f"There's {random.choice(['hidden treasure', 'a secret passage', 'an ancient altar', 'magic crystals'])} nearby.",
            f"The {random.choice(['guards', 'merchants', 'priests', 'children'])} know more than they let on.",
            f"A {random.choice(['strange figure', 'hooded stranger', 'wounded soldier', 'mysterious traveler'])} was seen recently.",
            f"The {random.choice(['well', 'old tree', 'abandoned house', 'cemetery'])} is {random.choice(['cursed', 'magical', 'haunted', 'sacred'])}."
        ]
        
        template = random.choice(self.response_templates['rumor'])
        return template.format(rumor_content=random.choice(rumors))
    
    def add_emotional_flourish(self, response: str, personality: str = 'neutral') -> str:
        """Add emotional flourishes to response based on personality"""
        
        if personality in self.personalities:
            mods = self.personalities[personality]['response_modifiers']
            
            # Add personality-specific phrasing
            if mods['enthusiasm'] > 0.7:
                if random.random() < 0.3:
                    response += f" {random.choice(['!', '!!', '!!!'])}"
            
            if mods['formality'] > 0.7:
                response = response.replace("gonna", "going to")
                response = response.replace("wanna", "want to")
            
            if mods['detail'] > 0.7 and random.random() < 0.3:
                response += f" {random.choice(['Indeed.', 'You see,', 'The truth is,', 'Mark my words,'])}"
        
        return response
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        
        # Simple keyword extraction (can be enhanced with NLP)
        words = text.lower().split()
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'is', 'at', 'which', 'on', 'and', 'or', 'but', 
                      'in', 'with', 'to', 'for', 'of', 'from', 'by', 'about', 'as'}
        
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        return keywords[:3]  # Return top 3 keywords
    
    def detect_emotion(self, text: str) -> Optional[str]:
        """Detect emotion from text"""
        
        emotion_keywords = {
            'happy': ['happy', 'glad', 'joy', 'great', 'wonderful', 'excellent'],
            'sad': ['sad', 'unhappy', 'depressed', 'miserable', 'heartbroken'],
            'angry': ['angry', 'mad', 'furious', 'annoyed', 'irritated'],
            'scared': ['scared', 'afraid', 'terrified', 'fear', 'frightened'],
            'curious': ['curious', 'wonder', 'interesting', 'fascinating']
        }
        
        text_lower = text.lower()
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        
        return None
    
    def get_profession_service(self, profession: str) -> str:
        """Get service description for profession"""
        
        services = {
            'blacksmith': 'weapons and armor',
            'merchant': 'goods and supplies',
            'innkeeper': 'food and lodging',
            'guard': 'protection',
            'priest': 'blessings and healing',
            'farmer': 'fresh produce',
            'scholar': 'knowledge and lore'
        }
        
        return services.get(profession.lower(), 'services')
    
    def get_random_fact(self, location: str) -> Optional[str]:
        """Get a random fact about a location"""
        
        if location in self.knowledge_base.get('locations', {}):
            facts = self.knowledge_base['locations'][location].get('facts', [])
            if facts:
                return f"Did you know? {random.choice(facts)}"
        
        return None
    
    def update_memory(self, key: str, value: Any):
        """Update AI memory"""
        self.memory[key] = value
    
    def get_conversation_summary(self) -> str:
        """Get summary of current conversation state"""
        
        summary = f"Topics discussed: {', '.join([t['category'] for t in self.memory['recent_topics'][-3:]])}"
        return summary
    
    def reset_conversation(self):
        """Reset conversation memory (for new NPCs)"""
        self.memory['recent_topics'] = []
        self.memory['emotional_state'] = 'neutral'