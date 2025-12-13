"""
Virtual Network Infrastructure - Core Network Management
Simulates TCP/IP layers and network communication between nodes
"""

import time
import threading
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PacketType(Enum):
    """TCP packet types for simulation"""
    SYN = "SYN"           # Connection initiation
    SYN_ACK = "SYN_ACK"   # Connection acknowledgment
    ACK = "ACK"           # Acknowledgment
    DATA = "DATA"         # Data transmission
    FIN = "FIN"           # Connection termination
    HEALTH_CHECK = "HEALTH_CHECK"  # Health probe


@dataclass
class NetworkPacket:
    """Represents a network packet in the virtual network"""
    packet_type: PacketType
    source_ip: str
    destination_ip: str
    payload: bytes
    timestamp: float
    packet_id: str
    seq_number: int = 0
    ack_number: int = 0
    checksum: int = 0
    
    def calculate_checksum(self) -> int:
        """Calculate simple checksum for packet integrity"""
        checksum = 0
        for byte in self.payload:
            checksum ^= byte
        return checksum
    
    def __repr__(self):
        return f"Packet({self.packet_type.value}, {self.source_ip}->{self.destination_ip}, {len(self.payload)}B)"


class NetworkInterface:
    """
    Represents a network interface for a virtual node
    Handles packet transmission, reception, and TCP simulation
    """
    
    def __init__(self, node_id: str, ip_address: str, bandwidth_mbps: float = 64.0):
        """
        Initialize network interface
        
        Args:
            node_id: Unique node identifier
            ip_address: IPv4 address (e.g., "192.168.1.1")
            bandwidth_mbps: Simulated bandwidth in Mbps (default 64Kb/s = 0.064Mbps)
        """
        self.node_id = node_id
        self.ip_address = ip_address
        self.bandwidth_mbps = bandwidth_mbps
        self.bandwidth_bps = (bandwidth_mbps * 1024 * 1024) / 8  # Convert to bytes per second
        
        # Network statistics
        self.packets_sent = 0
        self.packets_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.start_time = time.time()
        
        # Connection states
        self.connections: Dict[str, str] = {}  # peer_ip -> state
        self.packet_buffer: List[NetworkPacket] = []
        self.lock = threading.RLock()
        
    def send_packet(self, packet: NetworkPacket) -> Tuple[bool, float]:
        """
        Simulate packet transmission with bandwidth limitation
        
        Returns:
            Tuple of (success, transmission_time_seconds)
        """
        with self.lock:
            # Simulate bandwidth delay (64KB/s simulation)
            payload_size = len(packet.payload)
            transmission_time = payload_size / self.bandwidth_bps
            
            self.packets_sent += 1
            self.bytes_sent += payload_size
            
            logger.info(f"[{self.node_id}] Sending {len(packet.payload)}B to {packet.destination_ip} "
                       f"(delay: {transmission_time:.3f}s)")
            
            return True, transmission_time
    
    def receive_packet(self, packet: NetworkPacket) -> bool:
        """Receive and buffer a packet"""
        with self.lock:
            # Simulate packet reception delay
            payload_size = len(packet.payload)
            reception_time = payload_size / self.bandwidth_bps
            
            self.packet_buffer.append(packet)
            self.packets_received += 1
            self.bytes_received += payload_size
            
            logger.info(f"[{self.node_id}] Received packet from {packet.source_ip} "
                       f"({len(packet.payload)}B, ID: {packet.packet_id})")
            
            return True
    
    def get_pending_packets(self) -> List[NetworkPacket]:
        """Retrieve all pending packets"""
        with self.lock:
            packets = self.packet_buffer[:]
            self.packet_buffer.clear()
            return packets
    
    def get_statistics(self) -> Dict:
        """Get network interface statistics"""
        elapsed = time.time() - self.start_time
        return {
            'node_id': self.node_id,
            'ip_address': self.ip_address,
            'bandwidth_mbps': self.bandwidth_mbps,
            'packets_sent': self.packets_sent,
            'packets_received': self.packets_received,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'uptime_seconds': elapsed,
            'throughput_bps': self.bytes_sent / elapsed if elapsed > 0 else 0
        }


