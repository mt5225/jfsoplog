#!/usr/bin/env python3
import re
from collections import defaultdict
from typing import List, Dict
import statistics

def parse_log_line(line: str) -> Dict:
    """Parse a single JuiceFS log line using format from CLAUDE.md."""
    # Basic format: [UID,GID,PID] [operation] [arguments]: [OK] [debug info] <duration (s)>
    # With timestamp prefix in this log
    pattern = r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d+) \[uid:(\d+),gid:(\d+),pid:(\d+)\] (\w+) \(([^)]+)\): OK(.*?) <([\d.]+)>'
    
    match = re.match(pattern, line.strip())
    if not match:
        return None
    
    timestamp, uid, gid, pid, operation, args, result_debug, duration = match.groups()
    
    # Parse arguments based on operation type from CLAUDE.md specs
    args_list = [arg.strip() for arg in args.split(',')]
    
    parsed = {
        'timestamp': timestamp,
        'uid': int(uid),
        'gid': int(gid),
        'pid': int(pid),
        'operation': operation,
        'duration': float(duration),
        'args': args_list,
        'result_debug': result_debug.strip()
    }
    
    # Parse operation-specific arguments according to CLAUDE.md format
    if operation == 'read' and len(args_list) >= 4:
        # read, arguments (inode, size, offset, file-handler)
        parsed['inode'] = int(args_list[0])
        parsed['size'] = int(args_list[1])
        parsed['offset'] = int(args_list[2])
        parsed['handle'] = int(args_list[3])
        # Extract bytes read from result
        result_match = re.search(r'\((\d+)\)', result_debug)
        parsed['bytes_read'] = int(result_match.group(1)) if result_match else parsed['size']
    
    elif operation == 'open' and len(args_list) >= 2:
        # open, arguments (inode, flags)
        parsed['inode'] = int(args_list[0])
        parsed['flags'] = args_list[1]
        # Extract handle from debug info
        handle_match = re.search(r'\[handle:(\w+)\]', result_debug)
        parsed['handle'] = handle_match.group(1) if handle_match else None
    
    elif operation == 'getattr' and len(args_list) >= 1:
        # getattr, arguments (inode)
        parsed['inode'] = int(args_list[0]) if args_list[0].isdigit() else None
        if len(args_list) > 1:
            parsed['flags'] = args_list[1]
    
    elif operation == 'create' and len(args_list) >= 4:
        # create, arguments (parent-inode, name, mode, umask)
        parsed['parent_inode'] = int(args_list[0])
        parsed['name'] = args_list[1]
        parsed['mode'] = args_list[2]
        parsed['umask'] = args_list[3] if len(args_list) > 3 else None
    
    elif operation == 'write' and len(args_list) >= 4:
        # write, arguments (inode, size, offset, file-handler)
        parsed['inode'] = int(args_list[0])
        parsed['size'] = int(args_list[1])
        parsed['offset'] = int(args_list[2])
        parsed['handle'] = int(args_list[3])
    
    elif operation == 'unlink' and len(args_list) >= 2:
        # unlink, arguments (parent-inode, name)
        parsed['parent_inode'] = int(args_list[0])
        parsed['name'] = args_list[1]
    
    elif operation == 'flush' and len(args_list) >= 2:
        # flush, arguments (inode, file-handler)
        parsed['inode'] = int(args_list[0])
        parsed['handle'] = int(args_list[1])
    
    elif operation in ['lookup', 'statfs']:
        # These operations typically have inode as first argument
        if args_list and args_list[0].isdigit():
            parsed['inode'] = int(args_list[0])
    
    return parsed

