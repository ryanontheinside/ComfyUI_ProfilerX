import time
import psutil
import torch
import threading
import json
import os
import logging
from collections import defaultdict
from typing import Dict, List, Optional

logger = logging.getLogger('ComfyUI-ProfilerX')
logger.setLevel(logging.ERROR)

# Add console handler if not already added
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class ProfilerManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.active_profiles: Dict[str, Dict] = {}
        self.history: List[Dict] = []
        self.max_history = 10000
        self.process = psutil.Process()
        
        # Run benchmark
        logger.setLevel(logging.DEBUG)  # Temporarily set to debug to see benchmark
        self._benchmark_reset_stats()
        logger.setLevel(logging.ERROR)  # Reset to normal level
        
        # Rolling averages for nodes and workflow
        self.node_averages: Dict[str, Dict] = defaultdict(lambda: {
            'total_time': 0.0,
            'count': 0,
            'vram_usage': 0.0,
            'ram_usage': 0.0
        })
        self.workflow_averages = {
            'total_time': 0.0,
            'count': 0,
            'vram_peak': 0.0,
            'ram_peak': 0.0
        }
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        logger.debug(f"Data directory created/verified at: {self.data_dir}")
        
        # Load existing history
        self.history_file = os.path.join(self.data_dir, "profiling_history.json")
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
                logger.debug(f"Loaded {len(self.history)} profiles from history file")
            except Exception as e:
                logger.error(f"Failed to load history file: {e}")
                self.history = []
        else:
            logger.debug("No existing history file found")
            self.history = []

    def _update_node_average(self, node_type: str, execution_time: float, vram_used: float, ram_used: float) -> Dict:
        """Update rolling average for a node type"""
        avg = self.node_averages[node_type]
        avg['count'] += 1
        avg['total_time'] = (avg['total_time'] * (avg['count'] - 1) + execution_time) / avg['count']
        avg['vram_usage'] = (avg['vram_usage'] * (avg['count'] - 1) + vram_used) / avg['count']
        avg['ram_usage'] = (avg['ram_usage'] * (avg['count'] - 1) + ram_used) / avg['count']
        return avg

    def _update_workflow_average(self, execution_time: float, vram_peak: float, ram_peak: float) -> Dict:
        """Update rolling average for workflow execution"""
        self.workflow_averages['count'] += 1
        self.workflow_averages['total_time'] = (
            self.workflow_averages['total_time'] * (self.workflow_averages['count'] - 1) + execution_time
        ) / self.workflow_averages['count']
        self.workflow_averages['vram_peak'] = (
            self.workflow_averages['vram_peak'] * (self.workflow_averages['count'] - 1) + vram_peak
        ) / self.workflow_averages['count']
        self.workflow_averages['ram_peak'] = (
            self.workflow_averages['ram_peak'] * (self.workflow_averages['count'] - 1) + ram_peak
        ) / self.workflow_averages['count']
        return self.workflow_averages

    def _save_history(self):
        """Save profiling history to disk"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history[-self.max_history:], f, indent=2)
            logger.debug(f"Saved {len(self.history)} profiles to history file")
        except Exception as e:
            logger.error(f"Failed to save history file: {e}")

    @classmethod
    def get_instance(cls) -> 'ProfilerManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    logger.debug("Created new ProfilerManager instance")
        return cls._instance

    def start_workflow(self, prompt_id: str) -> None:
        """Start profiling a workflow execution"""
        logger.debug(f"Starting workflow profiling for prompt_id: {prompt_id}")
        self.active_profiles[prompt_id] = {
            'promptId': prompt_id,
            'startTime': time.time() * 1000,  # Convert to ms
            'nodes': {},
            'executionOrder': [],
            'totalVramPeak': 0,
            'totalRamPeak': 0,
            'cacheHits': 0,
            'cacheMisses': 0
        }

    def end_workflow(self, prompt_id: str) -> Optional[Dict]:
        """End profiling a workflow execution"""
        if prompt_id not in self.active_profiles:
            logger.warning(f"Attempted to end non-existent workflow profile: {prompt_id}")
            return None

        logger.debug(f"Ending workflow profiling for prompt_id: {prompt_id}")
        profile = self.active_profiles[prompt_id]
        profile['endTime'] = time.time() * 1000

        # Update peak memory usage
        profile['totalVramPeak'] = torch.cuda.max_memory_allocated()
        profile['totalRamPeak'] = self.process.memory_info().rss

        # Calculate and update workflow averages
        execution_time = profile['endTime'] - profile['startTime']
        avg = self._update_workflow_average(execution_time, profile['totalVramPeak'], profile['totalRamPeak'])
        profile['averages'] = {
            'execution_time': avg['total_time'],
            'vram_peak': avg['vram_peak'],
            'ram_peak': avg['ram_peak'],
            'count': avg['count']
        }

        # Store in history
        self.history.append(profile)
        if len(self.history) >= self.max_history:
            # Auto-archive when limit is reached
            logger.info(f"History limit of {self.max_history} reached. Auto-archiving...")
            self.archive_history()
            # History is now empty after archiving
        else:
            # Only save to current history file if we haven't archived
            self._save_history()

        # Cleanup
        del self.active_profiles[prompt_id]
        return profile

    def start_node(self, prompt_id: str, node_id: str, node_type: str, inputs: Dict) -> None:
        """Start profiling a node execution"""
        if prompt_id not in self.active_profiles:
            logger.warning(f"Attempted to start node profiling for non-existent workflow: {prompt_id}")
            return

        logger.debug(f"Starting node profiling - prompt: {prompt_id}, node: {node_id}, type: {node_type}")
        profile = self.active_profiles[prompt_id]
        
        # Reset peak stats to track this node's peak specifically
        torch.cuda.reset_peak_memory_stats()
        base_vram = torch.cuda.memory_allocated()  # Store base VRAM to calculate true peak increase
        
        profile['nodes'][node_id] = {
            'nodeId': node_id,
            'nodeType': node_type,
            'startTime': time.time() * 1000,
            'vramBefore': base_vram,  # This is also our base VRAM
            'ramBefore': self.process.memory_info().rss,
            'inputSizes': self._get_tensor_sizes(inputs),
            'outputSizes': {},
            'cacheHit': False
        }
        profile['executionOrder'].append(node_id)

    def end_node(self, prompt_id: str, node_id: str, outputs: Dict, cache_hit: bool = False) -> None:
        """End profiling a node execution"""
        if prompt_id not in self.active_profiles:
            logger.warning(f"Attempted to end node profiling for non-existent workflow: {prompt_id}")
            return
        if node_id not in self.active_profiles[prompt_id]['nodes']:
            logger.warning(f"Attempted to end non-existent node profile: {node_id}")
            return

        logger.debug(f"Ending node profiling - prompt: {prompt_id}, node: {node_id}, cache_hit: {cache_hit}")
        profile = self.active_profiles[prompt_id]
        node = profile['nodes'][node_id]
        node['endTime'] = time.time() * 1000
        node['vramAfter'] = torch.cuda.memory_allocated()
        total_peak = torch.cuda.max_memory_allocated()
        node['vramPeak'] = total_peak - node['vramBefore']  # Calculate the actual peak increase from base
        node['ramAfter'] = self.process.memory_info().rss
        node['outputSizes'] = self._get_tensor_sizes(outputs)
        node['cacheHit'] = cache_hit

        # Calculate and update averages
        execution_time = node['endTime'] - node['startTime']
        vram_used = node['vramAfter'] - node['vramBefore']
        ram_used = node['ramAfter'] - node['ramBefore']
        
        # Update rolling averages with the true peak
        avg = self._update_node_average(node['nodeType'], execution_time, vram_used, ram_used)
        node['averages'] = {
            'execution_time': avg['total_time'],
            'vram_usage': avg['vram_usage'],
            'ram_usage': avg['ram_usage'],
            'count': avg['count']
        }

        if cache_hit:
            profile['cacheHits'] += 1
        else:
            profile['cacheMisses'] += 1

    def record_error(self, prompt_id: str, node_id: str, error: str) -> None:
        """Record an error that occurred during node execution"""
        if prompt_id not in self.active_profiles:
            logger.warning(f"Attempted to record error for non-existent workflow: {prompt_id}")
            return
        if node_id not in self.active_profiles[prompt_id]['nodes']:
            logger.warning(f"Attempted to record error for non-existent node: {node_id}")
            return

        logger.error(f"Node error - prompt: {prompt_id}, node: {node_id}, error: {error}")
        self.active_profiles[prompt_id]['nodes'][node_id]['error'] = str(error)

    def get_latest_profile(self) -> Optional[Dict]:
        """Get the most recent workflow profile"""
        if not self.history:
            logger.debug("No profiles in history")
            return None
        logger.debug("Returning latest profile")
        return self.history[-1]

    def get_stats(self) -> Dict:
        """Get all profiling stats including current and historical data"""
        stats = {
            'current': self.active_profiles,
            'latest': self.get_latest_profile(),
            'node_averages': dict(self.node_averages),
            'workflow_averages': self.workflow_averages,
            'history': self.history[-10:]  # Return last 10 profiles
        }
        return stats

    def get_archives(self) -> List[Dict]:
        """Get list of archived history files"""
        archives = []
        archive_dir = os.path.join(self.data_dir, "archives")
        os.makedirs(archive_dir, exist_ok=True)
        
        try:
            for filename in os.listdir(archive_dir):
                if filename.endswith('.json'):
                    path = os.path.join(archive_dir, filename)
                    stat = os.stat(path)
                    archives.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created': stat.st_ctime,
                        'modified': stat.st_mtime
                    })
            return sorted(archives, key=lambda x: x['created'], reverse=True)
        except Exception as e:
            logger.error(f"Failed to get archives: {e}")
            return []

    def archive_history(self) -> Optional[str]:
        """Archive current history to a file"""
        if not self.history:
            logger.warning("No history to archive")
            return None
            
        archive_dir = os.path.join(self.data_dir, "archives")
        os.makedirs(archive_dir, exist_ok=True)
        
        try:
            timestamp = int(time.time())
            filename = f"profiling_history_{timestamp}.json"
            path = os.path.join(archive_dir, filename)
            
            with open(path, 'w') as f:
                json.dump(self.history, f, indent=2)
            
            # Clear current history
            self.history = []
            self._save_history()  # Save empty history to current file
            
            logger.debug(f"Created archive: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            return None

    def load_archive(self, filename: str) -> bool:
        """Load history from an archive file and delete it after loading"""
        path = os.path.join(self.data_dir, "archives", filename)
        if not os.path.exists(path):
            logger.error(f"Archive not found: {filename}")
            return False
            
        try:
            # Auto-archive current history if it exists
            if self.history:
                self.archive_history()
                logger.debug("Auto-archived current history before loading new archive")
            
            # Load the archive
            with open(path, 'r') as f:
                archived_history = json.load(f)
            
            if not isinstance(archived_history, list):
                logger.error(f"Invalid archive format: {filename}")
                return False
                
            # Update current history
            self.history = archived_history
            self._save_history()  # Update current history file
            
            # Delete the archive file since it's now loaded
            os.remove(path)
            logger.debug(f"Loaded and deleted archive: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to load archive: {e}")
            return False

    def delete_archive(self, filename: str) -> bool:
        """Delete an archived history file"""
        path = os.path.join(self.data_dir, "archives", filename)
        if not os.path.exists(path):
            logger.error(f"Archive not found: {filename}")
            return False
            
        try:
            os.remove(path)
            logger.debug(f"Deleted archive: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete archive: {e}")
            return False

    def _get_tensor_sizes(self, data):
        """Get sizes of tensors in the data"""
        if data is None:
            return {}
        
        sizes = {}
        if isinstance(data, list):
            for i, value in enumerate(data):
                if isinstance(value, torch.Tensor):
                    sizes[f"output_{i}"] = list(value.shape)
                elif isinstance(value, (list, tuple)):
                    sizes[f"output_{i}"] = [len(value)]
        return sizes

    def _benchmark_reset_stats(self, iterations=1000):
        """Benchmark the overhead of reset_peak_memory_stats"""
        start = time.perf_counter_ns()
        for _ in range(iterations):
            torch.cuda.reset_peak_memory_stats()
        end = time.perf_counter_ns()
        avg_ns = (end - start) / iterations
        logger.debug(f"Average reset_peak_memory_stats time: {avg_ns:.2f} nanoseconds")
        return avg_ns 