class VirtualNetwork:
    """
    Virtual Network - manages all nodes and network communication
    Simulates TCP/IP communication between distributed nodes
    """
    
    def __init__(self, network_name: str = "P2P_Network", cidr: str = "192.168.1.0/24"):
        """
        Initialize virtual network
        
        Args:
            network_name: Name of the virtual network
            cidr: Network CIDR notation for IP assignment
        """
        self.network_name = network_name
        self.cidr = cidr
        self.base_ip = "192.168.1"
        self.next_ip_octet = 2
        
        self.nodes: Dict[str, 'VirtualNode'] = {}
        self.network_interfaces: Dict[str, NetworkInterface] = {}
        self.routing_table: Dict[str, str] = {}  # ip -> node_id
        self.packet_loss_rate = 0.01  # 1% packet loss simulation
        
        self.lock = threading.RLock()
        self.is_running = False
        self.network_thread: Optional[threading.Thread] = None
        self.start_time = time.time()
        
        logger.info(f"[NETWORK] Virtual network '{network_name}' initialized on {cidr}")
    
    def assign_ip_address(self) -> str:
        """
        Assign next available IP address in the network
        YOU ARE THE ONE TO ASSIGN IP ADDRESSES
        """
        with self.lock:
            if self.next_ip_octet > 254:
                raise Exception("Network full - no more IP addresses available")
            
            ip = f"{self.base_ip}.{self.next_ip_octet}"
            self.next_ip_octet += 1
            logger.info(f"[NETWORK] Assigned IP: {ip}")
            return ip
    
    def register_node(self, node: 'VirtualNode', ip_address: Optional[str] = None) -> str:
        """
        Register a virtual node in the network
        
        Args:
            node: VirtualNode instance
            ip_address: Optional specific IP (auto-assigns if None)
            
        Returns:
            Assigned IP address
        """
        with self.lock:
            if ip_address is None:
                ip_address = self.assign_ip_address()
            
            node.network_interface.ip_address = ip_address
            self.nodes[node.node_id] = node
            self.network_interfaces[ip_address] = node.network_interface
            self.routing_table[ip_address] = node.node_id
            
            logger.info(f"[NETWORK] Node {node.node_id} registered with IP {ip_address}")
            return ip_address
    
    def send_packet(self, source_ip: str, dest_ip: str, packet: NetworkPacket) -> Tuple[bool, float]:
        """
        Send packet through the network with simulation
        
        Returns:
            Tuple of (success, actual_delivery_time)
        """
        with self.lock:
            if dest_ip not in self.routing_table:
                logger.warning(f"[NETWORK] Destination IP {dest_ip} not found in routing table")
                return False, 0.0
            
            # Simulate packet loss
            if random.random() < self.packet_loss_rate:
                logger.warning(f"[NETWORK] Packet loss simulation: packet dropped")
                return False, 0.0
            
            # Get destination node
            dest_node_id = self.routing_table[dest_ip]
            dest_node = self.nodes[dest_node_id]
            
            # Simulate network delay (propagation delay)
            propagation_delay = random.uniform(0.001, 0.01)  # 1-10ms
            
            # Send and receive through network interfaces
            success, transmission_time = self.network_interfaces[source_ip].send_packet(packet)
            
            if success:
                # Schedule reception with delay
                total_delay = transmission_time + propagation_delay
                
                def deliver():
                    time.sleep(total_delay)
                    dest_node.network_interface.receive_packet(packet)
                
                delivery_thread = threading.Thread(target=deliver, daemon=True)
                delivery_thread.start()
                
                return True, total_delay
        
        return False, 0.0
    
    def broadcast_health_check(self) -> Dict[str, bool]:
        """
        Broadcast health check messages to all nodes
        Network should be able to determine if node is alive or dead
        
        Returns:
            Dict of {node_id: is_alive}
        """
        health_status = {}
        
        with self.lock:
            for node_id, node in self.nodes.items():
                health_status[node_id] = node.is_alive()
                status = "ALIVE" if node.is_alive() else "DEAD"
                logger.info(f"[NETWORK] Health check: {node_id} - {status}")
        
        return health_status
    
    def get_network_topology(self) -> Dict:
        """Get complete network topology"""
        with self.lock:
            topology = {
                'network_name': self.network_name,
                'cidr': self.cidr,
                'nodes': len(self.nodes),
                'node_details': {}
            }
            
            for node_id, node in self.nodes.items():
                topology['node_details'][node_id] = {
                    'ip_address': node.network_interface.ip_address,
                    'status': 'ALIVE' if node.is_alive() else 'DEAD',
                    'stored_files': len(node.storage.file_segments),
                    'storage_used_gb': node.storage.get_used_space_gb()
                }
            
            return topology
    
    def get_statistics(self) -> Dict:
        """Get network-wide statistics"""
        with self.lock:
            total_packets_sent = 0
            total_packets_received = 0
            total_bytes_transmitted = 0
            
            node_stats = {}
            for ip, interface in self.network_interfaces.items():
                stats = interface.get_statistics()
                node_stats[ip] = stats
                total_packets_sent += stats['packets_sent']
                total_packets_received += stats['packets_received']
                total_bytes_transmitted += stats['bytes_sent'] + stats['bytes_received']
            
            elapsed = time.time() - self.start_time
            
            return {
                'network_name': self.network_name,
                'uptime_seconds': elapsed,
                'total_nodes': len(self.nodes),
                'total_packets_sent': total_packets_sent,
                'total_packets_received': total_packets_received,
                'total_bytes_transmitted': total_bytes_transmitted,
                'average_throughput_mbps': (total_bytes_transmitted * 8) / (1024 * 1024 * elapsed) if elapsed > 0 else 0,
                'packet_loss_rate': self.packet_loss_rate,
                'node_statistics': node_stats
            }


