# JuiceFS Operation Log Analyzer

A Python tool for analyzing JuiceFS filesystem operation logs to understand I/O patterns, performance characteristics, and access behaviors.

## Features

- **I/O Pattern Analysis**: Detects sequential vs random access patterns
- **Performance Metrics**: Latency, throughput, and duration statistics  
- **Operation Breakdown**: Detailed analysis of reads, writes, and metadata operations
- **Size Distribution**: I/O request size patterns
- **Temporal Analysis**: Time spans, operation rates, and gaps
- **Concurrency Metrics**: File handle usage and concurrent access patterns

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd oplog-analysis

# Install with uv
uv sync
```

## Usage

### Command Line Interface

```bash
# Analyze a JuiceFS operation log file
uv run oplog-analyze /path/to/logfile.log

# Alternative: run directly with Python
python -m src.oplog_analysis.log_analyzer /path/to/logfile.log
```

### Demo

```bash
# Run demo with sample logs (if available in logs/ directory)
python main.py
```

## Log Format

This tool analyzes JuiceFS logs with the format defined in `CLAUDE.md`:

```
[timestamp] [uid:X,gid:Y,pid:Z] operation (arguments): OK (result) <duration>
```

### Supported Operations

- **read**: `(inode, size, offset, file-handler)` - File read operations
- **write**: `(inode, size, offset, file-handler)` - File write operations  
- **open**: `(inode, flags)` - File open operations
- **getattr**: `(inode)` - File attribute queries
- **lookup**: Directory lookups
- **create**: `(parent-inode, name, mode, umask)` - File creation
- **flush**: `(inode, file-handler)` - File flush operations
- **unlink**: `(parent-inode, name)` - File deletion

## Output Analysis

The analyzer provides comprehensive reports including:

### Summary Section
- Total operations count and unique inodes
- Time span analysis (start, end, duration)
- Operations per second rate
- Access pattern classification (Sequential/Random/Mixed)
- Data transfer volumes (read/write breakdown)

### Operation Breakdown
- Distribution by operation type with percentages
- Visual bar charts showing operation frequency

### I/O Statistics
- Read/write operation counts and size statistics
- Min, max, average, and median I/O sizes
- Read/write ratio analysis

### Performance Metrics
- Duration statistics (min, max, avg, median, total)
- Throughput calculations (overall, read, write)

### I/O Behavior Analysis
- Sequential vs random access transition counts
- Seek pattern analysis (backward/forward seeks)
- Average and maximum seek distances
- File handle concurrency metrics
- High-activity file identification
- Temporal gap analysis

### Size Distribution
- Histogram of I/O request sizes by buckets
- Separate analysis for reads and writes

## Example Output

Here's an example analysis of a JuiceFS log showing high-throughput sequential reads:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            LOG ANALYSIS SUMMARY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Total Operations        │                                         10000 │
│ Unique Inodes          │                                            44 │
│ Time Span Start        │                    2025.08.01 09:37:51.270074 │
│ Time Span End          │                    2025.08.01 09:38:01.443013 │
│ Total Time Span        │                                      10.17s │
│ Operations per Second  │                                      983.0 │
│ Access Pattern         │                                    SEQUENTIAL │
│ Sequential Access      │                                       89.6% │
│ Random Access          │                                       10.4% │
│ Total Data Read        │                                       223.3MB │
│ Total Data Transfer    │                                       223.3MB │
├─────────────────────────────────────────────────────────────────────────────┤
│                           OPERATION BREAKDOWN                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ Flush              │     2396 ( 24.0%) │               ███████████ │
│ Getattr            │      811 (  8.1%) │                      ████ │
│ Lookup             │       98 (  1.0%) │                           │
│ Open               │     2397 ( 24.0%) │               ███████████ │
│ Read               │     1902 ( 19.0%) │                 █████████ │
│ Release            │     2396 ( 24.0%) │               ███████████ │
├─────────────────────────────────────────────────────────────────────────────┤
│                              I/O STATISTICS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Total Reads            │                                          1902 │
│ Min Read Size          │                                         4.0KB │
│ Max Read Size          │                                       128.0KB │
│ Avg Read Size          │                                       120.2KB │
│ Median Read Size       │                                       128.0KB │
│ Read/Write Ratio       │                                   100.0% / 0.0% │
├─────────────────────────────────────────────────────────────────────────────┤
│                           PERFORMANCE METRICS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Min Duration           │                                   0.000000s │
│ Max Duration           │                                   0.135695s │
│ Avg Duration           │                                   0.002311s │
│ Median Duration        │                                   0.000003s │
│ Total Duration         │                                     23.110s │
│ Avg Throughput         │                                      9.7MB/s │
│ Read Throughput        │                                      9.7MB/s │
├─────────────────────────────────────────────────────────────────────────────┤
│                              I/O BEHAVIOR                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Total Transitions      │                                          1874 │
│ Backward Seeks         │                                           116 │
│ Forward Seeks          │                                            79 │
│ Avg Seek Distance      │                                        74.9GB │
│ Max Seek Distance      │                                        34.3TB │
│ Unique File Handles    │                                          2412 │
│ Avg Ops per Handle     │                                        1.8 │
│ Files with >100 Ops    │                                            11 │
│ Max Time Gap           │                                      0.377s │
│ Avg Time Gap           │                                   0.001022s │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           I/O SIZE DISTRIBUTION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                               READ SIZES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ ≤4KB               │       19 (  1.0%) │                           │
│ ≤8KB               │        2 (  0.1%) │                           │
│ ≤32KB              │       42 (  2.2%) │                         █ │
│ ≤64KB              │       30 (  1.6%) │                           │
│ ≤128KB             │     1809 ( 95.1%) │ ███████████████████████████████████████████████ │
└─────────────────────────────────────────────────────────────────────────────┘
```

This example shows a **high-performance sequential workload** with:
- **983 operations/second** over 10 seconds
- **89.6% sequential access** pattern
- **9.7MB/s throughput** with mostly 128KB reads
- **2,412 file handles** with high concurrency
- **Large file operations** across terabyte-scale offsets

## Use Cases

This tool is useful for:

- **Performance Analysis**: Identify I/O bottlenecks and patterns
- **Workload Characterization**: Understand application access patterns  
- **Capacity Planning**: Analyze throughput and concurrency requirements
- **Troubleshooting**: Diagnose filesystem performance issues
- **Optimization**: Guide caching and prefetching strategies

## Requirements

- Python 3.8+
- uv package manager
- JuiceFS log files in the supported format

## License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.