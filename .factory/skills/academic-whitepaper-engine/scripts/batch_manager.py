#!/usr/bin/env python3
"""
Batch Processing Manager for PDF to Markdown Converter
Provides scheduling, monitoring, and automation capabilities
"""
import sys
import argparse
import logging

import schedule
import time
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    from tabulate import tabulate
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class BatchStatus(Enum):
    """Batch processing status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    """Batch job configuration"""
    name: str
    input_paths: List[str]
    output_dir: str
    config_file: Optional[str] = None
    schedule_time: Optional[str] = None  # Cron-like or specific time
    priority: int = 1
    max_retries: int = 3
    notify_on_completion: bool = True
    created_at: str = None
    status: BatchStatus = BatchStatus.PENDING
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    statistics: Optional[Dict] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BatchJob':
        return cls(**data)


class BatchManager:
    """Manages batch processing jobs"""
    
    def __init__(self, config_file: str = "batch_manager_config.yaml"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self.jobs: Dict[str, BatchJob] = {}
        self.history: List[Dict] = []
        self.load_jobs()
        
        # Ensure directories exist
        self.ensure_directories()
    
    def load_config(self) -> Dict:
        """Load configuration from YAML file"""
        default_config = {
            'storage': {
                'jobs_file': 'batch_jobs.json',
                'history_file': 'batch_history.json',
                'log_directory': 'batch_logs'
            },
            'scheduling': {
                'check_interval': 60,  # seconds
                'max_concurrent': 2,
                'retry_delay': 300,  # seconds
                'cleanup_days': 30
            },
            'monitoring': {
                'enable_dashboard': True,
                'dashboard_port': 8080,
                'enable_notifications': False,
                'stats_interval': 3600  # seconds
            },
            'converter': {
                'default_config': 'config.yaml',
                'default_output': 'batch_output',
                'default_workers': 2
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge configurations
                self.merge_configs(default_config, user_config)
        
        return default_config
    
    def merge_configs(self, base: Dict, update: Dict) -> Dict:
        """Merge configuration dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self.merge_configs(base[key], value)
            else:
                base[key] = value
        return base
    
    def ensure_directories(self):
        """Ensure necessary directories exist"""
        storage_config = self.config['storage']
        
        log_dir = Path(storage_config['log_directory'])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (log_dir / 'completed').mkdir(exist_ok=True)
        (log_dir / 'failed').mkdir(exist_ok=True)
        (log_dir / 'running').mkdir(exist_ok=True)
    
    def load_jobs(self):
        """Load jobs from storage"""
        jobs_file = Path(self.config['storage']['jobs_file'])
        if jobs_file.exists():
            try:
                with open(jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                    for name, job_data in jobs_data.items():
                        self.jobs[name] = BatchJob.from_dict(job_data)
                logger.info(f"Loaded {len(self.jobs)} jobs from {jobs_file}")
            except Exception as e:
                logger.error(f"Failed to load jobs: {e}")
    
    def save_jobs(self):
        """Save jobs to storage"""
        jobs_file = Path(self.config['storage']['jobs_file'])
        jobs_data = {name: job.to_dict() for name, job in self.jobs.items()}
        
        try:
            with open(jobs_file, 'w') as f:
                json.dump(jobs_data, f, indent=2)
            logger.debug(f"Saved {len(self.jobs)} jobs to {jobs_file}")
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")
    
    def load_history(self):
        """Load history from storage"""
        history_file = Path(self.config['storage']['history_file'])
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    self.history = json.load(f)
                logger.info(f"Loaded {len(self.history)} history entries")
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
    
    def save_history(self):
        """Save history to storage"""
        history_file = Path(self.config['storage']['history_file'])
        
        # Keep only recent history
        cutoff_date = datetime.now() - timedelta(days=self.config['scheduling']['cleanup_days'])
        recent_history = [
            entry for entry in self.history
            if datetime.fromisoformat(entry['completed_at']) > cutoff_date
        ]
        
        try:
            with open(history_file, 'w') as f:
                json.dump(recent_history, f, indent=2)
            logger.debug(f"Saved {len(recent_history)} history entries")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def add_job(self, job: BatchJob):
        """Add a new batch job"""
        if job.name in self.jobs:
            logger.warning(f"Job '{job.name}' already exists. Updating...")
        
        self.jobs[job.name] = job
        self.save_jobs()
        logger.info(f"Added job: {job.name}")
    
    def remove_job(self, job_name: str):
        """Remove a batch job"""
        if job_name in self.jobs:
            del self.jobs[job_name]
            self.save_jobs()
            logger.info(f"Removed job: {job_name}")
        else:
            logger.warning(f"Job '{job_name}' not found")
    
    def run_job(self, job_name: str) -> Dict:
        """Run a specific job"""
        if job_name not in self.jobs:
            logger.error(f"Job '{job_name}' not found")
            return {'status': 'error', 'message': 'Job not found'}
        
        job = self.jobs[job_name]
        job.status = BatchStatus.RUNNING
        job.last_run = datetime.now().isoformat()
        self.save_jobs()
        
        logger.info(f"Starting job: {job.name}")
        
        try:
            import subprocess
            script_path = Path(__file__).parent / "pdf_to_markdown_converter.py"
            
            for input_file in job.input_paths:
                subprocess.run([sys.executable, str(script_path), input_file, '-o', job.output_dir], check=True)
            
            # Update job status
            job.status = BatchStatus.COMPLETED
            job.statistics = {}
            
            # Add to history
            history_entry = {
                'job_name': job.name,
                'started_at': job.last_run,
                'completed_at': datetime.now().isoformat(),
                'status': 'completed',
                'statistics': {},
                'output_dir': job.output_dir
            }
            self.history.append(history_entry)
            
            logger.info(f"Completed job: {job.name}")
            
            return {
                'status': 'success',
                'job': job.to_dict(),
                'statistics': {}
            }
            
        except Exception as e:
            logger.error(f"Job '{job.name}' failed: {e}")
            
            job.status = BatchStatus.FAILED
            
            history_entry = {
                'job_name': job.name,
                'started_at': job.last_run,
                'completed_at': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e),
                'output_dir': job.output_dir
            }
            self.history.append(history_entry)
            
            return {
                'status': 'error',
                'job': job.to_dict(),
                'error': str(e)
            }
        finally:
            self.save_jobs()
            self.save_history()
    
    def run_all_pending(self):
        """Run all pending jobs"""
        pending_jobs = [
            job for job in self.jobs.values()
            if job.status == BatchStatus.PENDING
        ]
        
        if not pending_jobs:
            logger.info("No pending jobs to run")
            return
        
        logger.info(f"Running {len(pending_jobs)} pending jobs")
        
        for job in pending_jobs:
            self.run_job(job.name)
    
    def schedule_jobs(self):
        """Schedule jobs based on their schedule_time"""
        for job in self.jobs.values():
            if job.schedule_time:
                try:
                    # Parse schedule time
                    if ':' in job.schedule_time:
                        # Specific time (e.g., "09:00")
                        schedule.every().day.at(job.schedule_time).do(
                            self.run_job, job.name
                        ).tag(job.name)
                        logger.info(f"Scheduled job '{job.name}' at {job.schedule_time} daily")
                    elif job.schedule_time.startswith('@'):
                        # Interval (e.g., "@hourly", "@daily")
                        if job.schedule_time == '@hourly':
                            schedule.every().hour.do(self.run_job, job.name).tag(job.name)
                        elif job.schedule_time == '@daily':
                            schedule.every().day.do(self.run_job, job.name).tag(job.name)
                        elif job.schedule_time == '@weekly':
                            schedule.every().week.do(self.run_job, job.name).tag(job.name)
                except Exception as e:
                    logger.error(f"Failed to schedule job '{job.name}': {e}")
    
    def run_scheduler(self):
        """Run the scheduler continuously"""
        self.schedule_jobs()
        
        logger.info("Starting batch scheduler...")
        print("Batch Scheduler Started")
        print("Press Ctrl+C to stop")
        print("\nScheduled Jobs:")
        self.print_jobs_table()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(self.config['scheduling']['check_interval'])
                
                # Update console display periodically
                if int(time.time()) % 30 == 0:
                    self.update_display()
                    
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            print("\nScheduler stopped.")
    
    def print_jobs_table(self):
        """Print jobs in a formatted table"""
        if not HAS_PANDAS:
            print("Error: pandas and tabulate are required for this feature.")
            return
            
        table_data = []
        for job in self.jobs.values():
            table_data.append([
                job.name,
                job.status.value,
                job.schedule_time or "Manual",
                job.priority,
                job.last_run or "Never",
                len(job.input_paths)
            ])
        
        headers = ["Name", "Status", "Schedule", "Priority", "Last Run", "Files"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    def print_statistics(self):
        """Print processing statistics"""
        if not HAS_PANDAS:
            print("Error: pandas is required for this feature.")
            return
            
        if not self.history:
            print("No processing history available")
            return
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(self.history)
        
        print("\nProcessing Statistics:")
        print("=" * 50)
        
        # Overall statistics
        total_jobs = len(df)
        successful = len(df[df['status'] == 'completed'])
        failed = len(df[df['status'] == 'failed'])
        
        print(f"Total Jobs Run: {total_jobs}")
        print(f"Successful: {successful} ({successful/total_jobs*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total_jobs*100:.1f}%)")
        
        if successful > 0:
            # Extract statistics from successful jobs
            stats_data = []
            for entry in self.history:
                if entry['status'] == 'completed' and 'statistics' in entry:
                    stats = entry['statistics']
                    stats_data.append({
                        'job': entry['job_name'],
                        'files': stats.get('total_files', 0),
                        'pages': stats.get('total_pages', 0),
                        'words': stats.get('total_words', 0),
                        'time': stats.get('processing_time', 0)
                    })
            
            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                
                print("\nAverage per Job:")
                print(f"  Files: {stats_df['files'].mean():.1f}")
                print(f"  Pages: {stats_df['pages'].mean():.1f}")
                print(f"  Words: {stats_df['words'].mean():.0f}")
                print(f"  Time: {stats_df['time'].mean():.1f}s")
                
                print("\nTotals:")
                print(f"  Total Pages: {stats_df['pages'].sum():,}")
                print(f"  Total Words: {stats_df['words'].sum():,}")
                print(f"  Total Time: {stats_df['time'].sum():.1f}s")
    
    def generate_report(self, output_file: str = "batch_report.html"):
        """Generate an HTML report of batch processing"""
        if not HAS_PANDAS:
            logger.error("Error: pandas and matplotlib are required for report generation.")
            return
            
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            logger.warning("Plotly not installed. Install with: pip install plotly")
            return
        
        # Prepare data
        df = pd.DataFrame(self.history)
        
        if df.empty:
            logger.warning("No data available for report")
            return
        
        # Create figure
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Job Status Distribution', 'Processing Timeline',
                          'Files Processed Over Time', 'Success Rate Trend'),
            specs=[[{'type': 'pie'}, {'type': 'scatter'}],
                   [{'type': 'bar'}, {'type': 'scatter'}]]
        )
        
        # Job Status Distribution (Pie Chart)
        status_counts = df['status'].value_counts()
        fig.add_trace(
            go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                name="Status Distribution"
            ),
            row=1, col=1
        )
        
        # Processing Timeline
        df['started_at'] = pd.to_datetime(df['started_at'])
        df['completed_at'] = pd.to_datetime(df['completed_at'])
        df['duration'] = (df['completed_at'] - df['started_at']).dt.total_seconds()
        
        fig.add_trace(
            go.Scatter(
                x=df['started_at'],
                y=df['duration'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=df['status'].map({'completed': 'green', 'failed': 'red'}),
                    showscale=False
                ),
                text=df['job_name'],
                name="Job Duration"
            ),
            row=1, col=2
        )
        
        # Files Processed Over Time
        successful = df[df['status'] == 'completed']
        if not successful.empty:
            # Extract file counts
            file_counts = []
            for entry in self.history:
                if entry['status'] == 'completed' and 'statistics' in entry:
                    file_counts.append({
                        'date': pd.to_datetime(entry['completed_at']).date(),
                        'files': entry['statistics'].get('total_files', 0)
                    })
            
            if file_counts:
                files_df = pd.DataFrame(file_counts)
                daily_files = files_df.groupby('date')['files'].sum().reset_index()
                
                fig.add_trace(
                    go.Bar(
                        x=daily_files['date'],
                        y=daily_files['files'],
                        name="Files Processed"
                    ),
                    row=2, col=1
                )
        
        # Success Rate Trend (if enough data)
        if len(df) > 5:
            df['date'] = df['completed_at'].dt.date
            daily_stats = df.groupby('date').agg({
                'status': lambda x: (x == 'completed').sum() / len(x) * 100
            }).reset_index()
            
            fig.add_trace(
                go.Scatter(
                    x=daily_stats['date'],
                    y=daily_stats['status'],
                    mode='lines+markers',
                    name="Success Rate %"
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text="Batch Processing Report",
            showlegend=True
        )
        
        # Save as HTML
        fig.write_html(output_file)
        logger.info(f"Report generated: {output_file}")
        
        # Also generate a text report
        self.generate_text_report(f"{output_file}.txt")
    
    def generate_text_report(self, output_file: str):
        """Generate a text version of the report"""
        report = f"""
        Batch Processing Report
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        =====================================================
        
        Job Summary:
        -------------
        Total Jobs: {len(self.history)}
        Active Jobs: {len([j for j in self.jobs.values() if j.status == BatchStatus.PENDING])}
        
        Recent Activity (Last 10 jobs):
        ---------------------------------
        """
        
        recent_jobs = sorted(self.history, key=lambda x: x['completed_at'], reverse=True)[:10]
        for job in recent_jobs:
            report += f"\n  {job['job_name']}:"
            report += f"\n    Status: {job['status']}"
            report += f"\n    Completed: {job['completed_at']}"
            if 'statistics' in job:
                stats = job['statistics']
                report += f"\n    Files: {stats.get('total_files', 0)}"
                report += f"\n    Pages: {stats.get('total_pages', 0)}"
                report += f"\n    Words: {stats.get('total_words', 0):,}"
            report += "\n"
        
        report += "\nJob Listings:\n"
        report += "-" * 40 + "\n"
        
        for job in self.jobs.values():
            report += f"\n{job.name}:"
            report += f"\n  Status: {job.status.value}"
            report += f"\n  Schedule: {job.schedule_time or 'Manual'}"
            report += f"\n  Inputs: {len(job.input_paths)} paths"
            report += f"\n  Output: {job.output_dir}"
            report += f"\n  Last Run: {job.last_run or 'Never'}\n"
        
        with open(output_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Text report generated: {output_file}")
    
    def update_display(self):
        """Update console display"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"Batch Manager - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        self.print_jobs_table()
        print("\nNext scheduled runs:")
        for job in schedule.get_jobs():
            print(f"  {job.tags[0]}: {job.next_run}")


def main():
    """Main function for batch manager"""
    parser = argparse.ArgumentParser(
        description="Batch Processing Manager for PDF to Markdown Converter"
    )
    
    parser.add_argument(
        "--config",
        "-c",
        default="batch_manager_config.yaml",
        help="Configuration file for batch manager"
    )
    
    parser.add_argument(
        "--run",
        "-r",
        help="Run a specific job immediately"
    )
    
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run all pending jobs immediately"
    )
    
    parser.add_argument(
        "--schedule",
        "-s",
        action="store_true",
        help="Start the scheduler"
    )
    
    parser.add_argument(
        "--add-job",
        nargs=4,
        metavar=("NAME", "INPUTS", "OUTPUT", "SCHEDULE"),
        help="Add a new job (comma-separated inputs)"
    )
    
    parser.add_argument(
        "--list-jobs",
        action="store_true",
        help="List all jobs"
    )
    
    parser.add_argument(
        "--statistics",
        action="store_true",
        help="Show processing statistics"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate HTML report"
    )
    
    args = parser.parse_args()
    
    # Initialize batch manager
    manager = BatchManager(args.config)
    
    # Handle commands
    if args.add_job:
        name, inputs_str, output, schedule_time = args.add_job
        inputs = [inp.strip() for inp in inputs_str.split(',')]
        
        job = BatchJob(
            name=name,
            input_paths=inputs,
            output_dir=output,
            schedule_time=schedule_time if schedule_time != 'none' else None
        )
        
        manager.add_job(job)
        print(f"Added job: {name}")
    
    elif args.run:
        result = manager.run_job(args.run)
        print(f"Job result: {result}")
    
    elif args.run_all:
        manager.run_all_pending()
    
    elif args.list_jobs:
        manager.print_jobs_table()
    
    elif args.statistics:
        manager.print_statistics()
    
    elif args.report:
        manager.generate_report()
        print("Report generated: batch_report.html")
    
    elif args.schedule:
        manager.run_scheduler()
    
    else:
        # Interactive mode
        print("Batch Processing Manager")
        print("=" * 40)
        print("\nAvailable commands:")
        print("  --list-jobs     List all jobs")
        print("  --statistics    Show statistics")
        print("  --report        Generate report")
        print("  --schedule      Start scheduler")
        print("\nFor more options, use --help")


if __name__ == "__main__":
    main()