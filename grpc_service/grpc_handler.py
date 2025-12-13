"""
RPC Service Implementation for P2P Storage
Handles RPC communication between nodes using JSON-RPC over TCP
(Pure Python implementation - no gRPC compiler dependency needed)
"""

import socket
import json
import time
import logging
import threading
from typing import Optional, Dict, Callable

logger = logging.getLogger(__name__)


class JSONRPCServer:
    """
    Simple JSON-RPC server for inter-node communication over TCP
    Pure Python implementation with no external compilation required
    """
    
    def __init__(self, virtual_node, port: int = 50051):
        """
        Initialize RPC server
        
        Args:
            virtual_node: VirtualNode instance
            port: TCP port for RPC server
        """
        self.virtual_node = virtual_node
        self.port = port
        self.running = False
        self.server_socket = None
        self.server_thread = None
    
    def start(self):
        """Start the JSON-RPC server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('127.0.0.1', self.port))
            self.server_socket.listen(10)
            self.running = True
            
            self.server_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.server_thread.start()
            logger.info(f"JSON-RPC server started on port {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start RPC server: {e}")
            return False
    
    def _accept_connections(self):
        """Accept incoming RPC connections"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket, addr):
        """Handle a single RPC client connection"""
        try:
            # Receive JSON-RPC request
            data = client_socket.recv(65536).decode('utf-8')
            if not data:
                return
            
            request = json.loads(data)
            response = self._process_rpc_request(request)
            
            # Send JSON-RPC response
            client_socket.sendall(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"RPC client error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _process_rpc_request(self, request: Dict) -> Dict:
        """
        Process a JSON-RPC 2.0 request and return response
        
        Args:
            request: JSON-RPC request dict with method, params, id
            
        Returns:
            JSON-RPC response dict
        """
        try:
            method = request.get('method', '')
            params = request.get('params', {})
            req_id = request.get('id')
            
            result = None
            error = None
            
            if method == 'store_segment':
                result = self._store_segment(params)
            elif method == 'retrieve_segment':
                result = self._retrieve_segment(params)
            elif method == 'health_check':
                result = self._health_check()
            elif method == 'get_storage_info':
                result = self._get_storage_info()
            else:
                error = {'code': -32601, 'message': f'Method not found: {method}'}
            
            response = {
                'jsonrpc': '2.0',
                'id': req_id
            }
            
            if error:
                response['error'] = error
            else:
                response['result'] = result
            
            return response
            
        except Exception as e:
            logger.error(f"RPC processing error: {e}")
            return {
                'jsonrpc': '2.0',
                'error': {'code': -32603, 'message': str(e)},
                'id': request.get('id')
            }
    
    def _store_segment(self, params: Dict):
        """Store a file segment on this node"""
        try:
            from storage.virtual_storage import FileSegment
            
            # Handle base64-encoded data if needed
            data = params.get('data')
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            segment = FileSegment(
                segment_id=params['segment_id'],
                file_hash=params['file_hash'],
                chunk_number=params['chunk_number'],
                data=data,
                size_bytes=len(data),
                checksum=params['checksum']
            )
            
            self.virtual_node.storage.store_segment(segment)
            
            return {
                'status': 'stored',
                'segment_id': params['segment_id'],
                'size_bytes': len(data)
            }
            
        except Exception as e:
            raise Exception(f"Failed to store segment: {e}")
    
    def _retrieve_segment(self, params: Dict):
        """Retrieve a file segment from this node"""
        try:
            segment_id = params['segment_id']
            segment = self.virtual_node.storage.retrieve_segment(segment_id)
            
            if segment:
                # Return segment data as base64 string for JSON serialization
                import base64
                data_b64 = base64.b64encode(segment.data).decode('utf-8')
                
                return {
                    'status': 'retrieved',
                    'segment_id': segment.segment_id,
                    'chunk_number': segment.chunk_number,
                    'data_b64': data_b64,
                    'checksum': segment.checksum,
                    'size_bytes': len(segment.data)
                }
            else:
                raise Exception(f"Segment not found: {segment_id}")
                
        except Exception as e:
            raise Exception(f"Failed to retrieve segment: {e}")
    
    def _health_check(self):
        """Check node health status"""
        try:
            return {
                'status': 'healthy',
                'node_id': self.virtual_node.node_id,
                'uptime_seconds': getattr(self.virtual_node, 'uptime', 0),
                'storage_used_mb': self.virtual_node.storage.used_space / (1024 * 1024),
                'storage_total_mb': self.virtual_node.storage.total_capacity / (1024 * 1024)
            }
        except Exception as e:
            raise Exception(f"Failed to get health status: {e}")
    
    def _get_storage_info(self):
        """Get storage information"""
        try:
            return {
                'total_capacity_mb': self.virtual_node.storage.total_capacity / (1024 * 1024),
                'used_space_mb': self.virtual_node.storage.used_space / (1024 * 1024),
                'segments_stored': len(self.virtual_node.storage.segments),
                'files_stored': len(self.virtual_node.storage.file_metadata)
            }
        except Exception as e:
            raise Exception(f"Failed to get storage info: {e}")
    
    def stop(self):
        """Stop the RPC server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        logger.info("JSON-RPC server stopped")
    
    def wait_for_termination(self):
        """Wait for server termination (for compatibility)"""
        if self.server_thread:
            self.server_thread.join()


class JSONRPCClient:
    """
    JSON-RPC client for making RPC calls to remote nodes
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 50051):
        """
        Initialize RPC client
        
        Args:
            host: Remote host address
            port: Remote port
        """
        self.host = host
        self.port = port
        self.request_id = 0
    
    def call(self, method: str, params: Dict = None, timeout: int = 5) -> Dict:
        """
        Make a JSON-RPC call to remote node
        
        Args:
            method: RPC method name
            params: Method parameters
            timeout: Connection timeout in seconds
            
        Returns:
            Response from remote node
        """
        try:
            self.request_id += 1
            
            request = {
                'jsonrpc': '2.0',
                'method': method,
                'params': params or {},
                'id': self.request_id
            }
            
            socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_obj.settimeout(timeout)
            socket_obj.connect((self.host, self.port))
            
            # Send request
            socket_obj.sendall(json.dumps(request).encode('utf-8'))
            
            # Receive response
            response_data = socket_obj.recv(65536).decode('utf-8')
            response = json.loads(response_data)
            
            socket_obj.close()
            
            if 'error' in response and response['error']:
                raise Exception(f"RPC error: {response['error']['message']}")
            
            return response.get('result', {})
            
        except socket.timeout:
            raise Exception(f"RPC call to {self.host}:{self.port} timed out")
        except Exception as e:
            raise Exception(f"RPC call failed: {e}")
