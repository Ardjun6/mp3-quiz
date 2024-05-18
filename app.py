from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import os
import random
import string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'music'
socketio = SocketIO(app)

rooms = {}

def get_mp3_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.mp3')]

def generate_quiz_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def clean_filename(filename):
    return os.path.splitext(filename)[0].replace('_', ' ')

@app.route('/')
def index():
    error = request.args.get('error')
    return render_template('index.html', error=error)

@app.route('/upload', methods=['POST'])
def upload():
    if 'folder' not in request.files:
        return redirect(url_for('index'))
    files = request.files.getlist('folder')
    if len(files) < 5:
        return redirect(url_for('index', error='You must upload at least 5 files.'))
    for file in files:
        if file and file.filename.endswith('.mp3'):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return redirect(url_for('host'))

@app.route('/host')
def host():
    return render_template('host.html')

@app.route('/join')
def join():
    return render_template('join.html')

@app.route('/music/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('create_room')
def handle_create_room(data):
    room = generate_quiz_code()
    rooms[room] = {
        'files': get_mp3_files(app.config['UPLOAD_FOLDER']),
        'questions': [],
        'current_question': 0,
        'scores': {},
        'players': {}
    }
    join_room(room)
    print(f"Room created: {room} with files: {rooms[room]['files']}")
    emit('room_created', {'room': room, 'code': room}, room=room)

@socketio.on('join_room')
def handle_join_room(data):
    room = data['room']
    player_name = data['player_name']
    if room in rooms:
        join_room(room)
        rooms[room]['scores'][request.sid] = 0
        rooms[room]['players'][request.sid] = player_name
        print(f"User {player_name} joined room: {room}")
        emit('room_joined', {'room': room}, room=room)
    else:
        print(f"Room not found: {room}")
        emit('error', {'message': 'Room not found'})

@socketio.on('start_quiz')
def handle_start_quiz(data):
    room = data['room']
    if room not in rooms:
        print(f"Room not found when starting quiz: {room}")
        emit('error', {'message': 'Room not found'})
        return
    
    num_questions = int(data['num_questions'])
    mp3_files = rooms[room]['files']
    random.shuffle(mp3_files)
    questions = []
    for mp3 in mp3_files[:num_questions]:
        answers = random.sample(mp3_files, 3)  # Select 3 wrong answers
        if mp3 not in answers:
            answers.append(mp3)  # Ensure the correct answer is included
        random.shuffle(answers)  # Shuffle to ensure the correct answer is in a random position
        question = {
            'question': mp3,
            'answers': answers
        }
        questions.append(question)
    rooms[room]['questions'] = questions
    rooms[room]['current_question'] = 0
    print(f"Quiz started in room: {room} with questions: {questions}")
    emit('quiz_started', room=room)
    emit('next_question', {'question': questions[0]}, room=room)

@socketio.on('next_question')
def handle_next_question(data):
    room = data['room']
    if room not in rooms:
        print(f"Room not found when going to next question: {room}")
        emit('error', {'message': 'Room not found'})
        return

    room_data = rooms[room]
    question_index = room_data['current_question']
    questions = room_data['questions']
    
    if data.get('show_answer'):
        correct_answer = questions[question_index]['question']
        emit('show_answer', {'correct_answer': correct_answer}, room=room)
    else:
        question_index += 1
        if question_index < len(questions):
            room_data['current_question'] = question_index
            emit('next_question', {'question': questions[question_index]}, room=room)
        else:
            print(f"Quiz finished in room: {room}")
            emit('quiz_finished', room=room)

@socketio.on('answer')
def handle_answer(data):
    room = data['room']
    if room not in rooms:
        print(f"Room not found when answering: {room}")
        emit('error', {'message': 'Room not found'})
        return

    answer = data['answer']
    room_data = rooms[room]
    question_index = room_data['current_question']
    questions = room_data['questions']
    correct_answer = questions[question_index]['question']
    
    if answer == correct_answer:
        rooms[room]['scores'][request.sid] += 1

@socketio.on('get_scores')
def handle_get_scores(data):
    room = data['room']
    if room not in rooms:
        print(f"Room not found when getting scores: {room}")
        emit('error', {'message': 'Room not found'})
        return

    scores = rooms[room]['scores']
    players = rooms[room]['players']
    scores_with_names = {players[sid]: score for sid, score in scores.items()}
    emit('scores', {'scores': scores_with_names}, room=room)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    socketio.run(app, debug=True)
