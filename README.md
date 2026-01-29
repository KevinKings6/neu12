# neu12 - Emergency SOS Communication System

A full-stack emergency communication system with FastAPI backend and React Native/Expo frontend.

## Opening the Project in VS Code

### Method 1: Using Command Line
```bash
# Navigate to the project directory
cd /path/to/neu12

# Open in VS Code
code .
```

### Method 2: From VS Code
1. Open VS Code
2. Click `File` → `Open Folder...`
3. Navigate to the `neu12` project directory
4. Click `Select Folder`

### Method 3: Using Git
```bash
# Clone the repository
git clone https://github.com/KevinKings6/neu12.git
cd neu12

# Open in VS Code
code .
```

## Prerequisites

Before running this project, ensure you have the following installed:

- **Python 3.8+** - For the backend server
- **Node.js 18+** and **npm/yarn** - For the frontend
- **MongoDB** - Database server
- **VS Code** - Recommended IDE
- **Git** - Version control

## Recommended VS Code Extensions

Install these extensions for the best development experience:

### For Python Backend:
- Python (Microsoft)
- Pylance (Microsoft)
- Python Test Explorer
- autoDocstring
- Python Indent

### For React Native Frontend:
- ES7+ React/Redux/React-Native snippets
- ESLint
- Prettier - Code formatter
- React Native Tools
- TypeScript Vue Plugin (Volar)

### General Development:
- GitLens
- Path Intellisense
- Auto Rename Tag
- Bracket Pair Colorizer
- Thunder Client (for API testing)

## Project Structure

```
neu12/
├── backend/                 # FastAPI Python backend
│   ├── server.py           # Main server file
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables (create this)
├── frontend/               # React Native/Expo frontend
│   ├── app/               # App screens and routes
│   ├── assets/            # Images and static files
│   ├── contexts/          # React contexts
│   ├── package.json       # Node dependencies
│   └── .env              # Frontend environment variables (create this)
└── tests/                # Test files
```

## Setup Instructions

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with the following variables:
# MONGO_URL=mongodb://localhost:27017
# DB_NAME=emergency_sos
# JWT_SECRET_KEY=your-secret-key-here

# Run the backend server
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`
API documentation will be available at `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or
yarn install

# Create .env file if needed for API endpoint configuration

# Start the Expo development server
npm start
# or
yarn start
```

Follow the Expo CLI instructions to:
- Press `i` for iOS simulator
- Press `a` for Android emulator
- Scan QR code with Expo Go app on your phone

## Development Workflow in VS Code

### 1. Open Integrated Terminal
- Press `` Ctrl+` `` (Ctrl + backtick) or `View` → `Terminal`
- You can split terminals to run backend and frontend simultaneously

### 2. Run Backend and Frontend Simultaneously
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn server:app --reload

# Terminal 2 - Frontend (split terminal)
cd frontend
npm start
```

### 3. Debugging in VS Code

Create a `.vscode/launch.json` file:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "server:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### 4. Testing

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests (if configured)
cd frontend
npm test
```

### 5. Code Formatting

```bash
# Format Python code
cd backend
black .
isort .

# Format JavaScript/TypeScript code
cd frontend
npm run lint
```

## Common Issues and Solutions

### Issue: "Module not found" errors
- **Solution**: Make sure you've activated the virtual environment for Python and installed all dependencies

### Issue: MongoDB connection errors
- **Solution**: Ensure MongoDB is running and the connection string in `.env` is correct

### Issue: Port already in use
- **Solution**: Kill the process using the port or change the port number:
  ```bash
  # Find process on port 8000
  lsof -i :8000  # macOS/Linux
  netstat -ano | findstr :8000  # Windows
  ```

### Issue: Expo app won't connect to backend
- **Solution**: Update the API URL in the frontend configuration to use your machine's local IP address instead of `localhost`

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

[Add your license information here]

## Support

For issues or questions, please open an issue on GitHub.
