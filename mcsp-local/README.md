# Local MCSP Access Test

Isolated watsonx Orchestrate ADK setup for SaaS/AWS-style `api.dl.watson-orchestrate.ibm.com` instances.

## Official auth model

For AWS-hosted watsonx Orchestrate environments, the official ADK flow is:

```bash
orchestrate env add -n <environment-name> -u <service-instance-url> --type mcsp
orchestrate env activate <environment-name> --api-key <your-api-key>
```

Source:
- https://developer.watson-orchestrate.ibm.com/getting_started/installing
- https://developer.watson-orchestrate.ibm.com/environment/production_import

## Setup

```powershell
cd D:\codex\wson_aii-hackathon\mcsp-local
uv venv .venv --python 3.11
uv pip install --python .venv\Scripts\python.exe --upgrade ibm-watsonx-orchestrate python-dotenv
Copy-Item .env.example .env
```

Edit `.env` and set:
- `WXO_INSTANCE_URL`
- `WXO_API_KEY`
- `WXO_ENV_NAME`

## Run

```powershell
cd D:\codex\wson_aii-hackathon\mcsp-local
.\.venv\Scripts\python.exe setup_env.py
```

If the ADK login succeeds, the script will:
- configure a local ADK home under this folder
- add the remote environment with `--type mcsp`
- activate it with your API key
- print `env list`

## Manual follow-up

```powershell
$env:HOME='D:\codex\wson_aii-hackathon\mcsp-local\.orchestrate'
$env:USERPROFILE='D:\codex\wson_aii-hackathon\mcsp-local\.orchestrate'
.\.venv\Scripts\orchestrate.exe env list
```
