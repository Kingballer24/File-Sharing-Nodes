"""
Web-based User Interface for P2P Storage System
Provides Google Drive-like interface for file management
"""

from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
import logging
import os
from datetime import datetime, timedelta
from functools import wraps
import json

logger = logging.getLogger(__name__)


class P2PWebUI:
    """
    Web-based UI for P2P Storage System
    Provides REST API and web interface
    """
    
    def __init__(self, p2p_orchestrator, host: str = '0.0.0.0', port: int = 5000):
        """
        Initialize web UI
        
        Args:
            p2p_orchestrator: P2PStorageOrchestrator instance
            host: Server host
            port: Server port
        """
        self.app = Flask(__name__)
        self.app.secret_key = 'p2p_storage_secret_key_change_in_production'
        self.orchestrator = p2p_orchestrator
        self.host = host
        self.port = port
        
        # Enable CORS with credentials support
        CORS(self.app, supports_credentials=True, origins=['*'])
        
        # Register routes
        self._register_routes()
        
        logger.info(f"[Web] UI initialized on {host}:{port}")
    
    def _require_login(self, f):
        """Decorator to require user login"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    def _register_routes(self):
        """Register all Flask routes"""
        
        # Authentication endpoints
        @self.app.route('/api/auth/register', methods=['POST'])
        def register():
            """Register new user"""
            data = request.json
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            
            if not all([username, email, password]):
                return jsonify({'error': 'Missing required fields'}), 400
            
            success, message = self.orchestrator.auth_manager.register_user(
                username, email, password
            )
            
            if success:
                return jsonify({'success': True, 'message': message}), 201
            else:
                return jsonify({'error': message}), 400
        
        @self.app.route('/api/auth/login', methods=['POST'])
        def login():
            """Authenticate user"""
            try:
                data = request.json
                username = data.get('username')
                password = data.get('password')
                otp_code = data.get('otp_code')
                
                if not username or not password:
                    return jsonify({'error': 'Missing credentials'}), 400
                
                # If OTP code provided, verify with OTP
                if otp_code:
                    success, token, message = self.orchestrator.auth_manager.verify_otp_and_login(
                        username, password, otp_code
                    )
                    if success:
                        session['user'] = username
                        session['token'] = token
                        logger.info(f"[Auth] User {username} logged in with OTP")
                        return jsonify({
                            'success': True,
                            'message': message,
                            'token': token,
                            'user': username
                        }), 200
                    else:
                        return jsonify({'error': message}), 401
                
                # Try normal login
                success, token, message = self.orchestrator.auth_manager.login(
                    username, password
                )
                
                if success:
                    session['user'] = username
                    session['token'] = token
                    logger.info(f"[Auth] User {username} logged in successfully")
                    return jsonify({
                        'success': True,
                        'message': message,
                        'token': token,
                        'user': username
                    }), 200
                elif "OTP verification required" in message:
                    # OTP required, send back flag to show OTP form
                    logger.info(f"[Auth] OTP verification required for {username}")
                    return jsonify({
                        'success': False,
                        'otp_required': True,
                        'message': message,
                        'user': username
                    }), 401
                else:
                    logger.warning(f"[Auth] Login failed for {username}: {message}")
                    return jsonify({'error': message}), 401
            except Exception as e:
                logger.error(f"[Auth] Login error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/auth/demo-otp', methods=['GET'])
        def demo_otp():
            """Get current OTP code for demo users (demo only)"""
            try:
                username = request.args.get('username')
                if not username or username not in self.orchestrator.auth_manager.users:
                    return jsonify({'error': 'Invalid username'}), 400
                
                user = self.orchestrator.auth_manager.users[username]
                if not user.otp_enabled or not user.otp_manager:
                    return jsonify({'error': 'OTP not enabled for user'}), 400
                
                # Get current OTP code
                current_code = user.otp_manager.get_current_code()
                logger.info(f"[Demo] Current OTP for {username}: {current_code}")
                
                return jsonify({
                    'otp_code': current_code,
                    'message': 'Current OTP code (valid for ~30 seconds)'
                }), 200
            except Exception as e:
                logger.error(f"[Demo OTP] Error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/auth/logout', methods=['POST'])
        @self._require_login
        def logout():
            """Logout user"""
            session.clear()
            return jsonify({'success': True, 'message': 'Logged out'}), 200
        
        @self.app.route('/api/auth/enable-otp', methods=['POST'])
        @self._require_login
        def enable_otp():
            """Enable OTP for user"""
            username = session['user']
            user = self.orchestrator.auth_manager.users.get(username)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            user.enable_otp()
            
            return jsonify({
                'success': True,
                'secret_key': user.otp_manager.secret_key,
                'current_code': user.otp_manager.get_current_code(),
                'provisioning_uri': user.otp_manager.get_provisioning_uri(),
                'backup_codes': user.otp_manager.backup_codes
            }), 200
        
        # File operations
        @self.app.route('/api/files/upload', methods=['POST'])
        @self._require_login
        def upload_file():
            """Upload file to P2P network"""
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Save file temporarily
            temp_path = f"temp/{file.filename}"
            os.makedirs("temp", exist_ok=True)
            file.save(temp_path)
            
            try:
                # Upload to network - use preferred node from session if set
                preferred = session.get('preferred_node')
                if preferred and preferred in self.orchestrator.nodes:
                    node = self.orchestrator.nodes[preferred]
                else:
                    node = list(self.orchestrator.nodes.values())[0]

                file_id, segments = node.storage.chunk_file(temp_path)
                logger.info(f"[Web Upload] Using node {getattr(node, 'node_id', getattr(node, 'id', 'unknown'))} for initial chunking")
                
                # Distribute segments
                node_list = list(self.orchestrator.nodes.values())
                for i, segment in enumerate(segments):
                    target_node = node_list[i % len(node_list)]
                    target_node.storage.store_segment(segment)
                    logger.info(f"[Web Upload] Stored segment {i+1}/{len(segments)} on {getattr(target_node, 'node_id', getattr(target_node, 'id', 'unknown'))}")
                
                # Persist metadata for owner node so downloads survive server restarts
                try:
                    node.storage.save_metadata()
                except Exception:
                    logger.warning(f"[Web Upload] Failed to persist metadata for {getattr(node,'node_id', getattr(node,'id','unknown'))}")

                return jsonify({
                    'success': True,
                    'file_id': file_id,
                    'filename': file.filename,
                    'total_chunks': len(segments),
                    'message': 'File uploaded successfully'
                }), 201
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/files/list', methods=['GET'])
        @self._require_login
        def list_files():
            """List all files in network"""
            files = []
            
            for node_id, node in self.orchestrator.nodes.items():
                for file_id, metadata in node.storage.file_metadata.items():
                    files.append({
                        'file_id': file_id,
                        'filename': metadata.original_filename,
                        'size_bytes': metadata.total_size_bytes,
                        'size_mb': metadata.total_size_bytes / (1024*1024),
                        'chunks': metadata.total_chunks,
                        'created_at': metadata.created_at.isoformat(),
                        'stored_on': node_id
                    })
            
            return jsonify({
                'success': True,
                'files': files,
                'total': len(files)
            }), 200
        
        @self.app.route('/api/files/download/<file_id>', methods=['GET'])
        @self._require_login
        def download_file(file_id):
            """Download file from network"""
            try:
                # Allow specifying which node to use for reconstruction via query parameter
                preferred_node_id = request.args.get('node_id')
                
                # Find a node that has metadata for this file
                owner_node = None
                
                # Try preferred node first if specified
                if preferred_node_id and preferred_node_id in self.orchestrator.nodes:
                    candidate = self.orchestrator.nodes[preferred_node_id]
                    if file_id in candidate.storage.file_metadata:
                        owner_node = candidate
                
                # Fall back to searching all nodes
                if owner_node is None:
                    for node in self.orchestrator.nodes.values():
                        if file_id in node.storage.file_metadata:
                            owner_node = node
                            break

                if owner_node is None:
                    logger.warning(f"[Web Download] Metadata for file {file_id} not found on any node")
                    return jsonify({'error': 'File metadata not found on any node'}), 404

                # Use an absolute temp path so reconstruction can write reliably
                temp_dir = os.path.abspath(os.path.join(os.getcwd(), 'temp'))
                os.makedirs(temp_dir, exist_ok=True)
                output_path = os.path.join(temp_dir, f"{file_id}_download")

                # Callback to retrieve segments from any node
                def get_segment_callback(segment_id):
                    for n in self.orchestrator.nodes.values():
                        seg = n.storage.retrieve_segment(segment_id)
                        if seg is not None:
                            return seg
                    return None

                owner_node_id = getattr(owner_node,'node_id', getattr(owner_node,'id','unknown'))
                logger.info(f"[Web Download] Attempting reconstruction for {file_id} using owner {owner_node_id} (preferred: {preferred_node_id or 'none'})")
                success = owner_node.storage.reconstruct_file(file_id, output_path, get_segment_callback=get_segment_callback)
                logger.info(f"[Web Download] Reconstruction result for {file_id}: {success}")

                if success:
                    # Attempt to use original filename when sending
                    metadata = owner_node.storage.file_metadata.get(file_id)
                    original_name = getattr(metadata, 'original_filename', None) if metadata else None
                    try:
                        if original_name:
                            return send_file(output_path, as_attachment=True, download_name=original_name)
                        else:
                            return send_file(output_path, as_attachment=True)
                    except TypeError:
                        # Fallback for older Flask versions that use `attachment_filename`
                        if original_name:
                            return send_file(output_path, as_attachment=True, attachment_filename=original_name)
                        return send_file(output_path, as_attachment=True)
                else:
                    logger.error(f"[Web Download] Reconstruction failed for {file_id}; check segments and metadata")
                    return jsonify({'error': 'File reconstruction failed or segments missing'}), 404
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/files/<file_id>', methods=['DELETE'])
        @self._require_login
        def delete_file(file_id):
            """Delete file from network"""
            # Implement file deletion across nodes
            deleted_count = 0
            
            for node_id, node in self.orchestrator.nodes.items():
                if file_id in node.storage.file_metadata:
                    del node.storage.file_metadata[file_id]
                    deleted_count += 1
                
                # Delete segments
                segments_to_delete = [
                    sid for sid in node.storage.file_segments.keys()
                    if sid.startswith(f"{file_id}_chunk_")
                ]
                
                for segment_id in segments_to_delete:
                    del node.storage.file_segments[segment_id]
                    deleted_count += 1
            
            return jsonify({
                'success': True,
                'message': f'File deleted (removed {deleted_count} segments)',
                'file_id': file_id
            }), 200
        
        # Network operations
        @self.app.route('/api/network/topology', methods=['GET'])
        @self._require_login
        def network_topology():
            """Get network topology"""
            topology = self.orchestrator.virtual_network.get_network_topology()
            return jsonify(topology), 200
        
        @self.app.route('/api/network/statistics', methods=['GET'])
        @self._require_login
        def network_statistics():
            """Get network statistics"""
            stats = self.orchestrator.virtual_network.get_statistics()
            return jsonify(stats), 200
        
        @self.app.route('/api/network/health', methods=['GET'])
        @self._require_login
        def network_health():
            """Get network health status"""
            health = self.orchestrator.broadcast_health_check()
            
            alive_count = sum(1 for alive in health.values() if alive)
            
            return jsonify({
                'nodes': health,
                'alive': alive_count,
                'total': len(health),
                'status': 'HEALTHY' if alive_count == len(health) else 'DEGRADED'
            }), 200
        
        @self.app.route('/api/storage/status', methods=['GET'])
        @self._require_login
        def storage_status():
            """Get storage status across all nodes"""
            nodes_storage = {}
            
            total_capacity = 0
            total_used = 0
            
            for node_id, node in self.orchestrator.nodes.items():
                info = node.storage.get_storage_info()
                nodes_storage[node_id] = info
                
                total_capacity += info['capacity_gb']
                total_used += info['used_gb']
            
            return jsonify({
                'nodes': nodes_storage,
                'total': {
                    'capacity_gb': total_capacity,
                    'used_gb': total_used,
                    'available_gb': total_capacity - total_used,
                    'utilization_percent': (total_used / total_capacity * 100) if total_capacity > 0 else 0
                }
            }), 200

        @self.app.route('/api/nodes', methods=['GET'])
        @self._require_login
        def get_nodes():
            """Return list of nodes with status and storage info"""
            nodes = []
            health = self.orchestrator.broadcast_health_check()
            for node_id, node in self.orchestrator.nodes.items():
                info = node.storage.get_storage_info()
                nodes.append({
                    'node_id': node_id,
                    'ip': getattr(node, 'network_ip', getattr(node, 'ip', 'unknown')),
                    'capacity_gb': info.get('capacity_gb', 0),
                    'used_gb': info.get('used_gb', 0),
                    'status': 'ALIVE' if health.get(node_id, False) else 'DEAD'
                })

            preferred = session.get('preferred_node')
            return jsonify({'nodes': nodes, 'preferred': preferred}), 200

        @self.app.route('/api/nodes/select', methods=['POST'])
        @self._require_login
        def select_node():
            """Select preferred node for uploads (stored in session)"""
            data = request.json or {}
            node_id = data.get('node_id')
            if not node_id or node_id not in self.orchestrator.nodes:
                return jsonify({'error': 'Invalid node_id'}), 400
            session['preferred_node'] = node_id
            return jsonify({'success': True, 'preferred': node_id}), 200
        
        # Dashboard
        @self.app.route('/api/dashboard', methods=['GET'])
        @self._require_login
        def dashboard():
            """Get dashboard data"""
            info = self.orchestrator.get_system_info()
            
            return jsonify({
                'system': info,
                'storage': requests.get('/api/storage/status').json,
                'health': requests.get('/api/network/health').json
            }), 200
        
        # Root
        @self.app.route('/')
        def index():
            """Serve main page"""
            return self.get_dashboard_html()
    
    def get_dashboard_html(self) -> str:
        """Get HTML for web dashboard"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>P2P Storage - Dashboard</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                
                .header {
                    color: white;
                    text-align: center;
                    margin-bottom: 40px;
                }
                
                .header h1 {
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }
                
                .header p {
                    font-size: 1.1em;
                    opacity: 0.9;
                }
                
                .dashboard {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                
                .card {
                    background: white;
                    border-radius: 12px;
                    padding: 25px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }
                
                .card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 15px 50px rgba(0,0,0,0.15);
                }
                
                .card h2 {
                    color: #333;
                    margin-bottom: 15px;
                    font-size: 1.3em;
                }
                
                .card .stat {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin: 10px 0;
                    padding: 10px 0;
                    border-bottom: 1px solid #eee;
                }
                
                .card .stat:last-child {
                    border-bottom: none;
                }
                
                .card .stat label {
                    color: #666;
                    font-weight: 500;
                }
                
                .card .stat value {
                    color: #333;
                    font-weight: bold;
                    font-size: 1.1em;
                }
                
                .status-badge {
                    display: inline-block;
                    padding: 5px 12px;
                    border-radius: 20px;
                    font-size: 0.85em;
                    font-weight: bold;
                }
                
                .status-online { background: #4caf50; color: white; }
                .status-offline { background: #f44336; color: white; }

                /* Highlight selected node */
                .selected-node { background: #f5f8ff; border-left: 4px solid #667eea; }
                
                .progress-bar {
                    width: 100%;
                    height: 8px;
                    background: #eee;
                    border-radius: 4px;
                    overflow: hidden;
                    margin: 10px 0;
                }
                
                .progress-bar-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    transition: width 0.3s ease;
                }
                
                .button-group {
                    display: flex;
                    gap: 10px;
                    margin-top: 15px;
                }
                
                button {
                    flex: 1;
                    padding: 10px 15px;
                    border: none;
                    border-radius: 6px;
                    background: #667eea;
                    color: white;
                    font-weight: bold;
                    cursor: pointer;
                    transition: background 0.3s ease;
                }
                
                button:hover {
                    background: #764ba2;
                }
                
                .footer {
                    text-align: center;
                    color: white;
                    margin-top: 40px;
                    opacity: 0.8;
                }
            </style>
        </head>
        <body>
            <!-- Login Modal -->
            <div id="login-modal" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:1000; display:flex; align-items:center; justify-content:center;">
                <div style="background:white; padding:40px; border-radius:12px; box-shadow:0 20px 60px rgba(0,0,0,0.3); width:90%; max-width:400px;">
                    <h2 style="margin-bottom:20px; color:#333;">Login to P2P Storage</h2>
                    <form id="login-form" style="display:flex; flex-direction:column; gap:12px;">
                        <input type="text" id="login-username" placeholder="Username" required style="padding:12px; border:1px solid #ddd; border-radius:6px; font-size:1em;">
                        <input type="password" id="login-password" placeholder="Password" required style="padding:12px; border:1px solid #ddd; border-radius:6px; font-size:1em;">
                        <button type="submit" style="padding:12px; background:#667eea; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">Login</button>
                        <p style="text-align:center; color:#666; font-size:0.9em;">Demo accounts: alice/alice123, bob/bob123, charlie/charlie123</p>
                    </form>
                </div>
            </div>

            <!-- OTP Modal -->
            <div id="otp-modal" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:1001; display:none; align-items:center; justify-content:center;">
                <div style="background:white; padding:40px; border-radius:12px; box-shadow:0 20px 60px rgba(0,0,0,0.3); width:90%; max-width:400px;">
                    <h2 style="margin-bottom:20px; color:#333;">One-Time Password Verification</h2>
                    <p style="margin-bottom:20px; color:#666;">A one-time password is required to complete login.</p>
                    <form id="otp-form" style="display:flex; flex-direction:column; gap:12px;">
                        <input type="text" id="otp-code" placeholder="Enter OTP code" required style="padding:12px; border:1px solid #ddd; border-radius:6px; font-size:1.2em; text-align:center; letter-spacing:2px;">
                        <button type="submit" style="padding:12px; background:#667eea; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">Verify & Login</button>
                        <button type="button" onclick="getDemoOTP()" style="padding:12px; background:#4caf50; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">Get Demo OTP</button>
                        <p style="text-align:center; color:#666; font-size:0.85em;">Click "Get Demo OTP" to see the current one-time password for testing.</p>
                    </form>
                </div>
            </div>
            
            <div class="container">
                <div class="header">
                    <h1>🖥️ P2P Distributed Storage</h1>
                    <p>Secure, Decentralized File Storage System</p>
                </div>
                
                <div class="dashboard" id="dashboard">
                    <div class="card">
                        <h2>📊 System Status</h2>
                        <div class="stat">
                            <label>Network Status:</label>
                            <value><span class="status-badge status-online">ONLINE</span></value>
                        </div>
                        <div class="stat">
                            <label>Active Nodes:</label>
                            <value id="active-nodes">5/5</value>
                        </div>
                        <div class="stat">
                            <label>Uptime:</label>
                            <value id="uptime">00:00:00</value>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>💾 Storage Overview</h2>
                        <div class="stat">
                            <label>Total Capacity:</label>
                            <value id="total-capacity">50 GB</value>
                        </div>
                        <div class="stat">
                            <label>Used Space:</label>
                            <value id="used-space">0 GB</value>
                        </div>
                        <div class="stat">
                            <label>Available:</label>
                            <value id="available-space">50 GB</value>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-bar-fill" id="storage-fill" style="width: 0%"></div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>📁 Files</h2>

                        <div style="margin-bottom:12px">
                            <div id="preferred-node" style="margin-bottom:8px; color:#333; font-weight:600;">Preferred node: <span id="preferred-node-name">None</span></div>
                            <form id="upload-form">
                                <input type="file" id="file-input" name="file" />
                                <button type="submit">Upload</button>
                            </form>
                            <div class="progress-bar" style="margin-top:8px;">
                                <div class="progress-bar-fill" id="upload-progress" style="width: 0%"></div>
                            </div>
                        </div>

                        <div style="margin-top:14px">
                            <label style="display:block; margin-bottom:6px; color:#666;">Files in Network</label>
                            <div id="files-list" style="max-height:240px; overflow:auto;"></div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>🌐 Network Statistics</h2>
                        <div class="stat">
                            <label>Packets Sent:</label>
                            <value id="packets-sent">0</value>
                        </div>
                        <div class="stat">
                            <label>Packets Received:</label>
                            <value id="packets-received">0</value>
                        </div>
                        <div class="stat">
                            <label>Throughput:</label>
                            <value id="throughput">0 Mbps</value>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>🧩 Nodes</h2>
                        <div id="nodes-list" style="max-height:240px; overflow:auto; padding-top:6px;"></div>
                        <div style="margin-top:10px; text-align:right;">
                            <button onclick="loadNodes()">Refresh Nodes</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>🔐 Security</h2>
                        <div class="stat">
                            <label>Authenticated User:</label>
                            <value id="current-user">Not logged in</value>
                        </div>
                        <div class="stat">
                            <label>OTP Enabled:</label>
                            <value id="otp-status">Disabled</value>
                        </div>
                        <div class="button-group">
                            <button onclick="enableOTP()">🔑 Enable OTP</button>
                            <button onclick="logout()">🚪 Logout</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>⚡ Performance</h2>
                        <div class="stat">
                            <label>Avg Latency:</label>
                            <value id="avg-latency">0 ms</value>
                        </div>
                        <div class="stat">
                            <label>Packet Loss:</label>
                            <value id="packet-loss">0%</value>
                        </div>
                        <div class="stat">
                            <label>Response Time:</label>
                            <value id="response-time">0 ms</value>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>P2P Storage System v1.0 | Powered by Python, gRPC & Flask</p>
                    <p>© 2025 | Distributed Systems Research</p>
                </div>
            </div>
            
            <script>
                // Check if user is logged in on page load
                async function checkLogin() {
                    try {
                        const resp = await fetch('/api/files/list', {
                            credentials: 'include'
                        });
                        if (resp.status === 401) {
                            document.getElementById('login-modal').style.display = 'flex';
                            document.getElementById('dashboard').style.display = 'none';
                        } else {
                            document.getElementById('login-modal').style.display = 'none';
                            document.getElementById('dashboard').style.display = 'grid';
                            loadFiles();
                            loadNodes();
                        }
                    } catch (err) {
                        console.error('Auth check failed:', err);
                        document.getElementById('login-modal').style.display = 'flex';
                    }
                }

                // Handle login
                document.getElementById('login-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const username = document.getElementById('login-username').value;
                    const password = document.getElementById('login-password').value;

                    try {
                        const resp = await fetch('/api/auth/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            credentials: 'include',
                            body: JSON.stringify({ username, password })
                        });

                        const data = await resp.json();
                        if (resp.ok) {
                            console.log('Login successful, user:', username);
                            document.getElementById('current-user').textContent = username;
                            document.getElementById('login-modal').style.display = 'none';
                            document.getElementById('dashboard').style.display = 'grid';
                            document.getElementById('login-form').reset();
                            loadFiles();
                            loadNodes();
                        } else if (data.otp_required) {
                            console.log('OTP verification required');
                            // Store username and password for OTP submission
                            window.otpPending = { username, password };
                            document.getElementById('login-modal').style.display = 'none';
                            document.getElementById('otp-modal').style.display = 'flex';
                        } else {
                            alert('Login failed: ' + (data.error || 'Unknown error'));
                        }
                    } catch (err) {
                        console.error('Login error:', err);
                        alert('Login error: ' + err);
                    }
                });

                // Handle OTP submission
                document.getElementById('otp-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const otp_code = document.getElementById('otp-code').value;
                    const { username, password } = window.otpPending || {};

                    if (!username || !password) {
                        alert('Session expired. Please login again.');
                        document.getElementById('otp-modal').style.display = 'none';
                        document.getElementById('login-modal').style.display = 'flex';
                        return;
                    }

                    try {
                        const resp = await fetch('/api/auth/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            credentials: 'include',
                            body: JSON.stringify({ username, password, otp_code })
                        });

                        const data = await resp.json();
                        if (resp.ok) {
                            console.log('OTP verification successful');
                            document.getElementById('current-user').textContent = username;
                            document.getElementById('otp-modal').style.display = 'none';
                            document.getElementById('dashboard').style.display = 'grid';
                            document.getElementById('otp-form').reset();
                            window.otpPending = null;
                            loadFiles();
                            loadNodes();
                        } else {
                            alert('OTP verification failed: ' + (data.error || 'Invalid code'));
                            document.getElementById('otp-code').value = '';
                        }
                    } catch (err) {
                        console.error('OTP error:', err);
                        alert('OTP error: ' + err);
                    }
                });

                // Get demo OTP code
                async function getDemoOTP() {
                    const { username } = window.otpPending || {};
                    if (!username) {
                        alert('No username available');
                        return;
                    }

                    try {
                        const resp = await fetch(`/api/auth/demo-otp?username=${username}`);
                        const data = await resp.json();
                        if (resp.ok) {
                            document.getElementById('otp-code').value = data.otp_code;
                            alert('Demo OTP populated! Click "Verify & Login" to complete.');
                        } else {
                            alert('Failed to get OTP: ' + (data.error || 'Unknown error'));
                        }
                    } catch (err) {
                        alert('Error getting OTP: ' + err);
                    }
                }

                // Upload form handling
                const uploadForm = document.getElementById('upload-form');
                const fileInput = document.getElementById('file-input');
                const uploadProgress = document.getElementById('upload-progress');
                const filesList = document.getElementById('files-list');

                uploadForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const file = fileInput.files[0];
                    if (!file) { alert('Please choose a file to upload'); return; }

                    const formData = new FormData();
                    formData.append('file', file);

                    try {
                        const xhr = new XMLHttpRequest();
                        xhr.open('POST', '/api/files/upload', true);
                        xhr.upload.onprogress = function(evt) {
                            if (evt.lengthComputable) {
                                const pct = Math.round((evt.loaded / evt.total) * 100);
                                uploadProgress.style.width = pct + '%';
                            }
                        };

                        xhr.onload = function() {
                            if (xhr.status >= 200 && xhr.status < 300) {
                                uploadProgress.style.width = '0%';
                                fileInput.value = '';
                                loadFiles();
                                alert('Upload complete');
                            } else {
                                alert('Upload failed: ' + xhr.responseText);
                            }
                        };

                        xhr.onerror = function() {
                            alert('Upload error');
                        };

                        xhr.send(formData);

                    } catch (err) {
                        alert('Upload error: ' + err);
                    }
                });

                // Load file list from server
                async function loadFiles() {
                    try {
                        const resp = await fetch('/api/files/list', {
                            credentials: 'include'
                        });
                        if (!resp.ok) throw new Error('Failed to fetch files');
                        const data = await resp.json();
                        const list = data.files || [];
                        filesList.innerHTML = '';

                        if (list.length === 0) {
                            filesList.innerHTML = '<div style="color:#666">No files stored</div>';
                            return;
                        }

                        list.forEach(f => {
                            const row = document.createElement('div');
                            row.style.padding = '8px 6px';
                            row.style.borderBottom = '1px solid #eee';
                            row.style.display = 'flex';
                            row.style.justifyContent = 'space-between';
                            row.style.alignItems = 'center';

                            const left = document.createElement('div');
                            left.innerHTML = `<strong>${f.filename}</strong><div style="font-size:0.85em;color:#666">${(f.size_mb||0).toFixed(2)} MB — ${f.chunks} chunks — stored on ${f.stored_on}</div>`;

                            const right = document.createElement('div');
                            const btn = document.createElement('button');
                            btn.textContent = 'Download';
                            btn.style.background = '#4caf50';
                            btn.onclick = () => showDownloadNodeSelector(f.file_id, f.filename);

                            right.appendChild(btn);
                            row.appendChild(left);
                            row.appendChild(right);
                            filesList.appendChild(row);
                        });

                    } catch (err) {
                        filesList.innerHTML = '<div style="color:#c00">Failed to load files</div>';
                        console.error(err);
                    }
                }

                    // Load nodes and show status + allow selection
                    async function loadNodes() {
                        try {
                            const resp = await fetch('/api/nodes', { credentials: 'include' });
                            if (!resp.ok) throw new Error('Failed to fetch nodes');
                            const data = await resp.json();
                            const list = data.nodes || [];
                            const preferred = data.preferred || null;
                            const nodesList = document.getElementById('nodes-list');
                            nodesList.innerHTML = '';

                            if (list.length === 0) {
                                nodesList.innerHTML = '<div style="color:#666">No nodes available</div>';
                                return;
                            }

                                // update preferred display
                                const prefNameEl = document.getElementById('preferred-node-name');
                                if (prefNameEl) prefNameEl.textContent = preferred || 'None';

                                list.forEach(n => {
                                    const row = document.createElement('div');
                                    row.style.padding = '8px 6px';
                                    row.style.borderBottom = '1px solid #eee';
                                    row.style.display = 'flex';
                                    row.style.justifyContent = 'space-between';
                                    row.style.alignItems = 'center';

                                    const left = document.createElement('div');
                                    left.innerHTML = `<strong>${n.node_id}</strong><div style="font-size:0.85em;color:#666">${n.ip} — ${n.used_gb.toFixed(2)} / ${n.capacity_gb.toFixed(2)} GB</div>`;

                                    const right = document.createElement('div');
                                    const status = document.createElement('span');
                                    status.textContent = n.status === 'ALIVE' ? 'ONLINE' : 'OFFLINE';
                                    status.className = n.status === 'ALIVE' ? 'status-badge status-online' : 'status-badge status-offline';
                                    status.style.marginRight = '10px';

                                    const btn = document.createElement('button');
                                    btn.textContent = preferred === n.node_id ? 'Selected' : 'Select';
                                    btn.disabled = preferred === n.node_id;
                                    btn.onclick = async () => {
                                        try {
                                            const sel = await fetch('/api/nodes/select', {
                                                method: 'POST',
                                                headers: { 'Content-Type': 'application/json' },
                                                credentials: 'include',
                                                body: JSON.stringify({ node_id: n.node_id })
                                            });
                                            if (!sel.ok) throw new Error('Select failed');
                                            await loadNodes();
                                            alert('Preferred node set to ' + n.node_id);
                                        } catch (err) {
                                            alert('Failed to select node: ' + err);
                                        }
                                    };

                                    // highlight selected row
                                    if (preferred === n.node_id) {
                                        row.classList.add('selected-node');
                                    }

                                    right.appendChild(status);
                                    right.appendChild(btn);
                                    row.appendChild(left);
                                    row.appendChild(right);
                                    nodesList.appendChild(row);
                                });

                        } catch (err) {
                            document.getElementById('nodes-list').innerHTML = '<div style="color:#c00">Failed to load nodes</div>';
                            console.error(err);
                        }
                    }
                
                // Show node selector modal for download
                async function showDownloadNodeSelector(fileId, filename) {
                    try {
                        const resp = await fetch('/api/nodes', { credentials: 'include' });
                        if (!resp.ok) throw new Error('Failed to fetch nodes');
                        const data = await resp.json();
                        const nodes = data.nodes || [];
                        
                        if (nodes.length === 0) {
                            alert('No nodes available');
                            return;
                        }
                        
                        // Create modal dynamically
                        const modal = document.createElement('div');
                        modal.style.position = 'fixed';
                        modal.style.top = '0';
                        modal.style.left = '0';
                        modal.style.width = '100%';
                        modal.style.height = '100%';
                        modal.style.background = 'rgba(0,0,0,0.5)';
                        modal.style.display = 'flex';
                        modal.style.alignItems = 'center';
                        modal.style.justifyContent = 'center';
                        modal.style.zIndex = '9999';
                        
                        const content = document.createElement('div');
                        content.style.background = 'white';
                        content.style.padding = '20px';
                        content.style.borderRadius = '8px';
                        content.style.width = '400px';
                        content.style.maxHeight = '60vh';
                        content.style.overflowY = 'auto';
                        content.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
                        
                        const title = document.createElement('h3');
                        title.textContent = 'Download from Node';
                        title.style.marginTop = '0';
                        content.appendChild(title);
                        
                        const desc = document.createElement('p');
                        desc.textContent = 'Select which node to reconstruct and download the file from:';
                        desc.style.color = '#666';
                        desc.style.fontSize = '0.9em';
                        content.appendChild(desc);
                        
                        nodes.forEach(node => {
                            const nodeBtn = document.createElement('button');
                            nodeBtn.style.display = 'block';
                            nodeBtn.style.width = '100%';
                            nodeBtn.style.padding = '12px';
                            nodeBtn.style.margin = '8px 0';
                            nodeBtn.style.border = '1px solid #ddd';
                            nodeBtn.style.borderRadius = '4px';
                            nodeBtn.style.cursor = 'pointer';
                            nodeBtn.style.background = node.status === 'ALIVE' ? '#f0f7ff' : '#f5f5f5';
                            nodeBtn.style.textAlign = 'left';
                            nodeBtn.innerHTML = `<strong>${node.node_id}</strong> (${node.status}) <br><small style="color:#666">${node.ip}</small>`;
                            
                            nodeBtn.onclick = async () => {
                                modal.remove();
                                await downloadById(fileId, filename, node.node_id);
                            };
                            
                            nodeBtn.onmouseover = () => {
                                nodeBtn.style.background = node.status === 'ALIVE' ? '#e8f4ff' : '#f0f0f0';
                            };
                            
                            nodeBtn.onmouseout = () => {
                                nodeBtn.style.background = node.status === 'ALIVE' ? '#f0f7ff' : '#f5f5f5';
                            };
                            
                            if (node.status !== 'ALIVE') {
                                nodeBtn.disabled = true;
                                nodeBtn.style.opacity = '0.5';
                                nodeBtn.style.cursor = 'not-allowed';
                            }
                            
                            content.appendChild(nodeBtn);
                        });
                        
                        const cancelBtn = document.createElement('button');
                        cancelBtn.textContent = 'Cancel';
                        cancelBtn.style.width = '100%';
                        cancelBtn.style.padding = '12px';
                        cancelBtn.style.margin = '16px 0 0 0';
                        cancelBtn.style.background = '#ddd';
                        cancelBtn.style.border = 'none';
                        cancelBtn.style.borderRadius = '4px';
                        cancelBtn.style.cursor = 'pointer';
                        cancelBtn.onclick = () => modal.remove();
                        content.appendChild(cancelBtn);
                        
                        modal.appendChild(content);
                        document.body.appendChild(modal);
                        
                    } catch (err) {
                        alert('Failed to show node selector: ' + err);
                    }
                }
                
                // Download by file id from specific node
                async function downloadById(fileId, filename, nodeId) {
                    try {
                        let url = `/api/files/download/${fileId}`;
                        if (nodeId) {
                            url += `?node_id=${encodeURIComponent(nodeId)}`;
                        }
                        
                        const resp = await fetch(url, {
                            credentials: 'include'
                        });
                        if (!resp.ok) {
                            const text = await resp.text();
                            alert('Download failed: ' + text);
                            return;
                        }

                        const blob = await resp.blob();
                        const urlObj = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = urlObj;
                        a.download = filename || fileId;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        window.URL.revokeObjectURL(urlObj);
                    } catch (err) {
                        alert('Download error: ' + err);
                    }
                }

                function enableOTP() {
                    alert('OTP setup is available via API; use the CLI or implement UI flows');
                }

                function logout() {
                    fetch('/api/auth/logout', {
                        method:'POST',
                        credentials: 'include'
                    })
                        .then(()=>{ alert('Logged out'); window.location.reload(); })
                        .catch(()=>{ alert('Logout failed'); });
                }

                // Auto-refresh dashboard data and file list
                async function refreshDashboard() {
                    try {
                        // refresh files and storage stats
                        await loadFiles();
                        await loadNodes();
                    } catch (e) { console.error(e); }
                }

                // initial load
                checkLogin();
                setInterval(refreshDashboard, 8000);
            </script>
        </body>
        </html>
        """
    
    def run(self, debug: bool = False):
        """Start the web server"""
        logger.info(f"[Web] Starting web server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug)


def create_web_app(p2p_orchestrator):
    """Factory function to create web app"""
    web_ui = P2PWebUI(p2p_orchestrator)
    return web_ui


if __name__ == "__main__":
    # This would be run from main orchestrator
    print("Web UI module loaded")
