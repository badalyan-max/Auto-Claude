#!/usr/bin/env python3
"""
Git Sync Integration für Auto Claude Frontend
==============================================

Erstellt ein WebSocket/IPC-Interface zwischen Auto Git Sync und dem
Electron Frontend, damit die UI in Echtzeit über Git-Operationen
informiert wird.

Usage:
    python git_sync_integration.py --port 8765
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    print("ERROR: websockets package not found!")
    print("Install with: pip install websockets")
    sys.exit(1)


class GitSyncBridge:
    """Brücke zwischen Auto Git Sync und Electron Frontend."""
    
    def __init__(self, project_dir: Path, port: int = 8765):
        self.project_dir = project_dir
        self.port = port
        self.clients: set[WebSocketServerProtocol] = set()
        self.state_file = project_dir / ".auto-claude" / "git_sync_state.json"
    
    async def register_client(self, websocket: WebSocketServerProtocol):
        """Registriert einen neuen Client (Electron App)."""
        self.clients.add(websocket)
        print(f"[INFO] Client connected: {websocket.remote_address}")
        
        # Sende aktuellen State beim Connect
        await self.send_current_state(websocket)
    
    async def unregister_client(self, websocket: WebSocketServerProtocol):
        """Entfernt einen Client."""
        self.clients.discard(websocket)
        print(f"[INFO] Client disconnected: {websocket.remote_address}")
    
    async def send_current_state(self, websocket: WebSocketServerProtocol):
        """Sendet aktuellen Git Sync State an Client."""
        if not self.state_file.exists():
            return
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            message = {
                "type": "state",
                "data": state
            }
            
            await websocket.send(json.dumps(message))
        except Exception as e:
            print(f"[ERROR] Konnte State nicht senden: {e}")
    
    async def broadcast_event(self, event_type: str, data: dict):
        """Sendet Event an alle verbundenen Clients."""
        if not self.clients:
            return
        
        message = {
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        message_json = json.dumps(message)
        
        # Sende an alle Clients
        disconnected = []
        for client in self.clients:
            try:
                await client.send(message_json)
            except Exception:
                disconnected.append(client)
        
        # Entferne disconnected clients
        for client in disconnected:
            await self.unregister_client(client)
    
    async def watch_state_file(self):
        """Überwacht State-Datei auf Änderungen."""
        last_mtime = None
        
        print(f"[INFO] Überwache State-Datei: {self.state_file}")
        
        while True:
            if self.state_file.exists():
                current_mtime = self.state_file.stat().st_mtime
                
                if last_mtime is None:
                    last_mtime = current_mtime
                elif current_mtime != last_mtime:
                    # State-Datei hat sich geändert
                    print("[INFO] State-Datei geändert, broadcast...")
                    
                    try:
                        with open(self.state_file, 'r', encoding='utf-8') as f:
                            state = json.load(f)
                        
                        await self.broadcast_event("state_changed", state)
                    except Exception as e:
                        print(f"[ERROR] Konnte State nicht lesen: {e}")
                    
                    last_mtime = current_mtime
            
            await asyncio.sleep(1)
    
    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Behandelt WebSocket-Client-Verbindung."""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                # Verarbeite eingehende Nachrichten vom Client
                try:
                    data = json.loads(message)
                    command = data.get("command")
                    
                    if command == "get_state":
                        await self.send_current_state(websocket)
                    elif command == "reset_state":
                        # Reset State (nur für Admin)
                        if self.state_file.exists():
                            self.state_file.unlink()
                            await self.broadcast_event("state_reset", {})
                    else:
                        print(f"[WARN] Unknown command: {command}")
                
                except json.JSONDecodeError:
                    print(f"[WARN] Invalid JSON from client: {message}")
        
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def serve(self):
        """Startet WebSocket-Server."""
        print(f"[INFO] Starte Git Sync Bridge auf Port {self.port}")
        
        # Starte State-Watcher im Hintergrund
        asyncio.create_task(self.watch_state_file())
        
        # Starte WebSocket-Server
        async with websockets.serve(self.handle_client, "localhost", self.port):
            print(f"[INFO] Git Sync Bridge läuft auf ws://localhost:{self.port}")
            print("[INFO] Warte auf Verbindungen...")
            
            # Läuft unbegrenzt
            await asyncio.Future()


def main():
    parser = argparse.ArgumentParser(
        description="Git Sync Integration Bridge für Auto Claude Frontend"
    )
    parser.add_argument("--port", type=int, default=8765, help="WebSocket-Port")
    
    args = parser.parse_args()
    
    # Finde Projekt-Verzeichnis
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent.parent.resolve()
    
    # Erstelle Bridge
    bridge = GitSyncBridge(project_dir, args.port)
    
    # Starte Server
    try:
        asyncio.run(bridge.serve())
    except KeyboardInterrupt:
        print("\n[INFO] Bridge gestoppt")


if __name__ == "__main__":
    main()

