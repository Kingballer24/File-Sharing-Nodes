# P2P Distributed Storage System - Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     P2P STORAGE NETWORK                         │
│                    (Virtual Network Layer)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Node_01  │  │ Node_02  │  │ Node_03  │  │ Node_04  │       │
│  │          │  │          │  │          │  │          │       │
│  │ 10GB     │  │ 10GB     │  │ 10GB     │  │ 10GB     │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│       │              │              │              │            │
│       └──────────────┴──────────────┴──────────────┘            │
│           TCP/IP Network (64KB/s bandwidth)                     │
│                                                                 │
│  ┌──────────┐                                                  │
│  │ Node_05  │ ← Optional 5th+ nodes                            │
│  └──────────┘                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Component Architecture

### 1. Network Layer (TCP/IP Simulation)

```
VirtualNetwork
├── Nodes Management
│   ├── register_node()
│   ├── assign_ip_address()
│   └── broadcast_health_check()
│
├── Packet Routing
│   ├── send_packet()
│   ├── receive_packet()
│   └── NetworkPacket (SYN, ACK, DATA, FIN)
│
└── Network Statistics
    ├── get_statistics()
    ├── get_network_topology()
    └── packet_loss_rate simulation
```

#### NetworkInterface (Per-Node)

```
NetworkInterface
├── IP Management
│   ├── ip_address: "192.168.1.x"
│   └── bandwidth_mbps: 64.0
│
├── Packet Operations
│   ├── send_packet() → transmission_time
│   ├── receive_packet()
│   └── get_pending_packets()
│
└── Statistics
    ├── packets_sent / received
    ├── bytes_sent / received
    └── throughput_bps
```

#### VirtualNode

```
VirtualNode
├── Identification
│   ├── node_id: "Node_01"
│   └── network_interface: NetworkInterface
│
├── Storage
│   └── storage: VirtualStorage (10GB default)
│
├── State Management
│   ├── process_state: READY|WAITING|RUNNING|STOPPED
│   ├── is_running: bool
│   └── is_alive(): bool
│
├── Peer Management
│   ├── peers: {peer_id: peer_ip}
│   └── add_peer()
│
└── Health
    └── get_node_info()
```

### 2. Storage Layer (Distributed File Storage)

```
VirtualStorage (Per-Node)
├── Storage Allocation
│   ├── capacity_bytes: 10GB
│   ├── used_bytes: tracked
│   └── storage_root: actual HDD path
│
├── File Segments
│   └── file_segments: {segment_id: FileSegment}
│
├── File Operations
│   ├── chunk_file() → [FileSegment, ...]
│   ├── store_segment() → write to disk
│   ├── retrieve_segment() → read from disk
│   └── reconstruct_file() → merge segments
│
├── Metadata Management
│   ├── file_metadata: {file_id: FileMetadata}
│   ├── save_metadata() → JSON persistence
│   ├── load_metadata() → recover from disk
│   └── metadata.json file
│
└── Statistics
    ├── get_used_space_gb()
    ├── get_available_space_gb()
    └── get_storage_info()
```

#### FileSegment Structure

```
FileSegment
├── segment_id: "file_hash_chunk_0"
├── file_hash: SHA256 of original file
├── chunk_number: 0, 1, 2, ...
├── data: bytes (actual segment content)
├── size_bytes: 65536 (default 64KB)
├── checksum: SHA256 of segment
└── timestamp: datetime

On Disk: node_storage/Node_01/file_hash_chunk_0.bin
```

#### FileMetadata Structure

```
FileMetadata
├── file_id: first 16 chars of SHA256
├── original_filename: "document.pdf"
├── file_hash: full SHA256
├── total_size_bytes: original file size
├── chunk_size_bytes: 65536
├── total_chunks: number of segments
├── chunks: {chunk_num: node_id} mapping
├── created_at: datetime
└── replicas: replication factor
```

### 3. Authentication & Security Layer

