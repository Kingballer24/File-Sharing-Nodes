"""
P2P Storage System - Test & Validation Suite
Tests all major components and features
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemValidator:
    """Validates all P2P system components"""
    
    def __init__(self):
        """Initialize validator"""
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test(self, name: str, func):
        """Run a test"""
        try:
            logger.info(f"Testing: {name}...")
            func()
            self.results.append((name, True, "PASS"))
            self.passed += 1
            logger.info(f"[OK] {name}")
        except Exception as e:
            self.results.append((name, False, str(e)))
            self.failed += 1
            logger.error(f"[ERROR] {name}: {e}")
    
    def run_all_tests(self):
        """Run all validation tests"""
        logger.info("="*80)
        logger.info("P2P STORAGE SYSTEM - VALIDATION SUITE")
        logger.info("="*80)
        
        # Test imports
        self.test("Import network module", lambda: __import__('network.virtual_network'))
        self.test("Import storage module", lambda: __import__('storage.virtual_storage'))
        self.test("Import auth module", lambda: __import__('auth.authentication'))
        self.test("Import CLI module", lambda: __import__('cli.cli_interface'))
        self.test("Import web module", lambda: __import__('web.web_server'))
        
        # Test core components
        self.test("Virtual network creation", self.test_network_creation)
        self.test("Virtual node creation", self.test_node_creation)
        self.test("Network interface", self.test_network_interface)
        self.test("IP assignment", self.test_ip_assignment)
        
        # Test storage
        self.test("Virtual storage creation", self.test_storage_creation)
        self.test("File chunking", self.test_file_chunking)
        self.test("Segment storage", self.test_segment_storage)
        self.test("Metadata persistence", self.test_metadata_persistence)
        
        # Test authentication
        self.test("User registration", self.test_user_registration)
        self.test("Password hashing", self.test_password_hashing)
        self.test("OTP generation", self.test_otp_generation)
        
        # Test network operations
        self.test("Health check", self.test_health_check)
        self.test("Network topology", self.test_network_topology)
        self.test("Network statistics", self.test_network_statistics)
        
        # Print summary
        self.print_summary()
    
    def test_network_creation(self):
        """Test virtual network creation"""
        from network.virtual_network import VirtualNetwork
        
        network = VirtualNetwork("test_network")
        assert network.network_name == "test_network"
        assert len(network.nodes) == 0
    
    def test_node_creation(self):
        """Test virtual node creation"""
        from network.virtual_network import VirtualNode
        
        node = VirtualNode("test_node", storage_capacity_gb=10.0)
        assert node.node_id == "test_node"
        assert node.storage.capacity_gb == 10.0
    
    def test_network_interface(self):
        """Test network interface"""
        from network.virtual_network import NetworkInterface
        
        iface = NetworkInterface("test_node", "192.168.1.1", bandwidth_mbps=64.0)
        assert iface.node_id == "test_node"
        assert iface.ip_address == "192.168.1.1"
    
    def test_ip_assignment(self):
        """Test automatic IP assignment"""
        from network.virtual_network import VirtualNetwork, VirtualNode
        
        network = VirtualNetwork("test_network")
        node = VirtualNode("test_node")
        node.initialize_network_interface()
        
        ip = network.register_node(node)
        assert ip == "192.168.1.2"  # First assigned IP
        
        node2 = VirtualNode("test_node_2")
        node2.initialize_network_interface()
        ip2 = network.register_node(node2)
        assert ip2 == "192.168.1.3"  # Second assigned IP
    
    def test_storage_creation(self):
        """Test virtual storage creation"""
        from storage.virtual_storage import VirtualStorage
        
        storage = VirtualStorage("test_node", capacity_gb=5.0)
        assert storage.node_id == "test_node"
        assert storage.capacity_gb == 5.0
        assert storage.used_bytes == 0
    
    def test_file_chunking(self):
        """Test file chunking"""
        from storage.virtual_storage import VirtualStorage
        import tempfile
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as f:
            f.write(b"A" * (256 * 1024))  # 256KB file
            temp_path = f.name
        
        try:
            storage = VirtualStorage("test_node")
            file_id, segments = storage.chunk_file(temp_path, chunk_size_bytes=64*1024)
            
            assert len(segments) == 4  # 256KB / 64KB = 4 chunks
            assert segments[0].size_bytes == 64 * 1024
        finally:
            os.unlink(temp_path)
    
    def test_segment_storage(self):
        """Test segment storage"""
        from storage.virtual_storage import VirtualStorage, FileSegment
        
        storage = VirtualStorage("test_node")
        segment = FileSegment(
            segment_id="test_segment",
            file_hash="abc123",
            chunk_number=0,
            data=b"test data",
            size_bytes=9,
            checksum="def456"
        )
        
        success = storage.store_segment(segment)
        assert success is True
        assert "test_segment" in storage.file_segments
    
    def test_metadata_persistence(self):
        """Test metadata persistence"""
        from storage.virtual_storage import VirtualStorage
        
        storage = VirtualStorage("test_node")
        storage.save_metadata()
        
        # Check metadata file exists
        assert os.path.exists(storage.metadata_file)
    
    def test_user_registration(self):
        """Test user registration"""
        from auth.authentication import AuthenticationManager
        
        auth = AuthenticationManager()
        success, msg = auth.register_user("testuser", "test@example.com", "password123")
        
        assert success is True
        assert "testuser" in auth.users
    
    def test_password_hashing(self):
        """Test password hashing"""
        from auth.authentication import PasswordManager
        
        password = "test_password"
        hashed, salt = PasswordManager.hash_password(password)
        
        # Verify correct password
        assert PasswordManager.verify_password(password, hashed, salt) is True
        
        # Verify wrong password
        assert PasswordManager.verify_password("wrong_password", hashed, salt) is False
    
    def test_otp_generation(self):
        """Test OTP generation"""
        from auth.authentication import OTPManager
        
        otp = OTPManager("test@example.com")
        code = otp.get_current_code()
        
        assert len(code) == 6
        assert code.isdigit()
    
    def test_health_check(self):
        """Test health check"""
        from core.orchestrator import P2PStorageOrchestrator
        
        orchestrator = P2PStorageOrchestrator(node_count=3)
        orchestrator.initialize_nodes()
        
        health = orchestrator.broadcast_health_check()
        assert len(health) == 3
        
        # All nodes should be alive
        for is_alive in health.values():
            assert is_alive is True
    
    def test_network_topology(self):
        """Test network topology"""
        from core.orchestrator import P2PStorageOrchestrator
        
        orchestrator = P2PStorageOrchestrator(node_count=3)
        orchestrator.initialize_nodes()
        
        topology = orchestrator.virtual_network.get_network_topology()
        assert topology['nodes'] == 3
        assert len(topology['node_details']) == 3
    
    def test_network_statistics(self):
        """Test network statistics"""
        from core.orchestrator import P2PStorageOrchestrator
        
        orchestrator = P2PStorageOrchestrator(node_count=3)
        orchestrator.initialize_nodes()
        
        stats = orchestrator.virtual_network.get_statistics()
        assert stats['total_nodes'] == 3
        assert 'uptime_seconds' in stats
    
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY")
        logger.info("="*80)
        
        for name, passed, message in self.results:
            status = "[PASS]" if passed else "[FAIL]"
            logger.info(f"{status}: {name}")
            if not passed:
                logger.info(f"  → {message}")
        
        logger.info("="*80)
        logger.info(f"Total: {total} tests")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        
        if self.failed == 0:
            logger.info("\n[OK] ALL TESTS PASSED!")
            return 0
        else:
            logger.warning(f"\n[ERROR] {self.failed} TEST(S) FAILED")
            return 1


def main():
    """Run validation suite"""
    validator = SystemValidator()
    exit_code = validator.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
