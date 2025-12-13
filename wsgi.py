#!/usr/bin/env python3
"""
WSGI Entry Point for P2P Storage System Web UI
Production deployment with Waitress (Windows-compatible)
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import and initialize the P2P system
from core.orchestrator import P2PStorageOrchestrator
from web.web_server import create_web_app

# Create orchestrator instance
logger.info("[WSGI] Initializing P2P Storage System...")
orchestrator = P2PStorageOrchestrator(
    network_name='P2P_Storage_Network',
    node_count=5,
    storage_per_node_gb=10
)
orchestrator.initialize_nodes()
orchestrator.start_network()

logger.info("[WSGI] P2P Storage System initialized")

# Create Flask app
web_ui = create_web_app(orchestrator)
app = web_ui.app

logger.info("[WSGI] Flask app created and ready for Waitress")

if __name__ == "__main__":
    # Production: use waitress
    # Run: python wsgi.py
    # Or: waitress-serve --port=5000 --host=0.0.0.0 wsgi:app
    from waitress import serve
    logger.info("[WSGI] Starting Waitress server on http://0.0.0.0:5000")
    serve(app, host='0.0.0.0', port=5000, threads=4)