```
AuthenticationManager
├── User Management
│   ├── users: {username: User}
│   ├── register_user()
│   └── login()
│
└── OTP & Email
    ├── email_notifier: EmailNotifier
    └── otp_manager: OTPManager
```

#### User Model

```
User
├── Credentials
│   ├── username: unique
│   ├── email: unique
│   ├── password_hash: PBKDF2(SHA256)
│   └── password_salt: 32 bytes
│
├── Authentication
│   ├── otp_enabled: bool
│   ├── otp_manager: OTPManager
│   └── verify_password(): bool
│
├── Session Management
│   ├── session_tokens: {token: (timestamp, ip)}
│   ├── create_session() → token
│   ├── validate_session() → bool
│   └── last_login: datetime
│
└── Metadata
    ├── created_at: datetime
    └── get_user_info(): Dict
```

#### Password Security

```
Password Storage:
1. Generate salt: salt = os.urandom(32)
2. Hash: hash = PBKDF2-SHA256(password, salt, 100000 iterations)
3. Store: {username: (hash_hex, salt_hex)}

Password Verification:
1. Load: (hash_hex, salt_hex) = database
2. Compute: computed_hash = PBKDF2-SHA256(password, salt, 100000 iterations)
3. Compare: hmac.compare_digest(computed_hash, hash_hex)
```

#### OTP Authentication

```
OTP (TOTP) Flow:
1. User enables OTP → secret_key generated
2. User scans QR code → adds to authenticator app
3. App generates 6-digit code every 30 seconds
4. User enters code → verified with time window
5. Code marked as used → replay attack prevention

Backup Codes:
- 10 backup codes generated
- Each code usable once
- Used if authenticator unavailable
```

### 4. Communication Layer

#### gRPC Services

```
FileStorageService (gRPC)
├── StoreSegment(StoreSegmentRequest) → StoreSegmentResponse
├── RetrieveSegment(RetrieveSegmentRequest) → RetrieveSegmentResponse
├── HealthCheck(HealthCheckRequest) → HealthCheckResponse
└── GetNetworkTopology(NetworkTopologyRequest) → NetworkTopologyResponse

FileTransferService (gRPC)
├── UploadFile(UploadFileRequest) → UploadFileResponse
└── DownloadFile(DownloadFileRequest) → DownloadFileResponse
```

#### SSH Handler

```
SSHKeyManager
├── generate_keypair() → (private_key, public_key)
├── load_private_key()
└── load_public_key()

SSHRemoteNode
├── connect() → bool
├── execute_command() → (exit_code, stdout, stderr)
├── upload_file()
├── download_file()
└── disconnect()

SSHNodeManager
├── add_remote_node()
├── connect_to_node()
├── execute_on_node()
├── broadcast_command()
└── disconnect_all()
```

### 5. Orchestrator (System Coordinator)

```
P2PStorageOrchestrator
├── virtual_network: VirtualNetwork
├── nodes: {node_id: VirtualNode}
├── auth_manager: AuthenticationManager
├── ssh_key_manager: SSHKeyManager
├── ssh_node_manager: SSHNodeManager
│
├── Initialization
│   ├── initialize_nodes()
│   ├── start_network()
│   └── setup_demo_users()
│
├── Operations
│   ├── broadcast_health_check()
│   ├── get_system_info()
│   └── get_detailed_report()
│
└── Statistics
    └── network_stats, storage_stats
```

### 6. User Interface Layer

#### CLI Interface

```
P2PStorageCLI (cmd module)
├── Authentication Commands
│   ├── register
│   ├── login
│   ├── logout
│   └── enable_otp
│
├── File Operations
│   ├── upload
│   ├── download
│   └── (delete in web UI)
│
├── Network Commands
│   ├── nodes
│   ├── health
│   ├── storage
│   ├── topology
│   └── stats
│
└── System
    ├── clear
    ├── exit
    └── quit
```

#### Web Interface

