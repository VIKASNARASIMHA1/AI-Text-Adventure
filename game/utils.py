import random
import json
import yaml
from datetime import datetime
from colorama import Fore, Style, init
from typing import List, Dict, Any, Optional

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class Colors:
    """Color constants for terminal output"""
    HEADER = Fore.MAGENTA
    INFO = Fore.CYAN
    SUCCESS = Fore.GREEN
    WARNING = Fore.YELLOW
    ERROR = Fore.RED
    COMBAT = Fore.RED
    DIALOGUE = Fore.YELLOW
    LOCATION = Fore.BLUE
    ITEM = Fore.GREEN
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT

class TextFormatter:
    """Format text with colors and effects"""
    
    @staticmethod
    def header(text: str) -> str:
        return f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.RESET}"
    
    @staticmethod
    def info(text: str) -> str:
        return f"{Colors.INFO}{text}{Colors.RESET}"
    
    @staticmethod
    def success(text: str) -> str:
        return f"{Colors.SUCCESS}{text}{Colors.RESET}"
    
    @staticmethod
    def warning(text: str) -> str:
        return f"{Colors.WARNING}{text}{Colors.RESET}"
    
    @staticmethod
    def error(text: str) -> str:
        return f"{Colors.ERROR}{text}{Colors.RESET}"
    
    @staticmethod
    def combat(text: str) -> str:
        return f"{Colors.COMBAT}{text}{Colors.RESET}"
    
    @staticmethod
    def dialogue(text: str, speaker: str = "") -> str:
        if speaker:
            return f"{Colors.DIALOGUE}{speaker}: \"{text}\"{Colors.RESET}"
        return f"{Colors.DIALOGUE}{text}{Colors.RESET}"
    
    @staticmethod
    def location(text: str) -> str:
        return f"{Colors.LOCATION}{Colors.BOLD}{text}{Colors.RESET}"
    
    @staticmethod
    def item(text: str) -> str:
        return f"{Colors.ITEM}{text}{Colors.RESET}"
    
    @staticmethod
    def divider(char: str = "=", length: int = 60) -> str:
        return char * length

class Dice:
    """Dice rolling system"""
    
    @staticmethod
    def roll(dice_str: str) -> int:
        """
        Roll dice in format like "2d6+3"
        """
        import re
        pattern = r'(\d*)d(\d+)([+-]\d+)?'
        match = re.match(pattern, dice_str)
        
        if not match:
            return 0
        
        num_dice = int(match.group(1)) if match.group(1) else 1
        die_type = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0
        
        total = sum(random.randint(1, die_type) for _ in range(num_dice))
        return total + modifier
    
    @staticmethod
    def d20() -> int:
        return random.randint(1, 20)
    
    @staticmethod
    def d100() -> int:
        return random.randint(1, 100)

class GameLogger:
    """Log game events for debugging and replay"""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.events = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def log(self, event_type: str, data: Any):
        if not self.enabled:
            return
        
        self.events.append({
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        })
    
    def save(self, filename: Optional[str] = None):
        if not self.events:
            return
        
        if not filename:
            filename = f"game_log_{self.session_id}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.events, f, indent=2)