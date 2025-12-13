"""
SSH Implementation for Secure Remote Node Communication
"""

import os
import paramiko
import logging
from typing import Dict, Optional, Tuple
from paramiko import AutoAddPolicy, SSHClient, RSAKey
import io

logger = logging.getLogger(__name__)


class SSHKeyManager:
    """Manages SSH key generation and storage"""
    
    def __init__(self, keys_dir: str = "./ssh_keys"):
        """
        Initialize SSH key manager
        
        Args:
            keys_dir: Directory to store SSH keys
        """
        self.keys_dir = keys_dir
        os.makedirs(keys_dir, exist_ok=True)
        
        logger.info(f"[SSH] Key manager initialized: {keys_dir}")
    
    def generate_keypair(self, node_id: str, key_size: int = 2048) -> Tuple[str, str]:
        """
        Generate SSH keypair for a node
        
        Args:
            node_id: Node identifier
            key_size: RSA key size
            
        Returns:
            Tuple of (private_key_path, public_key_path)
        """
        try:
            private_key = paramiko.RSAKey.generate(bits=key_size)
            
            private_key_path = os.path.join(self.keys_dir, f"{node_id}_private")
            public_key_path = os.path.join(self.keys_dir, f"{node_id}_public.pub")
            
            # Save private key
            private_key.write_private_key_file(private_key_path)
            os.chmod(private_key_path, 0o600)
            
            # Save public key
            with open(public_key_path, 'w') as f:
                f.write(f"{private_key.get_name()} {private_key.get_base64()}")
            
            logger.info(f"[SSH] Keypair generated for {node_id}")
            return private_key_path, public_key_path
        
        except Exception as e:
            logger.error(f"[SSH] Error generating keypair: {e}")
            raise
    
    def load_private_key(self, key_path: str, password: Optional[str] = None) -> RSAKey:
        """Load private key from file"""
        try:
            return paramiko.RSAKey.from_private_key_file(key_path, password=password)
        except Exception as e:
            logger.error(f"[SSH] Error loading private key: {e}")
            raise
    
    def load_public_key(self, key_path: str) -> str:
        """Load public key from file"""
        try:
            with open(key_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"[SSH] Error loading public key: {e}")
            raise


class SSHRemoteNode:
    """SSH connection to a remote P2P node"""
    
    def __init__(self, node_id: str, ip_address: str, port: int = 22,
                 username: str = "p2p_node", private_key_path: str = None):
        """
        Initialize SSH connection
        
        Args:
            node_id: Remote node identifier
            ip_address: Remote node IP
            port: SSH port
            username: SSH username
            private_key_path: Path to private key
        """
        self.node_id = node_id
        self.ip_address = ip_address
        self.port = port
        self.username = username
        self.private_key_path = private_key_path
        
        self.ssh_client: Optional[SSHClient] = None
        self.is_connected = False
        
        logger.info(f"[SSH] Remote node initialized: {node_id} @ {ip_address}:{port}")
    
    def connect(self) -> bool:
        """Establish SSH connection to remote node"""
        try:
            self.ssh_client = SSHClient()
            self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            
            if self.private_key_path:
                pkey = paramiko.RSAKey.from_private_key_file(self.private_key_path)
                self.ssh_client.connect(
                    self.ip_address,
                    port=self.port,
                    username=self.username,
                    pkey=pkey,
                    timeout=10
                )
            else:
                self.ssh_client.connect(
                    self.ip_address,
                    port=self.port,
                    username=self.username,
                    timeout=10
                )
            
            self.is_connected = True
            logger.info(f"[SSH] Connected to {self.node_id}")
            return True
        
        except Exception as e:
            logger.error(f"[SSH] Connection error: {e}")
            self.is_connected = False
            return False
    
    def execute_command(self, command: str) -> Tuple[int, str, str]:
        """
        Execute command on remote node
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if not self.is_connected:
            if not self.connect():
                return -1, "", "Not connected"
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=30)
            return_code = stdout.channel.recv_exit_status()
            
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            logger.info(f"[SSH] Command executed on {self.node_id}: {command}")
            return return_code, output, error
        
        except Exception as e:
            logger.error(f"[SSH] Command execution error: {e}")
            return -1, "", str(e)
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload file to remote node
        
        Args:
            local_path: Local file path
            remote_path: Remote file path
            
        Returns:
            True if successful
        """
        if not self.is_connected:
            if not self.connect():
                return False
        
        try:
            sftp = self.ssh_client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            
            logger.info(f"[SSH] File uploaded to {self.node_id}: {remote_path}")
            return True
        
        except Exception as e:
            logger.error(f"[SSH] Upload error: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download file from remote node
        
        Args:
            remote_path: Remote file path
            local_path: Local file path
            
        Returns:
            True if successful
        """
        if not self.is_connected:
            if not self.connect():
                return False
        
        try:
            sftp = self.ssh_client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            
            logger.info(f"[SSH] File downloaded from {self.node_id}: {remote_path}")
            return True
        
        except Exception as e:
            logger.error(f"[SSH] Download error: {e}")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.ssh_client:
            self.ssh_client.close()
            self.is_connected = False
            logger.info(f"[SSH] Disconnected from {self.node_id}")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()


class SSHNodeManager:
    """Manages SSH connections to multiple remote nodes"""
    
    def __init__(self, key_manager: SSHKeyManager):
        """
        Initialize SSH node manager
        
        Args:
            key_manager: SSHKeyManager instance
        """
        self.key_manager = key_manager
        self.remote_nodes: Dict[str, SSHRemoteNode] = {}
        
        logger.info("[SSH] Node manager initialized")
    
    def add_remote_node(self, node_id: str, ip_address: str, 
                       port: int = 22, username: str = "p2p_node",
                       private_key_path: str = None) -> SSHRemoteNode:
        """Register a remote node"""
        remote_node = SSHRemoteNode(node_id, ip_address, port, username, private_key_path)
        self.remote_nodes[node_id] = remote_node
        
        logger.info(f"[SSH] Remote node added: {node_id}")
        return remote_node
    
    def connect_to_node(self, node_id: str) -> bool:
        """Connect to a remote node"""
        if node_id not in self.remote_nodes:
            logger.error(f"[SSH] Node not found: {node_id}")
            return False
        
        return self.remote_nodes[node_id].connect()
    
    def execute_on_node(self, node_id: str, command: str) -> Tuple[int, str, str]:
        """Execute command on remote node"""
        if node_id not in self.remote_nodes:
            return -1, "", "Node not found"
        
        return self.remote_nodes[node_id].execute_command(command)
    
    def broadcast_command(self, command: str) -> Dict[str, Tuple[int, str, str]]:
        """
        Execute command on all connected nodes
        
        Returns:
            Dict of {node_id: (return_code, stdout, stderr)}
        """
        results = {}
        
        for node_id, remote_node in self.remote_nodes.items():
            results[node_id] = remote_node.execute_command(command)
        
        return results
    
    def disconnect_all(self):
        """Disconnect from all remote nodes"""
        for remote_node in self.remote_nodes.values():
            remote_node.disconnect()
        
        logger.info("[SSH] All connections closed")
