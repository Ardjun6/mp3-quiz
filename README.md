# MP3 Quiz Application

This is a Flask-based web application that allows users to create and join a quiz game based on MP3 files. The host uploads a set of MP3 files, and participants answer questions about these files in a quiz format. The application uses Socket.IO for real-time interaction between the host and participants.

## Features

- **Host Uploads MP3 Files**: The host can upload a folder containing MP3 files to create a quiz.
- **Join with Room Code**: Participants can join the quiz using a unique room code.
- **Real-time Quiz Interaction**: The quiz interaction between the host and participants is handled in real-time using Socket.IO.
- **Theming**: The application supports both light and dark themes, which can be toggled by the user.
- **Question Handling**: The host can control the flow of the quiz, showing answers and moving to the next question.
- **Score Display**: At the end of the quiz, scores are displayed to all participants.

## Requirements

- Python 3.11
- Flask
- Flask-SocketIO
- werkzeug

## Installation

1. **Clone the repository**:

   ```sh
   git clone https://github.com/yourusername/mp3-quiz.git
   cd mp3-quiz
