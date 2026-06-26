# neuralspace/cli.py
import click
import sys
import os
import requests
from pathlib import Path

from neuralspace.scanner import SecurityScanner
from neuralspace.watcher import run_watcher
from neuralspace.trainer import train_atoms
from neuralspace.synthetic_generator import generate_dataset


@click.group()
def cli():
    """NeuralSpace - Cognitive Code Security Engine."""
    pass


@cli.command()
@click.argument('target_dir', default='./test_codebase')
@click.option('--quarantine', default='rename', help='Quarantine mode: rename or move')
def scan(target_dir, quarantine):
    """Scan a directory for malicious code (supports .py, .js, .ts, .go, .rs, .cpp, etc.)."""
    if not os.path.exists(target_dir):
        click.echo(f"[ERROR] Directory '{target_dir}' not found.")
        sys.exit(1)
    
    scanner = SecurityScanner(target_dir, quarantine_mode=quarantine)
    scanner.run_scan()


@cli.command()
@click.argument('target_dir', default='./test_codebase')
@click.option('--quarantine', default='rename', help='Quarantine mode: rename or move')
def watch(target_dir, quarantine):
    """Watch a directory and scan new files in real-time."""
    run_watcher(target_dir, quarantine)


@cli.command()
def train():
    """Train the neural atom on the training_data/ folder."""
    train_atoms()


@cli.command()
def generate():
    """Generate synthetic training data."""
    generate_dataset("./training_data/safe", "./training_data/threat", num_samples=50)


@cli.command()
def sync():
    """Sync global threat intelligence from the federated network."""
    # You'll need to deploy the aggregator and set this URL
    AGGREGATOR_URL = os.environ.get("NEURALSPACE_AGGREGATOR", "http://localhost:8000")
    
    try:
        response = requests.get(f"{AGGREGATOR_URL}/global-threats", timeout=5)
        data = response.json()
        click.echo(f"[*] Connected to global NeuralSpace network.")
        click.echo(f"[*] Total global threats identified: {data['total_threats']}")
        click.echo("\n📊 Top Threats:")
        for threat in data["top_threats"]:
            click.echo(f"   - Pattern: {threat['pattern']}")
            click.echo(f"     Occurrences: {threat['occurrences']} | Languages: {threat['languages']}")
    except Exception as e:
        click.echo(f"[!] Failed to sync with global network: {e}")


if __name__ == "__main__":
    cli()