def analyze_io_behavior(operations: List[Dict]) -> Dict:
    """Analyze detailed I/O behavior patterns."""
    if not operations:
        return {}
    
    # Analyze file handle usage
    handle_usage = defaultdict(int)
    inode_operations = defaultdict(int)
    operation_timestamps = []
    raw_timestamps = []
    
    for op in operations:
        if 'handle' in op and op['handle']:
            handle_usage[op['handle']] += 1
        if 'inode' in op and op['inode']:
            inode_operations[op['inode']] += 1
        
        # Parse timestamp for temporal analysis
        try:
            timestamp_str = op['timestamp']
            raw_timestamps.append(timestamp_str)
            
            # Convert to seconds for gap calculation
            time_parts = timestamp_str.split(' ')[1].split('.')
            time_part = time_parts[0]
            microsec = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            hour, minute, second = map(int, time_part.split(':'))
            total_seconds = hour * 3600 + minute * 60 + second + microsec / 1000000.0
            operation_timestamps.append(total_seconds)
        except:
            pass
    
    # Calculate time span and operation rate
    time_span_seconds = 0
    ops_per_second = 0
    start_time = ""
    end_time = ""
    
    if raw_timestamps:
        start_time = min(raw_timestamps)
        end_time = max(raw_timestamps)
        
        if len(operation_timestamps) > 1:
            operation_timestamps.sort()
            time_span_seconds = operation_timestamps[-1] - operation_timestamps[0]
            if time_span_seconds > 0:
                ops_per_second = len(operations) / time_span_seconds
    
    # Calculate temporal gaps
    temporal_gaps = []
    if len(operation_timestamps) > 1:
        operation_timestamps.sort()
        for i in range(1, len(operation_timestamps)):
            gap = operation_timestamps[i] - operation_timestamps[i-1]
            if gap > 0:  # Only positive gaps
                temporal_gaps.append(gap)
    
    # Count high-activity files (>100 operations)
    high_activity_files = sum(1 for count in inode_operations.values() if count > 100)
    
    return {
        'unique_handles': len(handle_usage),
        'avg_ops_per_handle': statistics.mean(handle_usage.values()) if handle_usage else 0,
        'high_activity_files': high_activity_files,
        'temporal_gaps': len(temporal_gaps),
        'max_gap': max(temporal_gaps) if temporal_gaps else 0,
        'avg_gap': statistics.mean(temporal_gaps) if temporal_gaps else 0,
        'time_span_seconds': time_span_seconds,
        'ops_per_second': ops_per_second,
        'start_time': start_time,
        'end_time': end_time
    }

def analyze_access_pattern(operations: List[Dict]) -> Dict:
    """Analyze access pattern and return detailed statistics."""
    io_ops = [op for op in operations if op['operation'] in ['read', 'write'] and 'offset' in op]
    
    if len(io_ops) < 2:
        return {
            'pattern': 'insufficient_data',
            'sequential_percentage': 0,
            'random_percentage': 0,
            'total_transitions': 0
        }
    
    # Group by inode
    by_inode = defaultdict(list)
    for op in io_ops:
        by_inode[op['inode']].append(op)
    
    sequential_count = 0
    random_count = 0
    backward_seeks = 0
    forward_seeks = 0
    seek_distances = []
    
    for ops in by_inode.values():
        if len(ops) < 2:
            continue
            
        # Sort by timestamp
        ops.sort(key=lambda x: x['timestamp'])
        
        # Analyze consecutive reads
        for i in range(1, len(ops)):
            prev_op = ops[i-1]
            curr_op = ops[i]
            
            prev_end = prev_op['offset'] + prev_op['size']
            curr_start = curr_op['offset']
            
            # Calculate seek distance
            seek_distance = abs(curr_start - prev_end)
            seek_distances.append(seek_distance)
            
            # Determine access pattern
            if seek_distance <= prev_op['size']:  # Allow some overlap tolerance
                sequential_count += 1
            else:
                random_count += 1
                # Track seek direction
                if curr_start < prev_op['offset']:
                    backward_seeks += 1
                else:
                    forward_seeks += 1
    
    total_transitions = sequential_count + random_count
    if total_transitions == 0:
        return {
            'pattern': 'unknown',
            'sequential_percentage': 0,
            'random_percentage': 0,
            'total_transitions': 0
        }
    
    seq_percentage = (sequential_count / total_transitions) * 100
    random_percentage = (random_count / total_transitions) * 100
    
    # Determine overall pattern
    if seq_percentage > 70:
        pattern = 'sequential'
    elif seq_percentage < 30:
        pattern = 'random'
    else:
        pattern = 'mixed'
    
    return {
        'pattern': pattern,
        'sequential_percentage': seq_percentage,
        'random_percentage': random_percentage,
        'total_transitions': total_transitions,
        'backward_seeks': backward_seeks,
        'forward_seeks': forward_seeks,
        'avg_seek_distance': statistics.mean(seek_distances) if seek_distances else 0,
        'max_seek_distance': max(seek_distances) if seek_distances else 0
    }

