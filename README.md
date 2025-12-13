# P2P Distributed Storage System

A complete distributed peer-to-peer file storage system built from scratch with advanced features for cloud storage simulation.

## Features

### Core Architecture
- **Virtual Network**: Simulates TCP/IP with 5+ independent nodes
- **Distributed Storage**: Files chunked and distributed across multiple nodes
- **Network Simulation**: Real TCP/IP layering with acknowledgments and error handling
- **Bandwidth Simulation**: 64KB/s bandwidth simulation with transfer time tracking

### Communication
- **gRPC/RPC**: Inter-node communication using gRPC and protocol buffers
- **SSH**: Secure remote node connections and command execution
- **Network Topology**: Dynamic node discovery and topology management

### Security & Authentication
- **User Registration & Login**: Multi-user support with authentication
- **OTP Authentication**: Time-based One-Time Password (TOTP) for enhanced security
- **Email Notifications**: Login alerts and OTP delivery via email
- **Password Security**: PBKDF2 hashing with salt for secure password storage
- **Session Management**: Token-based session management with expiry

### Features
- **File Operations**: Upload, download, delete files across network
- **Distributed Chunking**: Automatic file chunking (64KB default) and distribution
- **Node Health Monitoring**: Broadcast health checks to detect alive/dead nodes
- **Process Management**: Process states (READY, WAITING, RUNNING, STOPPED)
- **Storage Allocation**: Real HDD allocation per node with capacity limits
- **Persistent Metadata**: Metadata storage for file tracking and recovery

### User Interfaces
- **Command-Line Interface**: Full-featured CLI for all operations
- **Web UI**: Google Drive-like web interface (Flask + responsive HTML/CSS)
- **REST API**: RESTful API endpoints for integration

## Architecture

```
P2P Storage System
├── Core
│   ├── Orchestrator (main coordinator)
│   └── System initialization
├── Network
│   ├── Virtual Network (TCP/IP simulation)
│   ├── Network Interface (per-node)
│   ├── Packet handling (SYN, ACK, DATA, FIN)
│   └── Virtual Nodes
├── Storage
│   ├── Virtual Storage (per-node)
│   ├── File Chunking (64KB segments)
│   ├── Segment Management
│   └── Metadata Storage
├── Authentication
│   ├── User Management
│   ├── Password Hashing (PBKDF2)
│   ├── OTP Management (TOTP)
│   ├── Email Notifications
│   └── SSH Key Management
├── Communication
│   ├── gRPC Services
│   ├── SSH Handler
│   └── Protocol Buffers
├── CLI
│   └── Command-line Interface
├── Web
│   └── REST API + Web Dashboard
└── gRPC
    └── Service definitions (proto)
```

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Optional: SSH server for remote node connections

### Setup Steps

1. **Clone/Extract the project**
```bash
cd P2P
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Verify installation**
```bash
python main.py --help
```

## Usage

### Run Demo Mode
Demonstrates all features with automatic file uploads and distribution:

```bash
python main.py --mode demo
```

Output:
- Creates test files
- Chunks and distributes across 5 nodes
- Performs health checks
- Generates system report

### Run CLI Mode
Interactive command-line interface:

```bash
python main.py --mode cli
```

Available commands:
```
register <username> <email> <password>  - Register new user
login <username> <password>              - Login to system
enable_otp <username>                    - Enable OTP authentication
upload <file_path>                       - Upload file to network
download <file_id> <output_path>         - Download file from network
nodes                                    - List all nodes
health                                   - Check node health status
storage                                  - View storage statistics
topology                                 - Display network topology
stats                                    - Show network statistics
clear                                    - Clear screen
exit / quit                              - Exit program
```

### Run Web Mode
Start web interface (Google Drive-like):

```bash
python main.py --mode web
```

Then open browser: `http://localhost:5000`

### Custom Configuration

```bash
# Create network with 7 nodes, 15GB per node
python main.py --mode demo --nodes 7 --storage 15

# Create network with 10 nodes, 20GB per node
python main.py --mode cli --nodes 10 --storage 20
```

## File Distribution Example

When you upload a 2.5MB file:

1. **Chunking**: File split into 40 chunks of 64KB each
2. **Distribution**: Chunks distributed across 5 nodes (8 chunks each)
3. **Bandwidth Simulation**: Each chunk takes ~1 second to transfer at 64KB/s
4. **Total Upload Time**: ~40 seconds for 2.5MB file
5. **Metadata**: Central tracking of where each chunk is stored

