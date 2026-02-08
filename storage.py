"""Data persistence for ProfilerX — ported from profiler_core.py"""
import json
import os
import time
import threading
import logging
import concurrent.futures
from collections import defaultdict
from typing import Dict, List, Optional

logger = logging.getLogger('ComfyUI-ProfilerX')

class StorageManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.history: List[Dict] = []
        self.max_history = 10000
        self.node_averages: Dict[str, Dict] = defaultdict(lambda: {
            'total_time': 0.0, 'count': 0, 'vram_usage': 0.0, 'ram_usage': 0.0,
            '_m2_time': 0.0, '_m2_vram': 0.0, '_m2_ram': 0.0,
            'std_time': 0.0, 'std_vram': 0.0, 'std_ram': 0.0,
        })
        self.workflow_averages = {
            'total_time': 0.0, 'count': 0, 'vram_peak': 0.0, 'ram_peak': 0.0,
            '_m2_time': 0.0, '_m2_vram': 0.0, '_m2_ram': 0.0,
            'std_time': 0.0, 'std_vram': 0.0, 'std_ram': 0.0,
        }

        self.data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.history_file = os.path.join(self.data_dir, "profiling_history.json")

        # Load existing history
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
                self.history = []

        self._save_counter = 0
        self._save_batch_size = 5
        self._save_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="ProfilerSave")

    # --- Averages ---

    @staticmethod
    def _welford_update(avg, m2, n, new_value):
        """Welford's online algorithm: returns (new_avg, new_m2, stddev)."""
        delta = new_value - avg
        new_avg = avg + delta / n
        delta2 = new_value - new_avg
        new_m2 = m2 + delta * delta2
        stddev = (new_m2 / n) ** 0.5 if n > 1 else 0.0
        return new_avg, new_m2, stddev

    def _update_node_average(self, node_type: str, execution_time: float, vram_used: float, ram_used: float) -> Dict:
        avg = self.node_averages[node_type]
        avg['count'] += 1
        n = avg['count']
        avg['total_time'], avg['_m2_time'], avg['std_time'] = self._welford_update(
            avg['total_time'], avg['_m2_time'], n, execution_time)
        avg['vram_usage'], avg['_m2_vram'], avg['std_vram'] = self._welford_update(
            avg['vram_usage'], avg['_m2_vram'], n, vram_used)
        avg['ram_usage'], avg['_m2_ram'], avg['std_ram'] = self._welford_update(
            avg['ram_usage'], avg['_m2_ram'], n, ram_used)
        return avg

    def _update_workflow_average(self, execution_time: float, vram_peak: float, ram_peak: float) -> Dict:
        wa = self.workflow_averages
        wa['count'] += 1
        n = wa['count']
        wa['total_time'], wa['_m2_time'], wa['std_time'] = self._welford_update(
            wa['total_time'], wa['_m2_time'], n, execution_time)
        wa['vram_peak'], wa['_m2_vram'], wa['std_vram'] = self._welford_update(
            wa['vram_peak'], wa['_m2_vram'], n, vram_peak)
        wa['ram_peak'], wa['_m2_ram'], wa['std_ram'] = self._welford_update(
            wa['ram_peak'], wa['_m2_ram'], n, ram_peak)
        return wa

    # --- Save / Load ---

    def _save_history(self, force=False):
        if not force:
            self._save_counter += 1
            if self._save_counter < self._save_batch_size:
                return
            self._save_counter = 0
        self._save_executor.submit(self._sync_save_history)

    def _sync_save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history[-self.max_history:], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    # --- Run storage ---

    def save_run(self, run_data: Dict):
        """Save a completed run and update averages."""
        with self._lock:
            # Update node averages
            for node in run_data.get('nodes', {}).values():
                if not node.get('cacheHit', False):
                    self._update_node_average(
                        node.get('nodeType', 'unknown'),
                        node.get('endTime', 0) - node.get('startTime', 0),
                        node.get('vramAfter', 0) - node.get('vramBefore', 0),
                        node.get('ramAfter', 0) - node.get('ramBefore', 0),
                    )

            # Update workflow averages
            exec_time = run_data.get('endTime', 0) - run_data.get('startTime', 0)
            self._update_workflow_average(
                exec_time,
                run_data.get('totalVramPeak', 0),
                run_data.get('totalRamPeak', 0),
            )

            # Inject averages + stddev into run_data for frontend
            wa = self.workflow_averages
            run_data['averages'] = {
                'execution_time': wa['total_time'],
                'vram_peak': wa['vram_peak'],
                'ram_peak': wa['ram_peak'],
                'count': wa['count'],
                'std_time': wa['std_time'],
                'std_vram': wa['std_vram'],
                'std_ram': wa['std_ram'],
            }
            for node in run_data.get('nodes', {}).values():
                nt = node.get('nodeType', 'unknown')
                if nt in self.node_averages:
                    a = self.node_averages[nt]
                    node['averages'] = {
                        'execution_time': a['total_time'],
                        'vram_usage': a['vram_usage'],
                        'ram_usage': a['ram_usage'],
                        'count': a['count'],
                        'std_time': a['std_time'],
                        'std_vram': a['std_vram'],
                        'std_ram': a['std_ram'],
                    }

            self.history.append(run_data)
            if len(self.history) >= self.max_history:
                self.archive_history()
            else:
                self._save_history()

    @staticmethod
    def _strip_internal(d: Dict) -> Dict:
        """Strip internal _m2_* fields from a dict for API responses."""
        return {k: v for k, v in d.items() if not k.startswith('_')}

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                'current': {},
                'latest': self.history[-1] if self.history else None,
                'node_averages': {k: self._strip_internal(v) for k, v in self.node_averages.items()},
                'workflow_averages': self._strip_internal(self.workflow_averages),
                'history': self.history[-10:],
            }

    # --- Archives ---

    def _archive_dir(self):
        d = os.path.join(self.data_dir, "archives")
        os.makedirs(d, exist_ok=True)
        return d

    def get_archives(self) -> List[Dict]:
        archives = []
        try:
            for fn in os.listdir(self._archive_dir()):
                if fn.endswith('.json'):
                    path = os.path.join(self._archive_dir(), fn)
                    stat = os.stat(path)
                    archives.append({
                        'filename': fn, 'size': stat.st_size,
                        'created': stat.st_ctime, 'modified': stat.st_mtime,
                    })
            return sorted(archives, key=lambda x: x['created'], reverse=True)
        except Exception as e:
            logger.error(f"Failed to get archives: {e}")
            return []

    def archive_history(self) -> Optional[str]:
        if not self.history:
            return None
        try:
            fn = f"profiling_history_{int(time.time())}.json"
            path = os.path.join(self._archive_dir(), fn)
            with open(path, 'w') as f:
                json.dump(self.history, f, indent=2)
            self.history = []
            self._sync_save_history()
            return fn
        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            return None

    def load_archive(self, filename: str) -> bool:
        path = os.path.join(self._archive_dir(), filename)
        if not os.path.exists(path):
            return False
        try:
            if self.history:
                self.archive_history()
            with open(path, 'r') as f:
                data = json.load(f)
            if not isinstance(data, list):
                return False
            self.history = data
            self._sync_save_history()
            os.remove(path)
            return True
        except Exception as e:
            logger.error(f"Failed to load archive: {e}")
            return False

    def delete_archive(self, filename: str) -> bool:
        path = os.path.join(self._archive_dir(), filename)
        if not os.path.exists(path):
            return False
        try:
            os.remove(path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete archive: {e}")
            return False
