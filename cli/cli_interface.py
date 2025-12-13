"""
Command-Line Interface for P2P Storage System
Enables file upload, download, and node management from terminal
"""

import cmd
import os
import sys
import time
import json
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class P2PStorageCLI(cmd.Cmd):
    """
    Interactive command-line interface for P2P storage system
    
    Available commands:
    - login: Authenticate user
    - upload: Upload file to network
    - download: Download file from network
    - nodes: List all nodes in network
    - health: Check node health status
    - storage: View storage statistics
    - help: Show available commands
    - exit: Exit the program
    """
    
    intro = """
    ╔════════════════════════════════════════════════════════════╗
    ║        P2P DISTRIBUTED STORAGE SYSTEM - CLI v1.0          ║
    ║                                                            ║
    ║  A distributed file storage system with:                 ║
    ║  • Virtual network with 5+ nodes                          ║
    ║  • Distributed file storage & chunking                   ║
    ║  • gRPC-based communication                              ║
    ║  • SSH secure connections                                 ║
    ║  • OTP email authentication                               ║
    ║  • Real-time bandwidth simulation (64KB/s)               ║
    ║                                                            ║
    ║  Type 'help' for available commands                       ║
    ║  Type 'exit' or 'quit' to exit                           ║
    ╚════════════════════════════════════════════════════════════╝
    """
    
    prompt = "P2P-Storage > "
    
    def __init__(self, p2p_network=None, auth_manager=None):
        """
        Initialize CLI
        
        Args:
            p2p_network: VirtualNetwork instance
            auth_manager: AuthenticationManager instance
        """
        super().__init__()
        self.p2p_network = p2p_network
        self.auth_manager = auth_manager
        
        self.current_user = None
        self.session_token = None
        
        logger.info("[CLI] Command-line interface initialized")
    
    # Authentication Commands
    def do_register(self, arg):
        """REGISTER <username> <email> <password>
        Register a new user account"""
        
        if not arg:
            print("Usage: register <username> <email> <password>")
            return
        
        parts = arg.split()
        if len(parts) < 3:
            print("Error: Please provide username, email, and password")
            return
        
        username = parts[0]
        email = parts[1]
        password = ' '.join(parts[2:])
        
        success, message = self.auth_manager.register_user(username, email, password)
        
        if success:
            print(f"[OK] {message}")
            # Prompt for OTP setup
            otp_choice = input("Enable OTP authentication? (y/n): ").lower()
            if otp_choice == 'y':
                self.do_enable_otp(username)
        else:
            print(f"[ERROR] {message}")
    
    def do_login(self, arg):
        """LOGIN <username> <password>
        Authenticate and start a session"""
        
        if not arg:
            print("Usage: login <username> <password>")
            return
        
        parts = arg.split()
        if len(parts) < 2:
            print("Error: Please provide username and password")
            return
        
        username = parts[0]
        password = ' '.join(parts[1:])
        
        # Get node IP if available
        node_ip = None
        if self.p2p_network and self.p2p_network.nodes:
            node_ip = list(self.p2p_network.nodes.values())[0].network_interface.ip_address
        
        success, token, message = self.auth_manager.login(username, password, node_ip)
        
        if success:
            self.current_user = username
            self.session_token = token
            print(f"[OK] {message}")
            print(f"  Session token: {token[:20]}...")
        else:
            print(f"[ERROR] {message}")
    
    def do_enable_otp(self, arg):
        """ENABLE_OTP <username>
        Enable OTP authentication for a user"""
        
        if not arg:
            username = self.current_user
            if not username:
                print("Usage: enable_otp <username>")
                return
        else:
            username = arg.strip()
        
        if username not in self.auth_manager.users:
            print(f"[ERROR] User not found: {username}")
            return
        
        user = self.auth_manager.users[username]
        user.enable_otp()
        
        print(f"[OK] OTP enabled for {username}")
        print(f"  Secret key: {user.otp_manager.secret_key}")
        print(f"  Current code: {user.otp_manager.get_current_code()}")
        print(f"  Provisioning URI: {user.otp_manager.get_provisioning_uri()}")
        print(f"  Backup codes: {user.otp_manager.backup_codes}")
    
    def do_logout(self, arg):
        """LOGOUT
        End current session"""
        
        if not self.current_user:
            print("Not logged in")
            return
        
        self.current_user = None
        self.session_token = None
        print("[OK] Logged out successfully")
    
    # File Operations
    def do_upload(self, arg):
        """UPLOAD <local_file_path>
        Upload a file to the P2P network"""
        
        if not self.current_user:
            print("[ERROR] Please login first")
            return
        
        if not arg:
            print("Usage: upload <local_file_path>")
            return
        
        file_path = arg.strip()
        
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            return
        
        file_size = os.path.getsize(file_path)
        
        print(f"Starting upload: {file_path}")
        print(f"File size: {file_size / (1024*1024):.2f} MB")
        
        # Simulate upload
        if self.p2p_network and self.p2p_network.nodes:
            node = list(self.p2p_network.nodes.values())[0]
            
            try:
                # Chunk and store file
                file_id, segments = node.storage.chunk_file(file_path)
                
                print(f"File chunked into {len(segments)} segments")
                
                # Simulate distribution across nodes
                node_list = list(self.p2p_network.nodes.values())
                for i, segment in enumerate(segments):
                    target_node = node_list[i % len(node_list)]
                    
                    # Simulate bandwidth delay (64KB/s)
                    delay = segment.size_bytes / (64 * 1024)
                    
                    success = target_node.storage.store_segment(segment)
                    
                    if success:
                        progress = (i + 1) / len(segments) * 100
                        print(f"  [{progress:3.0f}%] Segment {i+1} stored on {target_node.node_id}")
                        time.sleep(0.1)  # Simulate network delay
                
                print(f"[OK] Upload complete!")
                print(f"  File ID: {file_id}")
                print(f"  Total chunks: {len(segments)}")
                
            except Exception as e:
                print(f"[ERROR] Upload error: {e}")
        else:
            print("[ERROR] No nodes available in network")
    
    def do_download(self, arg):
        """DOWNLOAD <file_id> <output_path>
        Download a file from the P2P network"""
        
        if not self.current_user:
            print("[ERROR] Please login first")
            return
        
        if not arg:
            print("Usage: download <file_id> <output_path>")
            return
        
        parts = arg.split()
        if len(parts) < 2:
            print("Error: Please provide file_id and output_path")
            return
        
        file_id = parts[0]
        output_path = parts[1]
        
        print(f"Starting download: {file_id}")
        
        if self.p2p_network and self.p2p_network.nodes:
            node = list(self.p2p_network.nodes.values())[0]
            
            try:
                success = node.storage.reconstruct_file(file_id, output_path)
                
                if success:
                    file_size = os.path.getsize(output_path)
                    print(f"[OK] Download complete!")
                    print(f"  Output: {output_path}")
                    print(f"  Size: {file_size / (1024*1024):.2f} MB")
                else:
                    print(f"[ERROR] Download failed")
            
            except Exception as e:
                print(f"[ERROR] Download error: {e}")
        else:
            print("[ERROR] No nodes available in network")
    
    # Network Information
    def do_nodes(self, arg):
        """NODES
        List all nodes in the virtual network"""
        
        if not self.p2p_network:
            print("Network not initialized")
            return
        
        print(f"\nNetwork: {self.p2p_network.network_name} ({self.p2p_network.cidr})")
        print("─" * 80)
        print(f"{'Node ID':<15} {'IP Address':<15} {'Status':<10} {'Storage':<20} {'Files':<8}")
        print("─" * 80)
        
        for node_id, node in self.p2p_network.nodes.items():
            status = "ALIVE" if node.is_alive() else "DEAD"
            storage = f"{node.storage.get_used_space_gb():.2f}GB / {node.storage.capacity_gb:.2f}GB"
            files = len(node.storage.file_metadata)
            
            ip = node.network_interface.ip_address if node.network_interface else "N/A"
            print(f"{node_id:<15} {ip:<15} {status:<10} {storage:<20} {files:<8}")
        
        print("─" * 80)
    
    def do_health(self, arg):
        """HEALTH
        Check health status of all nodes"""
        
        if not self.p2p_network:
            print("Network not initialized")
            return
        
        print("\nHealth Check Results:")
        print("─" * 60)
        
        health_status = self.p2p_network.broadcast_health_check()
        
        for node_id, is_alive in health_status.items():
            status = "[ALIVE]" if is_alive else "[DEAD]"
            print(f"{node_id:<20} {status}")
        
        alive_count = sum(1 for alive in health_status.values() if alive)
        print("─" * 60)
        print(f"Total: {alive_count}/{len(health_status)} nodes alive")
    
    def do_storage(self, arg):
        """STORAGE
        Display storage statistics across all nodes"""
        
        if not self.p2p_network:
            print("Network not initialized")
            return
        
        print("\nNetwork Storage Statistics:")
        print("─" * 100)
        print(f"{'Node ID':<15} {'Capacity':<15} {'Used':<15} {'Available':<15} {'Utilization':<15}")
        print("─" * 100)
        
        total_capacity = 0
        total_used = 0
        
        for node_id, node in self.p2p_network.nodes.items():
            info = node.storage.get_storage_info()
            total_capacity += info['capacity_gb']
            total_used += info['used_gb']
            
            util = info['utilization_percent']
            print(f"{node_id:<15} {info['capacity_gb']:.2f}GB{'':<8} "
                  f"{info['used_gb']:.2f}GB{'':<9} {info['available_gb']:.2f}GB{'':<9} {util:.1f}%")
        
        print("─" * 100)
        print(f"{'TOTAL':<15} {total_capacity:.2f}GB{'':<8} {total_used:.2f}GB{'':<9} "
              f"{(total_capacity - total_used):.2f}GB{'':<9} "
              f"{(total_used/total_capacity*100):.1f}%" if total_capacity > 0 else "N/A")
    
    def do_topology(self, arg):
        """TOPOLOGY
        Display network topology"""
        
        if not self.p2p_network:
            print("Network not initialized")
            return
        
        topology = self.p2p_network.get_network_topology()
        
        print("\nNetwork Topology:")
        print(json.dumps(topology, indent=2))
    
    def do_stats(self, arg):
        """STATS
        Display network statistics"""
        
        if not self.p2p_network:
            print("Network not initialized")
            return
        
        stats = self.p2p_network.get_statistics()
        
        print("\nNetwork Statistics:")
        print("─" * 60)
        print(f"Network Name:         {stats['network_name']}")
        print(f"Uptime:               {stats['uptime_seconds']:.1f} seconds")
        print(f"Total Nodes:          {stats['total_nodes']}")
        print(f"Total Packets Sent:   {stats['total_packets_sent']}")
        print(f"Total Packets Recv:   {stats['total_packets_received']}")
        print(f"Total Data Sent:      {stats['total_bytes_transmitted'] / (1024*1024):.2f} MB")
        print(f"Avg Throughput:       {stats['average_throughput_mbps']:.2f} Mbps")
        print(f"Packet Loss Rate:     {stats['packet_loss_rate']*100:.2f}%")
        print("─" * 60)
    
    # System Commands
    def do_clear(self, arg):
        """CLEAR
        Clear the screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def do_exit(self, arg):
        """EXIT
        Exit the program"""
        print("Goodbye!")
        return True
    
    def do_quit(self, arg):
        """QUIT
        Same as EXIT"""
        return self.do_exit(arg)
    
    def emptyline(self):
        """Handle empty input"""
        pass
    
    def default(self, line):
        """Handle unknown commands"""
        print(f"Unknown command: {line}")
        print("Type 'help' for available commands")
    
    def postcmd(self, stop, line):
        """Called after each command"""
        return stop


def start_cli(p2p_network=None, auth_manager=None):
    """Start the CLI interface"""
    cli = P2PStorageCLI(p2p_network, auth_manager)
    cli.cmdloop()