```
Original File (2.5MB)
│
├─> Chunk 01 → Node_01 → node_storage/Node_01/file_hash_chunk_00.bin
├─> Chunk 02 → Node_02 → node_storage/Node_02/file_hash_chunk_01.bin
├─> Chunk 03 → Node_03 → node_storage/Node_03/file_hash_chunk_02.bin
├─> Chunk 04 → Node_04 → node_storage/Node_04/file_hash_chunk_03.bin
├─> Chunk 05 → Node_05 → node_storage/Node_05/file_hash_chunk_04.bin
├─> Chunk 06 → Node_01 → node_storage/Node_01/file_hash_chunk_05.bin
└─> ... (continues round-robin)
```

## Network Simulation Details

### TCP/IP Layers
- **Application Layer**: gRPC services and CLI/Web interfaces
- **Transport Layer**: TCP simulation with packet types (SYN, SYN-ACK, ACK, DATA, FIN)
- **Network Layer**: IP routing and forwarding
- **Link Layer**: Bandwidth simulation and packet loss

### Packet Types
- **SYN**: Connection initiation (3-way handshake)
- **SYN-ACK**: Connection acknowledgment
- **ACK**: Acknowledgment for received data
- **DATA**: Actual file data transfer
- **FIN**: Connection termination
- **HEALTH_CHECK**: Periodic node health probes

### Bandwidth Simulation
- Default: 64KB/s (simulating slow network)
- Transmission delay: `payload_size / bandwidth_bps`
- Propagation delay: 1-10ms (random)
- Packet loss: 1% (configurable)

## Authentication Flow

### Basic Login
```
User → Login → Password Hash → Session Token
      (username/password)       (valid 24h)
```

### OTP Login
```
User → Login → Password Hash → Request OTP → Email OTP
                   (OK)        → Verify OTP → Session Token
```

### User Information
```
User Model:
├── Username (unique)
├── Email (unique)
├── Password Hash + Salt (PBKDF2)
├── OTP Manager (optional)
├── Session Tokens (multiple active)
└── Last Login Timestamp
```

## Storage Structure

Each node has its own storage directory:

```
node_storage/
├── Node_01/
│   ├── metadata.json                  (file metadata)
│   ├── file_hash_chunk_00.bin         (64KB segment)
│   ├── file_hash_chunk_01.bin
│   └── ...
├── Node_02/
│   ├── metadata.json
│   ├── file_hash_chunk_01.bin
│   └── ...
└── ...
```

### Metadata File
```json
{
  "file_id": {
    "file_id": "a1b2c3d4e5f6g7h8",
    "original_filename": "document.pdf",
    "file_hash": "sha256_hash...",
    "total_size_bytes": 2621440,
    "chunk_size_bytes": 65536,
    "total_chunks": 40,
    "chunks": {
      "0": "Node_01",
      "1": "Node_02",
      "2": "Node_03",
      ...
    },
    "created_at": "2025-01-10T10:30:00",
    "replicas": 1
  }
}
```

## Performance Metrics

### Bandwidth Simulation
- 64KB/s default rate
- Configurable per node
- Realistic transfer time calculation

### Network Statistics
- Packets sent/received
- Bytes transmitted
- Average throughput (Mbps)
- Packet loss rate
- Per-node interface statistics

### Storage Information
- Total capacity
- Used space
- Available space
- Utilization percentage
- Number of segments

## Node Health Monitoring

### Health Check
```python
# Broadcast to all nodes
health_status = network.broadcast_health_check()

# Returns: {node_id: is_alive}
# 'ALIVE' if node.is_running and state != 'STOPPED'
# 'DEAD' otherwise
```

### Node States
- **READY**: Idle, waiting for operations
- **WAITING**: Waiting for I/O (network, disk)
- **RUNNING**: Currently processing
- **STOPPED**: Offline or maintenance

## REST API Endpoints

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/enable-otp` - Enable OTP

### Files
- `POST /api/files/upload` - Upload file
- `GET /api/files/list` - List files
- `GET /api/files/download/<file_id>` - Download file
- `DELETE /api/files/<file_id>` - Delete file

### Network
- `GET /api/network/topology` - Get network topology
- `GET /api/network/statistics` - Get network stats
- `GET /api/network/health` - Check health status

### Storage
- `GET /api/storage/status` - Storage overview

## Security Considerations

### Password Security
- PBKDF2 with SHA256
- 100,000 iterations
- 32-byte random salt per user

### OTP Security
- Time-based (TOTP) with 30-second window
- Backup codes for account recovery
- Replay attack prevention

### Network Security
- SSH for remote connections
- Session tokens with expiry
- IP address validation (optional)

### File Security
- SHA256 checksums for integrity
- Distributed storage (no single point of failure)
- Segment-level checksums

## Troubleshooting

### Issue: Module not found
**Solution**: Ensure you're in the project root directory and Python path is set correctly.

### Issue: Port already in use
**Solution**: Change port or kill process on port 5000
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <pid> /F

# Linux/Mac
lsof -i :5000
kill -9 <pid>
```

