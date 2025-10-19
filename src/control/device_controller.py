import asyncio
import subprocess
import os
import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import win32api
import win32con
import win32gui
import win32process
import psutil
import keyboard
import mouse
from pathlib import Path

class CommandRiskLevel(Enum):
    SAFE = "safe"           # No confirmation needed
    MODERATE = "moderate"   # Requires confirmation
    HIGH = "high"          # Requires confirmation + extra warning
    CRITICAL = "critical"   # Requires confirmation + detailed explanation

@dataclass
class PendingCommand:
    command: str
    action: str
    risk_level: CommandRiskLevel
    description: str
    timestamp: float
    parameters: Dict[str, Any]

class WindowsDeviceController:
    """
    Full Windows workstation control with mandatory confirmation system
    Uses configurable confirmation keyword for all operations
    """
    
    def __init__(self, confirmation_keyword: str = "wolf-logic"):
        self.logger = logging.getLogger(__name__)
        self.confirmation_keyword = confirmation_keyword
        self.pending_commands: Dict[str, PendingCommand] = {}
        self.command_timeout = 30.0  # 30 seconds to confirm
        
        # Callback for requesting confirmation from user
        self.confirmation_callback: Optional[callable] = None
        
        # Command categories and their risk levels
        self.command_risks = {
            # File Operations
            "open_file": CommandRiskLevel.SAFE,
            "create_file": CommandRiskLevel.MODERATE,
            "delete_file": CommandRiskLevel.HIGH,
            "move_file": CommandRiskLevel.MODERATE,
            "copy_file": CommandRiskLevel.SAFE,
            
            # Application Control
            "launch_app": CommandRiskLevel.SAFE,
            "close_app": CommandRiskLevel.SAFE,
            "kill_process": CommandRiskLevel.HIGH,
            
            # System Control
            "shutdown": CommandRiskLevel.CRITICAL,
            "restart": CommandRiskLevel.CRITICAL,
            "sleep": CommandRiskLevel.MODERATE,
            "lock_workstation": CommandRiskLevel.SAFE,
            
            # Window Management
            "minimize_window": CommandRiskLevel.SAFE,
            "maximize_window": CommandRiskLevel.SAFE,
            "close_window": CommandRiskLevel.SAFE,
            "switch_window": CommandRiskLevel.SAFE,
            
            # Input Control
            "type_text": CommandRiskLevel.MODERATE,
            "press_key": CommandRiskLevel.MODERATE,
            "click_mouse": CommandRiskLevel.MODERATE,
            
            # System Settings
            "change_volume": CommandRiskLevel.SAFE,
            "change_brightness": CommandRiskLevel.SAFE,
            "change_wallpaper": CommandRiskLevel.MODERATE,
            
            # Network
            "network_disconnect": CommandRiskLevel.HIGH,
            "network_connect": CommandRiskLevel.MODERATE,
            
            # Registry/System Files
            "registry_edit": CommandRiskLevel.CRITICAL,
            "system_file_edit": CommandRiskLevel.CRITICAL,
            
            # PowerShell/Terminal
            "run_powershell": CommandRiskLevel.HIGH,
            "run_cmd": CommandRiskLevel.HIGH,
            "run_terminal": CommandRiskLevel.HIGH,
        }
    
    def set_confirmation_callback(self, callback: callable):
        """Set callback function to request confirmation from user"""
        self.confirmation_callback = callback
    
    async def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a system command with confirmation if required
        Returns: {"success": bool, "message": str, "data": Any}
        """
        try:
            # Parse and validate command
            risk_level = self.command_risks.get(command, CommandRiskLevel.HIGH)
            
            # Generate command description
            description = self._generate_command_description(command, kwargs)
            
            # Check if confirmation is needed
            if risk_level != CommandRiskLevel.SAFE:
                # Create pending command
                command_id = f"{command}_{int(time.time())}"
                pending_cmd = PendingCommand(
                    command=command,
                    action=description,
                    risk_level=risk_level,
                    description=description,
                    timestamp=time.time(),
                    parameters=kwargs
                )
                
                self.pending_commands[command_id] = pending_cmd
                
                # Request confirmation from user
                await self._request_confirmation(command_id, pending_cmd)
                
                # Wait for confirmation (handled by confirm_command method)
                return {
                    "success": False,
                    "message": f"Command '{command}' requires confirmation. Say 'wolf-logic' to proceed.",
                    "command_id": command_id,
                    "pending": True
                }
            else:
                # Execute safe command immediately
                return await self._execute_internal(command, **kwargs)
                
        except Exception as e:
            self.logger.error(f"Error executing command {command}: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "data": None
            }
    
    async def confirm_command(self, confirmation_text: str) -> Dict[str, Any]:
        """
        Process confirmation input from user
        """
        if self.confirmation_keyword.lower() not in confirmation_text.lower():
            return {
                "success": False,
                "message": f"Invalid confirmation. Please say '{self.confirmation_keyword}' to confirm pending commands."
            }
        
        # Find and execute pending commands that haven't timed out
        current_time = time.time()
        executed_commands = []
        
        for command_id, pending_cmd in list(self.pending_commands.items()):
            if current_time - pending_cmd.timestamp <= self.command_timeout:
                # Execute the pending command
                result = await self._execute_internal(
                    pending_cmd.command, 
                    **pending_cmd.parameters
                )
                executed_commands.append({
                    "command": pending_cmd.command,
                    "result": result
                })
                # Remove from pending
                del self.pending_commands[command_id]
        
        # Clean up timed out commands
        self.pending_commands = {
            cmd_id: cmd for cmd_id, cmd in self.pending_commands.items()
            if current_time - cmd.timestamp <= self.command_timeout
        }
        
        if executed_commands:
            return {
                "success": True,
                "message": f"Executed {len(executed_commands)} confirmed commands",
                "executed": executed_commands
            }
        else:
            return {
                "success": False,
                "message": "No pending commands to execute or all commands have timed out"
            }
    
    async def _request_confirmation(self, command_id: str, pending_cmd: PendingCommand):
        """Request confirmation from user via callback"""
        if self.confirmation_callback:
            risk_warnings = {
                CommandRiskLevel.MODERATE: "This action requires confirmation.",
                CommandRiskLevel.HIGH: "⚠️ WARNING: This is a potentially risky operation!",
                CommandRiskLevel.CRITICAL: "🚨 CRITICAL: This operation could significantly impact your system!"
            }
            
            warning = risk_warnings.get(pending_cmd.risk_level, "")
            message = f"{warning}\nAction: {pending_cmd.description}\nSay '{self.confirmation_keyword}' to confirm."
            
            try:
                if asyncio.iscoroutinefunction(self.confirmation_callback):
                    await self.confirmation_callback(message)
                else:
                    self.confirmation_callback(message)
            except Exception as e:
                self.logger.error(f"Error in confirmation callback: {e}")
    
    def _generate_command_description(self, command: str, kwargs: Dict[str, Any]) -> str:
        """Generate human-readable description of command"""
        descriptions = {
            "open_file": lambda k: f"Open file: {k.get('path', 'unknown')}",
            "delete_file": lambda k: f"DELETE file: {k.get('path', 'unknown')}",
            "launch_app": lambda k: f"Launch application: {k.get('app_name', 'unknown')}",
            "kill_process": lambda k: f"Force close process: {k.get('process_name', 'unknown')}",
            "shutdown": lambda k: "Shutdown the computer",
            "restart": lambda k: "Restart the computer", 
            "run_powershell": lambda k: f"Run PowerShell command: {k.get('script', 'unknown')}",
            "type_text": lambda k: f"Type text: '{k.get('text', '')}'",
            "registry_edit": lambda k: f"Edit registry: {k.get('key', 'unknown')}",
        }
        
        generator = descriptions.get(command, lambda k: f"Execute {command} with parameters: {k}")
        return generator(kwargs)
    
    async def _execute_internal(self, command: str, **kwargs) -> Dict[str, Any]:
        """Internal command execution - bypasses confirmation"""
        
        try:
            if command == "launch_app":
                return await self._launch_app(kwargs.get('app_name'), kwargs.get('path'))
            
            elif command == "open_file":
                return await self._open_file(kwargs.get('path'))
            
            elif command == "kill_process":
                return await self._kill_process(kwargs.get('process_name'))
            
            elif command == "run_powershell":
                return await self._run_powershell(kwargs.get('script'))
            
            elif command == "type_text":
                return await self._type_text(kwargs.get('text'))
            
            elif command == "press_key":
                return await self._press_key(kwargs.get('key'))
            
            elif command == "click_mouse":
                return await self._click_mouse(kwargs.get('x'), kwargs.get('y'), kwargs.get('button', 'left'))
            
            elif command == "shutdown":
                return await self._shutdown()
            
            elif command == "restart":
                return await self._restart()
            
            elif command == "lock_workstation":
                return await self._lock_workstation()
            
            elif command == "change_volume":
                return await self._change_volume(kwargs.get('level'))
            
            # Add more command implementations as needed
            else:
                return {
                    "success": False,
                    "message": f"Command '{command}' not implemented yet"
                }
                
        except Exception as e:
            self.logger.error(f"Error in _execute_internal for {command}: {e}")
            return {
                "success": False,
                "message": f"Execution error: {str(e)}"
            }
    
    # Individual command implementations
    async def _launch_app(self, app_name: str, path: str = None) -> Dict[str, Any]:
        """Launch an application"""
        try:
            if path:
                subprocess.Popen(path)
            else:
                # Try to find common applications
                common_apps = {
                    "notepad": "notepad.exe",
                    "calculator": "calc.exe",
                    "chrome": "chrome.exe",
                    "edge": "msedge.exe",
                    "firefox": "firefox.exe",
                    "explorer": "explorer.exe",
                    "cmd": "cmd.exe",
                    "powershell": "powershell.exe",
                    "terminal": "wt.exe"
                }
                
                app_exe = common_apps.get(app_name.lower(), f"{app_name}.exe")
                subprocess.Popen(app_exe)
            
            return {
                "success": True,
                "message": f"Launched {app_name}",
                "data": {"app": app_name, "path": path}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to launch {app_name}: {str(e)}"
            }
    
    async def _open_file(self, file_path: str) -> Dict[str, Any]:
        """Open a file with default application"""
        try:
            os.startfile(file_path)
            return {
                "success": True,
                "message": f"Opened file: {file_path}",
                "data": {"path": file_path}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to open file: {str(e)}"
            }
    
    async def _run_powershell(self, script: str) -> Dict[str, Any]:
        """Execute PowerShell command"""
        try:
            result = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "message": "PowerShell command executed",
                "data": {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"PowerShell execution failed: {str(e)}"
            }
    
    async def _type_text(self, text: str) -> Dict[str, Any]:
        """Type text using keyboard automation"""
        try:
            keyboard.write(text)
            return {
                "success": True,
                "message": f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}",
                "data": {"text": text}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to type text: {str(e)}"
            }
    
    async def _press_key(self, key: str) -> Dict[str, Any]:
        """Press a key or key combination"""
        try:
            keyboard.press_and_release(key)
            return {
                "success": True,
                "message": f"Pressed key: {key}",
                "data": {"key": key}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to press key: {str(e)}"
            }
    
    async def _shutdown(self) -> Dict[str, Any]:
        """Shutdown the computer"""
        try:
            subprocess.run(["shutdown", "/s", "/t", "5"], check=True)
            return {
                "success": True,
                "message": "Computer shutting down in 5 seconds",
                "data": {"action": "shutdown"}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to shutdown: {str(e)}"
            }
    
    async def _lock_workstation(self) -> Dict[str, Any]:
        """Lock the workstation"""
        try:
            win32api.LockWorkStation()
            return {
                "success": True,
                "message": "Workstation locked",
                "data": {"action": "lock"}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to lock workstation: {str(e)}"
            }
    
    def get_pending_commands(self) -> List[Dict[str, Any]]:
        """Get list of pending commands waiting for confirmation"""
        current_time = time.time()
        pending = []
        
        for cmd_id, cmd in self.pending_commands.items():
            if current_time - cmd.timestamp <= self.command_timeout:
                pending.append({
                    "id": cmd_id,
                    "command": cmd.command,
                    "description": cmd.description,
                    "risk_level": cmd.risk_level.value,
                    "time_remaining": self.command_timeout - (current_time - cmd.timestamp)
                })
        
        return pending