"""
Virtual Storage System - Distributed File Storage Management
Implements distributed storage across multiple nodes with file chunking
"""

import os
import hashlib
import json
import shutil
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FileSegment:
    """Represents a chunk of a distributed file"""
    segment_id: str
    file_hash: str
    chunk_number: int
    data: bytes
    size_bytes: int
    checksum: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for data integrity"""
        return hashlib.sha256(self.data).hexdigest()


@dataclass
class FileMetadata:
    """Metadata for a distributed file"""
    file_id: str
    original_filename: str
    file_hash: str
    total_size_bytes: int
    chunk_size_bytes: int
    total_chunks: int
    chunks: Dict[int, str] = field(default_factory=dict)  # chunk_num -> node_id
    created_at: datetime = field(default_factory=datetime.now)
    replicas: int = 1  # Number of replicas for redundancy
    
    def to_dict(self) -> Dict:
        """Convert metadata to dictionary"""
        return {
            'file_id': self.file_id,
            'original_filename': self.original_filename,
            'file_hash': self.file_hash,
            'total_size_bytes': self.total_size_bytes,
            'chunk_size_bytes': self.chunk_size_bytes,
            'total_chunks': self.total_chunks,
            'chunks': self.chunks,
            'created_at': self.created_at.isoformat(),
            'replicas': self.replicas
        }


class VirtualStorage:
    """
    Virtual Storage - implements distributed storage on actual HDD
    Each node has its own virtual storage allocating real disk space
    """
    
    def __init__(self, node_id: str, capacity_gb: float = 10.0):
        """
        Initialize virtual storage for a node
        
        Args:
            node_id: Node identifier
            capacity_gb: Storage capacity in GB
        """
        self.node_id = node_id
        self.capacity_gb = capacity_gb
        self.capacity_bytes = int(capacity_gb * 1024 * 1024 * 1024)
        
        # Create actual storage directory on host machine
        self.storage_root = f"./node_storage/{node_id}"
        os.makedirs(self.storage_root, exist_ok=True)
        
        # Storage segments
        self.file_segments: Dict[str, FileSegment] = {}  # segment_id -> FileSegment
        self.file_metadata: Dict[str, FileMetadata] = {}  # file_id -> FileMetadata
        
        # Track used space
        self.used_bytes = 0
        
        # Metadata file for persistence
        self.metadata_file = os.path.join(self.storage_root, "metadata.json")
        self.load_metadata()
        
        logger.info(f"[STORAGE {node_id}] Virtual storage initialized: {capacity_gb}GB "
                   f"at {self.storage_root}")
    
    def chunk_file(self, file_path: str, chunk_size_bytes: int = 64 * 1024) -> Tuple[str, List[FileSegment]]:
        """
        Chunk a file into segments for distributed storage
        Each chunk is a segment stored independently
        
        Args:
            file_path: Path to file to chunk
            chunk_size_bytes: Size of each chunk (default 64KB)
            
        Returns:
            Tuple of (file_id, list of FileSegments)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        file_hash = self._calculate_file_hash(file_path)
        file_id = file_hash[:16]  # Use first 16 chars of hash as file ID
        original_filename = os.path.basename(file_path)
        
        segments = []
        chunk_number = 0
        
        with open(file_path, 'rb') as f:
            while True:
                chunk_data = f.read(chunk_size_bytes)
                if not chunk_data:
                    break
                
                segment_id = f"{file_id}_chunk_{chunk_number}"
                checksum = hashlib.sha256(chunk_data).hexdigest()
                
                segment = FileSegment(
                    segment_id=segment_id,
                    file_hash=file_hash,
                    chunk_number=chunk_number,
                    data=chunk_data,
                    size_bytes=len(chunk_data),
                    checksum=checksum
                )
                
                segments.append(segment)
                chunk_number += 1
        
        # Create metadata
        metadata = FileMetadata(
            file_id=file_id,
            original_filename=original_filename,
            file_hash=file_hash,
            total_size_bytes=file_size,
            chunk_size_bytes=chunk_size_bytes,
            total_chunks=len(segments)
        )
        
        self.file_metadata[file_id] = metadata
        
        logger.info(f"[STORAGE {self.node_id}] File '{original_filename}' chunked into "
                   f"{len(segments)} segments (file_id: {file_id})")
        
        return file_id, segments
    
    def store_segment(self, segment: FileSegment) -> bool:
        """
        Store a file segment on this node
        
        Args:
            segment: FileSegment to store
            
        Returns:
            True if successful
        """
        # Check available space
        if self.used_bytes + segment.size_bytes > self.capacity_bytes:
            logger.error(f"[STORAGE {self.node_id}] Insufficient space for segment {segment.segment_id}")
            return False
        
        # Write segment to disk
        segment_path = os.path.join(self.storage_root, f"{segment.segment_id}.bin")
        try:
            with open(segment_path, 'wb') as f:
                f.write(segment.data)
            
            self.file_segments[segment.segment_id] = segment
            self.used_bytes += segment.size_bytes
            
            # Update metadata
            # Find metadata entry whose full file_hash matches this segment's file_hash
            for fid, meta in self.file_metadata.items():
                if meta.file_hash == segment.file_hash:
                    meta.chunks[segment.chunk_number] = self.node_id
                    break
            # Persist metadata to disk
            try:
                self.save_metadata()
            except Exception:
                pass
            
            logger.info(f"[STORAGE {self.node_id}] Segment {segment.segment_id} stored "
                       f"({segment.size_bytes} bytes)")
            
            return True
        
        except Exception as e:
            logger.error(f"[STORAGE {self.node_id}] Error storing segment: {e}")
            return False
    
    def retrieve_segment(self, segment_id: str) -> Optional[FileSegment]:
        """
        Retrieve a file segment from storage
        
        Args:
            segment_id: ID of segment to retrieve
            
        Returns:
            FileSegment if found, None otherwise
        """
        if segment_id in self.file_segments:
            return self.file_segments[segment_id]
        
        # Try to load from disk
        segment_path = os.path.join(self.storage_root, f"{segment_id}.bin")
        if os.path.exists(segment_path):
            try:
                with open(segment_path, 'rb') as f:
                    data = f.read()
                
                segment = FileSegment(
                    segment_id=segment_id,
                    file_hash="",
                    chunk_number=0,
                    data=data,
                    size_bytes=len(data),
                    checksum=hashlib.sha256(data).hexdigest()
                )
                
                self.file_segments[segment_id] = segment
                return segment
            
            except Exception as e:
                logger.error(f"[STORAGE {self.node_id}] Error loading segment: {e}")
        
        return None
    
    def reconstruct_file(self, file_id: str, output_path: str, 
                        get_segment_callback=None) -> bool:
        """
        Reconstruct file from segments (segments may be on different nodes)
        
        Args:
            file_id: File to reconstruct
            output_path: Path where reconstructed file should be saved
            get_segment_callback: Callback function to retrieve segments from other nodes
            
        Returns:
            True if successful
        """
        if file_id not in self.file_metadata:
            logger.error(f"[STORAGE {self.node_id}] File metadata not found: {file_id}")
            return False
        
        metadata = self.file_metadata[file_id]
        
        try:
            # Ensure output directory exists
            out_dir = os.path.dirname(os.path.abspath(output_path))
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            logger.info(f"[STORAGE {self.node_id}] Reconstructing file {file_id} to {output_path}")
            with open(output_path, 'wb') as output_file:
                for chunk_num in range(metadata.total_chunks):
                    segment_id = f"{file_id}_chunk_{chunk_num}"

                    # Try to get from local storage first
                    segment = self.retrieve_segment(segment_id)

                    # If not local and callback provided, fetch from remote
                    if segment is None and get_segment_callback:
                        logger.debug(f"[STORAGE {self.node_id}] Fetching segment {segment_id} from remote")
                        segment = get_segment_callback(segment_id)

                    if segment is None:
                        logger.error(f"[STORAGE {self.node_id}] Segment not found during reconstruction: {segment_id}")
                        return False

                    output_file.write(segment.data)

            logger.info(f"[STORAGE {self.node_id}] File reconstructed: {output_path} "
                       f"({metadata.total_size_bytes} bytes)")
            return True
        
        except Exception as e:
            logger.error(f"[STORAGE {self.node_id}] Error reconstructing file: {e}")
            return False
    
    def get_used_space_gb(self) -> float:
        """Get used storage space in GB"""
        return self.used_bytes / (1024 * 1024 * 1024)
    
    def get_available_space_gb(self) -> float:
        """Get available storage space in GB"""
        return (self.capacity_bytes - self.used_bytes) / (1024 * 1024 * 1024)
    
    def get_storage_info(self) -> Dict:
        """Get storage information"""
        return {
            'node_id': self.node_id,
            'capacity_gb': self.capacity_gb,
            'used_gb': self.get_used_space_gb(),
            'available_gb': self.get_available_space_gb(),
            'utilization_percent': (self.used_bytes / self.capacity_bytes * 100) if self.capacity_bytes > 0 else 0,
            'segments_stored': len(self.file_segments),
            'files_metadata': len(self.file_metadata),
            'storage_path': self.storage_root
        }
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def save_metadata(self):
        """Save metadata to disk for persistence"""
        try:
            metadata_dict = {}
            for file_id, metadata in self.file_metadata.items():
                metadata_dict[file_id] = metadata.to_dict()
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
            
            logger.info(f"[STORAGE {self.node_id}] Metadata saved")
        except Exception as e:
            logger.error(f"[STORAGE {self.node_id}] Error saving metadata: {e}")
    
    def load_metadata(self):
        """Load metadata from disk"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    metadata_dict = json.load(f)
                
                for file_id, meta_data in metadata_dict.items():
                    metadata = FileMetadata(
                        file_id=file_id,
                        original_filename=meta_data['original_filename'],
                        file_hash=meta_data['file_hash'],
                        total_size_bytes=meta_data['total_size_bytes'],
                        chunk_size_bytes=meta_data['chunk_size_bytes'],
                        total_chunks=meta_data['total_chunks'],
                        chunks=meta_data.get('chunks', {}),
                        replicas=meta_data.get('replicas', 1)
                    )
                    self.file_metadata[file_id] = metadata
                
                logger.info(f"[STORAGE {self.node_id}] Metadata loaded")
            
            except Exception as e:
                logger.error(f"[STORAGE {self.node_id}] Error loading metadata: {e}")
    
    def clear_storage(self):
        """Clear all storage for the node (CAUTION - destructive)"""
        try:
            shutil.rmtree(self.storage_root)
            os.makedirs(self.storage_root, exist_ok=True)
            self.file_segments.clear()
            self.file_metadata.clear()
            self.used_bytes = 0
            logger.info(f"[STORAGE {self.node_id}] Storage cleared")
        except Exception as e:
            logger.error(f"[STORAGE {self.node_id}] Error clearing storage: {e}")
