"""
Save system for AI Text Adventure Game
Handles saving, loading, compression, encryption, and save game management
"""

import os
import json
import zlib
import base64
import pickle
import shutil
import hashlib
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import threading
from collections import OrderedDict

from .utils import TextFormatter, Colors

class SaveSystem:
    """
    Main save game management system
    Handles saving/loading with compression, encryption, and backup
    """
    
    def __init__(self, save_dir: str = "data/saves"):
        self.save_dir = Path(save_dir)
        self.backup_dir = self.save_dir / "backups"
        self.temp_dir = self.save_dir / "temp"
        
        # Create directories
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Save settings
        self.max_saves = 10  # Maximum number of saves to keep
        self.max_backups = 5  # Maximum number of backups per save
        self.compress_saves = True
        self.encrypt_saves = False  # Set to True to enable encryption
        self.auto_save_interval = 300  # Auto-save every 5 minutes
        self.auto_save_enabled = True
        
        # Encryption key (in production, use environment variables)
        self.encryption_key = self.get_encryption_key()
        
        # Save metadata
        self.save_metadata = self.load_metadata()
        self.current_save = None
        
        # Auto-save thread
        self.auto_save_thread = None
        self.auto_save_running = False
        
    def get_encryption_key(self) -> bytes:
        """Get encryption key (from environment or generate)"""
        # In production, get from environment variable
        # key = os.environ.get('GAME_ENCRYPTION_KEY')
        # if key:
        #     return key.encode()
        
        # For development, use a fixed key (DO NOT use in production!)
        return b'your-secret-key-here-change-in-production'
    
    def simple_encrypt(self, data: bytes) -> bytes:
        """Simple XOR encryption (for demonstration)"""
        if not self.encrypt_saves:
            return data
        
        key = self.encryption_key
        encrypted = bytearray()
        for i, byte in enumerate(data):
            encrypted.append(byte ^ key[i % len(key)])
        return bytes(encrypted)
    
    def simple_decrypt(self, data: bytes) -> bytes:
        """Simple XOR decryption (for demonstration)"""
        return self.simple_encrypt(data)  # XOR is symmetric
    
    def compress_data(self, data: bytes) -> bytes:
        """Compress data using zlib"""
        if not self.compress_saves:
            return data
        return zlib.compress(data, level=9)
    
    def decompress_data(self, data: bytes) -> bytes:
        """Decompress data using zlib"""
        if not self.compress_saves:
            return data
        return zlib.decompress(data)
    
    def serialize_game_state(self, game_state: Dict) -> bytes:
        """Serialize game state to bytes"""
        try:
            # Convert to JSON string
            json_str = json.dumps(game_state, indent=None, separators=(',', ':'))
            return json_str.encode('utf-8')
        except Exception as e:
            print(f"Serialization error: {e}")
            # Fallback to pickle
            return pickle.dumps(game_state)
    
    def deserialize_game_state(self, data: bytes) -> Dict:
        """Deserialize game state from bytes"""
        try:
            # Try JSON first
            json_str = data.decode('utf-8')
            return json.loads(json_str)
        except:
            try:
                # Fallback to pickle
                return pickle.loads(data)
            except Exception as e:
                print(f"Deserialization error: {e}")
                return {}
    
    def calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA-256 checksum of data"""
        return hashlib.sha256(data).hexdigest()
    
    def verify_checksum(self, data: bytes, checksum: str) -> bool:
        """Verify data integrity"""
        return self.calculate_checksum(data) == checksum
    
    def save_game(self, game_state: Dict, save_name: str = None) -> bool:
        """
        Save game state to file
        Returns True if successful
        """
        
        if not save_name:
            # Generate save name based on timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_name = f"save_{timestamp}"
        
        # Ensure save name is valid
        save_name = self.sanitize_filename(save_name)
        save_path = self.save_dir / f"{save_name}.sav"
        meta_path = self.save_dir / f"{save_name}.meta"
        
        try:
            # Add metadata
            metadata = {
                'save_name': save_name,
                'timestamp': datetime.now().isoformat(),
                'player_name': game_state.get('player', {}).get('name', 'Unknown'),
                'player_level': game_state.get('player', {}).get('level', 1),
                'player_class': game_state.get('player', {}).get('class', 'Unknown'),
                'location': game_state.get('current_location', 'Unknown'),
                'play_time': game_state.get('turn_count', 0),
                'game_version': game_state.get('version', '1.0.0'),
                'checksum': None  # Will be set after serialization
            }
            
            # Serialize and compress
            serialized = self.serialize_game_state(game_state)
            compressed = self.compress_data(serialized)
            encrypted = self.simple_encrypt(compressed)
            
            # Calculate checksum
            checksum = self.calculate_checksum(encrypted)
            metadata['checksum'] = checksum
            
            # Save game data
            with open(save_path, 'wb') as f:
                f.write(encrypted)
            
            # Save metadata
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update metadata cache
            self.save_metadata[save_name] = metadata
            
            # Create backup
            self.create_backup(save_name)
            
            # Cleanup old saves
            self.cleanup_old_saves()
            
            print(f"💾 Game saved as '{save_name}'")
            return True
            
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def load_game(self, save_name: str) -> Optional[Dict]:
        """
        Load game state from file
        Returns game state dict or None if failed
        """
        
        save_path = self.save_dir / f"{save_name}.sav"
        meta_path = self.save_dir / f"{save_name}.meta"
        
        if not save_path.exists():
            print(f"Save file '{save_name}' not found.")
            return None
        
        try:
            # Load metadata
            metadata = {}
            if meta_path.exists():
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)
            
            # Load game data
            with open(save_path, 'rb') as f:
                encrypted = f.read()
            
            # Verify checksum
            if metadata.get('checksum'):
                if not self.verify_checksum(encrypted, metadata['checksum']):
                    print("Warning: Save file may be corrupted!")
                    response = input("Continue anyway? (y/n): ")
                    if response.lower() != 'y':
                        return None
            
            # Decrypt, decompress, deserialize
            compressed = self.simple_decrypt(encrypted)
            serialized = self.decompress_data(compressed)
            game_state = self.deserialize_game_state(serialized)
            
            # Add load time
            game_state['loaded_time'] = datetime.now().isoformat()
            
            self.current_save = save_name
            print(f"✅ Loaded game: {save_name}")
            
            return game_state
            
        except Exception as e:
            print(f"Error loading game: {e}")
            
            # Try to recover from backup
            print("Attempting to recover from backup...")
            return self.recover_from_backup(save_name)
    
    def create_backup(self, save_name: str) -> bool:
        """Create a backup of a save file"""
        
        save_path = self.save_dir / f"{save_name}.sav"
        meta_path = self.save_dir / f"{save_name}.meta"
        
        if not save_path.exists():
            return False
        
        # Create backup directory for this save
        backup_subdir = self.backup_dir / save_name
        backup_subdir.mkdir(exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_save = backup_subdir / f"{timestamp}.sav"
        backup_meta = backup_subdir / f"{timestamp}.meta"
        
        try:
            # Copy files
            shutil.copy2(save_path, backup_save)
            if meta_path.exists():
                shutil.copy2(meta_path, backup_meta)
            
            # Cleanup old backups
            self.cleanup_old_backups(save_name)
            
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def recover_from_backup(self, save_name: str) -> Optional[Dict]:
        """Recover a save from its latest backup"""
        
        backup_subdir = self.backup_dir / save_name
        
        if not backup_subdir.exists():
            print(f"No backups found for '{save_name}'.")
            return None
        
        # Get all backups
        backups = sorted(backup_subdir.glob("*.sav"))
        if not backups:
            print(f"No backup files found for '{save_name}'.")
            return None
        
        # Try each backup in reverse order (newest first)
        for backup_path in reversed(backups):
            try:
                print(f"Trying backup: {backup_path.name}")
                
                # Get corresponding metadata
                meta_path = backup_path.with_suffix('.meta')
                
                # Load data
                with open(backup_path, 'rb') as f:
                    encrypted = f.read()
                
                compressed = self.simple_decrypt(encrypted)
                serialized = self.decompress_data(compressed)
                game_state = self.deserialize_game_state(serialized)
                
                print(f"✅ Successfully recovered from backup!")
                
                # Restore this backup as the main save
                shutil.copy2(backup_path, self.save_dir / f"{save_name}.sav")
                if meta_path.exists():
                    shutil.copy2(meta_path, self.save_dir / f"{save_name}.meta")
                
                return game_state
                
            except Exception as e:
                print(f"Backup {backup_path.name} failed: {e}")
                continue
        
        print(f"Could not recover '{save_name}' from any backup.")
        return None
    
    def list_saves(self) -> List[str]:
        """List all available saves"""
        
        saves = []
        for file in self.save_dir.glob("*.sav"):
            save_name = file.stem
            # Check if metadata exists
            meta_path = file.with_suffix('.meta')
            if meta_path.exists():
                saves.append(save_name)
        
        return sorted(saves, reverse=True)  # Newest first
    
    def get_save_info(self, save_name: str) -> Optional[Dict]:
        """Get detailed information about a save"""
        
        meta_path = self.save_dir / f"{save_name}.meta"
        
        if not meta_path.exists():
            return None
        
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            # Add file info
            save_path = self.save_dir / f"{save_name}.sav"
            if save_path.exists():
                metadata['file_size'] = save_path.stat().st_size
                metadata['modified'] = datetime.fromtimestamp(
                    save_path.stat().st_mtime
                ).isoformat()
            
            return metadata
            
        except Exception:
            return None
    
    def delete_save(self, save_name: str) -> bool:
        """Delete a save file and its backups"""
        
        # Delete main save
        save_path = self.save_dir / f"{save_name}.sav"
        meta_path = self.save_dir / f"{save_name}.meta"
        
        try:
            if save_path.exists():
                save_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
            
            # Delete backups
            backup_subdir = self.backup_dir / save_name
            if backup_subdir.exists():
                shutil.rmtree(backup_subdir)
            
            # Remove from metadata cache
            if save_name in self.save_metadata:
                del self.save_metadata[save_name]
            
            print(f"🗑️ Deleted save: {save_name}")
            return True
            
        except Exception as e:
            print(f"Error deleting save: {e}")
            return False
    
    def rename_save(self, old_name: str, new_name: str) -> bool:
        """Rename a save file"""
        
        new_name = self.sanitize_filename(new_name)
        
        if new_name == old_name:
            return True
        
        if self.save_exists(new_name):
            print(f"Save '{new_name}' already exists.")
            return False
        
        try:
            # Rename files
            for ext in ['.sav', '.meta']:
                old_path = self.save_dir / f"{old_name}{ext}"
                new_path = self.save_dir / f"{new_name}{ext}"
                if old_path.exists():
                    old_path.rename(new_path)
            
            # Update metadata cache
            if old_name in self.save_metadata:
                metadata = self.save_metadata.pop(old_name)
                metadata['save_name'] = new_name
                self.save_metadata[new_name] = metadata
            
            print(f"📝 Renamed '{old_name}' to '{new_name}'")
            return True
            
        except Exception as e:
            print(f"Error renaming save: {e}")
            return False
    
    def save_exists(self, save_name: str) -> bool:
        """Check if a save exists"""
        return (self.save_dir / f"{save_name}.sav").exists()
    
    def sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename"""
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        return filename[:50]  # Limit length
    
    def load_metadata(self) -> Dict:
        """Load metadata for all saves"""
        
        metadata = {}
        
        for meta_path in self.save_dir.glob("*.meta"):
            try:
                with open(meta_path, 'r') as f:
                    data = json.load(f)
                    save_name = data.get('save_name', meta_path.stem)
                    metadata[save_name] = data
            except Exception:
                continue
        
        return metadata
    
    def cleanup_old_saves(self):
        """Delete old saves if exceeding max_saves"""
        
        saves = self.list_saves()
        
        if len(saves) <= self.max_saves:
            return
        
        # Sort by modification time
        saves_with_time = []
        for save in saves:
            save_path = self.save_dir / f"{save}.sav"
            if save_path.exists():
                mtime = save_path.stat().st_mtime
                saves_with_time.append((mtime, save))
        
        saves_with_time.sort()  # Oldest first
        
        # Delete oldest saves
        to_delete = len(saves) - self.max_saves
        for i in range(to_delete):
            if i < len(saves_with_time):
                save_name = saves_with_time[i][1]
                print(f"Auto-cleaning old save: {save_name}")
                self.delete_save(save_name)
    
    def cleanup_old_backups(self, save_name: str):
        """Delete old backups for a specific save"""
        
        backup_subdir = self.backup_dir / save_name
        
        if not backup_subdir.exists():
            return
        
        # Get all backup files
        backups = sorted(backup_subdir.glob("*.sav"))
        
        if len(backups) <= self.max_backups:
            return
        
        # Delete oldest backups
        to_delete = len(backups) - self.max_backups
        for backup_path in backups[:to_delete]:
            try:
                backup_path.unlink()
                # Try to delete corresponding metadata
                meta_path = backup_path.with_suffix('.meta')
                if meta_path.exists():
                    meta_path.unlink()
            except Exception:
                continue
    
    def export_save(self, save_name: str, export_path: str) -> bool:
        """Export a save to an external file"""
        
        save_path = self.save_dir / f"{save_name}.sav"
        meta_path = self.save_dir / f"{save_name}.meta"
        
        if not save_path.exists():
            return False
        
        export_dir = Path(export_path)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Copy files
            shutil.copy2(save_path, export_dir / f"{save_name}.sav")
            if meta_path.exists():
                shutil.copy2(meta_path, export_dir / f"{save_name}.meta")
            
            print(f"📤 Exported save to {export_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting save: {e}")
            return False
    
    def import_save(self, import_path: str) -> bool:
        """Import a save from an external file"""
        
        import_path = Path(import_path)
        
        if not import_path.exists():
            print(f"File not found: {import_path}")
            return False
        
        # Extract save name from filename
        save_name = import_path.stem
        
        # Check if save already exists
        if self.save_exists(save_name):
            response = input(f"Save '{save_name}' already exists. Overwrite? (y/n): ")
            if response.lower() != 'y':
                return False
        
        try:
            # Copy file
            dest_path = self.save_dir / f"{save_name}.sav"
            shutil.copy2(import_path, dest_path)
            
            # Try to import metadata if exists
            meta_path = import_path.with_suffix('.meta')
            if meta_path.exists():
                shutil.copy2(meta_path, self.save_dir / f"{save_name}.meta")
            
            print(f"📥 Imported save: {save_name}")
            return True
            
        except Exception as e:
            print(f"Error importing save: {e}")
            return False
    
    def create_checkpoint(self, game_state: Dict) -> str:
        """Create a temporary checkpoint (for quick save/load)"""
        
        checkpoint_name = f"checkpoint_{int(time.time())}"
        
        if self.save_game(game_state, checkpoint_name):
            return checkpoint_name
        
        return None
    
    def quick_save(self, game_state: Dict) -> bool:
        """Quick save to a fixed slot"""
        return self.save_game(game_state, "quicksave")
    
    def quick_load(self) -> Optional[Dict]:
        """Quick load from quicksave"""
        return self.load_game("quicksave")
    
    def start_auto_save(self, game_state_provider):
        """Start auto-save thread"""
        
        if self.auto_save_running:
            return
        
        self.auto_save_running = True
        
        def auto_save_loop():
            while self.auto_save_running:
                time.sleep(self.auto_save_interval)
                if self.auto_save_enabled:
                    try:
                        game_state = game_state_provider()
                        self.save_game(game_state, "autosave")
                        print(f"\n{Colors.INFO}💾 Auto-saved{Colors.RESET}")
                    except Exception as e:
                        print(f"Auto-save error: {e}")
        
        self.auto_save_thread = threading.Thread(target=auto_save_loop, daemon=True)
        self.auto_save_thread.start()
    
    def stop_auto_save(self):
        """Stop auto-save thread"""
        self.auto_save_running = False
    
    def get_save_preview(self, save_name: str) -> str:
        """Get a preview of save content"""
        
        info = self.get_save_info(save_name)
        
        if not info:
            return f"Save '{save_name}' not found."
        
        preview = f"""
{TextFormatter.header('💾 SAVE PREVIEW')}
{TextFormatter.divider()}

{Colors.BOLD}Name:{Colors.RESET} {save_name}
{Colors.BOLD}Player:{Colors.RESET} {info.get('player_name', 'Unknown')} (Level {info.get('player_level', 1)} {info.get('player_class', 'Unknown')})
{Colors.BOLD}Location:{Colors.RESET} {info.get('location', 'Unknown')}
{Colors.BOLD}Play Time:{Colors.RESET} {info.get('play_time', 0)} turns
{Colors.BOLD}Saved:{Colors.RESET} {self.format_timestamp(info.get('timestamp', ''))}
{Colors.BOLD}File Size:{Colors.RESET} {self.format_file_size(info.get('file_size', 0))}
"""
        return preview
    
    def format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "Unknown"
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def compare_saves(self, save1: str, save2: str) -> str:
        """Compare two saves and show differences"""
        
        info1 = self.get_save_info(save1)
        info2 = self.get_save_info(save2)
        
        if not info1 or not info2:
            return "Cannot compare: one or both saves not found."
        
        comparison = f"""
{TextFormatter.header('📊 SAVE COMPARISON')}
{TextFormatter.divider()}

{'Attribute':20} | {'Save 1':25} | {'Save 2':25}
{'-'*70}

Player     : {info1.get('player_name', 'Unknown'):<23} | {info2.get('player_name', 'Unknown'):<23}
Level      : {str(info1.get('player_level', 1)):<23} | {str(info2.get('player_level', 1)):<23}
Class      : {info1.get('player_class', 'Unknown'):<23} | {info2.get('player_class', 'Unknown'):<23}
Location   : {info1.get('location', 'Unknown'):<23} | {info2.get('location', 'Unknown'):<23}
Play Time  : {str(info1.get('play_time', 0)):<23} | {str(info2.get('play_time', 0)):<23}
Saved      : {self.format_timestamp(info1.get('timestamp', '')):<23} | {self.format_timestamp(info2.get('timestamp', '')):<23}
"""
        
        return comparison
    
    def repair_save(self, save_name: str) -> bool:
        """Attempt to repair a corrupted save file"""
        
        print(f"🔧 Attempting to repair save: {save_name}")
        
        # Try to recover from backup first
        recovered = self.recover_from_backup(save_name)
        if recovered:
            print("✅ Save repaired from backup!")
            return True
        
        # Try to fix metadata
        meta_path = self.save_dir / f"{save_name}.meta"
        save_path = self.save_dir / f"{save_name}.sav"
        
        if not save_path.exists():
            print("❌ Save file not found.")
            return False
        
        try:
            # Attempt to read the save file directly
            with open(save_path, 'rb') as f:
                data = f.read()
            
            # Try different decryption/decompression combinations
            attempts = [
                (True, True),   # Encrypted & Compressed
                (True, False),  # Encrypted only
                (False, True),  # Compressed only
                (False, False)  # Plain
            ]
            
            for encrypt, compress in attempts:
                try:
                    temp_data = data
                    if encrypt:
                        temp_data = self.simple_decrypt(temp_data)
                    if compress:
                        temp_data = self.decompress_data(temp_data)
                    
                    game_state = self.deserialize_game_state(temp_data)
                    
                    # Success! Save with correct settings
                    print(f"✅ Save repaired! Using encrypt={encrypt}, compress={compress}")
                    
                    # Update settings
                    self.encrypt_saves = encrypt
                    self.compress_saves = compress
                    
                    # Resave with correct format
                    self.save_game(game_state, save_name)
                    
                    return True
                    
                except Exception:
                    continue
            
            print("❌ Could not repair save file.")
            return False
            
        except Exception as e:
            print(f"❌ Repair failed: {e}")
            return False
    
    def merge_saves(self, save1: str, save2: str, new_name: str) -> bool:
        """Merge two saves into one (advanced feature)"""
        
        game1 = self.load_game(save1)
        game2 = self.load_game(save2)
        
        if not game1 or not game2:
            return False
        
        # Create merged game state
        merged = {
            'version': '1.0.0',
            'merged_from': [save1, save2],
            'merge_time': datetime.now().isoformat()
        }
        
        # Merge player data (take higher level)
        player1 = game1.get('player', {})
        player2 = game2.get('player', {})
        
        if player1.get('level', 1) >= player2.get('level', 1):
            merged['player'] = player1.copy()
            merged['player']['inventory'] = list(set(
                player1.get('inventory', []) + player2.get('inventory', [])
            ))
            merged['player']['gold'] = player1.get('gold', 0) + player2.get('gold', 0)
        else:
            merged['player'] = player2.copy()
            merged['player']['inventory'] = list(set(
                player2.get('inventory', []) + player1.get('inventory', [])
            ))
            merged['player']['gold'] = player2.get('gold', 0) + player1.get('gold', 0)
        
        # Merge world data (take discovered locations from both)
        world1 = game1.get('world', {})
        world2 = game2.get('world', {})
        
        discovered = set(game1.get('discovered_locations', []))
        discovered.update(game2.get('discovered_locations', []))
        
        merged['world'] = world1 if len(world1) >= len(world2) else world2
        merged['discovered_locations'] = list(discovered)
        
        # Merge quests
        quests1 = game1.get('quests', {})
        quests2 = game2.get('quests', {})
        
        merged['quests'] = {
            'completed': list(set(
                quests1.get('completed', []) + quests2.get('completed', [])
            )),
            'active': quests1.get('active', []) + quests2.get('active', [])
        }
        
        # Save merged game
        return self.save_game(merged, new_name)
    
    def verify_all_saves(self) -> List[str]:
        """Verify integrity of all saves"""
        
        corrupted = []
        saves = self.list_saves()
        
        print("🔍 Verifying all saves...")
        
        for save in saves:
            print(f"  Checking {save}...", end=" ")
            
            meta_path = self.save_dir / f"{save}.meta"
            save_path = self.save_dir / f"{save}.sav"
            
            try:
                # Check metadata
                if meta_path.exists():
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)
                
                # Check save file
                with open(save_path, 'rb') as f:
                    data = f.read()
                
                # Try to load
                game_state = self.load_game(save)
                if game_state:
                    print("✅ OK")
                else:
                    print("❌ Corrupted")
                    corrupted.append(save)
                    
            except Exception:
                print("❌ Error")
                corrupted.append(save)
        
        return corrupted
    
    def backup_all_saves(self) -> bool:
        """Create backups of all saves"""
        
        saves = self.list_saves()
        
        if not saves:
            print("No saves to backup.")
            return False
        
        # Create timestamped backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root = self.backup_dir / f"full_backup_{timestamp}"
        backup_root.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        
        for save in saves:
            try:
                save_path = self.save_dir / f"{save}.sav"
                meta_path = self.save_dir / f"{save}.meta"
                
                if save_path.exists():
                    shutil.copy2(save_path, backup_root / f"{save}.sav")
                if meta_path.exists():
                    shutil.copy2(meta_path, backup_root / f"{save}.meta")
                
                success_count += 1
                print(f"✅ Backed up: {save}")
                
            except Exception as e:
                print(f"❌ Failed to backup {save}: {e}")
        
        print(f"\n📦 Full backup created: {backup_root}")
        print(f"   {success_count}/{len(saves)} saves backed up")
        
        return success_count > 0
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Restore all saves from a backup"""
        
        backup_dir = Path(backup_path)
        
        if not backup_dir.exists():
            print(f"Backup directory not found: {backup_path}")
            return False
        
        # Create restore point
        restore_point = self.backup_dir / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        restore_point.mkdir(parents=True, exist_ok=True)
        
        # Backup current saves
        for save in self.list_saves():
            save_path = self.save_dir / f"{save}.sav"
            meta_path = self.save_dir / f"{save}.meta"
            
            if save_path.exists():
                shutil.copy2(save_path, restore_point / f"{save}.sav")
            if meta_path.exists():
                shutil.copy2(meta_path, restore_point / f"{save}.meta")
        
        # Restore from backup
        restored = 0
        for backup_file in backup_dir.glob("*.sav"):
            try:
                save_name = backup_file.stem
                dest_path = self.save_dir / f"{save_name}.sav"
                shutil.copy2(backup_file, dest_path)
                
                # Restore metadata if exists
                meta_backup = backup_file.with_suffix('.meta')
                if meta_backup.exists():
                    shutil.copy2(meta_backup, self.save_dir / f"{save_name}.meta")
                
                restored += 1
                print(f"✅ Restored: {save_name}")
                
            except Exception as e:
                print(f"❌ Failed to restore {backup_file.name}: {e}")
        
        print(f"\n📥 Restored {restored} saves from backup")
        print(f"📦 Previous saves backed up to: {restore_point}")
        
        return restored > 0
    
    def get_save_statistics(self) -> Dict:
        """Get statistics about saves"""
        
        saves = self.list_saves()
        
        stats = {
            'total_saves': len(saves),
            'total_backups': 0,
            'total_size': 0,
            'oldest_save': None,
            'newest_save': None,
            'average_size': 0,
            'by_player': {},
            'by_class': {},
            'by_location': {}
        }
        
        timestamps = []
        
        for save in saves:
            info = self.get_save_info(save)
            if info:
                # Size
                size = info.get('file_size', 0)
                stats['total_size'] += size
                
                # Timestamp
                try:
                    ts = datetime.fromisoformat(info.get('timestamp', ''))
                    timestamps.append(ts)
                except:
                    pass
                
                # Player stats
                player = info.get('player_name', 'Unknown')
                stats['by_player'][player] = stats['by_player'].get(player, 0) + 1
                
                # Class stats
                pclass = info.get('player_class', 'Unknown')
                stats['by_class'][pclass] = stats['by_class'].get(pclass, 0) + 1
                
                # Location stats
                loc = info.get('location', 'Unknown')
                stats['by_location'][loc] = stats['by_location'].get(loc, 0) + 1
        
        # Calculate averages
        if saves:
            stats['average_size'] = stats['total_size'] / len(saves)
        
        if timestamps:
            stats['oldest_save'] = min(timestamps).isoformat()
            stats['newest_save'] = max(timestamps).isoformat()
        
        # Count backups
        for backup_subdir in self.backup_dir.iterdir():
            if backup_subdir.is_dir():
                stats['total_backups'] += len(list(backup_subdir.glob("*.sav")))
        
        return stats
    
    def display_save_stats(self) -> str:
        """Display save statistics"""
        
        stats = self.get_save_statistics()
        
        display = f"""
{TextFormatter.header('📊 SAVE STATISTICS')}
{TextFormatter.divider()}

