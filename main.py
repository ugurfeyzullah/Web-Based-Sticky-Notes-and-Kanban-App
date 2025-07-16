from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg for non-interactive environments
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from openai import OpenAI
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_migrate import Migrate
from sqlalchemy import JSON  # For SQLite, use generic JSON type
import pandas as pd
import numpy as np
import json
import base64
import textwrap
import random
import os

# New imports for Gemini Integration
import google.generativeai as genai
import re
from typing import Optional


current_directory = os.path.dirname(os.path.abspath(__file__))
#print("current_directory", current_directory)

app = Flask(__name__)
# Example using Flask-SQLAlchemy
app.secret_key = 'asdfasfsagfdsgdfgfafewrtrtyrhfgb'
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
    container_position = db.Column(db.Text, nullable=True)  # Store container position as JSON string
    column_heights = db.Column(db.Text, nullable=True)  # Store heights of columns as JSON string
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

# New Category model for AI categorization
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), nullable=True)  # Hex color code
    team_id = db.Column(db.Integer, nullable=False)
    created_by_ai = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'

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
    deadline = db.Column(db.DateTime, nullable=True)
    
    # AI Categorization fields
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    ai_tags = db.Column(db.Text, nullable=True)  # Store AI-generated tags as JSON string
    ai_confidence = db.Column(db.Float, nullable=True)  # Confidence score for AI categorization
    is_ai_categorized = db.Column(db.Boolean, default=False)
    manual_override = db.Column(db.Boolean, default=False)  # Human intervention flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Track note creation time
    
    # Relationships
    category = db.relationship('Category', backref=db.backref('notes', lazy=True))

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
        # Get existing notes to preserve categorization
        existing_notes = Note.query.filter_by(team_id=team_id).all()
        
        # Create a mapping of existing notes by their unique characteristics
        existing_notes_map = {}
        for note in existing_notes:
            # Use a combination of title, content, and position as a unique key
            key = f"{note.title}_{note.content}_{note.top}_{note.left}"
            existing_notes_map[key] = note
        
        # Clear existing notes
        Note.query.filter_by(team_id=team_id).delete()
        
        for note_info in notes_data['notes']:
            # Create a key for this note to match with existing notes
            note_key = f"{note_info['title']}_{note_info['content']}_{note_info['top']}_{note_info['left']}"
            existing_note = existing_notes_map.get(note_key)
            
            # If we found a matching existing note, preserve its categorization
            if existing_note:
                new_note = Note(
                    title=note_info['title'],
                    content=note_info['content'],
                    top=note_info['top'],
                    left=note_info['left'],
                    color=note_info['color'],
                    deadline=datetime.strptime(note_info['deadline'], '%Y-%m-%dT%H:%M') if note_info['deadline'] else None,
                    team_id=team_id,
                    created_at=datetime.utcnow(),
                    # Preserve existing categorization data
                    category_id=existing_note.category_id,
                    ai_tags=existing_note.ai_tags,
                    ai_confidence=existing_note.ai_confidence,
                    is_ai_categorized=existing_note.is_ai_categorized,
                    manual_override=existing_note.manual_override
                )
            else:
                # This is a new note, create it without categorization
                new_note = Note(
                    title=note_info['title'],
                    content=note_info['content'],
                    top=note_info['top'],
                    left=note_info['left'],
                    color=note_info['color'],
                    deadline=datetime.strptime(note_info['deadline'], '%Y-%m-%dT%H:%M') if note_info['deadline'] else None,
                    team_id=team_id,
                    created_at=datetime.utcnow(),
                    # No categorization for new notes
                    category_id=None,
                    ai_tags=None,
                    ai_confidence=None,
                    is_ai_categorized=False,
                    manual_override=False
                )
            
            db.session.add(new_note)
        
        db.session.commit()
        return jsonify({"message": "Notes saved successfully!"})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Failed to save notes: {str(e)}")
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
            board.container_position = json.dumps(board_data.get('containerPosition')) if board_data.get('containerPosition') else None
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
        'columns': json.loads(kanban.columns) if kanban.columns else [],
        'container_position': json.loads(kanban.container_position) if kanban.container_position else None,
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
        'team_id': note.team_id,
        'category_id': note.category_id,
        'category_name': note.category.name if note.category else None,
        'category_color': note.category.color if note.category else None,
        'ai_tags': json.loads(note.ai_tags) if note.ai_tags else None,
        'ai_confidence': note.ai_confidence,
        'is_ai_categorized': note.is_ai_categorized,
        'manual_override': note.manual_override
    } for note in notes]
    return jsonify(notes_data)


@app.route('/reset_notes', methods=['POST'])
def reset_notes():
    if 'team_id' not in session:
        return jsonify({"error": "No team selected"}), 400

    team_id = session['team_id']
    print("team_id", team_id)
    try:
        # Clear category assignments from notes first
        notes = Note.query.filter_by(team_id=team_id).all()
        for note in notes:
            note.category_id = None
            note.ai_tags = None
            note.ai_confidence = None
            note.is_ai_categorized = False
            note.manual_override = False
        
        # Then delete notes and kanban boards
        Note.query.filter_by(team_id=team_id).delete()
        KanbanBoard.query.filter_by(team_id=team_id).delete()
        # Also delete categories for this team
        Category.query.filter_by(team_id=team_id).delete()
        
        db.session.commit()
        return jsonify({"message": f"All notes and categories for team {team_id} have been reset successfully!"})
    except Exception as e:
        db.session.rollback()
        print(f"Error in reset_notes: {str(e)}")
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


