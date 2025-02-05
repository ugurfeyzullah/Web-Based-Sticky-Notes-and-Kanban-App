# Kanban Notes & Task Management System with Chatbot Integration

![image](https://github.com/user-attachments/assets/c3f4f5d6-9aa2-4c12-bdac-19fd3a057eca)


## Table of Contents
- [Abstract](#abstract)
- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Abstract

This project is a Flask-based web application that combines a Kanban board with a note-taking and task management system. It includes user authentication, team-based access control, and integration with OpenAI for chatbot assistance. Users can create, update, and export notes and Kanban board data, as well as receive interactive guidance via the integrated chatbot. The system uses SQLAlchemy and Flask-Migrate for database management and supports dynamic team-key validation for team-specific access.

## Features

- **Kanban Board Management:**  
  Create and update Kanban boards with columns, deadlines, and container positions stored as JSON.

- **Notes & Sticky Notes:**  
  Save and export notes (with title, content, position, color, and deadline) for individual users and teams.

- **User Authentication:**  
  Secure signup, login, and account deletion with password hashing.

- **Team Key Validation:**  
  Validate team access using pre-defined team keys for controlled team-specific functionality.

- **Chatbot Integration:**  
  Interact with an OpenAI-powered chatbot to assist with planning and scheduling tasks.

- **Database Management:**  
  Use SQLAlchemy for ORM, with migrations managed by Flask-Migrate.  
  (Currently using SQLite; can be adapted for PostgreSQL if needed.)


https://github.com/user-attachments/assets/0f622b3f-1d76-42d7-a569-f34f20ca9228


## Installation

### Prerequisites

- **Python 3.9** (or later)
- A web browser to access the application

**Software Requirements:**

- **Flask** and related packages (see below)
- **Graphviz** (if you plan to generate diagrams; ensure it’s installed and accessible)
- **SMTP Email Account** (if email functionality is needed)
- **SQLite** (default database; no extra installation needed)  
  *(For PostgreSQL, ensure you have the appropriate database driver installed.)*

### Setup

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/kanban-notes-app.git
    cd kanban-notes-app
    ```
2. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Configure Environment Variables:**  
   Create a `.env` file (or set system environment variables) to store sensitive information. For example:
    ```
    SECRET_KEY=your_secret_key
    SQLALCHEMY_DATABASE_URI=sqlite:///users.db
    OPENAI_API_KEY=your_openai_api_key
    ```
4. **Set Up the Database:**  
   Initialize and run migrations using Flask-Migrate:
    ```bash
    flask db init
    flask db migrate -m "Initial migration."
    flask db upgrade
    ```
5. **Run the Application:**
    ```bash
    flask run
    ```
   The application will be available at `http://localhost:5000/`.

## Usage

- **Home Page:**  
  When you visit the home page, you’ll see a landing page (or a team selection page) where you can choose your team.  
  If a team key is required, you will be prompted to enter the key before accessing team-specific data.

- **Kanban Board & Notes:**  
  Use the provided interfaces to:
  - Create and update Kanban boards.
  - Add, edit, and delete sticky notes.
  - Save and export board and note data.
  - Adjust note positions, colors, and deadlines.
  
- **Chatbot:**  
  The integrated chatbot (powered by OpenAI) is available for assistance with planning, scheduling, and formatting inputs. Simply type your message in the chat window, and the bot will respond with helpful suggestions.

- **User Management:**  
  Sign up, log in, and delete your account via the provided forms. User sessions and team access are managed through Flask sessions.

- **Admin & Team Key Validation:**  
  Admins can view all users, and team keys are used to restrict access to team-specific boards and notes.


## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create your feature branch:
    ```bash
    git checkout -b feature/YourFeature
    ```
3. Commit your changes:
    ```bash
    git commit -am 'Add some feature'
    ```
4. Push to the branch:
    ```bash
    git push origin feature/YourFeature
    ```
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

- **Feyzullah Yavan**  
  Email: [feyzullah.yavan@kit.edu](mailto:feyzullah.yavan@kit.edu)  
  LinkedIn: [https://www.linkedin.com/in/ugurfey](https://www.linkedin.com/in/ugurfey)
  Website: https://kitdec2.pythonanywhere.com/


