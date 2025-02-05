from flask import Flask, render_template, request, jsonify,session,redirect,url_for,flash
import os
from openai import OpenAI
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON  # If using PostgreSQL


current_directory = os.path.dirname(os.path.abspath(__file__))
#print("current_directory", current_directory)

app = Flask(__name__)
# Example using Flask-SQLAlchemy
app.secret_key = 'YOUR KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Added for debugging
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class KanbanBoard(db.Model):
    __tablename__ = 'kanban_board'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    deadline = db.Column(db.String(255), nullable=True)
    container_position = db.Column(JSON, nullable=True)  # Store container position as JSON
    column_heights = db.Column(JSON, nullable=True)  # Store heights of columns as JSON
    columns = db.Column(db.Text, nullable=True)  # Other column data

    def __repr__(self):
        return f'<KanbanBoard {self.title}>'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

    
# New Note model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    top = db.Column(db.String(50))
    left = db.Column(db.String(50))
    color = db.Column(db.String(7))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    team_id = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.DateTime, nullable=True)  # Adding a deadline attribute

    def __repr__(self):
        return f"<Note id={self.id}, title='{self.title}', content='{self.content}', deadline='{self.deadline}'>"


    
# Create tables
with app.app_context():
    db.create_all()



@app.route('/save_notes', methods=['POST'])
def save_notes():
    if 'team_id' not in session:
        return jsonify({"berror": "No team selected"}), 400

    team_id = session['team_id']

    notes_data = request.get_json()
    print("SAVENOTESnotes_data", notes_data)

    try:
        Note.query.filter_by(team_id=team_id).delete()  # Clear existing notes for simplicity
        for note_info in notes_data['notes']:
            new_note = Note(
                title=note_info['title'],
                content=note_info['content'],
                top=note_info['top'],
                left=note_info['left'],
                color=note_info['color'],
                deadline = datetime.strptime(note_info['deadline'], '%Y-%m-%dT%H:%M') if note_info['deadline'] else None,
                team_id=team_id
            )
            db.session.add(new_note)
        db.session.commit()
        return jsonify({"message": "Notes saved successfully!"})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Failed to save notes: {str(e)}")  # Ensure you have logging configured
        return jsonify({"aerror": str(e)}), 500



import json  # Add this at the beginning of your file

@app.route('/save_kanban', methods=['POST'])
def save_kanban():
    if 'team_id' not in session:
        return jsonify({"berror": "No team selected"}), 400

    team_id = session['team_id']
    notes_data = request.get_json()
    print("Team ID:", team_id)
    print("Kanban Data:", notes_data)

    try:
        # Clear existing notes
        Note.query.filter_by(team_id=team_id).delete()
        db.session.commit()


        if 'kanbanBoard' in notes_data and notes_data['kanbanBoard']:
            board_data = notes_data['kanbanBoard']
            board = KanbanBoard.query.filter_by(team_id=team_id).first()

            if not board:
                board = KanbanBoard(team_id=team_id)

            board.title = board_data['title']
            board.deadline = board_data['deadline']
            board.container_position = board_data.get('containerPosition')
            # Serialize 'columns' into JSON before saving
            board.columns = json.dumps(board_data.get('columns', [])) 
            board.team_id=team_id # Provide default empty list if not present
            
            db.session.add(board)
            print(f"Adding/updating board: {board}")

        db.session.commit()
        return jsonify({"message": "Notes and board saved successfully!"})
    except Exception as e:
        db.session.rollback()
        print(f"Error during save operation: {e}")
        return jsonify({"aerror": str(e)}), 500


teamKeys = {
    '1': 'key1',
    '2': 'key2',
    # Add more teams and keys as needed
}

@app.route('/validate_key', methods=['POST'])
def validate_key():
    data = request.get_json()
    print("data", data)
    team = data.get('team')
    print("team", team)
    team = team.split('team')[1] 
    print("team", team)
    user_key = data.get('key')
    print("user_key", user_key)
    correct_key = teamKeys.get(team)
    print("correct_key", correct_key)  # Assuming you have a dictionary of keys

    if user_key == correct_key:
        session[f'{team}_authorized'] = True
        # Respond with success status and redirect URL
        return jsonify(success=True, redirect_url=url_for('team', team_id=team))
    else:
        # Respond with failure status and a message
        return jsonify(success=False, message="Invalid key"), 401

@app.route('/team/<team_id>', methods=['GET', 'POST'])
def team(team_id):
    team_notes_key = f'team_{team_id}_notes'
    print("team_notes_key", team_notes_key)
    session['team_id'] = team_id 
    print("sess,on",session.get)

    if not session.get(f'{team_id}_authorized'):
        flash('You must enter the correct key to access this page.')
        print("flash")

        return redirect(url_for('home'))

    
    if request.method == 'POST':
        notes = request.form.getlist('notes')
        session[team_notes_key] = notes

    if 'username' in session:
        username = session.get('username')
    else: 
        username = ""  
    return render_template('index.html', team=f'Team {team_id}', username = username )


@app.route('/', methods=['GET', 'POST'])
def home():

    username="ugur"

    return render_template('home.html',username=username)


@app.route('/api/kanban')
def api_kanban():
    if 'team_id' not in session:
        return jsonify({"error": "No team selected"}), 400
    
    team_id = session['team_id']
    print("team_id", team_id)

    notes = KanbanBoard.query.filter_by(team_id=team_id).all()
    print("KANBANKANVAN", notes)
    kanban_data = [{

        'title': kanban.title,
    
        'columns': kanban.columns,
        'container_position':kanban.container_position,
        'deadline': kanban.deadline,
        'team_id': kanban.team_id
    } for kanban in notes]
    print("kanban_data", kanban_data)
    return jsonify(kanban_data)


