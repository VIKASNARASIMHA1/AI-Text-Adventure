"""
Test suite for AI Text Adventure Game
Includes unit tests, integration tests, and game mechanics validation
"""

import unittest
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path to import game modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.utils import TextFormatter, Colors, Dice, GameLogger
from game.world import WorldGenerator, WorldManager
from game.ai_engine import AIEngine
from game.combat import CombatSystem, CombatState, DamageType
from game.quests import QuestManager, QuestType, QuestDifficulty, QuestStatus
from game.npc import NPCSystem, NPCRole, NPCStatus, RelationshipLevel
from game.inventory import InventorySystem, ItemType, ItemRarity, EquipmentSlot
from game.save_system import SaveSystem

class TestUtils(unittest.TestCase):
    """Test utility functions and classes"""
    
    def setUp(self):
        self.logger = GameLogger(enabled=True)
        
    def test_dice_rolls(self):
        """Test dice rolling functionality"""
        # Test basic dice
        result = Dice.roll("2d6")
        self.assertTrue(2 <= result <= 12)
        
        # Test with modifier
        result = Dice.roll("1d20+5")
        self.assertTrue(6 <= result <= 25)
        
        # Test d20
        result = Dice.d20()
        self.assertTrue(1 <= result <= 20)
        
        # Test d100
        result = Dice.d100()
        self.assertTrue(1 <= result <= 100)
        
        # Test invalid format
        result = Dice.roll("invalid")
        self.assertEqual(result, 0)
    
    def test_game_logger(self):
        """Test game logging functionality"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            self.logger.log('test_event', {'data': 'test_value'})
            self.logger.log('another_event', {'score': 100})
            
            self.assertEqual(len(self.logger.events), 2)
            self.assertEqual(self.logger.events[0]['type'], 'test_event')
            
            # Test save
            self.logger.save(temp_file)
            
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(len(saved_data), 2)
            self.assertEqual(saved_data[0]['type'], 'test_event')
            
        finally:
            os.unlink(temp_file)
    
    def test_text_formatter(self):
        """Test text formatting functions"""
        # Test header
        header = TextFormatter.header("Test")
        self.assertIsInstance(header, str)
        self.assertTrue(len(header) > 0)
        
        # Test info
        info = TextFormatter.info("Info message")
        self.assertIsInstance(info, str)
        
        # Test success
        success = TextFormatter.success("Success message")
        self.assertIsInstance(success, str)
        
        # Test warning
        warning = TextFormatter.warning("Warning message")
        self.assertIsInstance(warning, str)
        
        # Test error
        error = TextFormatter.error("Error message")
        self.assertIsInstance(error, str)
        
        # Test combat
        combat = TextFormatter.combat("Combat message")
        self.assertIsInstance(combat, str)
        
        # Test dialogue
        dialogue = TextFormatter.dialogue("Hello", "NPC")
        self.assertIsInstance(dialogue, str)
        self.assertIn("NPC", dialogue)
        self.assertIn("Hello", dialogue)
        
        # Test location
        location = TextFormatter.location("Town Square")
        self.assertIsInstance(location, str)
        
        # Test item
        item = TextFormatter.item("Sword")
        self.assertIsInstance(item, str)
        
        # Test divider
        divider = TextFormatter.divider()
        self.assertEqual(len(divider), 60)
        divider = TextFormatter.divider('-', 10)
        self.assertEqual(len(divider), 10)

class TestWorld(unittest.TestCase):
    """Test world generation and management"""
    
    def setUp(self):
        self.generator = WorldGenerator(seed=42)  # Fixed seed for reproducibility
        self.world_data = self.generator.generate_world(size='small')
        self.manager = WorldManager(self.world_data)
    
    def test_world_generation(self):
        """Test procedural world generation"""
        # Check that world has locations
        self.assertTrue(len(self.world_data) > 0)
        
        # Check location structure
        first_loc = list(self.world_data.values())[0]
        self.assertIn('id', first_loc)
        self.assertIn('name', first_loc)
        self.assertIn('type', first_loc)
        self.assertIn('description', first_loc)
        self.assertIn('exits', first_loc)
        self.assertIn('npcs', first_loc)
        self.assertIn('items', first_loc)
        self.assertIn('enemies', first_loc)
    
    def test_location_connections(self):
        """Test that locations are properly connected"""
        for loc_id, location in self.world_data.items():
            for direction, target in location['exits'].items():
                if target:  # Skip None exits
                    # Check that target exists
                    self.assertIn(target, self.world_data)
                    # Check that connection is bidirectional
                    target_loc = self.world_data[target]
                    opposite = self.generator.opposite_direction(direction)
                    self.assertIn(opposite, target_loc['exits'])
                    self.assertEqual(target_loc['exits'][opposite], loc_id)
    
    def test_world_manager_movement(self):
        """Test player movement between locations"""
        initial_loc = self.manager.current_location
        
        # Try invalid direction
        success, message = self.manager.move('invalid')
        self.assertFalse(success)
        self.assertEqual(self.manager.current_location, initial_loc)
        
        # Try valid direction if available
        current = self.manager.get_current_location()
        valid_exits = [d for d, t in current['exits'].items() if t]
        
        if valid_exits:
            direction = valid_exits[0]
            success, message = self.manager.move(direction)
            self.assertTrue(success)
            self.assertNotEqual(self.manager.current_location, initial_loc)
            self.assertIn(self.manager.current_location, self.manager.discovered_locations)
    
    def test_location_description(self):
        """Test location description generation"""
        description = self.manager.get_location_description()
        self.assertIsInstance(description, str)
        self.assertTrue(len(description) > 0)
    
    def test_map_generation(self):
        """Test map generation"""
        # Initially only current location discovered
        map_str = self.manager.get_map()
        self.assertIsInstance(map_str, str)
        
        # After discovering more locations
        self.manager.discovered_locations.add('test_loc')
        map_str = self.manager.get_map()
        self.assertIsInstance(map_str, str)

class TestAIEngine(unittest.TestCase):
    """Test AI response engine"""
    
    def setUp(self):
        self.player = {
            'name': 'TestPlayer',
            'class': 'Warrior',
            'level': 1,
            'health': 100
        }
        self.game_flags = {'reputation': {}}
        self.ai = AIEngine(self.player, self.game_flags)
        
    def test_command_analysis(self):
        """Test command intent analysis"""
        # Test greetings
        category, confidence = self.ai.analyze_command("hello there")
        self.assertEqual(category, 'greeting')
        self.assertGreater(confidence, 0.5)
        
        # Test farewells
        category, confidence = self.ai.analyze_command("goodbye")
        self.assertEqual(category, 'farewell')
        
        # Test questions
        category, confidence = self.ai.analyze_command("who are you")
        self.assertEqual(category, 'about_self')
        
        # Test help requests
        category, confidence = self.ai.analyze_command("can you help me")
        self.assertEqual(category, 'help_request')
        
        # Test unknown command
        category, confidence = self.ai.analyze_command("asdfghjkl")
        self.assertEqual(category, 'unknown')
    
    def test_response_generation(self):
        """Test response generation"""
        context = {
            'location': 'tavern',
            'npc_name': 'Greta',
            'npc_personality': 'friendly',
            'npc_profession': 'innkeeper',
            'npc_race': 'human'
        }
        
        # Test greeting
        response = self.ai.interpret_command("hello", context)
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
        
        # Test farewell
        response = self.ai.interpret_command("goodbye", context)
        self.assertIsInstance(response, str)
        
        # Test help request
        response = self.ai.interpret_command("help me", context)
        self.assertIsInstance(response, str)
    
    def test_keyword_extraction(self):
        """Test keyword extraction"""
        keywords = self.ai.extract_keywords("I need to find the ancient sword")
        self.assertIsInstance(keywords, list)
        self.assertIn('ancient', keywords)
    
    def test_emotion_detection(self):
        """Test emotion detection"""
        emotion = self.ai.detect_emotion("I am very happy today")
        self.assertEqual(emotion, 'happy')
        
        emotion = self.ai.detect_emotion("This makes me angry")
        self.assertEqual(emotion, 'angry')
        
        emotion = self.ai.detect_emotion("No emotion words here")
        self.assertIsNone(emotion)
    
    def test_rumor_generation(self):
        """Test rumor generation"""
        rumor = self.ai.generate_rumor("test_location")
        self.assertIsInstance(rumor, str)
        self.assertTrue(len(rumor) > 0)

class TestCombat(unittest.TestCase):
    """Test combat system"""
    
    def setUp(self):
        self.player = {
            'name': 'TestPlayer',
            'health': 100,
            'max_health': 100,
            'strength': 10,
            'defense': 5,
            'inventory': ['health_potion']
        }
        self.combat = CombatSystem(self.player)
        
    def test_combat_start(self):
        """Test combat initialization"""
        self.combat.start_combat('goblin')
        
        self.assertIsNotNone(self.combat.enemy)
        self.assertEqual(self.combat.state, CombatState.PLAYER_TURN)
        self.assertEqual(self.combat.enemy.name, 'Goblin')
        
    def test_player_attack(self):
        """Test player attacking"""
        self.combat.start_combat('goblin')
        initial_enemy_health = self.combat.enemy.health
        
        result = self.combat.process_player_turn('attack')
        self.assertIsInstance(result, str)
        
        # Enemy should have taken damage
        self.assertLess(self.combat.enemy.health, initial_enemy_health)
        
    def test_player_defend(self):
        """Test player defending"""
        self.combat.start_combat('goblin')
        
        result = self.combat.process_player_turn('defend')
        self.assertIsInstance(result, str)
        self.assertTrue(len(self.combat.player_buffs) > 0)
        
    def test_player_flee(self):
        """Test fleeing from combat"""
        self.combat.start_combat('goblin')
        
        result = self.combat.process_player_turn('flee')
        self.assertIsInstance(result, str)
        
        # May or may not succeed, but state should change accordingly
        if 'successfully flee' in result.lower():
            self.assertEqual(self.combat.state, CombatState.FLEE)
        
    def test_enemy_turn(self):
        """Test enemy turn processing"""
        self.combat.start_combat('goblin')
        initial_player_health = self.player['health']
        
        # Force enemy turn
        self.combat.state = CombatState.ENEMY_TURN
        result = self.combat.process_enemy_turn()
        
        self.assertIsInstance(result, str)
        # Player may have taken damage
        self.assertLessEqual(self.player['health'], initial_player_health)
        
    def test_combat_victory(self):
        """Test combat victory condition"""
        self.combat.start_combat('goblin')
        
        # Reduce enemy health to 0
        self.combat.enemy.health = 0
        
        result = self.combat.process_victory()
        self.assertIsInstance(result, str)
        self.assertIn('VICTORY', result)
        
    def test_combat_defeat(self):
        """Test combat defeat condition"""
        self.player['health'] = 0
        self.combat.start_combat('goblin')
        
        result = self.combat.process_defeat()
        self.assertIsInstance(result, str)
        self.assertIn('DEFEAT', result)
        
    def test_combat_status(self):
        """Test combat status display"""
        self.combat.start_combat('goblin')
        
        status = self.combat.get_combat_status()
        self.assertIsInstance(status, str)
        self.assertIn('COMBAT STATUS', status)
        
        log = self.combat.get_combat_log()
        self.assertIsInstance(log, str)
        
        actions = self.combat.get_available_actions()
        self.assertIsInstance(actions, str)
        
    def test_damage_types(self):
        """Test different damage types"""
        self.combat.start_combat('skeleton')  # Skeleton has resistances/weaknesses
        
        # Physical damage
        damage = self.combat.enemy.take_damage(20, DamageType.PHYSICAL)
        self.assertIsInstance(damage, int)
        
        # Holy damage (should be more effective)
        holy_damage = self.combat.enemy.take_damage(20, DamageType.HOLY)
        self.assertGreater(holy_damage, damage)

class TestQuests(unittest.TestCase):
    """Test quest system"""
    
    def setUp(self):
        self.player = {
            'name': 'TestPlayer',
            'level': 1,
            'inventory': [],
            'xp': 0,
            'xp_to_next': 100
        }
        self.game_flags = {'reputation': {}}
        self.quest_manager = QuestManager(self.player, self.game_flags)
        
    def test_quest_generation(self):
        """Test procedural quest generation"""
        quest = self.quest_manager.generate_quest(
            giver_name="TestGiver",
            location="TestLocation",
            difficulty=QuestDifficulty.MEDIUM
        )
        
        self.assertIsNotNone(quest)
        self.assertIn('id', quest)
        self.assertIn('name', quest)
        self.assertIn('description', quest)
        self.assertIn('objectives', quest)
        self.assertIn('rewards', quest)
        self.assertEqual(quest['giver'], "TestGiver")
        
    def test_quest_offer_accept(self):
        """Test quest offering and acceptance"""
        quest = self.quest_manager.generate_quest("TestGiver", "TestLocation")
        
        # Offer quest
        dialogue = self.quest_manager.offer_quest(quest, "TestGiver")
        self.assertIsInstance(dialogue, str)
        self.assertIn(quest, self.quest_manager.available_quests)
        
        # Accept quest
        success = self.quest_manager.accept_quest(quest['id'])
        self.assertTrue(success)
        self.assertIn(quest, self.quest_manager.active_quests)
        self.assertEqual(quest['status'], QuestStatus.ACTIVE)
        
    def test_quest_progress(self):
        """Test quest progress tracking"""
        # Create a kill quest
        quest = {
            'id': 'test_quest',
            'name': 'Test Quest',
            'objectives': [
                {'type': 'kill', 'target': 'Goblin', 'count': 3, 'current': 0}
            ],
            'status': QuestStatus.ACTIVE
        }
        self.quest_manager.active_quests.append(quest)
        
        # Update progress
        completions = self.quest_manager.update_quest_progress('kill', 'Goblin')
        self.assertEqual(len(completions), 0)  # Not complete yet
        self.assertEqual(quest['objectives'][0]['current'], 1)
        
        # Complete quest
        quest['objectives'][0]['current'] = 3
        completions = self.quest_manager.update_quest_progress('kill', 'Goblin')
        self.assertEqual(len(completions), 1)
        self.assertEqual(quest['status'], QuestStatus.COMPLETED)
        
    def test_quest_turn_in(self):
        """Test quest turn-in and rewards"""
        quest = self.quest_manager.generate_quest("TestGiver", "TestLocation")
        self.quest_manager.active_quests.append(quest)
        quest['status'] = QuestStatus.COMPLETED
        
        initial_gold = self.player.get('gold', 0)
        
        # Turn in quest
        dialogue = self.quest_manager.turn_in_quest(quest['id'], "TestGiver")
        self.assertIsInstance(dialogue, str)
        
        # Should have received rewards
        self.assertGreater(self.player.get('gold', 0), initial_gold)
        self.assertNotIn(quest, self.quest_manager.active_quests)
        self.assertIn(quest, self.quest_manager.completed_quests)
        
    def test_quest_failure(self):
        """Test quest failure"""
        quest = self.quest_manager.generate_quest("TestGiver", "TestLocation")
        self.quest_manager.active_quests.append(quest)
        
        message = self.quest_manager.fail_quest(quest['id'], "timeout")
        self.assertIsNotNone(message)
        self.assertNotIn(quest, self.quest_manager.active_quests)
        self.assertIn(quest, self.quest_manager.failed_quests)
        
    def test_quest_display(self):
        """Test quest display functions"""
        # Add some quests
        quest1 = self.quest_manager.generate_quest("Giver1", "Loc1")
        quest2 = self.quest_manager.generate_quest("Giver2", "Loc2")
        
        self.quest_manager.active_quests.append(quest1)
        self.quest_manager.completed_quests.append(quest2)
        
        # Test display
        display = self.quest_manager.display_quests()
        self.assertIsInstance(display, str)
        self.assertIn(quest1['name'], display)
        
        journal = self.quest_manager.display_journal()
        self.assertIsInstance(journal, str)
        self.assertIn('ACTIVE QUESTS', journal)
        self.assertIn('Completed Quests', journal)

class TestNPC(unittest.TestCase):
    """Test NPC system"""
    
    def setUp(self):
        self.player = {
            'name': 'TestPlayer',
            'level': 1,
            'inventory': []
        }
        self.game_flags = {'reputation': {}}
        self.npc_system = NPCSystem(self.player, self.game_flags)
        
    def test_npc_generation(self):
        """Test NPC generation"""
        npc = self.npc_system.generate_npc(
            role=NPCRole.MERCHANT,
            location="TestLocation",
            race="human"
        )
        
        self.assertIsNotNone(npc)
        self.assertIn('id', npc)
        self.assertIn('name', npc)
        self.assertIn('role', npc)
        self.assertEqual(npc['role'], NPCRole.MERCHANT)
        self.assertEqual(npc['location'], "TestLocation")
        
        # Add to system
        self.npc_system.add_npc_to_world(npc)
        self.assertIn(npc['id'], self.npc_system.npcs)
        
    def test_npc_name_generation(self):
        """Test NPC name generation"""
        name = self.npc_system.generate_name('human', NPCRole.VILLAGER)
        self.assertIsInstance(name, str)
        self.assertTrue(len(name.split()) >= 2)  # First and last name
        
    def test_npc_personality(self):
        """Test NPC personality generation"""
        personality = self.npc_system.generate_personality()
        self.assertIn('traits', personality)
        self.assertIn('modifiers', personality)
        self.assertTrue(len(personality['traits']) >= 2)
        
    def test_npc_schedule(self):
        """Test NPC schedule generation"""
        schedule = self.npc_system.generate_schedule('villager')
        self.assertIsInstance(schedule, dict)
        self.assertTrue(len(schedule) > 0)
        
    def test_npc_interaction(self):
        """Test NPC interaction"""
        npc = self.npc_system.generate_npc(NPCRole.INNKEEPER, "Tavern")
        self.npc_system.add_npc_to_world(npc)
        
        # Test greeting
        response = self.npc_system.interact(npc['id'], "hello", {})
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
        
        # Test farewell
        response = self.npc_system.interact(npc['id'], "goodbye", {})
        self.assertIsInstance(response, str)
        
    def test_relationship_system(self):
        """Test relationship tracking"""
        npc = self.npc_system.generate_npc(NPCRole.VILLAGER, "Town")
        self.npc_system.add_npc_to_world(npc)
        
        # Initial relationship
        rel = self.npc_system.relationships[npc['id']]['player']
        self.assertEqual(rel['value'], 0)
        self.assertEqual(rel['level'], RelationshipLevel.NEUTRAL)
        
        # Modify relationship
        self.npc_system.modify_relationship(npc['id'], 'help')
        self.assertGreater(self.npc_system.relationships[npc['id']]['player']['value'], 0)
        
        # Negative interaction
        self.npc_system.modify_relationship(npc['id'], 'insult')
        self.assertLess(self.npc_system.relationships[npc['id']]['player']['value'], 5)
        
    def test_npc_trade(self):
        """Test NPC trading"""
        npc = self.npc_system.generate_npc(NPCRole.MERCHANT, "Market")
        self.npc_system.add_npc_to_world(npc)
        
        response = self.npc_system.interact(npc['id'], "trade", {})
        self.assertIsInstance(response, str)
        self.assertIn("Wares", response)
        
    def test_npc_gossip(self):
        """Test gossip generation"""
        npc = self.npc_system.generate_npc(NPCRole.INNKEEPER, "Tavern")
        self.npc_system.add_npc_to_world(npc)
        
        # Build relationship to increase gossip chance
        self.npc_system.modify_relationship(npc['id'], 'help')
        self.npc_system.modify_relationship(npc['id'], 'gift')
        
        response = self.npc_system.interact(npc['id'], "gossip", {})
        self.assertIsInstance(response, str)
        
    def test_schedule_updates(self):
        """Test NPC schedule updates"""
        npc = self.npc_system.generate_npc(NPCRole.VILLAGER, "Home")
        self.npc_system.add_npc_to_world(npc)
        
        # Update schedule for different hours
        initial_location = npc['location']
        
        self.npc_system.update_schedules(22)  # Night time
        self.assertNotEqual(npc['status'], NPCStatus.AVAILABLE)

class TestInventory(unittest.TestCase):
    """Test inventory system"""
    
    def setUp(self):
        self.player = {
            'name': 'TestPlayer',
            'inventory': [],
            'equipment': {},
            'gold': 100,
            'health': 50,
            'max_health': 100
        }
        self.inventory = InventorySystem(self.player)
        
    def test_add_item(self):
        """Test adding items to inventory"""
        # Add single item
        success = self.inventory.add_item('health_potion')
        self.assertTrue(success)
        self.assertEqual(len(self.player['inventory']), 1)
        
        # Add stackable item
        success = self.inventory.add_item('bread', 3)
        self.assertTrue(success)
        
        # Find the bread item (might be in inventory)
        bread_item = None
        for item in self.player['inventory']:
            if item['name'] == 'Bread':
                bread_item = item
                break
        
        self.assertIsNotNone(bread_item)
        self.assertEqual(bread_item.get('count', 1), 3)
        
    def test_remove_item(self):
        """Test removing items from inventory"""
        self.inventory.add_item('health_potion', 2)
        
        # Remove one
        success = self.inventory.remove_item('health_potion')
        self.assertTrue(success)
        
        # Check remaining
        remaining = self.inventory.get_item('health_potion')
        self.assertIsNotNone(remaining)
        self.assertEqual(remaining.get('count', 1), 1)
        
        # Remove last
        success = self.inventory.remove_item('health_potion')
        self.assertTrue(success)
        
        # Should be gone
        self.assertIsNone(self.inventory.get_item('health_potion'))
        
    def test_get_item(self):
        """Test getting items by name"""
        self.inventory.add_item('long_sword')
        
        # Exact match
        item = self.inventory.get_item('long_sword')
        self.assertIsNotNone(item)
        self.assertEqual(item['name'], 'Long Sword')
        
        # Partial match
        item = self.inventory.get_item('sword')
        self.assertIsNotNone(item)
        
        # Non-existent
        item = self.inventory.get_item('nonexistent')
        self.assertIsNone(item)
        
    def test_use_consumable(self):
        """Test using consumable items"""
        self.inventory.add_item('health_potion')
        initial_health = self.player['health']
        
        result = self.inventory.use_item('health_potion')
        self.assertIsInstance(result, str)
        self.assertGreater(self.player['health'], initial_health)
        
        # Item should be gone
        self.assertIsNone(self.inventory.get_item('health_potion'))
        
    def test_equip_item(self):
        """Test equipping items"""
        self.inventory.add_item('long_sword')
        
        # Equip
        result = self.inventory.use_item('long_sword')
        self.assertIsInstance(result, str)
        
        # Check equipped
        item = self.inventory.get_item('long_sword')
        self.assertTrue(item.get('equipped', False))
        self.assertIn(EquipmentSlot.MAIN_HAND.value, self.player['equipment'])
        
        # Unequip
        result = self.inventory.use_item('long_sword')
        self.assertFalse(item.get('equipped', False))
        self.assertNotIn(EquipmentSlot.MAIN_HAND.value, self.player['equipment'])
        
    def test_item_value(self):
        """Test item value calculation"""
        self.inventory.add_item('long_sword')
        item = self.inventory.get_item('long_sword')
        
        value = self.inventory.get_item_value(item)
        self.assertGreater(value, 0)
        
    def test_inventory_weight(self):
        """Test inventory weight calculation"""
        self.inventory.add_item('long_sword')
        self.inventory.add_item('chainmail')
        
        weight = self.inventory.get_total_weight()
        self.assertGreater(weight, 0)
        
    def test_inventory_display(self):
        """Test inventory display"""
        self.inventory.add_item('health_potion', 2)
        self.inventory.add_item('long_sword')
        
        display = self.inventory.display()
        self.assertIsInstance(display, str)
        self.assertIn('INVENTORY', display)
        
    def test_crafting(self):
        """Test crafting system"""
        # Add ingredients
        self.inventory.add_item('herbs', 2)
        self.inventory.add_item('water_flask', 1)
        
        # Display recipes
        display = self.inventory.display_crafting()
        self.assertIsInstance(display, str)
        
        # Craft
        result = self.inventory.craft_item('health potion')
        self.assertIsInstance(result, str)
        
        # Should have crafted item
        self.assertIsNotNone(self.inventory.get_item('health_potion'))

class TestSaveSystem(unittest.TestCase):
    """Test save/load system"""
    
    def setUp(self):
        # Create temporary directory for saves
        self.test_dir = tempfile.mkdtemp()
        self.save_system = SaveSystem(save_dir=self.test_dir)
        
        self.test_game_state = {
            'player': {
                'name': 'TestHero',
                'level': 5,
                'class': 'Warrior',
                'health': 80,
                'max_health': 100,
                'inventory': ['sword', 'shield'],
                'gold': 150
            },
            'current_location': 'tavern',
            'turn_count': 100,
            'version': '1.0.0'
        }
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_save_game(self):
        """Test saving game state"""
        success = self.save_system.save_game(self.test_game_state, "test_save")
        self.assertTrue(success)
        
        # Check files exist
        self.assertTrue((Path(self.test_dir) / "test_save.sav").exists())
        self.assertTrue((Path(self.test_dir) / "test_save.meta").exists())
        
    def test_load_game(self):
        """Test loading game state"""
        self.save_system.save_game(self.test_game_state, "test_save")
        
        loaded_state = self.save_system.load_game("test_save")
        self.assertIsNotNone(loaded_state)
        self.assertEqual(loaded_state['player']['name'], 'TestHero')
        self.assertEqual(loaded_state['player']['level'], 5)
        self.assertEqual(loaded_state['current_location'], 'tavern')
        
    def test_list_saves(self):
        """Test listing saves"""
        self.save_system.save_game(self.test_game_state, "save1")
        self.save_system.save_game(self.test_game_state, "save2")
        
        saves = self.save_system.list_saves()
        self.assertEqual(len(saves), 2)
        self.assertIn('save1', saves)
        self.assertIn('save2', saves)
        
    def test_get_save_info(self):
        """Test getting save information"""
        self.save_system.save_game(self.test_game_state, "test_save")
        
        info = self.save_system.get_save_info("test_save")
        self.assertIsNotNone(info)
        self.assertEqual(info['player_name'], 'TestHero')
        self.assertEqual(info['player_level'], 5)
        
    def test_delete_save(self):
        """Test deleting save"""
        self.save_system.save_game(self.test_game_state, "test_save")
        self.assertTrue((Path(self.test_dir) / "test_save.sav").exists())
        
        success = self.save_system.delete_save("test_save")
        self.assertTrue(success)
        self.assertFalse((Path(self.test_dir) / "test_save.sav").exists())
        
    def test_rename_save(self):
        """Test renaming save"""
        self.save_system.save_game(self.test_game_state, "old_name")
        
        success = self.save_system.rename_save("old_name", "new_name")
        self.assertTrue(success)
        
        self.assertFalse((Path(self.test_dir) / "old_name.sav").exists())
        self.assertTrue((Path(self.test_dir) / "new_name.sav").exists())
        
    def test_backup_system(self):
        """Test backup creation and recovery"""
        self.save_system.save_game(self.test_game_state, "test_save")
        
        # Create backup
        success = self.save_system.create_backup("test_save")
        self.assertTrue(success)
        
        # Corrupt the save file
        save_path = Path(self.test_dir) / "test_save.sav"
        with open(save_path, 'wb') as f:
            f.write(b'corrupted data')
        
        # Try to load (should attempt recovery)
        loaded = self.save_system.load_game("test_save")
        
        # May or may not recover, but shouldn't crash
        self.assertIsNotNone(loaded) or self.assertIsNone(loaded)
        
    def test_quick_save_load(self):
        """Test quick save/load functionality"""
        success = self.save_system.quick_save(self.test_game_state)
        self.assertTrue(success)
        
        loaded = self.save_system.quick_load()
        self.assertIsNotNone(loaded)
        
    def test_save_exists(self):
        """Test checking if save exists"""
        self.assertFalse(self.save_system.save_exists("nonexistent"))
        
        self.save_system.save_game(self.test_game_state, "test_save")
        self.assertTrue(self.save_system.save_exists("test_save"))
        
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        dirty_name = "My/Save:File?*"
        clean = self.save_system.sanitize_filename(dirty_name)
        self.assertNotIn('/', clean)
        self.assertNotIn(':', clean)
        self.assertNotIn('?', clean)
        self.assertNotIn('*', clean)
        
    def test_save_statistics(self):
        """Test save statistics generation"""
        self.save_system.save_game(self.test_game_state, "save1")
        self.save_system.save_game(self.test_game_state, "save2")
        
        stats = self.save_system.get_save_statistics()
        self.assertEqual(stats['total_saves'], 2)
        self.assertGreater(stats['total_size'], 0)
        
        display = self.save_system.display_save_stats()
        self.assertIsInstance(display, str)
        self.assertIn('SAVE STATISTICS', display)

class TestIntegration(unittest.TestCase):
    """Integration tests for game systems working together"""
    
    def setUp(self):
        self.player = {
            'name': 'TestHero',
            'class': 'Warrior',
            'level': 1,
            'health': 100,
            'max_health': 100,
            'mana': 50,
            'max_mana': 50,
            'strength': 10,
            'defense': 5,
            'inventory': [],
            'equipment': {},
            'gold': 50
        }
        self.game_flags = {'reputation': {}}
        
        # Initialize all systems
        self.npc_system = NPCSystem(self.player, self.game_flags)
        self.quest_manager = QuestManager(self.player, self.game_flags)
        self.inventory = InventorySystem(self.player)
        self.combat = CombatSystem(self.player)
        
        # Generate a simple world
        self.world_gen = WorldGenerator(seed=42)
        self.world_data = self.world_gen.generate_world(size='small')
        self.world = WorldManager(self.world_data)
        
    def test_npc_quest_interaction(self):
        """Test NPC giving quest to player"""
        # Create quest giver NPC
        npc = self.npc_system.generate_npc(
            role=NPCRole.QUEST_GIVER,
            location="town_square"
        )
        self.npc_system.add_npc_to_world(npc)
        
        # Generate quest for NPC
        quest = self.quest_manager.generate_quest(
            giver_name=npc['name'],
            location=npc['location']
        )
        
        # NPC offers quest
        dialogue = self.quest_manager.offer_quest(quest, npc['name'])
        self.assertIsInstance(dialogue, str)
        
        # Player accepts
        success = self.quest_manager.accept_quest(quest['id'])
        self.assertTrue(success)
        
        # Complete quest objective (simulated)
        if quest['objectives'][0]['type'] == 'kill':
            completions = self.quest_manager.update_quest_progress(
                'kill', 
                quest['objectives'][0]['target'],
                quest['objectives'][0]['count']
            )
            
        elif quest['objectives'][0]['type'] == 'collect':
            # Add items to inventory
            for _ in range(quest['objectives'][0]['count']):
                self.inventory.add_item('goblin_ear')
            
            completions = self.quest_manager.update_quest_progress(
                'collect',
                quest['objectives'][0]['item'],
                quest['objectives'][0]['count']
            )
        
        # Turn in quest
        if quest['status'] == QuestStatus.COMPLETED:
            reward = self.quest_manager.turn_in_quest(quest['id'], npc['name'])
            self.assertIsInstance(reward, str)
            
    def test_combat_loot_inventory(self):
        """Test combat rewards affecting inventory"""
        # Start combat
        self.combat.start_combat('goblin')
        
        # Kill enemy
        self.combat.enemy.health = 0
        victory = self.combat.process_victory()
        
        # Should have received gold and possibly items
        self.assertGreater(self.player['gold'], 50)
        
    def test_npc_trade_inventory(self):
        """Test NPC trading affecting inventory"""
        # Create merchant
        merchant = self.npc_system.generate_npc(
            role=NPCRole.MERCHANT,
            location="market"
        )
        self.npc_system.add_npc_to_world(merchant)
        
        # Initial gold
        initial_gold = self.player['gold']
        
        # Trade interaction (simulated)
        trade_menu = self.npc_system.interact(merchant['id'], "trade", {})
        self.assertIn("Wares", trade_menu)
        
    def test_quest_rewards_inventory(self):
        """Test quest rewards adding to inventory"""
        # Create and complete quest
        quest = self.quest_manager.generate_quest(
            giver_name="TestGiver",
            location="TestLocation"
        )
        
        # Force completion
        quest['status'] = QuestStatus.COMPLETED
        
        initial_inventory_size = len(self.player['inventory'])
        
        # Turn in
        self.quest_manager.turn_in_quest(quest['id'], "TestGiver")
        
        # Should have received items
        self.assertGreaterEqual(len(self.player['inventory']), initial_inventory_size)
        
    def test_item_use_in_combat(self):
        """Test using items during combat"""
        # Add healing potion
        self.inventory.add_item('health_potion')
        
        # Start combat
        self.combat.start_combat('goblin')
        
        # Take some damage
        self.player['health'] = 50
        
        # Use item during combat (simulated)
        result = self.inventory.use_item('health_potion')
        
        # Health should be restored
        self.assertGreater(self.player['health'], 50)
        
    def test_full_game_loop(self):
        """Test a complete game loop with multiple systems"""
        
        # 1. Player starts in town
        start_location = self.world.current_location
        self.assertIsNotNone(start_location)
        
        # 2. Talk to NPC
        npcs = self.npc_system.get_npcs_at_location(start_location)
        if npcs:
            npc = npcs[0]
            response = self.npc_system.interact(npc['id'], "hello", {})
            self.assertIsInstance(response, str)
        
        # 3. Get quest
        quest = self.quest_manager.generate_quest(
            giver_name="Elder",
            location=start_location
        )
        self.quest_manager.accept_quest(quest['id'])
        
        # 4. Travel to another location
        current = self.world.get_current_location()
        exits = [d for d, t in current['exits'].items() if t]
        if exits:
            success, _ = self.world.move(exits[0])
            self.assertTrue(success)
        
        # 5. Encounter combat (simulated)
        self.combat.start_combat('goblin')
        self.combat.enemy.health = 0
        victory = self.combat.process_victory()
        self.assertIn('VICTORY', victory)
        
        # 6. Complete quest
        for objective in quest['objectives']:
            if objective['type'] == 'kill':
                self.quest_manager.update_quest_progress(
                    'kill',
                    objective['target'],
                    objective['count']
                )
        
        # 7. Return and turn in
        if quest['status'] == QuestStatus.COMPLETED:
            reward = self.quest_manager.turn_in_quest(quest['id'], "Elder")
            self.assertIsInstance(reward, str)
        
        # 8. Save game
        game_state = {
            'player': self.player,
            'world': self.world_data,
            'current_location': self.world.current_location,
            'turn_count': 100
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            save_system = SaveSystem(save_dir=tmpdir)
            success = save_system.save_game(game_state, "integration_test")
            self.assertTrue(success)

if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestUtils))
    suite.addTest(unittest.makeSuite(TestWorld))
    suite.addTest(unittest.makeSuite(TestAIEngine))
    suite.addTest(unittest.makeSuite(TestCombat))
    suite.addTest(unittest.makeSuite(TestQuests))
    suite.addTest(unittest.makeSuite(TestNPC))
    suite.addTest(unittest.makeSuite(TestInventory))
    suite.addTest(unittest.makeSuite(TestSaveSystem))
    suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(not result.wasSuccessful())