### Issue: Permission denied on SSH key
**Solution**: Fix permissions
```bash
chmod 600 ssh_keys/*_private
chmod 644 ssh_keys/*_public.pub
```

### Issue: Storage full
**Solution**: Check node storage and clear if needed
```python
# In Python
from storage.virtual_storage import VirtualStorage
storage = VirtualStorage('Node_01')
storage.clear_storage()  # WARNING: Deletes all data
```

## Example Workflow

### Step 1: Start System
```bash
python main.py --mode cli --nodes 5 --storage 10
```

### Step 2: Register User
```
P2P-Storage > register alice alice@example.com mypassword
✓ User registered successfully
Enable OTP authentication? (y/n): y
```

### Step 3: Login
```
P2P-Storage > login alice mypassword
✓ Login successful
  Session token: abc123def456...
```

### Step 4: Upload File
```
P2P-Storage > upload test_files/document.pdf
Starting upload: test_files/document.pdf
File size: 2.45 MB
File chunked into 40 segments
  [100%] Segment 40 stored on Node_05
✓ Upload complete!
  File ID: a1b2c3d4e5f6g7h8
  Total chunks: 40
```

### Step 5: View Nodes
```
P2P-Storage > nodes
Network: P2P_Storage_Network (192.168.1.0/24)
─────────────────────────────────────────────────────────
Node ID         IP Address      Status     Storage          Files
─────────────────────────────────────────────────────────
Node_01         192.168.1.2     ALIVE      2.50GB / 10.00GB  8
Node_02         192.168.1.3     ALIVE      2.50GB / 10.00GB  8
Node_03         192.168.1.4     ALIVE      2.50GB / 10.00GB  8
Node_04         192.168.1.5     ALIVE      2.50GB / 10.00GB  8
Node_05         192.168.1.6     ALIVE      2.50GB / 10.00GB  8
─────────────────────────────────────────────────────────
```

### Step 6: Health Check
```
P2P-Storage > health
Health Check Results:
────────────────────────────────────────────────────────
Node_01              ✓ ALIVE
Node_02              ✓ ALIVE
Node_03              ✓ ALIVE
Node_04              ✓ ALIVE
Node_05              ✓ ALIVE
────────────────────────────────────────────────────────
Total: 5/5 nodes alive
```

## Advanced Topics

### gRPC Service Implementation
1. Proto files are in `grpc_service/p2p_service.proto`
2. Generate Python code:
```bash
python -m grpc_tools.protoc -I./grpc_service \
  --python_out=./grpc_service \
  --grpc_python_out=./grpc_service \
  ./grpc_service/p2p_service.proto
```

### SSH Remote Execution
```python
from auth.ssh_handler import SSHKeyManager, SSHNodeManager

key_manager = SSHKeyManager()
ssh_manager = SSHNodeManager(key_manager)

# Add remote node
ssh_manager.add_remote_node("Node_01", "192.168.1.2")

# Execute command
exit_code, stdout, stderr = ssh_manager.execute_on_node("Node_01", "ls -la")
```

### Custom Bandwidth Simulation
```python
# Create node with custom bandwidth (1 Mbps)
node = VirtualNode("Node_01", storage_capacity_gb=10.0)
node.initialize_network_interface(bandwidth_mbps=1.0)

# Now file transfers will be faster
```

## File Format Specifications

### Network Packet Structure
```python
@dataclass
class NetworkPacket:
    packet_type: PacketType      # SYN, ACK, DATA, etc.
    source_ip: str
    destination_ip: str
    payload: bytes
    timestamp: float
    packet_id: str
    seq_number: int
    ack_number: int
    checksum: int
```

### File Segment Structure
```python
@dataclass
class FileSegment:
    segment_id: str              # "file_hash_chunk_0"
    file_hash: str               # SHA256 of original file
    chunk_number: int
    data: bytes                  # Actual segment data
    size_bytes: int
    checksum: str                # SHA256 of segment
    timestamp: datetime
```

## Future Enhancements

- [ ] Replication across multiple nodes
- [ ] Fault tolerance and recovery
- [ ] Advanced caching strategies
- [ ] Load balancing
- [ ] Sharding for larger datasets
- [ ] Blockchain-based verification
- [ ] API rate limiting
- [ ] Advanced monitoring dashboard
- [ ] Automated backup system
- [ ] Data compression

## License

Educational Use - Cloud Systems Research

## Support

For issues, improvements, or questions:
1. Check the troubleshooting section
2. Review log files in `p2p_storage.log`
3. Check existing issues in documentation

## References

- TCP/IP Protocol Stack
- Distributed Systems Concepts
- Peer-to-Peer Network Architecture
- gRPC and Protocol Buffers
- Cryptographic Hashing Algorithms
- RESTful API Design

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Authors**: Cloud Systems Research Team
