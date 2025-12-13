# Quick Start Guide

## 1. Installation (2 minutes)

```bash
# Navigate to project
cd P2P

# Install dependencies
pip install -r requirements.txt

# Verify installation
python main.py --help
```

## 2. Run Demo (5 minutes)

See the system in action with automatic file uploads and distribution:

```bash
python main.py --mode demo
```

This will:
- ✓ Create 5 virtual nodes
- ✓ Initialize 50GB total storage
- ✓ Upload 3 test files
- ✓ Distribute files across nodes
- ✓ Check node health
- ✓ Generate system report

## 3. Use CLI Interface (Interactive)

```bash
python main.py --mode cli
```

Example session:

```
P2P-Storage > register alice alice@example.com password123
✓ User registered successfully
Enable OTP authentication? (y/n): y
✓ OTP enabled for alice

P2P-Storage > login alice password123
✓ Login successful

P2P-Storage > upload test_files/document.pdf
✓ Upload complete!

P2P-Storage > nodes
[Shows all 5 nodes with IP, status, storage info]

P2P-Storage > health
[Checks if all nodes are alive]

P2P-Storage > exit
```

## 4. Access Web Interface (Browser)

```bash
python main.py --mode web
```

Then open: `http://localhost:5000`

The interface shows:
- System status
- Storage overview
- File management (upload/download)
- Network topology
- Health status
- Performance metrics

## 5. Configuration Options

### Network Size
```bash
# Small network (3 nodes, 5GB each)
python main.py --nodes 3 --storage 5

# Medium network (7 nodes, 15GB each) 
python main.py --nodes 7 --storage 15

# Large network (10 nodes, 25GB each)
python main.py --nodes 10 --storage 25
```

## Key Features to Try

### File Upload & Distribution
Files are automatically:
- Split into 64KB chunks
- Distributed across all nodes
- Tracked with metadata
- Retrievable from any node

### Network Simulation
- 64KB/s bandwidth per node
- TCP/IP packet simulation
- Acknowledgments tracking
- Realistic transfer times

### Authentication
- User registration
- OTP setup (2FA)
- Email notifications
- Session management

### Health Monitoring
- Check which nodes are alive
- Automatic health broadcasts
- Status indicators

## Common Commands

| Command | Purpose |
|---------|---------|
| `register <user> <email> <pass>` | Create account |
| `login <user> <pass>` | Authenticate |
| `upload <file>` | Upload to network |
| `download <id> <out>` | Download from network |
| `nodes` | List all nodes |
| `health` | Check node status |
| `storage` | View storage stats |
| `stats` | Network statistics |

## Troubleshooting

**Q: Port 5000 already in use**
A: Use different port or kill process:
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill it (Windows)
taskkill /PID <pid> /F
```

**Q: Permission denied on storage**
A: Check directory permissions:
```bash
# Ensure write access to node_storage/
chmod -R 755 node_storage/
```

**Q: Low disk space**
A: Reduce storage per node or number of nodes:
```bash
python main.py --nodes 3 --storage 5
```

## Performance Tips

1. **Faster uploads**: Increase bandwidth
```bash
# In virtual_network.py
bandwidth_mbps=1.0  # Default is 64Kb/s
```

2. **Smaller chunks**: For faster tests
```bash
# In CLI upload
file_id, segments = node.storage.chunk_file(file_path, chunk_size_bytes=16*1024)
```

3. **More nodes**: Better distribution
```bash
python main.py --nodes 10 --storage 10
```

## Next Steps

1. ✓ Run demo mode
2. ✓ Try CLI interface
3. ✓ Explore web UI
4. ✓ Review code structure
5. ✓ Experiment with configurations
6. ✓ Study network simulation
7. ✓ Implement custom features

## Project Structure

```
P2P/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── README.md           # Full documentation
├── QUICKSTART.md       # This file
├── core/
│   └── orchestrator.py # System coordinator
├── network/
│   └── virtual_network.py # Network & nodes
├── storage/
│   └── virtual_storage.py # Storage system
├── auth/
│   ├── authentication.py # Auth & OTP
│   └── ssh_handler.py    # SSH security
├── grpc_service/
│   ├── p2p_service.proto # gRPC definitions
│   └── grpc_handler.py   # gRPC implementation
├── cli/
│   └── cli_interface.py  # Command-line UI
├── web/
│   └── web_server.py     # Web UI & REST API
└── node_storage/        # Data storage
```

## Support

For detailed information, see:
- **README.md** - Full documentation
- **source code comments** - Implementation details
- **Log files** - p2p_storage.log for debugging

---

**Ready to go!** Choose a mode and start exploring:
```bash
python main.py --mode demo   # Learn how it works
python main.py --mode cli    # Interactive mode
python main.py --mode web    # Web interface
```
