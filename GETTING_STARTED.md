# P2P Distributed Storage System - Getting Started

## Welcome! 👋

You now have a complete, production-ready P2P distributed storage system. This guide will help you get started immediately.

## What You Have

A fully implemented distributed storage system featuring:
- ✓ 5 virtual nodes with independent storage
- ✓ TCP/IP network simulation with realistic delays
- ✓ File distribution across multiple nodes
- ✓ User authentication with OTP (2FA)
- ✓ SSH secure connections
- ✓ gRPC inter-node communication
- ✓ CLI and Web interfaces
- ✓ Real-time bandwidth simulation (64KB/s)

## Quick Start (2 minutes)

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Run Demo
```bash
python main.py --mode demo
```

This will:
- Create 5 virtual nodes (50GB total storage)
- Upload and distribute test files
- Show network health status
- Generate a system report

## Main Operating Modes

### Demo Mode (Learning)
```bash
python main.py --mode demo
```
**Best for**: Understanding how the system works
- Automated demonstration
- Real file uploads
- Network simulation visible
- System report generated

### CLI Mode (Interactive)
```bash
python main.py --mode cli
```
**Best for**: Manual testing and operations
- Register users
- Login with authentication
- Upload/download files
- Check node status
- Monitor storage

### Web Mode (User-Friendly)
```bash
python main.py --mode web
```
**Best for**: Visual interaction (like Google Drive)
- Open http://localhost:5000 in browser
- Graphical file manager
- Real-time monitoring
- REST API available

## Key Features to Try

### 1. File Upload (Distributed Storage)
Files are automatically:
- Split into 64KB chunks
- Distributed across all 5 nodes
- Tracked with metadata
- Recoverable from any node

**Example (CLI):**
```
P2P-Storage > upload test_files/document.pdf
Starting upload: test_files/document.pdf
File size: 2.45 MB
File chunked into 40 segments
✓ Upload complete!
  File ID: a1b2c3d4e5f6g7h8
```

### 2. Network Health Monitoring
Checks if nodes are alive or dead:

**Example (CLI):**
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

### 3. OTP Authentication (2FA)
Secure login with one-time passwords:

**Example (CLI):**
```
P2P-Storage > register alice alice@example.com password
✓ User registered successfully
Enable OTP authentication? (y/n): y
✓ OTP enabled for alice
  Secret key: JBSWY3DPEBLW64TMMQ======
  Current code: 123456
```

### 4. Real-time Bandwidth Simulation
Realistic file transfer times at 64KB/s:
- 64KB file: 1 second
- 256KB file: 4 seconds  
- 1MB file: 16 seconds
- 5MB file: 80 seconds

## Project Structure

```
P2P/
├── main.py                    → Entry point (START HERE)
├── README.md                  → Full documentation
├── QUICKSTART.md             → Quick reference
├── ARCHITECTURE.md           → System design
├── IMPLEMENTATION_SUMMARY.md → What was built
│
├── core/
│   └── orchestrator.py       → System coordinator
├── network/
│   └── virtual_network.py    → Virtual network & nodes
├── storage/
│   └── virtual_storage.py    → File storage
├── auth/
│   ├── authentication.py     → User auth & OTP
│   └── ssh_handler.py        → SSH security
├── grpc_service/
│   ├── p2p_service.proto     → RPC definitions
│   └── grpc_handler.py       → gRPC services
├── cli/
│   └── cli_interface.py      → Command-line UI
└── web/
    └── web_server.py         → Web UI & REST API
```

## Example Workflow

### Step 1: Start the system
```bash
python main.py --mode cli
```

### Step 2: Create an account
```
P2P-Storage > register bob bob@example.com secure123
✓ User registered successfully
Enable OTP authentication? (y/n): n
```

### Step 3: Login
```
P2P-Storage > login bob secure123
✓ Login successful
  Session token: abc123def456xyz789...
```

### Step 4: Upload a file
```
P2P-Storage > upload test_files/image.jpg
Starting upload: test_files/image.jpg
File size: 3.25 MB
File chunked into 52 segments
  [100%] Segment 52 stored on Node_05
✓ Upload complete!
  File ID: x1y2z3a4b5c6d7e8
```

### Step 5: List all nodes
```
P2P-Storage > nodes
Network: P2P_Storage_Network (192.168.1.0/24)
─────────────────────────────────────────────────────────
Node ID      IP Address      Status    Storage          Files
─────────────────────────────────────────────────────────
Node_01      192.168.1.2     ALIVE     3.25GB / 10GB    13
Node_02      192.168.1.3     ALIVE     3.25GB / 10GB    13
Node_03      192.168.1.4     ALIVE     3.25GB / 10GB    13
Node_04      192.168.1.5     ALIVE     3.25GB / 10GB    13
Node_05      192.168.1.6     ALIVE     3.25GB / 10GB    13
─────────────────────────────────────────────────────────
```

### Step 6: View storage stats
```
P2P-Storage > storage
Network Storage Statistics:
─────────────────────────────────────────────────────────
Node_01    10.00GB      3.25GB      6.75GB      32.5%
Node_02    10.00GB      3.25GB      6.75GB      32.5%
Node_03    10.00GB      3.25GB      6.75GB      32.5%
Node_04    10.00GB      3.25GB      6.75GB      32.5%
Node_05    10.00GB      3.25GB      6.75GB      32.5%
─────────────────────────────────────────────────────────
TOTAL      50.00GB      16.25GB     33.75GB     32.5%
```

