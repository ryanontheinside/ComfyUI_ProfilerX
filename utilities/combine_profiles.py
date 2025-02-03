#!/usr/bin/env python3
"""Utility script to combine multiple .prof files into one"""
import os
import glob
import pstats
import argparse
from pathlib import Path

def combine_profiles(data_dir, output_file, pattern="execution_*.prof"):
    """Combine all matching .prof files in data_dir into one"""
    combined_stats = pstats.Stats()
    
    # Find all matching .prof files
    prof_files = glob.glob(os.path.join(data_dir, pattern))
    if not prof_files:
        print(f"No .prof files found matching pattern: {pattern}")
        return None
        
    try:
        # Add each file's stats to the combined stats
        for prof_file in prof_files:
            print(f"Adding {prof_file}")
            combined_stats.add(prof_file)
            
        # Save combined stats
        output_path = os.path.join(data_dir, output_file)
        combined_stats.dump_stats(output_path)
        print(f"Successfully combined {len(prof_files)} profiles into {output_file}")
        return output_path
        
    except Exception as e:
        print(f"Error combining profiles: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine multiple .prof files into one")
    parser.add_argument("--data-dir", default="data", help="Directory containing .prof files")
    parser.add_argument("--output", default="combined_executions.prof", help="Output filename")
    parser.add_argument("--pattern", default="execution_*.prof", help="Glob pattern for files to combine")
    
    args = parser.parse_args()
    
    # Resolve data directory relative to script location
    script_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(script_dir, args.data_dir)
    
    combine_profiles(data_dir, args.output, args.pattern) 