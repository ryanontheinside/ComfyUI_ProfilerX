"""Core profiling handler using ComfyUI's ProgressHandler API"""
import time
import logging
from comfy_execution.progress import ProgressHandler
from .metrics import snapshot_memory, reset_peak, get_peak
from .storage import StorageManager

logger = logging.getLogger('ComfyUI-ProfilerX')


class ProfilerXProgressHandler(ProgressHandler):
    def __init__(self, storage: StorageManager):
        super().__init__("profilerx")
        self.storage = storage
        self.registry = None
        # Current run state
        self._current_run = None
        self._started_nodes = set()  # Track which nodes got start_handler

    def set_registry(self, registry):
        self.registry = registry

    def reset(self):
        """Called when progress registry resets (new execution starting).
        Finalize previous run if any, then clear state."""
        if self._current_run is not None:
            self._finalize_run()
        self._current_run = None
        self._started_nodes = set()

    def _init_run(self, prompt_id: str):
        """Lazily initialize a new run on first node event."""
        if self._current_run is not None and 'endTime' not in self._current_run:
            return
        # Either no run, or previous run was already flushed — start fresh
        self._current_run = None
        self._started_nodes = set()
        self._current_run = {
            'promptId': prompt_id,
            'startTime': time.time() * 1000,
            'nodes': {},
            'executionOrder': [],
            'totalVramPeak': 0,
            'totalRamPeak': 0,
            'cacheHits': 0,
            'cacheMisses': 0,
        }

    def _finalize_run(self):
        """Finalize and save the current run."""
        run = self._current_run
        if run is None:
            return
        if 'endTime' in run:
            return  # Already finalized
        run['endTime'] = time.time() * 1000
        vram_peak, ram_peak = get_peak()
        run['totalVramPeak'] = vram_peak
        run['totalRamPeak'] = ram_peak
        logger.info(f"Finalizing run {run.get('promptId', '?')}: {len(run.get('nodes', {}))} nodes, "
                     f"{run.get('cacheMisses', 0)} executed, {run.get('cacheHits', 0)} cached")
        self.storage.save_run(run)

    def flush(self):
        """Flush current run to storage if it has data. Called by stats endpoint."""
        if self._current_run is not None and self._current_run.get('nodes'):
            self._finalize_run()

    def _get_class_type(self, node_id: str) -> str:
        """Get class_type for a node from the dynamic prompt."""
        try:
            if self.registry and self.registry.dynprompt:
                node_info = self.registry.dynprompt.get_node(node_id)
                if node_info:
                    return node_info.get('class_type', 'unknown')
        except Exception:
            pass
        return 'unknown'

    def start_handler(self, node_id: str, state, prompt_id: str):
        """Called when a node starts executing (not called for cached nodes)."""
        self._init_run(prompt_id)
        self._started_nodes.add(node_id)

        class_type = self._get_class_type(node_id)
        vram_before, ram_before = snapshot_memory()
        reset_peak()

        self._current_run['nodes'][node_id] = {
            'nodeId': node_id,
            'nodeType': class_type,
            'startTime': time.time() * 1000,
            'vramBefore': vram_before,
            'ramBefore': ram_before,
            'cacheHit': False,
        }
        self._current_run['executionOrder'].append(node_id)

    def finish_handler(self, node_id: str, state, prompt_id: str):
        """Called when a node finishes. If start_handler was never called, it's a cache hit."""
        self._init_run(prompt_id)

        if node_id not in self._started_nodes:
            # Cache hit — finish called without start
            class_type = self._get_class_type(node_id)
            self._current_run['nodes'][node_id] = {
                'nodeId': node_id,
                'nodeType': class_type,
                'startTime': 0,
                'endTime': 0,
                'vramBefore': 0,
                'vramAfter': 0,
                'vramPeak': 0,
                'ramBefore': 0,
                'ramAfter': 0,
                'cacheHit': True,
            }
            self._current_run['executionOrder'].append(node_id)
            self._current_run['cacheHits'] += 1
        else:
            # Normal execution finish
            node = self._current_run['nodes'].get(node_id)
            if node is None:
                return
            node['endTime'] = time.time() * 1000
            vram_after, ram_after = snapshot_memory()
            vram_peak, _ = get_peak()
            node['vramAfter'] = vram_after
            node['vramPeak'] = vram_peak - node['vramBefore']
            node['ramAfter'] = ram_after
            self._current_run['cacheMisses'] += 1
