# ComfyUI ProfilerX

> **v2.0 — Fully rewritten for modern ComfyUI!** The old version broke when ComfyUI moved to async execution. This rewrite uses ComfyUI's official `ProgressHandler` API instead of monkey-patching, so it's stable and forward-compatible. If you tried ProfilerX before and hit crashes, update and try again — it works now.

A performance profiling suite for ComfyUI that automatically tracks execution time, memory usage, and cache performance of your workflows.

## Features

- 🔄 Real-time monitoring of workflow execution
- 📊 Memory usage tracking (VRAM and RAM)
- ⚡ Node execution time breakdown
- 💾 Cache hit/miss statistics
- 📈 Historical data tracking and analysis with standard deviation
- 🎯 Zero configuration required
- 📱 Responsive UI that integrates with ComfyUI's interface
- ⚙️ Time-range filtering for analytics
- 🔍 Sortable performance tables
- 🍎 Apple Silicon (MPS) support

## Requirements

- ComfyUI (latest version)
- Python 3.8+
- GPU for VRAM monitoring (CUDA or Apple Silicon MPS; CPU-only systems track RAM only)
- Modern web browser

## Installation

### Option 1: ComfyUI Manager (Recommended)
1. Install [ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager)
2. Use the Manager's interface to install "ComfyUI ProfilerX"
3. Restart ComfyUI

### Option 2: Manual Installation
1. Clone this repository into your `custom_nodes` directory:
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/ryanontheinside/ComfyUI_ProfilerX
```

2. Install the required Python package:
```bash
cd ComfyUI_ProfilerX
pip install -r requirements.txt
```

3. Restart ComfyUI

## Usage

The profiler integrates directly into ComfyUI's interface:

1. After installation, you'll see a chart icon button in the top menu bar
2. Run your workflows as normal
3. Click the icon to open the dashboard, which shows:
   - Total execution time with average and standard deviation
   - Peak memory usage (VRAM and RAM)
   - Cache performance metrics (hits/misses)
   - Per-node execution time breakdown
   - Historical performance trends
   - Node analytics with stddev across runs

<img src="https://github.com/user-attachments/assets/4dd514a4-8d52-4047-9f2c-3588a669e2c9" alt="ProfilerX Interface" width="600">

The profiler runs automatically in the background, collecting data for every workflow execution. No additional configuration is needed.

## Features in Detail

### Latest Run
- Per-node execution time, VRAM delta, RAM delta
- Cache hit/miss status per node
- Workflow totals with averages and ±stddev

### Node Analytics
- Average execution time and VRAM per node type
- Standard deviation columns for time and VRAM
- Cache hit rate per node type
- Time-range filtering
- Sortable columns

### Historical Trends
- Recent workflow runs with duration, VRAM peak, cache rate
- Time-range filtering (1h, 6h, 24h, 7d, all)
- Overall workflow averages

### Data Management
- Automatic history tracking (up to 10,000 runs)
- Data persistence between sessions
- Archive create/load/delete from the Settings tab
- Auto-archive when history limit is reached

## How it Works

ProfilerX uses ComfyUI's official `ProgressHandler` API to collect performance metrics with minimal overhead:

- A single small patch re-injects the profiler handler when ComfyUI resets progress state for each execution
- `start_handler` / `finish_handler` callbacks measure per-node timing and memory
- Cache hits are detected automatically (nodes that receive `finish` without `start`)
- VRAM is tracked via `torch.cuda` (NVIDIA) or `torch.mps` (Apple Silicon), RAM via `psutil`
- Standard deviation is computed incrementally using Welford's online algorithm
- Historical data is stored locally in `data/profiling_history.json`

## REST API

ProfilerX exposes endpoints for the frontend (also usable by scripts):

- `GET /profilerx/stats` — latest run, history, node averages, workflow averages
- `GET /profilerx/archives` — list archive files
- `POST /profilerx/archive` — archive current history
- `POST /profilerx/archive/{filename}/load` — load an archive
- `DELETE /profilerx/archive/{filename}` — delete an archive

## Other Projects by RyanOnTheInside

Check out my other ComfyUI custom nodes:

- [ComfyUI_RyanOnTheInside](https://github.com/RyanOnTheInside/ComfyUI_RyanOnTheInside) - Everything Reactivity
- [ComfyUI_RealTimeNodes](https://github.com/RyanOnTheInside/ComfyUI_RealTimeNodes) - Real-Time ComfyUI Use Cases

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT License - feel free to use this in your own projects!