```
P2PWebUI (Flask)
├── REST API Endpoints
│   ├── /api/auth/* (authentication)
│   ├── /api/files/* (file operations)
│   ├── /api/network/* (network info)
│   ├── /api/storage/* (storage info)
│   └── /api/dashboard (overview)
│
├── Web Pages
│   ├── / (login/dashboard)
│   ├── /dashboard (main interface)
│   └── /files (file manager)
│
└── Features
    ├── User authentication
    ├── File upload/download
    ├── Network status
    ├── Storage visualization
    └── Real-time stats
```

## Data Flow Diagrams

### File Upload Flow

```
User Upload Request
    ↓
[CLI / Web Interface]
    ↓
Upload to Node_01
    ↓
Chunk File (64KB segments)
    ↓
┌─ Chunk 1 → Store on Node_01
├─ Chunk 2 → Store on Node_02
├─ Chunk 3 → Store on Node_03
├─ Chunk 4 → Store on Node_04
└─ Chunk 5 → Store on Node_05
    ↓
Update Metadata (where each chunk is stored)
    ↓
Save Metadata to JSON
    ↓
Return file_id to user
```

### File Download Flow

```
User Download Request (file_id)
    ↓
Lookup Metadata
    ↓
┌─ Retrieve Chunk 1 from Node_01
├─ Retrieve Chunk 2 from Node_02
├─ Retrieve Chunk 3 from Node_03
├─ Retrieve Chunk 4 from Node_04
└─ Retrieve Chunk 5 from Node_05
    ↓
Merge Chunks in Order
    ↓
Verify Checksum
    ↓
Return File to User
```

### Authentication Flow

```
Basic Login:
User → Credentials → Password Verification → Session Token
                        ↓
                    PBKDF2 Hash Check
                        ↓
                     Match? → Yes/No

OTP Login:
User → Credentials → Password Check → OTP Required
                        ↓              ↓
                       Pass          User enters OTP code
                                         ↓
                                    Time window check
                                         ↓
                                    Replay check
                                         ↓
                                    Valid? → Session Token
```

### Health Check Flow

```
Coordinator requests health check
    ↓
Broadcast to all nodes
    ↓
Each node returns:
├─ Node_01 → is_alive = True (READY state)
├─ Node_02 → is_alive = True (READY state)
├─ Node_03 → is_alive = False (STOPPED state)
├─ Node_04 → is_alive = True (RUNNING state)
└─ Node_05 → is_alive = True (READY state)
    ↓
Aggregate results
    ↓
Log and report to user
```

## Process States

```
┌─────────┐
│  READY  │ (Idle, waiting for operations)
└────┬────┘
     │ operation requested
     ↓
┌─────────┐
│ WAITING │ (Waiting for I/O: network, disk)
└────┬────┘
     │ I/O available
     ↓
┌─────────┐
│RUNNING  │ (Processing operation)
└────┬────┘
     │ operation complete
     ↓
┌─────────┐
│ READY  │ (Return to ready state)
└─────────┘

Alternative:
Any State → STOPPED (shutdown/error)
```

## Network Packet Structure

```
NetworkPacket
├── packet_type: SYN, SYN_ACK, ACK, DATA, FIN, HEALTH_CHECK
├── source_ip: "192.168.1.2"
├── destination_ip: "192.168.1.3"
├── payload: bytes (actual data)
├── timestamp: unix timestamp
├── packet_id: unique identifier
├── seq_number: sequence number (TCP)
├── ack_number: acknowledgment number (TCP)
└── checksum: integrity check

Simulated Network Behavior:
├── Transmission Delay = payload_size / bandwidth_bps
├── Propagation Delay = 1-10ms (random)
├── Packet Loss = 1% (configurable)
└── Total Delivery Time = Transmission + Propagation + Processing
```

## Bandwidth Simulation

```
Bandwidth: 64KB/s (0.064 Mbps)

Example Transfer Times:
├── 64KB file → 1 second
├── 128KB file → 2 seconds
├── 256KB file → 4 seconds
├── 1MB file → 16 seconds
└── 5MB file → 80 seconds

Real transfer simulation:
1. Calculate transmission time
2. Sleep for calculated time
3. Add random propagation delay (1-10ms)
4. Simulate packet loss (1%)
5. Deliver packet when all delays complete
```

