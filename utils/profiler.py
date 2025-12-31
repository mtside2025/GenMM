"""
Processing Time Profiler Module
Provides profiling functionality for performance measurement and analysis.
"""
import time
import os
from datetime import datetime
from collections import defaultdict
from contextlib import contextmanager


class Profiler:
    """Class for profiling processing time"""
    
    def __init__(self, enabled=False):
        """
        Args:
            enabled: bool, whether to enable profiling
        """
        self.enabled = enabled
        self.timers = defaultdict(list)  # {name: [time1, time2, ...]}
        self.stack = []  # Stack for managing nested timers
        self.start_time = None
        self.end_time = None
        self.metadata = {}  # Additional information (iterations, frames, etc.)
        
    def start(self):
        """Start overall measurement"""
        if self.enabled:
            self.start_time = time.time()
            self.timers.clear()
            self.stack.clear()
            self.metadata.clear()
    
    def stop(self):
        """Stop overall measurement"""
        if self.enabled:
            self.end_time = time.time()
    
    def set_metadata(self, key, value):
        """Set metadata (iterations, frames, etc.)"""
        if self.enabled:
            self.metadata[key] = value
    
    @contextmanager
    def timer(self, name):
        """
        Timer to be used as a context manager
        
        Usage:
            with profiler.timer("processing_name"):
                # processing
        """
        if not self.enabled:
            yield
            return
        
        start = time.time()
        self.stack.append(name)
        try:
            yield
        finally:
            elapsed = time.time() - start
            self.timers[name].append(elapsed)
            self.stack.pop()
    
    def get_total_time(self):
        """Get total processing time"""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time
    
    def get_timer_stats(self, name):
        """Get statistics for a specific timer"""
        if name not in self.timers:
            return None
        
        times = self.timers[name]
        total = sum(times)
        count = len(times)
        avg = total / count if count > 0 else 0
        
        return {
            'total': total,
            'count': count,
            'avg': avg,
            'min': min(times) if times else 0,
            'max': max(times) if times else 0
        }
    
    def get_summary(self):
        """Get profiling results summary"""
        if not self.enabled:
            return None
        
        total_time = self.get_total_time()
        summary = {
            'total_time': total_time,
            'timers': {},
            'metadata': self.metadata.copy()
        }
        
        for name in sorted(self.timers.keys()):
            stats = self.get_timer_stats(name)
            if stats:
                summary['timers'][name] = stats
        
        return summary
    
    def print_summary(self):
        """Print profiling results to console (English only)"""
        if not self.enabled:
            return
        
        summary = self.get_summary()
        if summary is None:
            return
        
        print("\n" + "="*80)
        print("Processing Time Profile")
        print("="*80)
        
        # Total processing time
        print(f"\n[Total Processing Time]")
        print(f"  Total: {summary['total_time']:.3f} seconds")
        
        # Metadata information
        if summary['metadata']:
            print(f"\n[Processing Info]")
            
            # Display normalized iteration info prominently
            if 'iterations_per_level' in summary['metadata'] and 'num_pyramid_levels' in summary['metadata']:
                iters_per_level = summary['metadata']['iterations_per_level']
                num_levels = summary['metadata']['num_pyramid_levels']
                total_iters = summary['metadata'].get('total_iterations', iters_per_level * num_levels)
                # Calculate time per iteration using iterations_per_level (not total_iterations)
                time_per_iter = summary['total_time'] / iters_per_level if iters_per_level > 0 else 0
                print(f"  >>> Iterations: {iters_per_level} steps/level × {num_levels} levels = {total_iters} total")
                print(f"  >>> Time per iteration: {time_per_iter:.3f} sec/iter")
            
            # Display other metadata
            for key, value in summary['metadata'].items():
                if key not in ['iterations_per_level', 'num_pyramid_levels', 'total_iterations']:
                    print(f"  {key}: {value}")
            
            # Time per frame
            if 'total_frames' in summary['metadata']:
                frames = summary['metadata']['total_frames']
                time_per_frame = summary['total_time'] / frames if frames > 0 else 0
                print(f"  >>> Time per frame: {time_per_frame:.3f} sec/frame")
        
        # Detailed time by process
        if summary['timers']:
            print(f"\n[Time by Process]")
            print(f"  {'Process Name':<40} {'Total (sec)':<15} {'Count':<10} {'Avg (sec)':<15} {'%':<10}")
            print(f"  {'-'*40} {'-'*15} {'-'*10} {'-'*15} {'-'*10}")
            
            total_time = summary['total_time']
            for name, stats in sorted(summary['timers'].items(), key=lambda x: x[1]['total'], reverse=True):
                percentage = (stats['total'] / total_time * 100) if total_time > 0 else 0
                print(f"  {name:<40} {stats['total']:>12.3f} {stats['count']:>10d} {stats['avg']:>12.3f} {percentage:>9.1f}%")
        
        print("="*80 + "\n")
    
    def save_to_file(self, filepath):
        """Save profiling results to CSV file (timing statistics only)"""
        if not self.enabled:
            return
        
        summary = self.get_summary()
        if summary is None:
            return
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            # Write CSV header only (no metadata comments)
            f.write("Process Name,Total Time (sec),Count,Average Time (sec),Percentage (%)\n")
            
            # Write process data
            if summary['timers']:
                total_time = summary['total_time']
                for name, stats in sorted(summary['timers'].items(), key=lambda x: x[1]['total'], reverse=True):
                    percentage = (stats['total'] / total_time * 100) if total_time > 0 else 0
                    f.write(f"{name},{stats['total']:.3f},{stats['count']},{stats['avg']:.3f},{percentage:.1f}\n")
        
        print(f"Profile saved to: {filepath}")


# Global profiler instance
_global_profiler = Profiler(enabled=False)


def get_profiler():
    """Get global profiler"""
    return _global_profiler


def enable_profiling():
    """Enable profiling"""
    _global_profiler.enabled = True


def disable_profiling():
    """Disable profiling"""
    _global_profiler.enabled = False
