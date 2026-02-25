# 🎮 AI Text Adventure

## 🎯 **Overview**

AI Text Adventure Game is a sophisticated, Python-based interactive fiction game that combines **procedural generation**, **artificial intelligence**, and **complex game systems** to create a unique adventure every time you play. Unlike traditional text adventures, , this game features:

- **Intelligent NPCs** with dynamic personalities and relationship systems
- **Procedurally generated worlds** that are different each playthrough
- **Turn-based combat** with special abilities and status effects
- **Dynamic quest system** that creates unique missions on-the-fly
- **Persistent save system** with encryption and automatic backups

---

## ✨ **Features**

### 🎨 **Core Game Systems**

| System | Description | Key Features |
|--------|-------------|--------------|
| **World Generation** | Procedurally creates unique game worlds | 10+ location types, interconnected maps, random encounters |
| **AI Engine** | Powers NPC conversations and responses | Natural language processing, emotion detection, context awareness |
| **Combat System** | Turn-based battles with tactical depth | 15+ enemy types, special abilities, status effects, damage types |
| **Quest System** | Dynamic mission generation | 7 quest types, procedural objectives, reward scaling, chain quests |
| **NPC System** | Living characters with personalities | 8 personality types, relationship tracking, daily schedules, memories |
| **Inventory** | Comprehensive item management | 50+ items, equipment slots, crafting, stackable items |
| **Save System** | Secure progress persistence | Encryption, compression, automatic backups, cloud-ready |

### 🤖 **AI Capabilities**

- **Natural Language Understanding**: NPCs understand and respond to player input contextually
- **Emotional Intelligence**: Characters react to player's emotional state
- **Relationship Memory**: NPCs remember past interactions and adjust behavior
- **Dynamic Dialogue**: Thousands of unique conversation combinations
- **Rumor Generation**: NPCs share procedurally generated gossip about the world

### 🎪 **Procedural Generation**

Every new game creates:
- **Unique world map** with interconnected locations
- **Distinct NPCs** with names, personalities, and schedules
- **Original quests** with custom objectives and rewards
- **Random encounters** scaled to player level
- **Dynamic loot** from defeated enemies

### 💾 **Save System Features**

- **Encrypted save files** for security
- **Automatic compression** to save space
- **Version tracking** for compatibility
- **Automatic backups** (keeps last 5 versions)
- **Corruption detection** with checksums
- **Recovery tools** for corrupted saves
- **Quick save/load** (F5/F9)
- **Auto-save** every 5 minutes

---

## 🚀 **Quick Start**

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ai-text-adventure.git
cd ai-text-adventure

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up the data directory
python scripts/setup_data.py

# 4. Start the game!
python play.py

```

### Basic Commands

| Category    | Commands                                      | Description            |
|------------|-----------------------------------------------|------------------------|
| Movement   | go north, go south, go east, go west         | Move between locations |
| Interaction| look, talk [name], take [item], use [item]   | Interact with world    |
| Combat     | attack, defend, flee, use [item]             | Combat actions         |
| Inventory  | inventory, equip [item], drop [item]         | Manage items           |
| Quests     | quests, journal, complete [quest]            | Track progress         |
| System     | save [name], load [name], help, quit         | Game management        |

### Example Gameplay

```
📍 [Town Square]
════════════════════════════════════════════════════════════
A bustling town square with a fountain in the center. 
Merchants call out their wares from colorful stalls.

🚪 Exits: north, south, east, west
👥 People: Greta (innkeeper), Marcus (elder), Thorin (blacksmith)
📦 Items: map, water_skin

📍 [Town Square] > talk greta

🗣️ Greta: "Welcome to my inn, traveler! Can I get you a room for the night?
        10 gold gets you a warm bed and a hot meal."

📍 [Town Square] > take map
You take the map.

📍 [Town Square] > go north

📍 [Market District]
════════════════════════════════════════════════════════════
Colorful stalls line the streets. The smell of exotic spices 
fills the air. Merchants haggle with customers.

🚪 Exits: south, blacksmith
👥 People: merchant, butcher, baker
📦 Items: potion, bread, cheese
```

---

## 🏗️ Architecture

### Project Structure

```
ai-text-adventure/
├── game/                      # Core game modules
│   ├── __init__.py
│   ├── main.py                # Main game loop
│   ├── world.py               # Procedural world generation
│   ├── ai_engine.py           # AI response system
│   ├── combat.py              # Combat mechanics
│   ├── quests.py              # Quest system
│   ├── npc.py                 # NPC management
│   ├── inventory.py           # Item system
│   ├── save_system.py         # Save/load functionality
│   └── utils.py               # Helper functions
│
├── tests/                      # Test suite
│   └── test_game.py           # 67+ unit tests
│
├── data/                        # Game data
│   ├── saves/                  # Player saves (auto-generated)
│   ├── config/                  # Configuration files
│   │   ├── settings.json
│   │   ├── keybindings.json
│   │   └── game_config.json
│   ├── logs/                    # Game logs (auto-generated)
├── scripts/                      # Utility scripts
│   ├── setup_data.py
├── requirements.txt
├── README.md
├── LICENSE
└── play.py                       # Entry point
```

---

## System Architecture Diagram

<div class="mermaid">
graph TD
    A[Main Game Loop] --> B[World Manager]
    A --> C[Combat System]
    A --> D[Quest Manager]
    A --> E[NPC System]
    A --> F[Inventory System]
    A --> G[Save System]
    
    E --> H[AI Engine]
    E --> I[Relationship Tracker]
    
    D --> J[Quest Generator]
    D --> K[Reward Calculator]
    
    F --> L[Item Database]
    F --> M[Crafting System]
    
    G --> N[Encryption]
    G --> O[Compression]
    G --> P[Backup Manager]
    
    B --> Q[Location Generator]
    B --> R[Encounter System]

    %% Styling
    classDef main fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef world fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef combat fill:#ffebee,stroke:#b71c1c,stroke-width:2px
    classDef quest fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef npc fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef inventory fill:#e0f2f1,stroke:#004d40,stroke-width:2px
    classDef save fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef ai fill:#fff8e1,stroke:#ff6f00,stroke-width:2px

    class A main
    class B,Q,R world
    class C combat
    class D,J,K quest
    class E,H,I npc
    class F,L,M inventory
    class G,N,O,P save
    class H,I ai
</div>

<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>
    mermaid.initialize({ startOnLoad: true });
</script>

---

## 📊 Performance

Memory usage: ~50-100 MB during normal gameplay

Save file size: 10-50 KB compressed

World generation: < 1 second for medium worlds

AI response time: < 100ms

Combat calculations: < 10ms per turn

---

## Acknowledgments

Inspired by classic text adventures like Zork and Adventure

NPC personalities based on The Sims relationship system

Combat system inspired by classic RPGs like Final Fantasy

Quest system influenced by The Elder Scrolls series

---