## File Distribution Example

```
Uploading 2.5MB File:

1. Chunking:
   2.5MB / 64KB = 40 chunks
   
2. Distribution (round-robin):
   Chunk 01 → Node_01
   Chunk 02 → Node_02
   Chunk 03 → Node_03
   Chunk 04 → Node_04
   Chunk 05 → Node_05
   Chunk 06 → Node_01 (wrap around)
   ... (continues)
   
   Result:
   Node_01: chunks 1, 6, 11, 16, 21, 26, 31, 36 (8 chunks)
   Node_02: chunks 2, 7, 12, 17, 22, 27, 32, 37 (8 chunks)
   Node_03: chunks 3, 8, 13, 18, 23, 28, 33, 38 (8 chunks)
   Node_04: chunks 4, 9, 14, 19, 24, 29, 34, 39 (8 chunks)
   Node_05: chunks 5, 10, 15, 20, 25, 30, 35, 40 (8 chunks)

3. Metadata:
   {
     "file_id": "a1b2c3d4e5f6g7h8",
     "chunks": {
       "0": "Node_01",
       "1": "Node_02",
       "2": "Node_03",
       ...
     }
   }

4. Retrieval:
   - Look up metadata
   - Fetch chunks from respective nodes
   - Merge in order
   - Verify integrity
```

## Storage Allocation

```
Total Network Storage: 50GB (5 nodes × 10GB each)

Per-Node Storage:
├── Node_01: 10GB
│   ├── Used: varies
│   ├── Metadata: metadata.json
│   └── Segments: multiple .bin files
├── Node_02: 10GB
├── Node_03: 10GB
├── Node_04: 10GB
└── Node_05: 10GB

Storage Utilization:
├── calculate used_bytes
├── calculate available = capacity - used
├── calculate utilization% = (used / capacity) × 100
└── Prevent overfill (error if used + new > capacity)
```

## Error Handling

```
Network Errors:
├── Packet Loss → Retry mechanism
├── Connection Timeout → Error message
├── Invalid IP → Routing error
└── Segment not found → Query other nodes

Storage Errors:
├── Insufficient space → Reject write
├── Corrupted segment → Retry/recover
├── Missing metadata → Attempt recovery
└── Failed write → Log and notify

Authentication Errors:
├── Invalid credentials → Reject login
├── Expired session → Request re-login
├── OTP mismatch → Reject
└── Invalid token → Unauthorized
```

## Scalability Considerations

```
Current Design: 5-10 nodes, 10-25GB per node

Scaling Up:
├── More nodes → More distribution
├── Larger capacity → More storage
├── Replication → Data redundancy
├── Caching → Performance
└── Load balancing → Even distribution

Performance Bottlenecks:
├── Bandwidth (64KB/s simulation)
├── Disk I/O (local storage)
├── Network latency (1-10ms)
└── Metadata lookup (JSON serialization)
```

## Security Architecture

```
Layers:
1. Application Layer
   ├── User authentication
   ├── Session tokens
   └── Authorization checks

2. Transport Layer
   ├── gRPC encryption (TLS capable)
   ├── SSH tunneling
   └── OTP verification

3. Storage Layer
   ├── Checksum verification
   ├── Segment-level checksums
   └── Metadata protection

4. Network Layer
   ├── IP filtering
   ├── Packet validation
   └── Firewall rules (simulated)
```

---

This comprehensive architecture enables:
- ✓ Distributed storage across independent nodes
- ✓ Real TCP/IP simulation with realistic delays
- ✓ Secure communication with encryption
- ✓ Robust file management and recovery
- ✓ User authentication with OTP
- ✓ Scalable to multiple nodes
- ✓ Monitoring and health checks
- ✓ Persistent data storage on real HDD
