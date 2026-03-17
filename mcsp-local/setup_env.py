from pathlib import Path
import os
import subprocess
import sys

try:
    from dotenv import dotenv_values
except ImportError:
    print('python-dotenv is not installed in this virtual environment.', file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / '.env'
ADK_HOME = ROOT / '.orchestrate'

if not ENV_FILE.exists():
    print(f'Missing {ENV_FILE}. Copy .env.example to .env and fill in your values.', file=sys.stderr)
    sys.exit(1)

cfg = dotenv_values(ENV_FILE)
env_name = (cfg.get('WXO_ENV_NAME') or '').strip()
instance_url = (cfg.get('WXO_INSTANCE_URL') or '').strip()
api_key = (cfg.get('WXO_API_KEY') or '').strip()

missing = [
    name
    for name, value in [
        ('WXO_ENV_NAME', env_name),
        ('WXO_INSTANCE_URL', instance_url),
        ('WXO_API_KEY', api_key),
    ]
    if not value or value == 'replace_me'
]
if missing:
    print('Missing required values in .env: ' + ', '.join(missing), file=sys.stderr)
    sys.exit(1)

ADK_HOME.mkdir(exist_ok=True)
exe = ROOT / '.venv' / 'Scripts' / 'orchestrate.exe'
if not exe.exists():
    print(f'ADK CLI not found at {exe}. Install dependencies first.', file=sys.stderr)
    sys.exit(1)

env = os.environ.copy()
env['HOME'] = str(ADK_HOME)
env['USERPROFILE'] = str(ADK_HOME)

def display_cmd(cmd):
    if '--api-key' not in cmd:
        return ' '.join(cmd)
    masked = []
    skip_next = False
    for i, part in enumerate(cmd):
        if skip_next:
            skip_next = False
            continue
        masked.append(part)
        if part == '--api-key' and i + 1 < len(cmd):
            masked.append('********')
            skip_next = True
    return ' '.join(masked)

commands = [
    [str(exe), 'env', 'add', '-n', env_name, '-u', instance_url, '--type', 'mcsp'],
    [str(exe), 'env', 'activate', env_name, '--api-key', api_key],
    [str(exe), 'env', 'list'],
]

for cmd in commands:
    print(f'\n> {display_cmd(cmd)}')
    result = subprocess.run(cmd, env=env, cwd=ROOT)
    if result.returncode != 0:
        sys.exit(result.returncode)

print('\nEnvironment configured successfully.')
print(f'Use this isolated ADK home for future commands: {ADK_HOME}')
print(f"PowerShell: $env:HOME='{ADK_HOME}'; $env:USERPROFILE='{ADK_HOME}'")
