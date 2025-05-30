# Create virtual environment with pip

For linux/mac:
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For windows command line (not power shell):
```
python -m venv .venv
.\.venv\scripts\activate.bat
pip install -r requirements.txt
```

# Create virtual environment and build with uv
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

# Configure application for local development
Copy the .env.example file to .env file and set the API key for the OpenAI service. 
The configuration of storage account is prepared for default Azurite emulator setup, no change is needed.

# Start mock server
Use launch configuration named "Python Debugger: Mock server" defined in the .vscode/launch.json file

# Access Mock Server API locally
Open SwaggerUI at: http://localhost:9000/docs

# Running the application
Use launch configuration named "Python Debugger: App" defined in the .vscode/launch.json file

# Access API locally
Open SwaggerUI at: http://localhost:8000/docs