### Step 7: Download file
```
P2P-Storage > download x1y2z3a4b5c6d7e8 downloaded_image.jpg
Starting download: x1y2z3a4b5c6d7e8
✓ Download complete!
  Output: downloaded_image.jpg
  Size: 3.25 MB
```

## Advanced Usage

### Custom Network Configuration
```bash
# Create 7 nodes with 15GB each (105GB total)
python main.py --mode cli --nodes 7 --storage 15

# Create 3 nodes with 5GB each (smaller test)
python main.py --mode demo --nodes 3 --storage 5

# Create 10 nodes with 20GB each (large network)
python main.py --mode web --nodes 10 --storage 20
```

### Testing the System
```bash
# Run validation tests
python test_validation.py
```

Validates:
- ✓ Module imports
- ✓ Network creation
- ✓ Node management
- ✓ Storage operations
- ✓ Authentication
- ✓ Health checks

## Common Tasks

| Task | Command |
|------|---------|
| **Register user** | `register <user> <email> <pass>` |
| **Login** | `login <user> <pass>` |
| **Upload file** | `upload <filepath>` |
| **Download file** | `download <file_id> <output>` |
| **View all nodes** | `nodes` |
| **Check health** | `health` |
| **Storage stats** | `storage` |
| **Network topology** | `topology` |
| **Network stats** | `stats` |
| **Enable OTP** | `enable_otp <user>` |
| **Clear screen** | `clear` |
| **Exit** | `exit` or `quit` |

## Understanding the System

### Node Distribution
When you upload a 2.5MB file:
```
Original File (2.5MB)
         ↓
   Chunking (64KB each = 40 chunks)
         ↓
   Distribution (round-robin)
         ↓
Chunk 01 → Node_01
Chunk 02 → Node_02
Chunk 03 → Node_03
Chunk 04 → Node_04
Chunk 05 → Node_05
Chunk 06 → Node_01 (repeat)
... and so on
```

Result: Each node stores ~8 chunks = distributed storage!

### Bandwidth Simulation
File transfers happen at **64KB/s**:
- Your 2.5MB file takes ~40 seconds to upload
- This simulates realistic network delays
- Each node works independently
- Real TCP/IP behavior simulated

### Security Features
1. **Passwords**: Hashed with PBKDF2 (100,000 iterations)
2. **OTP**: 6-digit codes that change every 30 seconds
3. **Sessions**: 24-hour tokens with IP validation
4. **SSH**: Encrypted remote connections
5. **Checksums**: File integrity verification

## Troubleshooting

### "Port 5000 already in use"
```bash
# Kill the process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <pid> /F

# Linux/Mac:
lsof -i :5000
kill -9 <pid>
```

### "ModuleNotFoundError"
```bash
# Ensure you're in the correct directory and dependencies are installed
cd P2P
pip install -r requirements.txt
python main.py --help
```

### "Permission Denied on storage"
```bash
# Check directory permissions
dir node_storage/
# Or delete and recreate
rmdir /s node_storage
```

## Next Steps

1. ✓ **Run demo mode** → See it in action
2. ✓ **Try CLI mode** → Interactive testing
3. ✓ **Open web UI** → Visual interface
4. ✓ **Read README.md** → Deep dive into features
5. ✓ **Study code** → Learn the implementation
6. ✓ **Run tests** → Validate everything works
7. ✓ **Experiment** → Try custom configurations

## Learning Resources

- **README.md**: Complete feature documentation
- **QUICKSTART.md**: Quick reference guide
- **ARCHITECTURE.md**: System design and data flows
- **IMPLEMENTATION_SUMMARY.md**: What was built and why
- **Source code**: Well-commented Python files
- **Logs**: Check p2p_storage.log for detailed info

## Performance Tips

1. **Faster testing**: Reduce file sizes
```bash
# Create small test file
python -c "open('test_files/small.txt', 'w').write('x'*1024)"
```

2. **More nodes**: Better distribution
```bash
python main.py --mode cli --nodes 10 --storage 10
```

3. **Monitor bandwidth**: Watch transfer times
- The delays are realistic!
- This simulates real network behavior

## Getting Help

If something doesn't work:

1. **Check the logs**: `p2p_storage.log`
2. **Run tests**: `python test_validation.py`
3. **Read the docs**: README.md, QUICKSTART.md, ARCHITECTURE.md
4. **Review code**: Comments explain the implementation
5. **Try demo mode**: `python main.py --mode demo`

## System Requirements

- Python 3.8+
- 100MB disk space (for demo)
- ~500MB free disk (for test files)
- Internet connection (optional, for email OTP)

## Summary

You now have a complete P2P storage system that demonstrates:
- ✓ Distributed systems concepts
- ✓ Cloud storage architecture
- ✓ Security best practices
- ✓ Real network simulation
- ✓ Professional code structure

**Start exploring:**
```bash
python main.py --mode demo
```

Enjoy! 🚀

---

**Questions?** Check the documentation files:
- README.md - Full guide
- QUICKSTART.md - Quick reference
- ARCHITECTURE.md - System design
- IMPLEMENTATION_SUMMARY.md - What was built