{Colors.BOLD}Overview:{Colors.RESET}
  • Total Saves: {stats['total_saves']}
  • Total Backups: {stats['total_backups']}
  • Total Size: {self.format_file_size(stats['total_size'])}
  • Average Size: {self.format_file_size(stats['average_size'])}

{Colors.BOLD}Timeline:{Colors.RESET}
  • Newest: {stats['newest_save'] or 'N/A'}
  • Oldest: {stats['oldest_save'] or 'N/A'}

{Colors.BOLD}By Player:{Colors.RESET}
"""
        
        for player, count in sorted(stats['by_player'].items(), key=lambda x: x[1], reverse=True)[:5]:
            display += f"  • {player}: {count} save(s)\n"
        
        display += f"\n{Colors.BOLD}By Class:{Colors.RESET}\n"
        for pclass, count in sorted(stats['by_class'].items(), key=lambda x: x[1], reverse=True):
            display += f"  • {pclass}: {count} save(s)\n"
        
        display += f"\n{Colors.BOLD}Top Locations:{Colors.RESET}\n"
        for loc, count in sorted(stats['by_location'].items(), key=lambda x: x[1], reverse=True)[:5]:
            display += f"  • {loc}: {count} visit(s)\n"
        
        return display
    
    def __str__(self) -> str:
        """String representation"""
        saves = self.list_saves()
        return f"SaveSystem(saves={len(saves)}, dir={self.save_dir})"