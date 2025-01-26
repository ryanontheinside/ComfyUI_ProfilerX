# ComfyUI ProfilerX

A performance profiling suite for ComfyUI that automatically tracks execution time, memory usage, and cache performance of your workflows.

## Features

- 🔄 Real-time monitoring of workflow execution
- 📊 Memory usage tracking (VRAM and RAM)
- ⚡ Node execution time breakdown
- 💾 Cache hit/miss statistics
- 📈 Beautiful, interactive charts and tables
- 🎯 Zero configuration required
- 📱 Responsive UI that integrates with ComfyUI's interface
- 📊 Historical data tracking and analysis
- ⚙️ Time-range filtering for analytics
- 🔍 Sortable performance tables

## Requirements

- ComfyUI (latest version)
- Python 3.8+
- CUDA-capable GPU (for VRAM monitoring)
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

1. After installation, you'll see a new performance monitoring panel in the top-right corner
2. Run your workflows as normal
3. The dashboard will automatically update with:
   - Total execution time
   - Peak memory usage (VRAM and RAM)
   - Cache performance metrics
   - Per-node execution time breakdown
   - Historical performance trends

<img src="https://github.com/user-attachments/assets/4dd514a4-8d52-4047-9f2c-3588a669e2c9" alt="ProfilerX Interface" width="600">

The profiler runs automatically in the background, collecting data for every workflow execution. No additional configuration is needed.

## Features in Detail

### Real-time Monitoring
- Live execution time tracking
- Memory usage graphs (VRAM and RAM)
- Cache hit/miss counters
- Node-by-node progress tracking

### Analytics Dashboard
- Historical performance trends
- Node execution time breakdown
- Memory usage patterns
- Cache efficiency analysis
- Time-range filtering
- Sortable performance tables

### Data Management
- Automatic history tracking
- Data persistence between sessions
- Archive management
- Export capabilities

## How it Works

ProfilerX integrates directly with ComfyUI's execution system to collect performance metrics:

- Execution time is measured for both individual nodes and the entire workflow
- Memory usage is tracked using `torch.cuda` for VRAM and `psutil` for RAM
- Cache performance is monitored by intercepting ComfyUI's caching system
- All data is collected automatically with minimal performance impact
- Historical data is stored locally for trend analysis

## Execution Tracking

In addition to workflow profiling, this extension includes a detailed execution tracking system that monitors ComfyUI's internal method calls. This can be useful for:
- Understanding the execution flow of your workflows
- Identifying bottlenecks in specific operations
- Debugging performance issues
- Analyzing method call patterns and timing

### Enabling Execution Tracking

By default, execution tracking is disabled. To enable it:

1. Open `ComfyUI_ProfilerX/execution_core.py`
2. Find the `ENABLED` flag at the top of the `ExecutionTracker` class:
```python
class ExecutionTracker:
    _instance = None
    _lock = threading.Lock()
    ENABLED = False  # Change this to True to enable tracking
```
3. Change `ENABLED = False` to `ENABLED = True`
4. Restart ComfyUI

When enabled, the tracker will record detailed timing information for internal ComfyUI operations in `ComfyUI_ProfilerX/data/method_traces.json`.



## Other Projects by RyanOnTheInside

Check out my other ComfyUI custom nodes:

- [ComfyUI_RyanOnTheInside](https://github.com/RyanOnTheInside/ComfyUI_RyanOnTheInside) - Everything Reactivity
- [ComfyUI_RealTimeNodes](https://github.com/RyanOnTheInside/ComfyUI_RealTimeNodes) - Real-Time ComfyUI Use Cases

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT License - feel free to use this in your own projects!