def format_size(size_bytes: int) -> str:
    """Format size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"

def analyze_log(file_path: str):
    """Main analysis function."""
    operations = []
    
    print(f"Analyzing log file: {file_path}")
    print("=" * 80)
    
    with open(file_path, 'r') as f:
        for line in f:
            parsed = parse_log_line(line)
            if parsed:
                operations.append(parsed)
    
    if not operations:
        print("No valid operations found in log file")
        return
    
    # Basic statistics
    op_counts = defaultdict(int)
    total_read_bytes = 0
    total_write_bytes = 0
    read_sizes = []
    write_sizes = []
    durations = []
    inodes = set()
    
    for op in operations:
        op_counts[op['operation']] += 1
        durations.append(op['duration'])
        
        if op['operation'] == 'read' and 'size' in op:
            read_sizes.append(op['size'])
            total_read_bytes += op.get('bytes_read', op['size'])
        elif op['operation'] == 'write' and 'size' in op:
            write_sizes.append(op['size'])
            total_write_bytes += op['size']
        
        if 'inode' in op:
            inodes.add(op['inode'])
    
    # Analyze access pattern and I/O behavior
    access_analysis = analyze_access_pattern(operations)
    
    # Additional I/O behavior analysis
    io_analysis = analyze_io_behavior(operations)
    
    # Print ASCII table
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│                            LOG ANALYSIS SUMMARY                            │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ Total Operations        │ {len(operations):>45} │")
    print(f"│ Unique Inodes          │ {len(inodes):>45} │")
    if io_analysis and io_analysis['start_time'] and io_analysis['end_time']:
        print(f"│ Time Span Start        │ {io_analysis['start_time']:>45} │")
        print(f"│ Time Span End          │ {io_analysis['end_time']:>45} │")
        if io_analysis['time_span_seconds'] > 0:
            span_minutes = io_analysis['time_span_seconds'] / 60
            span_hours = span_minutes / 60
            if span_hours >= 1:
                print(f"│ Total Time Span        │ {span_hours:>42.2f}h │")
            elif span_minutes >= 1:
                print(f"│ Total Time Span        │ {span_minutes:>42.2f}m │")
            else:
                print(f"│ Total Time Span        │ {io_analysis['time_span_seconds']:>42.2f}s │")
            print(f"│ Operations per Second  │ {io_analysis['ops_per_second']:>42.1f} │")
    print(f"│ Access Pattern         │ {access_analysis['pattern'].upper():>45} │")
    print(f"│ Sequential Access      │ {access_analysis['sequential_percentage']:>42.1f}% │")
    print(f"│ Random Access          │ {access_analysis['random_percentage']:>42.1f}% │")
    print(f"│ Total Data Read        │ {format_size(total_read_bytes):>45} │")
    if total_write_bytes > 0:
        print(f"│ Total Data Written     │ {format_size(total_write_bytes):>45} │")
    total_bytes = total_read_bytes + total_write_bytes
    if total_bytes > 0:
        print(f"│ Total Data Transfer    │ {format_size(total_bytes):>45} │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    print("│                           OPERATION BREAKDOWN                               │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    
    for op_type, count in sorted(op_counts.items()):
        percentage = (count / len(operations)) * 100
        print(f"│ {op_type.capitalize():<18} │ {count:>8} ({percentage:>5.1f}%) │ {'█' * int(percentage/2):>25} │")
    
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    print("│                              I/O STATISTICS                                │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    
    if read_sizes:
        print(f"│ Total Reads            │ {len(read_sizes):>45} │")
        print(f"│ Min Read Size          │ {format_size(min(read_sizes)):>45} │")
        print(f"│ Max Read Size          │ {format_size(max(read_sizes)):>45} │")
        print(f"│ Avg Read Size          │ {format_size(int(statistics.mean(read_sizes))):>45} │")
        print(f"│ Median Read Size       │ {format_size(int(statistics.median(read_sizes))):>45} │")
    
    if write_sizes:
        print(f"│ Total Writes           │ {len(write_sizes):>45} │")
        print(f"│ Min Write Size         │ {format_size(min(write_sizes)):>45} │")
        print(f"│ Max Write Size         │ {format_size(max(write_sizes)):>45} │")
        print(f"│ Avg Write Size         │ {format_size(int(statistics.mean(write_sizes))):>45} │")
        print(f"│ Median Write Size      │ {format_size(int(statistics.median(write_sizes))):>45} │")
    
    # Read/Write ratio
    total_io_ops = len(read_sizes) + len(write_sizes)
    if total_io_ops > 0:
        read_percentage = (len(read_sizes) / total_io_ops) * 100
        write_percentage = (len(write_sizes) / total_io_ops) * 100
        print(f"│ Read/Write Ratio       │ {read_percentage:>39.1f}% / {write_percentage:.1f}% │")
    
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    print("│                           PERFORMANCE METRICS                              │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ Min Duration           │ {min(durations):>42.6f}s │")
    print(f"│ Max Duration           │ {max(durations):>42.6f}s │")
    print(f"│ Avg Duration           │ {statistics.mean(durations):>42.6f}s │")
    print(f"│ Median Duration        │ {statistics.median(durations):>42.6f}s │")
    print(f"│ Total Duration         │ {sum(durations):>42.3f}s │")
    
    if total_bytes > 0:
        total_time = sum(durations)
        throughput = total_bytes / total_time if total_time > 0 else 0
        print(f"│ Avg Throughput         │ {format_size(int(throughput)):>42}/s │")
        
        if total_read_bytes > 0:
            read_throughput = total_read_bytes / total_time if total_time > 0 else 0
            print(f"│ Read Throughput        │ {format_size(int(read_throughput)):>42}/s │")
        
        if total_write_bytes > 0:
            write_throughput = total_write_bytes / total_time if total_time > 0 else 0
            print(f"│ Write Throughput       │ {format_size(int(write_throughput)):>42}/s │")
    
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    print("│                              I/O BEHAVIOR                                  │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ Total Transitions      │ {access_analysis['total_transitions']:>45} │")
    print(f"│ Backward Seeks         │ {access_analysis['backward_seeks']:>45} │")
    print(f"│ Forward Seeks          │ {access_analysis['forward_seeks']:>45} │")
    if access_analysis['avg_seek_distance'] > 0:
        print(f"│ Avg Seek Distance      │ {format_size(int(access_analysis['avg_seek_distance'])):>45} │")
        print(f"│ Max Seek Distance      │ {format_size(int(access_analysis['max_seek_distance'])):>45} │")
    
    if io_analysis:
        print(f"│ Unique File Handles    │ {io_analysis['unique_handles']:>45} │")
        print(f"│ Avg Ops per Handle     │ {io_analysis['avg_ops_per_handle']:>42.1f} │")
        print(f"│ Files with >100 Ops    │ {io_analysis['high_activity_files']:>45} │")
        if io_analysis['temporal_gaps']:
            print(f"│ Max Time Gap           │ {io_analysis['max_gap']:>42.3f}s │")
            print(f"│ Avg Time Gap           │ {io_analysis['avg_gap']:>42.6f}s │")
    
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    
    # Size distribution
    if read_sizes or write_sizes:
        print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
        print("│                           I/O SIZE DISTRIBUTION                             │")
        print("├─────────────────────────────────────────────────────────────────────────────┤")
        
        if read_sizes:
            print("│                               READ SIZES                                    │")
            print("├─────────────────────────────────────────────────────────────────────────────┤")
            read_size_buckets = defaultdict(int)
            for size in read_sizes:
                if size <= 4096:
                    read_size_buckets['≤4KB'] += 1
                elif size <= 8192:
                    read_size_buckets['≤8KB'] += 1
                elif size <= 32768:
                    read_size_buckets['≤32KB'] += 1
                elif size <= 65536:
                    read_size_buckets['≤64KB'] += 1
                elif size <= 131072:
                    read_size_buckets['≤128KB'] += 1
                else:
                    read_size_buckets['>128KB'] += 1
            
            for bucket, count in sorted(read_size_buckets.items(), key=lambda x: ['≤4KB', '≤8KB', '≤32KB', '≤64KB', '≤128KB', '>128KB'].index(x[0])):
                percentage = (count / len(read_sizes)) * 100
                print(f"│ {bucket:<18} │ {count:>8} ({percentage:>5.1f}%) │ {'█' * int(percentage/2):>25} │")
        
        if write_sizes:
            if read_sizes:
                print("├─────────────────────────────────────────────────────────────────────────────┤")
            print("│                              WRITE SIZES                                   │")
            print("├─────────────────────────────────────────────────────────────────────────────┤")
            write_size_buckets = defaultdict(int)
            for size in write_sizes:
                if size <= 4096:
                    write_size_buckets['≤4KB'] += 1
                elif size <= 8192:
                    write_size_buckets['≤8KB'] += 1
                elif size <= 32768:
                    write_size_buckets['≤32KB'] += 1
                elif size <= 65536:
                    write_size_buckets['≤64KB'] += 1
                elif size <= 131072:
                    write_size_buckets['≤128KB'] += 1
                else:
                    write_size_buckets['>128KB'] += 1
            
            for bucket, count in sorted(write_size_buckets.items(), key=lambda x: ['≤4KB', '≤8KB', '≤32KB', '≤64KB', '≤128KB', '>128KB'].index(x[0])):
                percentage = (count / len(write_sizes)) * 100
                print(f"│ {bucket:<18} │ {count:>8} ({percentage:>5.1f}%) │ {'█' * int(percentage/2):>25} │")
        
        print("└─────────────────────────────────────────────────────────────────────────────┘")

def main():
    """Main entry point for the CLI."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: juicefs-analyze <log_file_path>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    analyze_log(log_file)

if __name__ == "__main__":
    main()