class VirtualNode:
    """
    Virtual Node - represents a single node in the P2P network
    Each node has its own network interface, storage, and process management
    """
    
    def __init__(self, node_id: str, storage_capacity_gb: float = 10.0):
        """
        Initialize a virtual node
        
        Args:
            node_id: Unique identifier for the node
            storage_capacity_gb: Storage capacity in GB
        """
        self.node_id = node_id
        self.network_interface: Optional[NetworkInterface] = None
        
        # Import here to avoid circular imports
        from storage.virtual_storage import VirtualStorage
        self.storage = VirtualStorage(node_id, storage_capacity_gb)
        
        # Process management
        self.process_state = "READY"  # READY, WAITING, RUNNING, STOPPED
        self.is_running = True
        self.creation_time = time.time()
        
        # Connected peers
        self.peers: Dict[str, str] = {}  # peer_node_id -> peer_ip
        
        logger.info(f"[NODE {node_id}] Virtual node initialized with {storage_capacity_gb}GB storage")
    
    def initialize_network_interface(self, bandwidth_mbps: float = 64.0):
        """Initialize the network interface for this node"""
        self.network_interface = NetworkInterface(self.node_id, "", bandwidth_mbps)
        logger.info(f"[NODE {self.node_id}] Network interface initialized")
    
    def is_alive(self) -> bool:
        """Check if node is alive"""
        return self.is_running and self.process_state != "STOPPED"
    
    def set_process_state(self, state: str):
        """Update process state (READY, WAITING, RUNNING, STOPPED)"""
        valid_states = ["READY", "WAITING", "RUNNING", "STOPPED"]
        if state not in valid_states:
            raise ValueError(f"Invalid state: {state}")
        
        self.process_state = state
        logger.info(f"[NODE {self.node_id}] Process state changed to {state}")
    
    def add_peer(self, peer_node_id: str, peer_ip: str):
        """Register a peer node"""
        self.peers[peer_node_id] = peer_ip
        logger.info(f"[NODE {self.node_id}] Peer {peer_node_id} ({peer_ip}) added")
    
    def get_node_info(self) -> Dict:
        """Get detailed node information"""
        return {
            'node_id': self.node_id,
            'ip_address': self.network_interface.ip_address if self.network_interface else None,
            'status': 'ALIVE' if self.is_alive() else 'DEAD',
            'process_state': self.process_state,
            'storage_capacity_gb': self.storage.capacity_gb,
            'storage_used_gb': self.storage.get_used_space_gb(),
            'storage_available_gb': self.storage.get_available_space_gb(),
            'files_stored': len(self.storage.file_segments),
            'peers': self.peers,
            'uptime_seconds': time.time() - self.creation_time
        }
