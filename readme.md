# Voice Analyzer App

This is a web application built with Vue using Vite as the build tool for the front end, and Flask for the backend. The app allows users to log in, upload audio files for transcription, and view the most frequent words in the transcriptions.

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Features](#features)
  - [Login Page](#login-page)
  - [Transcription Page](#transcription-page)
  - [Most Frequent Page](#most-frequent-page)
- [Backend](#backend)
- [Usage](#usage)
- [Contributing](#contributing)

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- Node.js
- npm (Node Package Manager)
- Python
- pip (Python Package Installer)

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your-username/vue-vite-flask-transcription-app.git```

2. **Frontend Setup**
    ```cd frontend
    npm install```
3. **Backend Setup**
    ```pip install -r requirements.txt```

### Features
**Login Page**
    Users can log in using their credentials.
    Firebase authentication is used for secure login.
**Transcription Page**
    Users can upload audio files for transcription.
    Transcription status is displayed, and results are shown upon completion.
**Most Frequent Page**
    Users can view the most frequent words in the transcriptions.
    Word frequency analysis is performed on the transcribed text.

### Backend
    The backend is built with Flask and uses SQLAlchemy for database operations. Firebase authentication is integrated for user authentication. File uploads are handled using Flask's request object.
### Usage
**Frontend**
    ```cd frontend
    npm run dev```
**Backend**
```python api.py```

### Contributing
Contributions are welcome! If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.
