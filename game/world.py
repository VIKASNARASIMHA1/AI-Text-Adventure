import random
from typing import Dict, List, Tuple, Optional
from .utils import TextFormatter, Dice

class WorldGenerator:
    """
    Procedurally generates an entire game world with:
    - Multiple regions
    - Interconnected locations
    - Dynamic NPCs
    - Random encounters
    - Hidden secrets
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)
        self.world = {}
        self.regions = []
        self.connections = []
        
    def generate_world(self, size: str = "medium") -> Dict:
        """
        Generate a complete world
        Sizes: small (10 locs), medium (25 locs), large (50 locs)
        """
        sizes = {
            'small': {'regions': 2, 'locs_per_region': 5, 'dungeons': 1},
            'medium': {'regions': 4, 'locs_per_region': 6, 'dungeons': 2},
            'large': {'regions': 6, 'locs_per_region': 8, 'dungeons': 3}
        }
        
        config = sizes.get(size, sizes['medium'])
        
        # Generate regions
        for i in range(config['regions']):
            region = self.generate_region(i, config['locs_per_region'])
            self.regions.append(region)
            self.world.update(region['locations'])
        
        # Generate dungeons
        for i in range(config['dungeons']):
            dungeon = self.generate_dungeon()
            self.world.update(dungeon)
        
        # Create connections between locations
        self.create_connections()
        
        # Add special locations
        self.add_special_locations()
        
        return self.world
    
    def generate_region(self, region_id: int, num_locations: int) -> Dict:
        """Generate a region with multiple locations"""
        
        region_types = [
            'Forest', 'Mountain', 'Coastal', 'Desert', 
            'Swamp', 'Plains', 'Highlands', 'Valley'
        ]
        
        region_name = f"{self.random.choice(region_types)} of "
        region_name += f"{self.generate_name()} {self.random.choice(['Realm', 'Kingdom', 'Lands'])}"
        
        location_templates = [
            {
                'name_prefix': ['Ancient', 'Misty', 'Dark', 'Sunlit', 'Sacred', 'Forgotten'],
                'name_suffix': ['Village', 'Town', 'Outpost', 'Camp', 'Settlement', 'Keep'],
                'type': 'civilization'
            },
            {
                'name_prefix': ['Deep', 'Twisted', 'Whispering', 'Silent', 'Echoing'],
                'name_suffix': ['Forest', 'Woods', 'Grove', 'Thicket'],
                'type': 'wilderness'
            },
            {
                'name_prefix': ['Crystal', 'Murky', 'Still', 'Rushing', 'Hidden'],
                'name_suffix': ['Lake', 'River', 'Stream', 'Pond', 'Waterfall'],
                'type': 'water'
            },
            {
                'name_prefix': ['Broken', 'Jagged', 'Misty', 'Forgotten', 'Eternal'],
                'name_suffix': ['Hills', 'Mountains', 'Peaks', 'Cliffs', 'Highlands'],
                'type': 'highlands'
            }
        ]
        
        locations = {}
        
        for i in range(num_locations):
            template = self.random.choice(location_templates)
            
            # Generate location name
            prefix = self.random.choice(template['name_prefix'])
            suffix = self.random.choice(template['name_suffix'])
            name = f"{prefix} {suffix}"
            
            # Generate location ID
            loc_id = f"{region_id}_{i}_{self.random.randint(1000, 9999)}"
            
            # Create location
            locations[loc_id] = self.create_location(
                loc_id, name, template['type'], region_name
            )
        
        return {
            'name': region_name,
            'id': f"region_{region_id}",
            'locations': locations
        }
    
    def create_location(self, loc_id: str, name: str, loc_type: str, region: str) -> Dict:
        """Create a single location"""
        
        # Generate description
        descriptions = {
            'civilization': [
                "The sounds of daily life fill the air. {people} go about their business.",
                "A bustling {settlement} with {feature} at its center.",
                "Smoke rises from chimneys as {people} gather in the square."
            ],
            'wilderness': [
                "Ancient trees tower overhead, their canopy blocking the sun.",
                "The wind whispers through the {trees} as wildlife rustles nearby.",
                "A {feeling} atmosphere pervades this place. You feel {emotion}."
            ],
            'water': [
                "The water is {water_quality} and {water_temp}. {water_feature} can be seen.",
                "Ripples spread across the surface as {creatures} swim by.",
                "The {water_body} stretches before you, its depths mysterious."
            ],
            'highlands': [
                "Wind sweeps across the {terrain}, carrying the scent of {smell}.",
                "The view from here is {view}, spanning for miles.",
                "Rocky {formation} rise around you, shaped by countless storms."
            ]
        }
        
        # Generate random features
        features = {
            'people': ['merchants', 'farmers', 'travelers', 'locals', 'guards'],
            'settlement': ['village', 'town', 'hamlet', 'outpost', 'camp'],
            'feature': ['fountain', 'statue', 'market', 'shrine', 'well'],
            'trees': ['oaks', 'pines', 'willows', 'birches', 'redwoods'],
            'feeling': ['serene', 'foreboding', 'peaceful', 'eerie', 'mystical'],
            'emotion': ['watched', 'at peace', 'uneasy', 'curious', 'humble'],
            'water_quality': ['clear', 'murky', 'crystal', 'dark', 'sparkling'],
            'water_temp': ['cool', 'warm', 'cold', 'refreshing', 'icy'],
            'water_feature': ['Fish jumping', 'Water lilies', 'Mist rising', 'Bubbles'],
            'creatures': ['fish', 'frogs', 'waterfowl', 'turtles'],
            'water_body': ['lake', 'river', 'pond', 'stream'],
            'terrain': ['rocky slopes', 'grassy plateaus', 'bare cliffs'],
            'smell': ['pine', 'wildflowers', 'fresh air', 'rain'],
            'view': ['breathtaking', 'stunning', 'impressive', 'vast'],
            'formation': ['outcroppings', 'spires', 'cliffs', 'crags']
        }
        
        # Build description
        desc_template = self.random.choice(descriptions[loc_type])
        description = desc_template.format(**{
            k: self.random.choice(v) for k, v in features.items()
            if '{' + k + '}' in desc_template
        })
        
        # Determine available exits
        possible_exits = ['north', 'south', 'east', 'west']
        num_exits = self.random.randint(2, 4)
        exits = self.random.sample(possible_exits, num_exits)
        
        # Generate NPCs
        num_npcs = self.random.randint(0, 3)
        npcs = [self.generate_npc() for _ in range(num_npcs)]
        
        # Generate items
        num_items = self.random.randint(0, 4)
        items = [self.generate_item() for _ in range(num_items)]
        
        # Generate possible enemies
        possible_enemies = {
            'civilization': ['thief', 'corrupt_guard', 'criminal'],
            'wilderness': ['wolf', 'bear', 'goblin', 'orc', 'spider'],
            'water': ['giant_frog', 'snake', 'crocodile'],
            'highlands': ['eagle', 'mountain_lion', 'troll']
        }
        
        enemies = possible_enemies.get(loc_type, ['wolf', 'goblin'])
        enemy_level = self.random.randint(1, 5)
        
        return {
            'id': loc_id,
            'name': name,
            'type': loc_type,
            'region': region,
            'description': description,
            'exits': {exit: None for exit in exits},  # Will be connected later
            'npcs': npcs,
            'items': items,
            'enemies': enemies,
            'enemy_level': enemy_level,
            'danger_level': self.random.randint(1, 10),
            'secrets': self.generate_secrets(),
            'visited': False
        }
    
    def generate_npc(self) -> Dict:
        """Generate a random NPC"""
        
        races = ['Human', 'Elf', 'Dwarf', 'Halfling', 'Gnome', 'Half-Elf']
        professions = [
            'Merchant', 'Guard', 'Farmer', 'Blacksmith', 'Innkeeper',
            'Priest', 'Scholar', 'Thief', 'Adventurer', 'Hermit'
        ]
        
        personalities = [
            'friendly', 'grumpy', 'mysterious', 'talkative', 'shy',
            'wise', 'foolish', 'brave', 'cowardly', 'curious'
        ]
        
        quest_giver = self.random.random() < 0.3  # 30% chance to give quests
        
        return {
            'name': self.generate_name(),
            'race': self.random.choice(races),
            'profession': self.random.choice(professions),
            'personality': self.random.choice(personalities),
            'quest_giver': quest_giver,
            'dialogue': self.generate_dialogue(),
            'inventory': [self.generate_item() for _ in range(self.random.randint(0, 3))]
        }
    
    def generate_name(self) -> str:
        """Generate a random fantasy name"""
        
        prefixes = ['Al', 'Bal', 'Cal', 'Dal', 'El', 'Fel', 'Gal', 'Hal',
                   'Il', 'Jal', 'Kal', 'Lal', 'Mal', 'Nal', 'Ol', 'Pal']
        
        middles = ['an', 'en', 'in', 'on', 'un', 'ar', 'er', 'ir',
                   'or', 'ur', 'ath', 'eth', 'ith', 'oth']
        
        suffixes = ['dor', 'nor', 'mir', 'mar', 'ric', 'lin', 'wyn',
                   'gar', 'las', 'ras', 'vik', 'rik']
        
        pattern = self.random.choice(['prefix+suffix', 'prefix+middle+suffix'])
        
        if pattern == 'prefix+suffix':
            return self.random.choice(prefixes) + self.random.choice(suffixes)
        else:
            return (self.random.choice(prefixes) + 
                   self.random.choice(middles) + 
                   self.random.choice(suffixes))
    
    def generate_item(self) -> Dict:
        """Generate a random item"""
        
        item_types = {
            'weapon': {
                'prefixes': ['Iron', 'Steel', 'Bronze', 'Silver', 'Golden'],
                'names': ['Sword', 'Axe', 'Bow', 'Dagger', 'Mace'],
                'value': (10, 50),
                'damage': (2, 8)
            },
            'armor': {
                'prefixes': ['Leather', 'Chain', 'Plate', 'Hide', 'Bone'],
                'names': ['Helmet', 'Chestplate', 'Shield', 'Boots', 'Gloves'],
                'value': (15, 60),
                'defense': (1, 5)
            },
            'potion': {
                'prefixes': ['Healing', 'Mana', 'Strength', 'Speed', 'Invisibility'],
                'names': ['Potion', 'Elixir', 'Potion', 'Draught', 'Tonic'],
                'value': (5, 30),
                'effect': 'various'
            },
            'treasure': {
                'prefixes': ['Gold', 'Silver', 'Jeweled', 'Ancient', 'Magic'],
                'names': ['Coin', 'Gem', 'Ring', 'Amulet', 'Statue'],
                'value': (20, 100),
                'effect': None
            }
        }
        
        item_type = self.random.choice(list(item_types.keys()))
        template = item_types[item_type]
        
        name = f"{self.random.choice(template['prefixes'])} {self.random.choice(template['names'])}"
        
        item = {
            'name': name,
            'type': item_type,
            'value': self.random.randint(*template['value'])
        }
        
        if 'damage' in template:
            item['damage'] = self.random.randint(*template['damage'])
        if 'defense' in template:
            item['defense'] = self.random.randint(*template['defense'])
        
        return item
    
    def generate_dialogue(self) -> List[str]:
        """Generate dialogue lines for NPC"""
        
        dialogue_templates = [
            "Hello there, traveler!",
            "Nice weather we're having.",
            "Be careful on the roads.",
            "Have you heard any news?",
            "I don't get many visitors here.",
            "The old ruins are dangerous at night.",
            "I could tell you stories for hours.",
            "You look like you've traveled far."
        ]
        
        return self.random.sample(dialogue_templates, 
                                  k=self.random.randint(2, 5))
    
    def generate_secrets(self) -> List[Dict]:
        """Generate hidden secrets in location"""
        
        secrets = []
        num_secrets = self.random.randint(0, 3)
        
        secret_types = [
            {'name': 'hidden_treasure', 'difficulty': 15},
            {'name': 'secret_passage', 'difficulty': 12},
            {'name': 'ancient_altar', 'difficulty': 18},
            {'name': 'buried_cache', 'difficulty': 10},
            {'name': 'concealed_door', 'difficulty': 14}
        ]
        
        for _ in range(num_secrets):
            secret = self.random.choice(secret_types).copy()
            secret['found'] = False
            secret['perception_dc'] = secret.pop('difficulty')
            secrets.append(secret)
        
        return secrets
    
    def generate_dungeon(self) -> Dict:
        """Generate a dungeon with multiple rooms"""
        
        dungeon_name = f"{self.random.choice(['Ancient', 'Forgotten', 'Cursed', 'Haunted'])} " + \
                      f"{self.random.choice(['Crypts', 'Caverns', 'Ruins', 'Temple', 'Tomb'])}"
        
        num_rooms = self.random.randint(3, 7)
        rooms = {}
        
        # Generate entrance
        entrance_id = f"dungeon_entrance_{self.random.randint(1000, 9999)}"
        rooms[entrance_id] = self.create_location(
            entrance_id,
            f"Entrance to {dungeon_name}",
            'dungeon',
            'Dungeon'
        )
        rooms[entrance_id]['description'] = f"A dark opening leads into {dungeon_name}. " + \
                                            "The air smells damp and musty."
        
        # Generate rooms
        for i in range(num_rooms):
            room_id = f"dungeon_room_{i}_{self.random.randint(1000, 9999)}"
            room_name = f"{self.random.choice(['Dark', 'Echoing', 'Narrow', 'Vast', 'Chamber of'])} " + \
                        f"{self.random.choice(['Shadows', 'Echoes', 'Secrets', 'Whispers', 'the Ancients'])}"
            
            rooms[room_id] = self.create_location(
                room_id,
                room_name,
                'dungeon',
                'Dungeon'
            )
            
            # Dungeons have more enemies
            rooms[room_id]['enemies'] = ['skeleton', 'zombie', 'ghost', 'cultist']
            rooms[room_id]['enemy_level'] = self.random.randint(3, 8)
        
        return rooms
    
    def create_connections(self):
        """Create bidirectional connections between locations"""
        
        all_locations = list(self.world.keys())
        
        for loc_id in all_locations:
            location = self.world[loc_id]
            
            for direction in location['exits']:
                if location['exits'][direction] is None:
                    # Find a location to connect to
                    possible_targets = [l for l in all_locations 
                                       if l != loc_id and self.world[l]['exits'].get(self.opposite_direction(direction)) is None]
                    
                    if possible_targets:
                        target = self.random.choice(possible_targets)
                        location['exits'][direction] = target
                        self.world[target]['exits'][self.opposite_direction(direction)] = loc_id
    
    def opposite_direction(self, direction: str) -> str:
        opposites = {
            'north': 'south', 'south': 'north',
            'east': 'west', 'west': 'east'
        }
        return opposites.get(direction, direction)
    
    def add_special_locations(self):
        """Add unique special locations"""
        
        specials = [
            {
                'name': 'The Floating Islands',
                'type': 'special',
                'description': 'Islands float impossibly in the sky, connected by glowing bridges.'
            },
            {
                'name': 'The Crystal Cave',
                'type': 'special',
                'description': 'Massive crystals grow from every surface, pulsing with inner light.'
            },
            {
                'name': 'The Sunken City',
                'type': 'special',
                'description': 'Ancient spires rise from the water, remnants of a forgotten civilization.'
            }
        ]
        
        for special in specials:
            loc_id = f"special_{self.random.randint(1000, 9999)}"
            self.world[loc_id] = {
                'id': loc_id,
                'name': special['name'],
                'type': special['type'],
                'region': 'Special Location',
                'description': special['description'],
                'exits': {},
                'npcs': [],
                'items': [self.generate_item() for _ in range(3)],
                'enemies': ['guardian', 'elemental'],
                'enemy_level': 10,
                'danger_level': 8,
                'secrets': [],
                'visited': False
            }

class WorldManager:
    """Manages the game world state"""
    
    def __init__(self, world_data: Dict):
        self.world = world_data
        self.current_location = list(world_data.keys())[0]  # Start at first location
        self.discovered_locations = {self.current_location}
        self.location_history = []
        
    def move(self, direction: str) -> Tuple[bool, str]:
        """Move to a new location"""
        
        current = self.world[self.current_location]
        
        if direction not in current['exits']:
            return False, f"You can't go {direction} from here."
        
        target_id = current['exits'][direction]
        
        if target_id is None:
            return False, f"There's no path {direction} from here."
        
        # Move to new location
        self.location_history.append(self.current_location)
        self.current_location = target_id
        self.discovered_locations.add(target_id)
        self.world[target_id]['visited'] = True
        
        return True, self.get_location_description(target_id)
    
    def get_current_location(self) -> Dict:
        """Get current location data"""
        return self.world[self.current_location]
    
    def get_location_description(self, loc_id: Optional[str] = None) -> str:
        """Get formatted description of a location"""
        
        if loc_id is None:
            loc_id = self.current_location
        
        location = self.world[loc_id]
        
        desc = f"\n{TextFormatter.location('📍 ' + location['name'])}\n"
        desc += TextFormatter.divider() + "\n"
        desc += location['description'] + "\n\n"
        
        # Exits
        exits = [d for d, target in location['exits'].items() if target is not None]
        if exits:
            desc += f"{TextFormatter.info('🚪 Exits:')} {', '.join(exits)}\n"
        
        # NPCs
        if location['npcs']:
            npc_names = [npc['name'] for npc in location['npcs']]
            desc += f"{TextFormatter.info('👥 People:')} {', '.join(npc_names)}\n"
        
        # Items
        if location['items']:
            item_names = [item['name'] for item in location['items']]
            desc += f"{TextFormatter.item('📦 Items:')} {', '.join(item_names)}\n"
        
        # Danger level indicator
        if location['danger_level'] > 7:
            desc += f"{TextFormatter.warning('⚠️  This place feels very dangerous!')}\n"
        elif location['danger_level'] > 4:
            desc += f"{TextFormatter.warning('⚠️  You should be careful here.')}\n"
        
        # First visit message
        if not location.get('visited', False):
            desc += f"\n{TextFormatter.info('✨ This is your first time here.')}"
        
        return desc
    
    def get_map(self) -> str:
        """Get a simple ASCII map of discovered locations"""
        
        if len(self.discovered_locations) < 2:
            return "You haven't discovered enough of the world to see a map."
        
        map_str = f"\n{TextFormatter.header('🗺️  DISCOVERED AREAS')}\n"
        map_str += TextFormatter.divider('-') + "\n"
        
        for loc_id in self.discovered_locations:
            location = self.world[loc_id]
            marker = "► " if loc_id == self.current_location else "  "
            map_str += f"{marker}{location['name']}\n"
        
        return map_str