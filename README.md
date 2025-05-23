# Create virtual environment and build
```
uv venv -p 3.12 .venv
source .venv/bin/activate
```

Next generate requirements file
```
uv pip compile pyproject.toml -o requirements.txt
```

Build the application
```
uv build
```

Install all the dependencies
```
uv sync
```

## Configure application for local development
Copy the .env.example file to .env file and set the API key for the OpenAI service. 
The configuration of storage account is prepared for default Azurite emulator setup, no change is needed.

## Running the application locally
Use launch configuration named "Python Debugger: App" defined in the .vscode/launch.json file

## Access API locally
Open SwaggerUI at: http://localhost:8000/docs