@app.route('/categorize_notes', methods=['POST'])
def categorize_notes():
    """AI-powered categorization of notes"""
    if 'team_id' not in session:
        return jsonify({"error": "No team selected"}), 400

    team_id = session['team_id']
    
    try:
        # Get all notes for the team
        notes = Note.query.filter_by(team_id=team_id).all()
        
        if not notes:
            return jsonify({"message": "No notes to categorize"}), 200
        
        # Prepare notes data for AI
        notes_content = []
        for note in notes:
            notes_content.append({
                'id': note.id,
                'title': note.title,
                'content': note.content
            })
        
        # Call AI categorization
        categories_data = ai_categorize_notes(notes_content)
        
        # Process AI response and update database
        updated_notes = []
        for note_data in categories_data.get('notes', []):
            note = Note.query.get(note_data['id'])
            if note:
                # Find or create category
                category = None
                if note_data.get('category'):
                    category = Category.query.filter_by(
                        name=note_data['category'], 
                        team_id=team_id
                    ).first()
                    
                    if not category:
                        # Get color from categories_data if available
                        category_color = generate_category_color()
                        for cat in categories_data.get('categories', []):
                            if cat['name'] == note_data['category']:
                                category_color = cat.get('color_suggestion', category_color)
                                break
                        
                        category = Category(
                            name=note_data['category'],
                            team_id=team_id,
                            created_by_ai=True,
                            color=category_color,
                            description=note_data.get('category_description', '')
                        )
                        db.session.add(category)
                        db.session.flush()  # Get the ID
                
                # Update note with AI categorization
                note.category_id = category.id if category else None
                note.ai_tags = json.dumps(note_data.get('tags', [])) if note_data.get('tags') else None
                note.ai_confidence = note_data.get('confidence', 0.0)
                note.is_ai_categorized = True
                note.manual_override = False
                
                # Update note color to match category color
                if category and category.color:
                    note.color = category.color
                
                updated_notes.append({
                    'id': note.id,
                    'category': note_data.get('category'),
                    'tags': note_data.get('tags', []),
                    'confidence': note_data.get('confidence', 0.0),
                    'color': note.color  # Include the new color in response
                })
        
        db.session.commit()
        
        return jsonify({
            "message": "Notes categorized successfully",
            "categories": categories_data.get('categories', []),
            "updated_notes": updated_notes
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in categorize_notes: {str(e)}")
        return jsonify({"error": str(e)}), 500

# COPY AND PASTE THIS UPDATED FUNCTION

def ai_categorize_notes(notes_content):
    """Use OpenAI API to categorize notes with fallback to manual categorization"""
    
    # First try OpenAI API
    try:
        # FIXED: Use environment variable for API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found")
        client = OpenAI(api_key=api_key)
        
        # Prepare the prompt
        notes_text = ""
        for note in notes_content:
            notes_text += f"Note ID {note['id']}: {note['title']} - {note['content']}\n"
        
        prompt = f"""
        Analyze the following sticky notes and categorize them into logical thematic groups. 
        For each note, provide:
        1. A category name (create new categories as needed)
        2. 2-3 relevant tags
        3. A confidence score (0.0-1.0)
        4. A brief description for each category
        
        Notes to categorize:
        {notes_text}
        
        Please respond in JSON format with this structure:
        {{
            "categories": [
                {{
                    "name": "Category Name",
                    "description": "Brief description of what this category contains",
                    "color_suggestion": "hex color code"
                }}
            ],
            "notes": [
                {{
                    "id": note_id,
                    "category": "Category Name",
                    "tags": ["tag1", "tag2", "tag3"],
                    "confidence": 0.85,
                    "category_description": "Why this note fits in this category"
                }}
            ]
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"}, # Enforce JSON response
            messages=[
                {"role": "system", "content": "You are an expert at organizing and categorizing ideas and tasks. Provide clear, logical categorizations in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Parse JSON response
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        print("Falling back to local categorization...")
        # Fallback to local categorization
        return create_local_categories(notes_content)

def create_local_categories(notes_content):
    """Create categories locally without AI when API fails"""
    
    # Define category keywords and their corresponding categories
    category_mapping = {
        'Software Development': ['software', 'installation', 'coding', 'debugging', 'platform', 'uwb', 'development'],
        'Research & Publications': ['paper', 'publication', 'research', 'gan', 'generative', 'academic', 'icearc', 'ccc'],
        'Team Management': ['meeting', 'engagement', 'plan', 'team', 'collaboration', 'bi-weekly'],
        'Training & Education': ['lab', 'session', 'training', 'education', 'hiwis'],
        'Administrative': ['timesheet', 'control', 'monitoring', 'report', 'status', 'performance', 'review']
    }
    
    # Initialize result structure
    categories = []
    categorized_notes = []
    used_categories = set()
    
    # Categorize each note
    for note in notes_content:
        best_category = None
        best_score = 0
        matching_tags = []
        
        # Check content against category keywords
        content_lower = (note['title'] + ' ' + note['content']).lower()
        
        for category, keywords in category_mapping.items():
            score = 0;
            note_tags = []
            
            for keyword in keywords:
                if keyword in content_lower:
                    score += 1
                    note_tags.append(keyword)
            
            if score > best_score:
                best_score = score
                best_category = category
                matching_tags = note_tags[:3]  # Limit to 3 tags
        
        # If no good match found, use "General Tasks"
        if best_score == 0:
            best_category = "General Tasks"
            matching_tags = ["task", "general"]
        
        # Add category to used categories
        used_categories.add(best_category)
        
        # Add note to categorized list
        categorized_notes.append({
            "id": note['id'],
            "category": best_category,
            "tags": matching_tags,
            "confidence": min(0.6 + (best_score * 0.1), 0.95)  # Base confidence 0.6-0.95
        })
    
    # Create category definitions for used categories
    category_descriptions = {
        'Software Development': 'Software installation, coding, debugging, and technical development tasks',
        'Research & Publications': 'Academic research, paper writing, and publication activities',
        'Team Management': 'Team meetings, collaboration, and coordination activities',
        'Training & Education': 'Training sessions, educational activities, and workshops',
        'Administrative': 'Administrative tasks, reporting, and monitoring activities',
        'General Tasks': 'General tasks that don\'t fit into specific categories'
    }
    
    category_colors = {
        'Software Development': '#4ECDC4',
        'Research & Publications': '#FF6B6B',
        'Team Management': '#45B7D1',
        'Training & Education': '#96CEB4',
        'Administrative': '#FFEAA7',
        'General Tasks': '#DDA0DD'
    }
    
    for category in used_categories:
        categories.append({
            "name": category,
            "description": category_descriptions.get(category, "Category description"),
            "color_suggestion": category_colors.get(category, '#98D8C8')
        })
    
    return {
        "categories": categories,
        "notes": categorized_notes
    }

def generate_category_color():
    """Generate a random hex color for categories"""
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
    return random.choice(colors)

@app.route('/update_note_category', methods=['POST'])
def update_note_category():
    """Allow manual override of AI categorization"""
    if 'team_id' not in session:
        return jsonify({"error": "No team selected"}), 400
    
    data = request.get_json()
    note_id = data.get('note_id')
    category_name = data.get('category_name')
    team_id = session['team_id']
    
    try:
        note = Note.query.get(note_id)
        if not note or note.team_id != int(team_id):
            return jsonify({"error": "Note not found"}), 404
        
        if category_name:
            # Find or create category
            category = Category.query.filter_by(
                name=category_name, 
                team_id=team_id
            ).first()
            
            if not category:
                category = Category(
                    name=category_name,
                    team_id=team_id,
                    created_by_ai=False,
                    color=generate_category_color()
                )
                db.session.add(category)
                db.session.flush()
            
            note.category_id = category.id
            # Update note color to match category color
            if category and category.color:
                note.color = category.color
        else:
            note.category_id = None
        
        note.manual_override = True
        db.session.commit()
        
        return jsonify({
            "message": "Category updated successfully",
            "color": note.color if note.category_id else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories')
def api_categories():
    """Get all categories for the current team"""
    if 'team_id' not in session:
        return jsonify({"error": "No team selected"}), 400
    
    team_id = session['team_id']
    categories = Category.query.filter_by(team_id=team_id).all()
    
    categories_data = [{
        'id': category.id,
        'name': category.name,
        'color': category.color,
        'description': '\n'.join([f"{i+1}. {note.title}" for i, note in enumerate(category.notes)]) if category.notes else category.description,
        'note_titles': [note.title for note in category.notes],  # Add note titles
        'created_by_ai': category.created_by_ai,
        'note_count': len(category.notes)
    } for category in categories]
    
    return jsonify(categories_data)

@app.route('/clear_categories', methods=['POST'])
def clear_categories():
    """Clear all categories and remove categorization from notes"""
    if 'team_id' not in session:
        return jsonify({"error": "No team selected"}), 400
    
    team_id = session['team_id']
    
    try:
        # Clear category assignments from notes
        notes = Note.query.filter_by(team_id=team_id).all()
        for note in notes:
            note.category_id = None
            note.ai_tags = None
            note.ai_confidence = None
            note.is_ai_categorized = False
            note.manual_override = False
        
        # Delete all categories for this team
        Category.query.filter_by(team_id=team_id).delete()
        
        db.session.commit()
        
        return jsonify({"message": "All categories cleared successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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

def create_default_team1_notes():
    """Create default sticky notes for team 1 with project tasks"""
    team_id = 1
    
    default_tasks = [
        {
            'title': 'Software installation on main PC',
            'content': 'UWB installation included\nAssigned: Yavan, Feyzullah\nStart: 07/02/2025 | Due: 07/11/2025\nBucket: Executing',
            'color': '#FF6B6B',
            'position': {'top': '100px', 'left': '50px'}
        },
        {
            'title': 'Industry engagement plan extended',
            'content': 'Extended with Atefeh\nAssigned: Aali, Atefeh + one more\nStart: 07/07/2025 | Due: 07/11/2025\nBucket: Initiating',
            'color': '#4ECDC4',
            'position': {'top': '100px', 'left': '300px'}
        },
        {
            'title': 'Collaboration platform coding debugging',
            'content': 'Platform debugging and fixes\nAssigned: Yavan, Feyzullah\nStart: 07/14/2025 | Due: 07/25/2025\nBucket: Planning',
            'color': '#45B7D1',
            'position': {'top': '100px', 'left': '550px'}
        },
        {
            'title': 'ICEARC25 extended paper publication',
            'content': 'Research paper publication\nAssigned: Yavan, Feyzullah\nStart: 07/14/2025 | Due: 07/31/2025\nBucket: Initiating',
            'color': '#96CEB4',
            'position': {'top': '280px', 'left': '50px'}
        },
        {
            'title': 'Bi-Weekly Meetings',
            'content': 'Regular team meetings\nAssigned: Atefeh Aali + Feyzullah Yavan\nStart: 07/18/2025 | Due: 07/18/2025 (recurring)\nBucket: Planning',
            'color': '#FFEAA7',
            'position': {'top': '280px', 'left': '300px'}
        },
        {
            'title': 'Generative design with GAN',
            'content': 'GAN trained with CubiCasa5k dataset\nAssigned: Yavan, Feyzullah\nStart: 07/31/2025 | Due: 11/30/2025\nBucket: Initiating',
            'color': '#DDA0DD',
            'position': {'top': '280px', 'left': '550px'}
        },
        {
            'title': 'Time Sheet Control for Hiwis',
            'content': 'Regular timesheet monitoring\nAssigned: Aali, Atefeh (TI)\nStart: 08/04/2025 | Due: 08/04/2025 (recurring)\nBucket: Executing',
            'color': '#98D8C8',
            'position': {'top': '460px', 'left': '50px'}
        },
        {
            'title': 'CCC25 extended paper publication',
            'content': 'Conference paper submission\nAssigned: Yavan, Feyzullah\nStart: 08/20/2025 | Due: 10/31/2025\nBucket: Initiating',
            'color': '#F7DC6F',
            'position': {'top': '460px', 'left': '300px'}
        },
        {
            'title': 'Feyzullah-Lab session for Hiwis',
            'content': 'Lab training sessions\nAssigned: Yavan, Feyzullah\nStart: 07/09/2025 | Due: recurring\nBucket: Initiating',
            'color': '#BB8FCE',
            'position': {'top': '460px', 'left': '550px'}
        },
        {
            'title': 'Atefeh-Lab session for Hiwis',
            'content': 'Lab training sessions\nAssigned: Aali, Atefeh (TI)\nStart: 07/16/2025 | Due: recurring\nBucket: Initiating',
            'color': '#85C1E9',
            'position': {'top': '640px', 'left': '50px'}
        },
        {
            'title': 'Feyzullah-Time Sheet Control',
            'content': 'Timesheet monitoring by Feyzullah\nAssigned: Yavan, Feyzullah\nStart: 08/01/2025 | Due: recurring\nBucket: Initiating',
            'color': '#FFB6C1',
            'position': {'top': '640px', 'left': '300px'}
        },
        {
            'title': 'Report monthly status',
            'content': 'Monthly progress reporting\nAssigned: (no assignee shown)\nStart: 08/08/2025 | Due: recurring\nBucket: Monitoring and control',
            'color': '#98FB98',
            'position': {'top': '640px', 'left': '550px'}
        },
        {
            'title': 'Atefeh-Time Sheet Control',
            'content': 'Timesheet monitoring by Atefeh\nAssigned: Aali, Atefeh (TI)\nStart: 09/05/2025 | Due: recurring\nBucket: Initiating',
            'color': '#F0E68C',
            'position': {'top': '820px', 'left': '50px'}
        },
        {
            'title': 'Conduct team performance reviews',
            'content': 'Regular performance evaluations\nAssigned: (no assignee shown)\nStart: 09/08/2025 | Due: recurring\nBucket: Monitoring and control',
            'color': '#DDA0DD',
            'position': {'top': '820px', 'left': '300px'}
        }
    ]
    
    # Create the default notes
    for task in default_tasks:
        # Parse date if available
        deadline = None
        if 'Due:' in task['content']:
            try:
                # Extract date from content
                due_line = [line for line in task['content'].split('\n') if 'Due:' in line][0]
                if 'recurring' not in due_line:
                    # Extract the date part after "Due: "
                    date_part = due_line.split('Due:')[1].strip()
                    # If there's a pipe or other character, get only the date portion
                    if '|' in date_part:
                        date_str = date_part.split('|')[0].strip()
                    else:
                        date_str = date_part.split()[0].strip()
                    
                    # Parse the date string to datetime
                    if '/' in date_str:
                        month, day, year = date_str.split('/')
                        # Set the time to noon to ensure it appears properly in the UI
                        deadline = datetime(int(year), int(month), int(day), 12, 0)
                        print(f"Extracted deadline for '{task['title']}': {deadline}")
            except Exception as e:
                print(f"Error parsing date for '{task['title']}': {e}")
                pass  # If date parsing fails, leave as None
        
        new_note = Note(
            title=task['title'],
            content=task['content'],
            top=task['position']['top'],
            left=task['position']['left'],
            color=task['color'],
            deadline=deadline,
            team_id=team_id,
            created_at=datetime.utcnow()  # Add the missing created_at field
        )
        db.session.add(new_note)
    
    try:
        db.session.commit()
        print(f"Created {len(default_tasks)} default notes for team 1")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating default notes: {str(e)}")

@app.route('/create_default_notes/<team_id>', methods=['POST'])
def create_default_notes(team_id):
    """Manually create default notes for a specific team"""
    if 'team_id' not in session:
        return jsonify({"error": "No team selected"}), 400
    
    if team_id == '1':
        # First clear existing notes for team 1
        Note.query.filter_by(team_id=1).delete()
        Category.query.filter_by(team_id=1).delete()  # Also clear categories
        db.session.commit()
        
        # Create default notes
        create_default_team1_notes()
        return jsonify({"message": "Default notes created successfully for team 1"})
    else:
        return jsonify({"error": "Default notes only available for team 1"}), 400

@app.route('/load_default_notes', methods=['POST'])
def load_default_notes():
    """Load default notes for the current team without clearing existing ones"""
    if 'team_id' not in session:
        return jsonify({"error": "No team selected"}), 400
    
    team_id = session['team_id']
    
    if team_id == '1':
        create_default_team1_notes()
        # Also create categories and categorize the notes
        create_sample_categories_team1()
        return jsonify({"message": "Default notes loaded successfully!"})
    else:
        return jsonify({"error": "Default notes only available for team 1"}), 400

def create_sample_categories_team1():
    """Create sample categories for team 1 to demonstrate AI categorization"""
    team_id = 1
    
    # Get existing categories
    existing_categories = {cat.name: cat.id for cat in Category.query.filter_by(team_id=team_id).all()}
    
    # Create sample categories
    sample_categories = [
        {
            'name': 'Research & Publications',
            'description': 'Academic papers, research activities, and publication tasks',
            'color': '#FF6B6B',
            'created_by_ai': True
        },
        {
            'name': 'Software Development',
            'description': 'Coding, debugging, and software installation tasks',
            'color': '#4ECDC4',
            'created_by_ai': True
        },
        {
            'name': 'Team Management',
            'description': 'Meetings, reviews, and team coordination activities',
            'color': '#45B7D1',
            'created_by_ai': True
        },
        {
            'name': 'Training & Education',
            'description': 'Lab sessions, workshops, and educational activities',
            'color': '#96CEB4',
            'created_by_ai': True
        },
        {
            'name': 'Administrative',
            'description': 'Time tracking, reporting, and administrative tasks',
            'color': '#FFEAA7',
            'created_by_ai': True
        }
    ]
    
    category_mapping = {}
    
    # Create categories (only if they don't exist)
    for cat_data in sample_categories:
        if cat_data['name'] in existing_categories:
            # Category already exists, use existing ID
            category_mapping[cat_data['name']] = existing_categories[cat_data['name']]
        else:
            # Create new category
            category = Category(
                name=cat_data['name'],
                description=cat_data['description'],
                color=cat_data['color'],
                team_id=team_id,
                created_by_ai=cat_data['created_by_ai']
            )
            db.session.add(category)
            db.session.flush()
            category_mapping[cat_data['name']] = category.id
    
    # Update existing notes with categories and AI data
    note_categorization = {
        'Software installation on main PC': {
            'category': 'Software Development',
            'tags': ['installation', 'uwb', 'setup'],
            'confidence': 0.95
        },
        'Industry engagement plan extended': {
            'category': 'Team Management',
            'tags': ['engagement', 'planning', 'collaboration'],
            'confidence': 0.88
        },
        'Collaboration platform coding debugging': {
            'category': 'Software Development',
            'tags': ['debugging', 'platform', 'coding'],
            'confidence': 0.92
        },
        'ICEARC25 extended paper publication': {
            'category': 'Research & Publications',
            'tags': ['publication', 'research', 'academic'],
            'confidence': 0.98
        },
        'Bi-Weekly Meetings': {
            'category': 'Team Management',
            'tags': ['meetings', 'coordination', 'regular'],
            'confidence': 0.85
        },
        'Generative design with GAN': {
            'category': 'Research & Publications',
            'tags': ['gan', 'research', 'ai'],
            'confidence': 0.94
        },
        'Time Sheet Control for Hiwis': {
            'category': 'Administrative',
            'tags': ['timesheet', 'control', 'monitoring'],
            'confidence': 0.90
        },
        'CCC25 extended paper publication': {
            'category': 'Research & Publications',
            'tags': ['publication', 'conference', 'paper'],
            'confidence': 0.97
        },
        'Feyzullah-Lab session for Hiwis': {
            'category': 'Training & Education',
            'tags': ['training', 'lab', 'education'],
            'confidence': 0.91
        },
        'Atefeh-Lab session for Hiwis': {
            'category': 'Training & Education',
            'tags': ['training', 'lab', 'education'],
            'confidence': 0.91
        },
        'Feyzullah-Time Sheet Control': {
            'category': 'Administrative',
            'tags': ['timesheet', 'control', 'admin'],
            'confidence': 0.89
        },
        'Report monthly status': {
            'category': 'Administrative',
            'tags': ['reporting', 'status', 'monthly'],
            'confidence': 0.87
        },
        'Atefeh-Time Sheet Control': {
            'category': 'Administrative',
            'tags': ['timesheet', 'control', 'admin'],
            'confidence': 0.89
        },
        'Conduct team performance reviews': {
            'category': 'Team Management',
            'tags': ['review', 'performance', 'evaluation'],
            'confidence': 0.93
        }
    }
    
    # Update notes with categorization
    for note_title, cat_data in note_categorization.items():
        note = Note.query.filter_by(title=note_title, team_id=team_id).first()
        if note:
            category_id = category_mapping.get(cat_data['category'])
            note.category_id = category_id
            note.ai_tags = json.dumps(cat_data['tags']) if cat_data['tags'] else None
            note.ai_confidence = cat_data['confidence']
            note.is_ai_categorized = True
            note.manual_override = False
            
            # Update note color to match category color
            if category_id:
                category = Category.query.get(category_id)
                if category and category.color:
                    note.color = category.color
    
    try:
        db.session.commit()
        print(f"Created {len(sample_categories)} categories and updated notes with AI categorization")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample categories: {str(e)}")

@app.route('/create_sample_categories/<team_id>', methods=['POST'])
def create_sample_categories(team_id):
    """Manually create sample categories for a specific team (optional feature)"""
    if team_id == '1':
        # First clear existing categories for team 1
        Category.query.filter_by(team_id=1).delete()
        db.session.commit()
        
        # Create sample categories if needed
        create_sample_categories_team1()
        return jsonify({"message": "Sample categories created successfully for team 1"})
    else:
        return jsonify({"error": "Sample categories only available for team 1"}), 400

# Gantt chart route
@app.route('/gantt_chart', methods=['GET', 'POST'])
def gantt_chart():
    if request.method == 'POST':
        # Get the data from the form
        chart_title = request.form.get('chart_title', 'Gantt Chart')
        x_axis_label = request.form.get('x_axis_label', 'Date')
        y_axis_label = request.form.get('y_axis_label', 'Tasks')
        date_format = request.form.get('date_format', '%Y-%m-%d')
        
        # Get notes data for the current team
        if 'team_id' not in session:
            return jsonify({"error": "No team selected"}), 400
        
        team_id = session['team_id']
        notes = Note.query.filter_by(team_id=team_id).all()
        
        # Prepare data for the Gantt chart
        tasks = []
        for note in notes:
            task = {
                'id': note.id,
                'title': note.title,
                'start': note.deadline - timedelta(days=2) if note.deadline else None,
                'end': note.deadline + timedelta(days=2) if note.deadline else None,
                'color': note.color if note.color else '#FFFFFF',
                'category': note.category.name if note.category else 'Uncategorized'
            }
            tasks.append(task)
        
        # Create a DataFrame for the tasks
        df = pd.DataFrame(tasks)
        
        # Generate the Gantt chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Define color palette
        colors = df['color'].tolist()
        
        # Plot each task
        for i, task in df.iterrows():
            ax.barh(task['title'], (task['end'] - task['start']).days, left=(task['start'] - df['start'].min()).days, color=task['color'])
        
        # Format the x-axis with date labels
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
        
        # Set labels and title
        ax.set_xlabel(x_axis_label)
        ax.set_ylabel(y_axis_label)
        ax.set_title(chart_title)
        
        # Rotate date labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the chart to a BytesIO object
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        
        # Encode the image to base64 for embedding in HTML
        chart_data = base64.b64encode(img.getvalue()).decode()
        
        return jsonify({"success": True, "chart_data": chart_data})
    
    return render_template('gantt_chart.html')

# === START: GEMINI DURATION ESTIMATION FUNCTIONS ===

def setup_gemini_api():
    """Setup Gemini API with API key from environment variables"""
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found")
        
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print(f"Error setting up Gemini API: {e}")
        return None

def calculate_duration_with_gemini(task_title: str, task_content: str = "") -> int:
    """
    Use Google Gemini LLM to estimate task duration based on title and content
    
    Args:
        task_title: The title of the task
        task_content: Additional content/description of the task
        
    Returns:
        int: Estimated duration in days (1-30)
    """
    try:
        # Setup Gemini model
        model = setup_gemini_api()
        if not model:
            print("Failed to setup Gemini API, falling back to default duration")
            return 7  # Default fallback
        
        # Create a comprehensive prompt for duration estimation
        prompt = f"""
        You are a project management expert. Analyze the following task and estimate how many days it would take to complete.

        Task Title: "{task_title}"
        Task Description: "{task_content}"

        Consider these factors when estimating:
        - Complexity and scope of the task
        - Typical industry standards for similar work
        - Required research, planning, implementation, and testing phases
        - Potential dependencies and coordination needs
        - Quality assurance and review processes

        Provide your estimate as a single number between 1 and 30 days.
        
        Guidelines:
        - Simple tasks (setup, configuration, quick fixes): 1-3 days
        - Medium tasks (development, implementation, writing): 5-10 days
        - Complex tasks (research, extensive development, publications): 10-21 days
        - Very complex tasks (large projects, comprehensive systems): 21-30 days

        Respond with ONLY the number of days (no explanation, just the number).
        """
        
        # Generate response from Gemini
        response = model.generate_content(prompt)
        
        # Extract duration from response
        duration_text = response.text.strip()
        
        # Parse the duration number
        duration_match = re.search(r'\b(\d+)\b', duration_text)
        if duration_match:
            duration = int(duration_match.group(1))
            # Ensure duration is within valid range
            duration = max(1, min(30, duration))
            print(f"Gemini estimated duration for '{task_title}': {duration} days")
            return duration
        else:
            print(f"Could not parse duration from Gemini response: '{duration_text}'")
            return 7  # Default fallback
            
    except Exception as e:
        print(f"Error getting duration from Gemini: {e}")
        return 7  # Default fallback

def calculate_duration_with_gemini_detailed(task_title: str, task_content: str = "") -> dict:
    """
    Enhanced version that returns detailed analysis along with duration estimate
    
    Returns:
        dict: Contains duration, reasoning, and confidence level
    """
    try:
        model = setup_gemini_api()
        if not model:
            return {
                "duration": 7,
                "reasoning": "API setup failed, using default",
                "confidence": 0.3
            }
        
        prompt = f"""
        You are a project management expert. Analyze the following task and provide a detailed duration estimate.

        Task Title: "{task_title}"
        Task Description: "{task_content}"

        Please provide your analysis in the following JSON format:
        {{
            "duration": [number between 1-30],
            "reasoning": "[brief explanation of your estimation],
            "confidence": [confidence level between 0.1-1.0],
            "complexity_factors": ["list", "of", "key", "factors"],
            "risk_factors": ["potential", "delays", "or", "issues"]
        }}

        Consider:
        - Technical complexity
        - Resource requirements
        - Dependencies and coordination needs
        - Research and planning time
        - Implementation and testing phases
        - Documentation and review processes

        Respond with valid JSON only.
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Try to parse JSON response
        try:
            import json
            # Remove code block markers if present
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            analysis = json.loads(response_text)
            
            # Validate and sanitize the response
            duration = max(1, min(30, int(analysis.get('duration', 7))))
            confidence = max(0.1, min(1.0, float(analysis.get('confidence', 0.5))))
            
            return {
                "duration": duration,
                "reasoning": analysis.get('reasoning', 'No reasoning provided'),
                "confidence": confidence,
                "complexity_factors": analysis.get('complexity_factors', []),
                "risk_factors": analysis.get('risk_factors', [])
            }
            
        except json.JSONDecodeError:
            # Fallback to simple number extraction
            duration_match = re.search(r'\b(\d+)\b', response_text)
            duration = int(duration_match.group(1)) if duration_match else 7
            duration = max(1, min(30, duration))
            
            return {
                "duration": duration,
                "reasoning": "Could not parse detailed analysis",
                "confidence": 0.4
            }
            
    except Exception as e:
        print(f"Error in detailed Gemini analysis: {e}")
        return {
            "duration": 7,
            "reasoning": f"Error occurred: {str(e)}",
            "confidence": 0.3
        }

def calculate_duration_fallback(task_title: str, task_content: str = "") -> int:
    """
    Fallback method using the original keyword-based approach
    """
    # This is your original method as backup
    complexity_indicators = {
        'simple': 3, 'easy': 3, 'quick': 2,
        'complex': 10, 'difficult': 14, 'challenging': 12,
        'extensive': 14, 'research': 10, 'implement': 7,
        'develop': 7, 'create': 5, 'setup': 3,
        'configure': 4, 'test': 5, 'review': 3, 'document': 5
    }
    
    default_duration = 7
    text_to_analyze = f"{task_title} {task_content}".lower()
    
    max_duration = default_duration
    for keyword, duration in complexity_indicators.items():
        if keyword in text_to_analyze:
            max_duration = max(max_duration, duration)
    
    return max(1, min(30, max_duration))
    
# Integration function to replace the existing calculate_duration_for_task
def calculate_duration_for_task(task_title: str, task_content: str = "") -> int:
    """
    Main function to calculate task duration using Gemini LLM
    This replaces the existing keyword-based approach
    """
    # First try with Gemini
    duration = calculate_duration_with_gemini(task_title, task_content)
    
    # If Gemini fails, you can still fall back to the original method
    if duration == 7 and (not task_title or not task_content):
        # Fallback to original keyword-based method if needed
        return calculate_duration_fallback(task_title, task_content)
    
    return duration
    
# === END: GEMINI DURATION ESTIMATION FUNCTIONS ===


@app.route('/generate_gantt_chart', methods=['POST'])
def create_gantt_chart():
    """Create a Gantt chart based on the notes with deadlines"""
    print("=== BASIC GANTT CHART CREATION STARTED ===")
    
    if 'team_id' not in session:
        print("ERROR: No team_id in session")
        return jsonify({"error": "No team selected"}), 400
    
    team_id = session['team_id']
    print(f"Team ID: {team_id}")
    
    try:
        # Get all notes for the team that have deadlines
        print("Querying notes with deadlines...")
        notes = Note.query.filter_by(team_id=team_id).filter(Note.deadline != None).all()
        print(f"Found {len(notes)} notes with deadlines")
        
        if not notes or len(notes) == 0:
            print("ERROR: No notes with deadlines found")
            return jsonify({"error": "No notes with deadlines found"}), 404
        
        today = datetime.now()
        print(f"Today's date: {today}")
        
        # Prepare tasks data for Gantt chart
        tasks_data = []
        print("Processing notes for Gantt chart...")
        
        for i, note in enumerate(notes):
            print(f"Processing note {i+1}: '{note.title}'")
            print(f"  - Deadline: {note.deadline}")
            print(f"  - Category: {note.category.name if note.category else 'None'}")
            
            # Get note category name
            category_name = note.category.name if note.category else "Uncategorized"
            
            # If deadline is in the past, set start date to ensure at least 1-day duration
            if note.deadline < today:
                # For past deadlines, make it a 1-day task ending today
                start_date = today - timedelta(days=1)
                finish_date = today
                print(f"  - Deadline in past, creating 1-day task ending today")
            else:
                # Calculate start date based on complexity (estimated duration before deadline)
                # THIS IS THE LINE THAT USES THE NEW GEMINI-POWERED FUNCTION
                duration_days = calculate_duration_for_task(note.title, note.content)
                print(f"  - Estimated duration: {duration_days} days")
                start_date = note.deadline - timedelta(days=duration_days)
                finish_date = note.deadline
                print(f"  - Calculated start date: {start_date}")
                
                # If calculated start date is in the past, adjust to ensure at least 1-day duration
                if start_date < today:
                    start_date = today
                    # Ensure minimum 1-day duration
                    if finish_date <= start_date:
                        finish_date = start_date + timedelta(days=1)
                    print(f"  - Adjusted start date to today with minimum 1-day duration")
            
            task_data = {
                "Task": note.title,
                "Start": start_date.strftime("%d.%m.%Y"),
                "Finish": finish_date.strftime("%d.%m.%Y"),
                "Section": category_name
            }
            tasks_data.append(task_data)
            print(f"  - Task data: {task_data}")
        
        print(f"Total tasks prepared: {len(tasks_data)}")
        print("Starting Gantt chart generation...")
        
        # Generate the Gantt chart
        gantt_image_base64 = generate_gantt_chart(tasks_data)
        print(f"Gantt chart generated successfully. Image size: {len(gantt_image_base64)} characters")
        
        result = {
            "success": True,
            "message": "Gantt chart generated successfully",
            "gantt_chart": gantt_image_base64,
            "tasks_count": len(tasks_data)
        }
        print("=== BASIC GANTT CHART CREATION COMPLETED ===")
        return jsonify(result)
        
    except Exception as e:
        print(f"ERROR in create_gantt_chart: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        app.logger.error(f"Error generating Gantt chart: {str(e)}")
        return jsonify({"error": str(e)}), 500

# COPY AND PASTE THIS UPDATED FUNCTION

@app.route('/ai_generate_gantt_chart', methods=['POST'])
def ai_generate_gantt_chart():
    """Enhanced AI Gantt chart generation with task analysis and categorization"""
    print("=== AI GANTT CHART CREATION STARTED ===")
    
    if 'team_id' not in session:
        print("ERROR: No team_id in session")
        return jsonify({"error": "No team selected"}), 400
    
    team_id = session['team_id']
    print(f"Team ID: {team_id}")
    
    try:
        # Step 1: Collect all tasks (not just those with deadlines)
        print("Step 1: Collecting all notes...")
        all_notes = Note.query.filter_by(team_id=team_id).all()
        print(f"Found {len(all_notes)} total notes")
        
        if not all_notes:
            print("ERROR: No notes found")
            return jsonify({"error": "No notes found to generate a schedule."}), 404
        
        # Step 2: Use Gemini to estimate duration for each task
        print("Step 2: Preparing task data and estimating durations with Gemini...")
        tasks_data = []
        for i, note in enumerate(all_notes, 1):
            # FIXED: Call Gemini-powered function to estimate duration for EVERY task
            estimated_duration = calculate_duration_for_task(note.title, note.content)
            
            task_info = {
                'id': note.id,
                'number': i,
                'title': note.title,
                'content': note.content,
                'deadline': note.deadline.strftime('%Y-%m-%d') if note.deadline else None,
                'category': note.category.name if note.category else None,
                'estimated_duration_days': estimated_duration  # NEW: Add Gemini's estimate
            }
            tasks_data.append(task_info)
            print(f"  > Task '{note.title}' - Gemini Estimated Duration: {estimated_duration} days")
        
        print(f"Prepared and enriched {len(tasks_data)} tasks for AI scheduling")
        
        # Step 3: Send to GPT-4 for intelligent scheduling
        print("Step 3: Sending to GPT-4 for schedule generation...")
        schedule_data = ai_generate_enhanced_schedule(tasks_data)
        
        if not schedule_data or 'tasks' not in schedule_data or not schedule_data['tasks']:
            print("ERROR: Failed to generate schedule data from AI. The AI might have returned an empty or invalid response.")
            return jsonify({"error": "AI failed to generate a valid schedule. Please try again."}), 500
        
        print(f"AI returned {len(schedule_data['tasks'])} scheduled tasks")
        
        # Step 4: Generate Gantt chart from the AI-created schedule
        print("Step 4: Generating Gantt chart visualization...")
        gantt_image_base64 = generate_gantt_chart(schedule_data['tasks'])
        print(f"AI Gantt chart generated successfully.")
        
        result = {
            "success": True,
            "message": "AI-Optimized schedule generated successfully!",
            "gantt_chart": gantt_image_base64,
            "tasks": schedule_data['tasks'],
            "tasks_count": len(schedule_data['tasks'])
        }
        print("=== AI GANTT CHART CREATION COMPLETED ===")
        return jsonify(result)
        
    except Exception as e:
        print(f"ERROR in ai_generate_gantt_chart: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        app.logger.error(f"Error in enhanced AI Gantt chart generation: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# COPY AND PASTE THIS UPDATED FUNCTION

def ai_generate_enhanced_schedule(tasks_data):
    """Use GPT-4 to generate an intelligent schedule based on tasks with pre-estimated durations."""
    print("=== GPT-4 SCHEDULE GENERATION STARTED ===")
    
    try:
        # FIXED: Use environment variable for API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found")
        client = OpenAI(api_key=api_key)

        # Prepare task information for LLM, now including the duration from Gemini
        print("Preparing task information for GPT-4 prompt...")
        tasks_text = ""
        for task in tasks_data:
            deadline_info = f", Deadline: {task['deadline']}" if task['deadline'] else ", No strict deadline"
            category_info = f", Category: {task['category']}" if task['category'] else ""
            # FIXED: Pass the Gemini-estimated duration to the prompt
            duration_info = f", Estimated Duration: {task['estimated_duration_days']} days"
            
            tasks_text += f"- Task {task['number']}: {task['title']}{duration_info}{deadline_info}{category_info}\n"
            tasks_text += f"  Content: {task['content']}\n"
        
        current_date = datetime.now().strftime("%d.%m.%Y")
        print(f"Current date for AI: {current_date}")
        
        # FIXED: New, more robust prompt asking for a JSON object
        prompt = f"""
        You are an expert project manager. Your job is to create a realistic project schedule based on the following tasks.

        Current Date: {current_date}

        TASKS:
        {tasks_text}

        INSTRUCTIONS:
        1. For each task, you are given an "Estimated Duration". Use this duration to calculate the schedule.
        2. Determine a logical "Start" and "Finish" date for EVERY task. The Finish date should be the Start date plus the duration.
        3. You MUST respect hard "Deadline" dates. The "Finish" date for a task cannot be after its deadline. Adjust its "Start" date accordingly to meet the deadline.
        4. For tasks without a deadline, sequence them logically. Consider potential dependencies (e.g., a "debugging" task should come after a "coding" task).
        5. Assign a "Section" (category) for each task. Use the provided category if available, otherwise infer a suitable one from: 'Research', 'Development', 'Management', 'Administrative', 'General'.

        CRITICAL: Your entire response must be a single, valid JSON object. The root of the object must have a key "tasks" which contains a list of the scheduled task objects.

        EXAMPLE JSON STRUCTURE:
        {{
          "tasks": [
            {{
              "Task": "Task name",
              "Start": "DD.MM.YYYY",
              "Finish": "DD.MM.YYYY",
              "Section": "Category Name"
            }}
          ]
        }}

        REQUIREMENTS:
        - The schedule must include ALL {len(tasks_data)} tasks.
        - Use "DD.MM.YYYY" format for all dates.
        - All "Start" dates must be on or after the current date.
        - Do not include any text, explanations, or code formatting like ```json before or after the JSON object.
        """
        
        print("Sending request to OpenAI GPT-4...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},  # Enforce JSON output
            messages=[
                {"role": "system", "content": "You are a project scheduling expert. You will respond ONLY with a valid JSON object containing a 'tasks' list."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2  # Lower temperature for more deterministic scheduling
        )
        
        # FIXED: Robust JSON parsing
        response_text = response.choices[0].message.content
        print("Received response from OpenAI. Parsing JSON...")
        schedule_result = json.loads(response_text)
        
        if 'tasks' in schedule_result and isinstance(schedule_result['tasks'], list):
            print(f"Successfully parsed {len(schedule_result['tasks'])} tasks from AI response.")
            print("=== GPT-4 SCHEDULE GENERATION COMPLETED ===")
            return schedule_result
        else:
            print("ERROR: AI response was valid JSON but missing the 'tasks' list.")
            return create_enhanced_fallback_schedule(tasks_data)

    except Exception as e:
        print(f"ERROR in ai_generate_enhanced_schedule: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        print("Falling back to enhanced local scheduling...")
        return create_enhanced_fallback_schedule(tasks_data)


def generate_gantt_chart(tasks_data):
    """Generate a Gantt chart from task data"""
    print("=== GANTT CHART VISUALIZATION STARTED ===")
    print(f"Generating chart for {len(tasks_data)} tasks")
    
    # Wrap the text of the task names
    def wrap_labels(labels, width=40):
        return [textwrap.fill(label, width) for label in labels]

    try:
        # Convert to DataFrame and prepare dates
        print("Creating DataFrame and processing dates...")
        df = pd.DataFrame(tasks_data)
        print(f"DataFrame shape: {df.shape}")
        print(f"DataFrame columns: {df.columns.tolist()}")
        
        df['Start'] = pd.to_datetime(df['Start'], dayfirst=True)
        df['Finish'] = pd.to_datetime(df['Finish'], dayfirst=True)
        df = df.sort_values(by='Start').reset_index(drop=True)  # Sort tasks by start date
        df['Task'] = wrap_labels(df['Task'])
        df['Duration'] = df['Finish'] - df['Start']
        
        print("Date processing completed")

        # Prepare plotting
        print("Preparing matplotlib plot...")
        fig, ax = plt.subplots(figsize=(15, 8))  # Adjusted figure size for longer x-axis
        
        # Generate colors for sections dynamically
        unique_sections = df['Section'].unique()
        print(f"Unique sections: {unique_sections}")
        colors = {}
        color_options = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan']
        
        for i, section in enumerate(unique_sections):
            colors[section] = color_options[i % len(color_options)]
        
        print(f"Color mapping: {colors}")

        # Plot each task with adjusted bar height
        print("Plotting tasks...")
        bar_height = 0.4  # Slimmer bars
        for i, task in df.iterrows():
            start_date = mdates.date2num(task['Start'])
            end_date = mdates.date2num(task['Finish'])
            ax.barh(task['Task'], end_date - start_date, left=start_date, height=bar_height,
                    color=colors[task['Section']], edgecolor='black')
            # Add horizontal guide lines
            ax.hlines(y=task['Task'], xmin=mdates.date2num(df['Start'].min()), xmax=start_date, 
                     colors='gray', linestyles='--', linewidth=0.7)
            # Add duration text
            duration_text = f"{task['Duration'].days} days"
            ax.text(end_date + 1, i, duration_text, va='center', ha='left', fontsize=10)

        print("Task plotting completed")

        # Invert y-axis to start from top
        ax.invert_yaxis()

        # Format x-axis as date and set limits to include all dates
        ax.xaxis_date()
        plt.xlim([mdates.date2num(df['Start'].min()), mdates.date2num(df['Finish'].max()) + 15])  # Add padding for duration text

        # Set font sizes
        title_fontsize = 16
        axislabel_fontsize = 14
        ticklabel_fontsize = 10
        legend_fontsize = 12

        # Y-axis labels
        plt.yticks(rotation=0)

        # Rotate x-axis date labels for better readability
        plt.xticks(rotation=45)

        # Apply font sizes
        ax.set_title("Project Schedule", fontsize=title_fontsize)
        ax.set_xlabel("Dates", fontsize=axislabel_fontsize)
        ax.set_ylabel("Tasks", fontsize=axislabel_fontsize)
        ax.tick_params(axis='x', labelsize=ticklabel_fontsize)
        ax.tick_params(axis='y', labelsize=ticklabel_fontsize)

        # Add legend for sections in the top right corner
        legend_elements = [Patch(facecolor=colors[section], edgecolor='black', label=section) 
                          for section in df['Section'].unique()]
        ax.legend(handles=legend_elements, title="Categories", loc='upper right', fontsize=legend_fontsize)

        # Enabling vertical grid lines for better readability
        ax.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)  # Ensure grid lines are below the bars

        # Create secondary x-axis for weekdays on top
        secax = ax.secondary_xaxis('top')
        secax.xaxis.set_major_locator(mdates.DayLocator())
        secax.xaxis.set_major_formatter(mdates.DateFormatter('%a'))
        secax.tick_params(axis='x', labelsize=6)  # Smaller font size for weekdays

        # Highlight weekends
        min_date = df['Start'].min()
        max_date = df['Finish'].max()
        weekends = pd.date_range(start=min_date, end=max_date).to_pydatetime()
        for date in weekends:
            if date.weekday() >= 5:  # Saturday and Sunday
                ax.axvspan(mdates.date2num(date), mdates.date2num(date + pd.Timedelta(days=1)),
                          color='gray', alpha=0.2)

        plt.tight_layout()
        print("Chart formatting completed")
        
        # Save chart to a bytes buffer
        print("Saving chart to buffer...")
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=120)
        buffer.seek(0)
        plt.close(fig)  # Close the figure to free memory
        
        # Encode as base64 for embedding in HTML
        print("Encoding to base64...")
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        print(f"Chart generation completed. Final image size: {len(img_str)} characters")
        print("=== GANTT CHART VISUALIZATION COMPLETED ===")
        return img_str
        
    except Exception as e:
        print(f"ERROR in generate_gantt_chart: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise e

def create_enhanced_fallback_schedule(tasks_data):
    """Enhanced fallback when AI fails"""
    tasks = []
    current_date = datetime.now()
    
    # Process tasks with deadlines first
    tasks_with_deadlines = [t for t in tasks_data if t['has_deadline']]
    tasks_without_deadlines = [t for t in tasks_data if not t['has_deadline']]
    
    # Sort by deadline
    tasks_with_deadlines.sort(key=lambda x: datetime.strptime(x['deadline'], '%Y-%m-%d'))
    
    # Handle tasks with deadlines
    for task in tasks_with_deadlines:
        deadline = datetime.strptime(task['deadline'], '%Y-%m-%d')
        duration = estimate_task_duration(task['title'], task['content'])
        start_date = deadline - timedelta(days=duration)
        
        if start_date < current_date:
            start_date = current_date
        
        section = task['category'] if task['is_categorized'] else categorize_task_simple(task['title'], task['content'])
        
        tasks.append({
            "Task": task['title'],
            "Start": start_date.strftime("%d.%m.%Y"),
            "Finish": deadline.strftime("%d.%m.%Y"),
            "Section": section
        })
    
    # Handle tasks without deadlines
    next_start_date = current_date
    for task in tasks_without_deadlines:
        duration = estimate_task_duration(task['title'], task['content'])
        finish_date = next_start_date + timedelta(days=duration)
        
        section = task['category'] if task['is_categorized'] else categorize_task_simple(task['title'], task['content'])
        
        tasks.append({
            "Task": task['title'],
            "Start": next_start_date.strftime("%d.%m.%Y"),
            "Finish": finish_date.strftime("%d.%m.%Y"),
            "Section": section
        })
        
        next_start_date = finish_date
    
    return {"tasks": tasks}

def estimate_task_duration(title, content):
    """Estimate task duration based on complexity"""
    text = (title + ' ' + content).lower()
    
    duration_map = {
        'simple': 2, 'quick': 1, 'easy': 2,
        'complex': 10, 'difficult': 12, 'research': 7,
        'develop': 8, 'create': 6, 'implement': 8,
        'test': 4, 'document': 4, 'meeting': 1,
        'review': 3
    }
    
    estimated_duration = 5  # Default
    
    for indicator, days in duration_map.items():
        if indicator in text:
            estimated_duration = max(estimated_duration, days)
    
    return min(estimated_duration, 20)  # Cap at 20 days

def categorize_task_simple(title, content):
    """Simple task categorization"""
    text = (title + ' ' + content).lower()
    
    if any(word in text for word in ['research', 'paper', 'publication', 'academic']):
        return 'Research & Publications'
    elif any(word in text for word in ['software', 'coding', 'debug', 'install', 'platform']):
        return 'Software Development'
    elif any(word in text for word in ['meeting', 'team', 'collaboration', 'engagement']):
        return 'Team Management'
    elif any(word in text for word in ['training', 'lab', 'education', 'session']):
        return 'Training & Education'
    elif any(word in text for word in ['timesheet', 'report', 'status', 'control']):
        return 'Administrative'
    else:
        return 'General'
# PASTE THIS NEW HELPER FUNCTION AT THE END OF YOUR FILE

def get_project_context_for_chatbot(team_id):
    """Gathers all notes and categories for the team to provide context to the chatbot."""
    notes = Note.query.filter_by(team_id=team_id).order_by(Note.created_at.desc()).all()
    
    if not notes:
        return "The project is currently empty. There are no notes or tasks."

    context = "Here is a summary of the current project tasks and notes:\n\n"
    for note in notes:
        deadline_str = f" (Deadline: {note.deadline.strftime('%Y-%m-%d')})" if note.deadline else ""
        category_str = f" [Category: {note.category.name}]" if note.category else ""
        
        context += f"- Task: {note.title}{deadline_str}{category_str}\n"
        context += f"  - Details: {note.content.strip()}\n\n"
        
    return context

# COPY AND PASTE THIS ENTIRE UPDATED FUNCTION TO REPLACE THE OLD ONE

@app.route('/ask_chatbot', methods=['POST'])
def ask_chatbot():
    """
    Handles requests from the chatbot interface.
    Dynamically uses Gemini or OpenAI based on the CHATBOT_MODEL environment variable.
    """
    print("=== CHATBOT REQUEST RECEIVED ===")
    
    # Check if team_id is in session
    if 'team_id' not in session:
        print("ERROR: No team_id in session")
        return jsonify({"error": "No team selected. Please select a team first."}), 400

    # Get request data
    try:
        data = request.get_json()
        if not data:
            print("ERROR: No JSON data received")
            return jsonify({"error": "No data received"}), 400
        
        user_message = data.get('message')
        history = data.get('history', [])
        
        print(f"User message: {user_message}")
        print(f"History length: {len(history)}")
        
    except Exception as e:
        print(f"ERROR: Failed to parse request data: {str(e)}")
        return jsonify({"error": "Invalid request format"}), 400

    if not user_message:
        print("ERROR: No message provided")
        return jsonify({"error": "No message provided."}), 400

    try:
        team_id = session['team_id']
        print(f"Team ID: {team_id}")
        
        # Get project context
        project_context = get_project_context_for_chatbot(team_id)
        print(f"Project context length: {len(project_context)} characters")
        
        # Determine which AI model to use from environment variables
        model_choice = os.getenv('CHATBOT_MODEL', 'openai').lower()
        print(f"Using model: {model_choice}")

        bot_response = ""

        # --- GEMINI CHATBOT LOGIC ---
        if model_choice == 'gemini':
            print("Using Gemini model")
            model = setup_gemini_api()
            if not model:
                raise ValueError("Failed to setup Gemini API. Check GOOGLE_API_KEY.")

            system_prompt = f"""
            You are a helpful and concise project management assistant. Your knowledge is based on the following project data.
            Use ONLY this data to answer the user's questions. If the answer isn't in the data, state that you don't have that information.

            --- PROJECT CONTEXT ---
            {project_context}
            --- END OF CONTEXT ---
            """
            
            # Convert OpenAI-style history to Gemini's format
            gemini_history = []
            for item in history:
                gemini_history.append({'role': 'user', 'parts': [item['user']]})
                gemini_history.append({'role': 'model', 'parts': [item['bot']]})

            # Start a chat session with the system prompt and history
            chat_session = model.start_chat(
                history=gemini_history,
            )
            
            # Send the new message with the system prompt as context
            full_prompt = f"{system_prompt}\n\nUser Question: {user_message}"
            response = chat_session.send_message(full_prompt)
            bot_response = response.text

        # --- OPENAI CHATBOT LOGIC (DEFAULT) ---
        else:
            print("Using OpenAI model")
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
            
            client = OpenAI(api_key=api_key)

            system_prompt = f"""
            You are a helpful and concise project management assistant. 
            Your knowledge is based on the following project data. Use this data to answer the user's questions.
            If the answer isn't in the data, say you don't have that information.

            --- PROJECT CONTEXT ---
            {project_context}
            --- END OF CONTEXT ---
            """
            
            messages = [{"role": "system", "content": system_prompt}]
            for item in history:
                messages.append({"role": "user", "content": item['user']})
                messages.append({"role": "assistant", "content": item['bot']})
            messages.append({"role": "user", "content": user_message})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.5,
                max_tokens=250
            )
            bot_response = response.choices[0].message.content

        print(f"Bot response: {bot_response}")
        return jsonify({"response": bot_response})

    except ValueError as ve:
        print(f"Configuration ERROR: {str(ve)}")
        return jsonify({"error": "AI service configuration error. Please contact administrator."}), 500
    
    except Exception as e:
        print(f"ERROR in ask_chatbot: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500




if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(debug=True, host='0.0.0.0', port=5000)