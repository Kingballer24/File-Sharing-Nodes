"""
Main Orchestrator - Coordinates all P2P storage system components
Initializes the virtual network, nodes, and services
"""

import time
import logging
import threading
from typing import Dict, Optional, List
from network.virtual_network import VirtualNetwork, VirtualNode
from auth.authentication import AuthenticationManager, OTPManager, EmailNotifier
from auth.ssh_handler import SSHKeyManager, SSHNodeManager
from storage.virtual_storage import VirtualStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class P2PStorageOrchestrator:
    """
    Main orchestrator for the P2P distributed storage system
    Manages all components: network, storage, authentication, etc.
    """
    
    def __init__(self, network_name: str = "P2P_Storage_Network",
                 node_count: int = 5,
                 storage_per_node_gb: float = 10.0):
        """
        Initialize the P2P storage system
        
        Args:
            network_name: Name of the virtual network
            node_count: Number of nodes to create (at least 5)
            storage_per_node_gb: Storage capacity per node in GB
        """
        if node_count < 5:
            logger.warning(f"Node count {node_count} is less than recommended 5")
        
        self.network_name = network_name
        self.node_count = node_count
        self.storage_per_node_gb = storage_per_node_gb
        
        # Initialize core components
        self.virtual_network = VirtualNetwork(network_name)
        self.auth_manager = AuthenticationManager()
        self.ssh_key_manager = SSHKeyManager()
        self.ssh_node_manager = SSHNodeManager(self.ssh_key_manager)
        
        # Network nodes
        self.nodes: Dict[str, VirtualNode] = {}
        self.is_running = False
        
        logger.info(f"[ORCHESTRATOR] P2P Storage System initialized")
        logger.info(f"[ORCHESTRATOR] Network: {network_name}, Nodes: {node_count}, "
                   f"Storage/Node: {storage_per_node_gb}GB")
    
    def initialize_nodes(self):
        """
        Create and initialize all virtual nodes
        Each node has its own network interface and storage
        """
        logger.info("[ORCHESTRATOR] Initializing virtual nodes...")
        
        for i in range(self.node_count):
            node_id = f"Node_{i+1:02d}"
            
            # Create virtual node
            node = VirtualNode(node_id, storage_capacity_gb=self.storage_per_node_gb)
            node.initialize_network_interface(bandwidth_mbps=64.0)  # 64KB/s simulation
            
            # Register in network (auto-assign IP)
            ip_address = self.virtual_network.register_node(node)
            
            # Store locally
            self.nodes[node_id] = node
            
            # Connect nodes as peers
            for other_id, other_node in self.nodes.items():
                if other_id != node_id:
                    node.add_peer(other_id, other_node.network_interface.ip_address)
                    other_node.add_peer(node_id, node.network_interface.ip_address)
            
            logger.info(f"[ORCHESTRATOR] Node {node_id} created: {ip_address}")
        
        logger.info(f"[ORCHESTRATOR] All {self.node_count} nodes initialized")
    
    def start_network(self):
        """Start the virtual network"""
        self.is_running = True
        logger.info("[ORCHESTRATOR] Virtual network started")
    
    def stop_network(self):
        """Stop the virtual network"""
        self.is_running = False
        logger.info("[ORCHESTRATOR] Virtual network stopped")
    
    def broadcast_health_check(self):
        """Perform network-wide health check"""
        return self.virtual_network.broadcast_health_check()
    
    def setup_demo_users(self):
        """Create demo users for testing"""
        demo_users = [
            ("alice", "alice@p2p.local", "alice123"),
            ("bob", "bob@p2p.local", "bob123"),
            ("charlie", "charlie@p2p.local", "charlie123"),
        ]
        
        for username, email, password in demo_users:
            success, msg = self.auth_manager.register_user(username, email, password)
            if success:
                # Enable OTP for demo
                user = self.auth_manager.users[username]
                user.enable_otp()
                logger.info(f"[ORCHESTRATOR] Demo user created: {username}")
    
    def get_system_info(self) -> Dict:
        """Get comprehensive system information"""
        return {
            'system_name': self.network_name,
            'status': 'RUNNING' if self.is_running else 'STOPPED',
            'nodes': len(self.nodes),
            'network_info': self.virtual_network.get_network_topology(),
            'network_stats': self.virtual_network.get_statistics(),
            'users': len(self.auth_manager.users)
        }
    
    def get_detailed_report(self) -> str:
        """Generate detailed system report"""
        lines = []
        lines.append("=" * 80)
        lines.append("P2P DISTRIBUTED STORAGE SYSTEM - DETAILED REPORT")
        lines.append("=" * 80)
        
        # System Status
        lines.append("\n[SYSTEM STATUS]")
        lines.append(f"Network Name:       {self.network_name}")
        lines.append(f"Status:             {'RUNNING' if self.is_running else 'STOPPED'}")
        lines.append(f"Total Nodes:        {self.node_count}")
        lines.append(f"Total Storage:      {self.node_count * self.storage_per_node_gb:.0f}GB")
        
        # Network Topology
        lines.append("\n[NETWORK TOPOLOGY]")
        topology = self.virtual_network.get_network_topology()
        for node_id, details in topology['node_details'].items():
            lines.append(f"\n  {node_id}:")
            lines.append(f"    IP Address:     {details['ip_address']}")
            lines.append(f"    Status:         {details['status']}")
            lines.append(f"    Files Stored:   {details['stored_files']}")
            lines.append(f"    Storage Used:   {details['storage_used_gb']:.2f}GB")
        
        # Network Statistics
        lines.append("\n[NETWORK STATISTICS]")
        stats = self.virtual_network.get_statistics()
        lines.append(f"Uptime:             {stats['uptime_seconds']:.1f}s")
        lines.append(f"Packets Sent:       {stats['total_packets_sent']}")
        lines.append(f"Packets Received:   {stats['total_packets_received']}")
        lines.append(f"Data Transmitted:   {stats['total_bytes_transmitted'] / (1024*1024):.2f}MB")
        lines.append(f"Avg Throughput:     {stats['average_throughput_mbps']:.2f}Mbps")
        
        # Users
        lines.append(f"\n[USERS]")
        lines.append(f"Total Users:        {len(self.auth_manager.users)}")
        for username, user in self.auth_manager.users.items():
            lines.append(f"  {username}:")
            lines.append(f"    Email:          {user.email}")
            lines.append(f"    OTP Enabled:    {user.otp_enabled}")
            lines.append(f"    Active Sessions: {len(user.session_tokens)}")
        
        lines.append("\n" + "=" * 80)
        
        return "\n".join(lines)


