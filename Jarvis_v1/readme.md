# Local AI Assistant

A self-hosted voice-controlled AI assistant running on an Ubuntu server, providing home automation, media control, and other useful functions.

## Features

- **Voice Control**: Wake word detection, speech-to-text, and text-to-speech capabilities
- **LLM Integration**: Local language model processing using Ollama
- **Home Automation**: Integration with Home Assistant for smart home control
- **Media Control**: Control music playback via MPD or Spotify
- **TV Control**: HDMI-CEC, IR blaster, and WebOS TV control
- **Task Scheduling**: Schedule commands to run at specific times
- **Web API**: RESTful API for remote control
- **Command Line Interface**: CLI for direct command execution

## System Architecture

The system is designed with a modular architecture based on a Microservices Control Plane (MCP) that coordinates the following components:

- **Core Components**:
  - Audio Listener: Captures and processes audio input
  - Command Processor: Interprets commands and routes to appropriate handlers
  - LLM Service: Integrates with Ollama for language model processing
  - Wake Word Detection: Listens for wake word using Porcupine
  - Speech-to-Text: Transcribes audio using Whisper
  - Text-to-Speech: Generates speech using Coqui TTS or Piper
  - Task Scheduler: Schedules tasks to run at specific times

- **Integrations**:
  - Home Assistant: Controls smart home devices
  - Media Control: Controls music playback
  - TV Control: Controls TVs via various protocols
  - Web Automation: Automates web tasks
  - SMS/Email: Sends messages

- **Interfaces**:
  - REST API: HTTP API for remote control
  - CLI: Command-line interface for direct command execution

## Requirements

- Ubuntu 22.04 Server (headless)
- Python 3.8 or higher
- Audio input/output devices
- Ollama for LLM
- Additional hardware for specific integrations (HDMI-CEC adapter, IR blaster, etc.)

## Installation

### Option 1: Using Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/local-ai-assistant.git
   cd local-ai-assistant
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start the services with Docker Compose:
   ```bash
   docker-compose up -d
   ```

### Option 2: Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/local-ai-assistant.git
   cd local-ai-assistant
   ```

2. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install -y \
       build-essential \
       portaudio19-dev \
       libffi-dev \
       libssl-dev \
       libasound2-dev \
       libsndfile1 \
       ffmpeg \
       cmake \
       libudev-dev \
       libcec-dev \
       cec-utils
   ```

3. Install Ollama for LLM support:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   # Pull the default model
   ollama pull llama3
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Create a Python virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

6. Start the assistant:
   ```bash
   python run.py
   ```

## Configuration

The system is configured using environment variables in the `.env` file. See `.env.example` for all available options.

### Audio Device Configuration

List available audio devices:
```bash
python -m cli devices
```

Set the input device in your `.env` file:
```
AUDIO_DEVICE_INDEX=1
```

### Wake Word Configuration

The system uses Porcupine for wake word detection. You'll need to:

1. Get an access key from [Picovoice Console](https://console.picovoice.ai/)
2. Set the key in your `.env` file:
   ```
   PORCUPINE_ACCESS_KEY=your_access_key
   ```

You can also create a custom wake word using Picovoice Console and specify the path:
```
WAKE_WORD_PATH=path/to/custom/wake_word.ppn
```

### Home Assistant Integration

To connect to Home Assistant:

1. Create a long-lived access token in Home Assistant
2. Configure the connection in your `.env` file:
   ```
   HASS_URL=http://homeassistant.local:8123
   HASS_TOKEN=your_long_lived_access_token
   ```

### Media Control Configuration

For MPD:
```
MPD_HOST=localhost
MPD_PORT=6600
```

For Spotify:
```
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

### TV Control Configuration

Configure TV control in your `.env` file:
```
TV_TYPE=webos  # Options: webos, roku, hdmi-cec, ir
TV_IP=192.168.1.100  # For WebOS or Roku TV
TV_MAC=00:11:22:33:44:55  # For WebOS Wake-on-LAN
```

## Usage

### Voice Commands

1. Say the wake word (default is "Computer")
2. After the acknowledgment tone, speak your command
3. The system will process the command and respond

Example commands:
- "Turn on the living room lights"
- "Set the temperature to 72 degrees"
- "Play music by Taylor Swift on Spotify"
- "What's the weather like today?"
- "Turn on the TV and switch to HDMI 1"

### CLI Usage

Run commands directly from the command line:

```bash
# Start the assistant
python -m cli start

# Send a command
python -m cli command "Turn on the living room lights"

# Listen for a single voice command
python -m cli listen

# Test text-to-speech
python -m cli test_tts "Hello, this is a test"

# Test speech-to-text
python -m cli test_stt

# Test wake word detection
python -m cli test_wake_word
```

### API Usage

The system provides a RESTful API for remote control:

```bash
# Send a command
curl -X POST http://localhost:8000/command -H "Content-Type: application/json" -d '{"command": "Turn on the living room lights"}'

# Schedule a task
curl -X POST http://localhost:8000/schedule -H "Content-Type: application/json" -d '{"job_id": "morning_lights", "command": "Turn on the living room lights", "schedule": "every day at 7:00"}'

# List scheduled tasks
curl http://localhost:8000/schedule

# Delete a scheduled task
curl -X DELETE http://localhost:8000/schedule/morning_lights
```

## Extending the System

### Adding New Integrations

To add a new integration:

1. Create a new module in the `integrations` directory
2. Implement the integration class with appropriate methods
3. Update the command processor to handle the new integration

### Creating Custom Command Handlers

To create a custom command handler:

1. Extend the command processor with a new handler method
2. Register the handler in the `_register_handlers` method
3. Update the system prompt in the `_parse_command` method to include the new intent

## Troubleshooting

### Audio Issues

- Check that the correct audio device is selected (use `python -m cli devices`)
- Verify microphone permissions for the application
- Check audio levels and input sensitivity

### Wake Word Detection

- Verify that your Porcupine access key is valid
- Try adjusting the wake word sensitivity in the `.env` file
- Test wake word detection with `python -m cli test_wake_word`

### Home Assistant Connection

- Verify that the Home Assistant URL is correct
- Check that the access token has the necessary permissions
- Ensure the server can reach Home Assistant (check firewall rules)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