@app.route('/api/notes')
def api_notes():
    if 'team_id' not in session:
        return jsonify({"error": "No team selected"}), 400
    
    team_id = session['team_id']

    notes = Note.query.filter_by(team_id=team_id).all()
    print("APInotes", notes)

    notes_data = [{
        'id': note.id,
        'title': note.title,
        'content': note.content,
        'top': note.top,
        'left': note.left,
        'color': note.color,
        'deadline': note.deadline.strftime('%Y-%m-%d %H:%M:%S') if note.deadline else None,
        'user_id': note.user_id,
        'team_id': note.team_id
    } for note in notes]
    return jsonify(notes_data)


@app.route('/reset_notes', methods=['POST'])
def reset_notes():
    if 'team_id' not in session:
        return jsonify({"error": "No team selected"}), 400

    team_id = session['team_id']
    print("team_id", team_id)
    try:
        Note.query.filter_by(team_id=team_id).delete()
        KanbanBoard.query.filter_by(team_id=team_id).delete()
        print("Note", Note)
        db.session.commit()
        return jsonify({"message": f"All notes for team {team_id} have been reset successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/delete_note', methods=['POST'])
def delete_note():
    note_id = request.json.get('noteId')  # Ensure the correct key is used in the JSON payload from the client.
    team_id = session['team_id']
    print("team_id", team_id)
    print("note_id", note_id)
    if not note_id:
        return jsonify({"error": "Note ID is required"}), 400

    try:
        # Use session to get the note instead of the deprecated method
        note = db.session.get(Note, note_id)
        if not note:
            return jsonify({"error": "Note not found"}), 404

        db.session.delete(note)
        db.session.commit()
        print("db", db)
        return jsonify(team_id=team_id)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/notes')
def show_notes():
    notes = Note.query.all()
    return render_template('notes.html', notes=notes)


@app.route('/export_notes', methods=['POST'])
def export_notes():
    data = request.get_json()
    notes_data = data.get('notesData', [])
    print("notes_data(export)", notes_data)
    session['tasks']=notes_data
    print("session", session)

    for note_data in notes_data:
        title = note_data.get('title')
        content = note_data.get('content')

        # Process title and content as needed
        print(f"Title: {title}, Content: {content}")

    return jsonify(success=True)


@app.route('/chat', methods=['POST'])
def chat():

    client = OpenAI(api_key="YOUR KEY")
    memory = [
        {"role": "system", "content": "You are a assistant to plan the schedule, tasks and other activities for user." }
    ]

    team_id = session['team_id']
    print("team_id", team_id)
    notes = Note.query.filter_by(team_id=team_id).all()

    print("notes", notes)
    tasks_message = {"role": "system", "content": f"Current tasks are; {notes}"}

    memory.append(tasks_message)

    # Create a system message for the tasks
    # for note_data in notes:
    #     title = note_data.get('title')
    #     content = note_data.get('content')
    #     
    #     print("tasks_message", tasks_message)
    #     print("memory",memory)




    user_message = request.json['message']
    memory.append({"role": "user", "content": user_message})


    print("memory", memory)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=memory,
        temperature=0.1,  # Adjust as needed
    )   # Adjust as needed)
    reply = response.choices[0].message.content
    memory.append({"role": "assistant", "content": reply})


    session['messages'] =memory

    show_button = False
    return jsonify({"reply": reply, "showButton": show_button})

    
# New Feedback model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feedback_text = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Optional: Add a foreign key to link feedback to a user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('feedbacks', lazy=True))

    def __repr__(self):
        return f'<Feedback {self.id}>'
    
# Create tables
with app.app_context():
    db.create_all()


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()  # Use this method to get JSON data
    print(data)

    if not data:
        return jsonify(success=False, error="No data received"), 400

    # Now you can use the data as a regular dictionary
    username = data.get('newUsername')
    email = data.get('email')
    password = data.get('newPassword')  # Make sure to handle passwords securely

    print(username, email, password)  # Inspect the values

    # Check if user already exists
    user = User.query.filter_by(username=username).first()
    if user:
        print("var")
        return jsonify(success=False, error="Username already taken"), 409



    # Create new user and set password
    new_user = User(username=username, email=email)
    new_user.set_password(password)

    # Add new user to the database
    db.session.add(new_user)
    db.session.commit()

    return jsonify(success=True)

    

@app.route('/delete_user', methods=['GET'])
def delete_user():
    # Find the user in the database
    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    # If the user is not found, return an error
    if not user:
        return jsonify(success=False, error="User not found"), 404

    # Delete the user from the database
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('logout')) # Redirect to the home page or login page


@app.route('/login', methods=['POST'])
def login():

    if not request.is_json:
        return jsonify(success=False, error="Missing JSON in request"), 400
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Input validation (basic example)
    if not username or not password:
        return jsonify(success=False, error="Username and password are required"), 400


    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        # Login successful
        session['user_id'] = user.id 
        session['username'] = user.username # Store the user's ID in the session
        return jsonify(success=True, username=user.username )
    else:
        # Login failed
        return jsonify(success=False, error="Invalid username or password"), 401

@app.route('/admin/users')
def list_users():
    users = User.query.all()  # Get all users from the database
    return render_template('admin_users.html', users=users)

@app.route('/logout')
def logout():

        # Iterate over all possible team authorizations and clear them
    for key in list(session.keys()):
        if '_authorized' in key:
            session.pop(key)
    # Remove 'user_id' and 'username' from session
    # Remove 'user_id' and 'username' from session
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('home')) # Redirect to the home page or login page











if __name__ == '__main__':
    app.run(debug=True)


