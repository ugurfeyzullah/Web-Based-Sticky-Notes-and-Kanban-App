# Interactive Planning V3 - Enhanced Kanban Notes & Task Management System

A comprehensive Flask-based web application that combines Kanban board functionality with intelligent task management, featuring AI-powered assistance, Gantt chart generation, and advanced project planning capabilities.

![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v2.3+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🚀 Features

### Core Functionality
- **Interactive Kanban Board**: Create, update, and manage tasks with drag-and-drop functionality
- **Smart Sticky Notes**: Color-coded notes with position tracking and deadline management
- **User Authentication**: Secure signup, login, and team-based access control
- **Team Management**: Multi-team support with team key validation
- **Database Management**: SQLAlchemy ORM with Flask-Migrate for database versioning

### AI-Powered Features
- **OpenAI Integration**: Intelligent chatbot for project assistance and task guidance
- **Google Gemini AI**: Advanced duration estimation and task complexity analysis
- **AI Categorization**: Automatic task categorization with confidence scoring
- **Smart Scheduling**: AI-optimized project timeline generation

### Advanced Planning Tools
- **Gantt Chart Generation**: Visual project timelines with Matplotlib integration
- **Duration Estimation**: AI-powered task duration prediction using Gemini LLM
- **Project Analytics**: Task complexity analysis and risk assessment
- **Data Export**: Export notes and project data in various formats

### Enhanced UI/UX
- **Modern Interface**: Responsive design with intuitive navigation
- **Real-time Updates**: Dynamic content updates without page refresh
- **Customizable Themes**: Color-coded categories and personalized layouts
- **Interactive Elements**: Drag-and-drop, modal dialogs, and smooth animations

## 🛠️ Technology Stack

- **Backend**: Flask 2.3+, SQLAlchemy 2.0+, Flask-Migrate
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Database**: SQLite (development), PostgreSQL (production ready)
- **AI Integration**: OpenAI GPT-4, Google Gemini AI
- **Visualization**: Matplotlib, Pandas for data processing
- **Security**: Werkzeug, bcrypt password hashing
- **Authentication**: Flask-Session, secure session management

## 📋 Prerequisites

- Python 3.9 or higher
- pip package manager
- Git (for version control)
- Web browser (Chrome, Firefox, Safari, Edge)

### API Keys Required
- OpenAI API Key (for chatbot functionality)
- Google Gemini API Key (for duration estimation)

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ugurfeyzullah/Web-Based-Sticky-Notes-and-Kanban-App.git
cd Web-Based-Sticky-Notes-and-Kanban-App
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory:
```env
SECRET_KEY=your_secret_key_here
SQLALCHEMY_DATABASE_URI=sqlite:///users.db
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_gemini_api_key
CHATBOT_MODEL=openai  # or 'gemini'
FLASK_ENV=development
```

### 5. Database Setup
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Run the Application
```bash
python main.py
```

The application will be available at `http://localhost:5000`

## 📖 Usage Guide

### Getting Started
1. **Create Account**: Sign up with username, email, and password
2. **Team Selection**: Choose or create a team using team keys
3. **Add Tasks**: Create sticky notes with titles, content, and deadlines
4. **Organize**: Use categories and colors to organize your tasks

### AI Features
- **Chatbot**: Ask questions about your project and get intelligent responses
- **Duration Estimation**: Get AI-powered estimates for task completion times
- **Auto-Categorization**: Let AI automatically categorize your tasks
- **Smart Scheduling**: Generate optimized project timelines

### Gantt Charts
- **Basic Gantt**: Generate timeline charts from existing tasks
- **AI-Enhanced Gantt**: Use AI to create optimized project schedules
- **Export Options**: Save charts as PNG images

### Team Collaboration
- **Team Keys**: Secure team access with validation keys
- **Shared Boards**: Collaborate on the same Kanban board
- **User Management**: Admin features for user oversight

## 🏗️ Project Structure

```
InteractivePlanning_V3/
├── main.py                 # Main Flask application
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── LICENSE                # MIT License
├── migrations/            # Database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── script.py.mako
├── static/                # Static files (CSS, JS, images)
│   ├── styles.css
│   ├── scripts.js
│   ├── user.js
│   └── *.jpg
├── templates/             # HTML templates
│   ├── index.html
│   ├── home.html
│   ├── notes.html
│   └── *.html
└── instance/              # Instance-specific files
    └── users.db           # SQLite database
```

## 🔑 API Endpoints

### Authentication
- `POST /signup` - User registration
- `POST /login` - User authentication
- `GET /logout` - User logout
- `GET /delete_user` - Account deletion

### Notes & Tasks
- `GET /api/notes` - Get all notes for team
- `POST /api/notes` - Create new note
- `POST /delete_note` - Delete specific note
- `POST /reset_notes` - Clear all notes
- `POST /export_notes` - Export notes data

### AI Features
- `POST /ask_chatbot` - Chat with AI assistant
- `POST /categorize_notes` - AI categorization
- `POST /generate_gantt_chart` - Basic Gantt chart
- `POST /ai_generate_gantt_chart` - AI-optimized Gantt chart

### Categories
- `GET /api/categories` - Get all categories
- `POST /update_note_category` - Update note category
- `POST /clear_categories` - Clear all categories

## 🧪 Testing

### Manual Testing
1. Test user registration and login
2. Create and manage notes
3. Test AI features (chatbot, categorization)
4. Generate Gantt charts
5. Test team functionality

### API Testing
Use tools like Postman or curl to test API endpoints:
```bash
curl -X POST http://localhost:5000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "content": "Test content"}'
```

## 🚀 Deployment

### Production Setup
1. **Database**: Configure PostgreSQL or MySQL
2. **Environment**: Set production environment variables
3. **Security**: Use strong secret keys and HTTPS
4. **Monitoring**: Implement logging and error tracking

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "main.py"]
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/YourFeature`
3. **Make your changes**: Implement your feature or fix
4. **Write tests**: Ensure your code is tested
5. **Commit changes**: `git commit -am 'Add some feature'`
6. **Push to branch**: `git push origin feature/YourFeature`
7. **Submit a Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Write clear commit messages
- Document new features
- Test thoroughly before submitting

## 📝 Changelog

### Version 3.0.0 (Current)
- Added AI-powered duration estimation with Google Gemini
- Implemented intelligent task categorization
- Enhanced Gantt chart generation with AI optimization
- Added comprehensive chatbot with project context
- Improved UI/UX with modern design elements
- Enhanced security with bcrypt password hashing
- Added comprehensive database migrations

### Version 2.0.0
- Added basic Gantt chart functionality
- Implemented team-based access control
- Added note categorization system
- Enhanced user authentication

### Version 1.0.0
- Initial release with basic Kanban functionality
- User registration and authentication
- Basic note management

## 🐛 Known Issues

- Large datasets may cause performance issues in Gantt chart generation
- AI responses may vary in quality depending on API availability
- Mobile responsiveness needs improvement in some areas

## 🔮 Roadmap

- [ ] Mobile app development
- [ ] Real-time collaboration features
- [ ] Advanced analytics dashboard
- [ ] Integration with external calendar systems
- [ ] Multi-language support
- [ ] Advanced reporting features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Feyzullah Yavan**
- Email: feyzullah.yavan@kit.edu
- LinkedIn: [https://www.linkedin.com/in/ugurfey](https://www.linkedin.com/in/ugurfey)
- Website: [https://kitdec2.pythonanywhere.com/](https://kitdec2.pythonanywhere.com/)

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Google for Gemini AI API
- Flask community for excellent documentation
- All contributors and testers

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/ugurfeyzullah/Web-Based-Sticky-Notes-and-Kanban-App/issues) page
2. Create a new issue with detailed description
3. Contact the author via email
4. Check the documentation for common solutions

---

**Made with ❤️ by Feyzullah Yavan**