def create_test_file(filename: str = "test_file.bin", size_mb: int = 1) -> str:
    """Create a test file for uploading"""
    import os
    import random
    
    # Create test files directory
    os.makedirs("test_files", exist_ok=True)
    
    filepath = f"test_files/{filename}"
    
    with open(filepath, 'wb') as f:
        # Write random data
        data = os.urandom(size_mb * 1024 * 1024)
        f.write(data)
    
    logger.info(f"[TEST] Test file created: {filepath} ({size_mb}MB)")
    return filepath


def run_system_demo():
    """
    Run a demonstration of the P2P storage system
    Shows all major features in action
    """
    
    logger.info("=" * 80)
    logger.info("STARTING P2P DISTRIBUTED STORAGE SYSTEM DEMO")
    logger.info("=" * 80)
    
    # Initialize orchestrator with 5 nodes
    orchestrator = P2PStorageOrchestrator(
        network_name="P2P_Storage_Network",
        node_count=5,
        storage_per_node_gb=10.0
    )
    
    # Initialize nodes
    orchestrator.initialize_nodes()
    
    # Start network
    orchestrator.start_network()
    
    # Setup demo users
    orchestrator.setup_demo_users()
    
    # Create test file
    test_file = create_test_file("test_video.bin", size_mb=5)
    
    # Simulate file upload
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: FILE UPLOAD AND DISTRIBUTION")
    logger.info("=" * 80)
    
    node_1 = orchestrator.nodes["Node_01"]
    
    try:
        # Chunk the file
        file_id, segments = node_1.storage.chunk_file(test_file, chunk_size_bytes=256*1024)
        
        logger.info(f"\nFile ID: {file_id}")
        logger.info(f"Total Segments: {len(segments)}")
        logger.info(f"Chunk Size: 256KB")
        
        # Distribute segments across nodes
        node_list = list(orchestrator.nodes.values())
        
        logger.info("\nDistributing segments across nodes:")
        for i, segment in enumerate(segments):
            target_node = node_list[i % len(node_list)]
            success = target_node.storage.store_segment(segment)
            
            if success:
                logger.info(f"  Segment {i+1}: Stored on {target_node.node_id} ({segment.size_bytes} bytes)")
                # Simulate bandwidth delay
                time.sleep(0.05)
        
        logger.info(f"\n[OK] File successfully distributed across {len(node_list)} nodes")
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
    
    # Health check
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: NETWORK HEALTH CHECK")
    logger.info("=" * 80)
    
    health_status = orchestrator.broadcast_health_check()
    for node_id, is_alive in health_status.items():
        status = "[ALIVE]" if is_alive else "[DEAD]"
        logger.info(f"{node_id}: {status}")
    
    # Show detailed report
    logger.info("\n" + "=" * 80)
    logger.info("SYSTEM REPORT")
    logger.info("=" * 80)
    
    report = orchestrator.get_detailed_report()
    logger.info("\n" + report)
    
    # Save report to file
    with open("system_report.txt", 'w') as f:
        f.write(report)
    
    logger.info("\nReport saved to: system_report.txt")
    
    logger.info("\n" + "=" * 80)
    logger.info("DEMO COMPLETE")
    logger.info("=" * 80)
    
    return orchestrator


if __name__ == "__main__":
    # Run the demo
    orchestrator = run_system_demo()
    
    # The system is now ready to use via CLI or web interface
    print("\n\nSystem initialized. You can now:")
    print("1. Run the CLI interface: python -m cli.cli_interface")
    print("2. Start the web server: python web/web_server.py")
    print("3. Access the web UI at http://localhost:5000")
