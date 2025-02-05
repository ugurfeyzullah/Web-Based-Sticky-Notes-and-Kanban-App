// Function to toggle theme
function toggleTheme() {
    document.body.classList.toggle('light-theme');
    if (document.body.classList.contains('light-theme')) {
        localStorage.setItem('theme', 'light');
    } else {
        localStorage.setItem('theme', 'dark');
    }
}

// Function to toggle the chatbot window visibility
function toggleChatbot() {
    var chatbotWindow = document.getElementById('chatbotWindow');
    // Toggle the chatbot window visibility
    if (chatbotWindow.style.display === 'none' || chatbotWindow.style.display === '') {
        chatbotWindow.style.display = 'block';
        // Save the state as open
        localStorage.setItem('chatbotState', 'open');
    } else {
        chatbotWindow.style.display = 'none';
        // Save the state as closed
        localStorage.setItem('chatbotState', 'closed');
    }
}

// Function to set the initial state of the chatbot based on localStorage
function setInitialChatbotState() {
    var chatbotWindow = document.getElementById('chatbotWindow');
    // Get the chatbot state from localStorage
    var chatbotState = localStorage.getItem('chatbotState');

    // If the state is 'open', display the chatbot; otherwise, hide it
    if (chatbotState === 'open') {
        chatbotWindow.style.display = 'block';
    } else {
        chatbotWindow.style.display = 'none';
    }
}

// Set the initial state when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    setInitialChatbotState();
});

function deleteStickyNote(noteId) {
    const note = document.getElementById(noteId);
    if (note) {
        note.remove();
    } else {
        fetch('/delete_note', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ noteId: noteId.replace('note', '') })  // Assuming your note IDs are prefixed with 'note'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Received team ID:', data.team_id);  // Use the JSON data here
            window.location.href = `/team/${data.team_id}`;
            if (data.error) {
                console.error('Failed to delete note:', data.error);
            } else {
                console.log('Successfully deleted note:', data.message);
                note.remove(); // Remove the note element from the DOM
            }
        })
        .catch(error => console.error('Error sending delete request:', error));
    }
}

// Function to update authentication display
function updateAuthDisplay(username) {
    const authContainer = document.getElementById('authContainer');
    if (username) {
        authContainer.innerHTML = `
            <details class="dropdown">
                <summary role="usermenu">
                    <a class="usermenu">${username}</a>
                </summary>
                <ul>
                    <li><a href="#">As in...</a></li>
                    <li><a href="/delete_user">Delete Account</a></li>
                </ul>
            </details>
            <button class="signup-button" onclick="location.href='/logout'">Log out</button>
        `;
    } else {
        authContainer.innerHTML = `
            <button id="loginBtn" class="login-button">Login</button>
            <button id="signupBtn" class="signup-button">Sign Up</button>
        `;
        addModalEventListeners();
    }
}

// Function to add event listeners to login and signup buttons
function addModalEventListeners() {
    var loginModal = document.getElementById('loginModal');
    var signupModal = document.getElementById('signupModal');
    var closeBtns = document.getElementsByClassName('close');

    // Event listeners for opening the modals
    document.querySelector('.login-button').onclick = function() {
        loginModal.style.display = "block";
    };
    document.querySelector('.signup-button').onclick = function() {
        signupModal.style.display = "block";
    };

    // Event listener for closing the modals
    for (var i = 0; i < closeBtns.length; i++) {
        closeBtns[i].onclick = function() {
            this.parentElement.parentElement.style.display = "none";
        };
    }

    // Close the modal if clicked outside
    window.onclick = function(event) {
        if (event.target === loginModal || event.target === signupModal) {
            event.target.style.display = "none";
        }
    };
}

// Function to handle signup form submission
function handleSignupFormSubmission() {
    var signupForm = document.getElementById('signupForm');
    signupForm.onsubmit = function(e) {
        e.preventDefault(); 
        var formData = {
            newUsername: document.getElementsByName('newUsername')[0].value,
            email: document.getElementsByName('email')[0].value,
            newPassword: document.getElementsByName('newPassword')[0].value
        };

        fetch('/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            alert(data.success ? 'Sign up successful. Check your email!' : 'Signup failed: ' + data.error);
            signupModal.style.display = data.success ? 'none' : 'block';
        });
    };
}

// Function to handle login form submission
function handleLoginFormSubmission() {
    var loginForm = document.getElementById('loginForm');
    loginForm.onsubmit = function(e) {
        e.preventDefault();
        var loginData = {
            username: document.getElementsByName('username')[0].value,
            password: document.getElementsByName('password')[0].value
        };

        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(loginData)
        })
        .then(response => response.json())
        .then(data => {
            alert(data.success ? 'Login successful!' : 'Login failed: ' + data.error);
            if (data.success) {
                loginModal.style.display = 'none';
                updateAuthDisplay(data.username);
            }
        });
    };
}

// Function to handle DOMContentLoaded event
function onDOMContentLoaded() {
    addModalEventListeners();
    handleSignupFormSubmission();
    handleLoginFormSubmission();
    updateAuthDisplay(loggedInUsername);
    loadNotesFromLocalStorage();
}

// Event listener for DOMContentLoaded
document.addEventListener('DOMContentLoaded', onDOMContentLoaded);

function hidePlaceholder(element) {
    if (element.innerText === "Click and type here!") {
        element.innerText = "";
    }
}

function loadNotesFromLocalStorage() {
    const savedNotes = localStorage.getItem("stickyNotes");
    if (savedNotes) {
        const notesArray = JSON.parse(savedNotes);
        notesArray.forEach(note => {
            const container = document.getElementById("container");
            const newNote = document.createElement("div");
            newNote.className = "note";
            newNote.id = note.id;
            newNote.innerHTML = `
                <div class="title" contenteditable="true" onclick="hidePlaceholder(this)">${note.title}</div>
                <div class="content" contenteditable="true">${note.content}</div>
                <input type="color" class="color-picker" onchange="changeNoteColor('${note.id}', this.value)" value="${note.color}">
                <div class="header">
                    <button class="delete" onclick="deleteStickyNote('${note.id}')" contenteditable="false">Delete ${note.id}</button>
                </div>
            `;
            newNote.style.top = note.top;
            newNote.style.left = note.left;
            newNote.style.backgroundColor = note.color; // Set background color
            newNote.addEventListener("mousedown", startDrag);
            container.appendChild(newNote);
        });
    }
}
function changeNoteColor(noteId, color) {
    console.log('Changing color for noteId:', noteId, 'to color:', color);
    const note = document.getElementById(noteId);
    if (note) {
        note.style.backgroundColor = color;
    } else {
        console.error('Failed to find note with ID:', noteId);
    }
}

// Function to export notes to Flask
function exportNotes() {
    const notes = document.getElementsByClassName("note");
    const allNotesData = [];

    for (const note of notes) {
        const title = note.querySelector(".title").innerText;
        const content = note.querySelector(".content").innerText;
        const color = note.querySelector(".color-picker").value;
        const position_x = note.style.left.replace('px', '');
        const position_y = note.style.top.replace('px', '');
        allNotesData.push({ title, content, color, position_x, position_y });
    }

    // Send the notes data to Flask
    sendNotesToFlask(allNotesData);
}

// Function to send notes data to Flask
function sendNotesToFlask(notesData) {
    // Make an AJAX request to your Flask server
    fetch('/export_notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            notesData: notesData,
        }),
    })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));
}

// // Function to save notes to a database
// function saveNotesToDatabase() {
//     const notes = document.getElementsByClassName("note");
//     console.log('Notes:', notes);
//     const notesData = Array.from(notes).map(note => ({
//         id: note.id,
//         title: note.querySelector(".title").innerText,
//         content: note.querySelector(".content").innerText,
//         deadline: note.querySelector(".deadline").value,
//         top: note.style.top,
//         left: note.style.left,
//         color: note.querySelector(".color-picker").value
//     }));

//     fetch('/save_note', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({ notes: notesData })
//     })
//     .then(response => response.json())
//     .then(data => console.log('Notes saved to database:', data))
//     .catch(error => console.error('Error saving notes to database:', error));
// }

function collectNotesData() {
    const notes = document.getElementsByClassName("note");
    console.log('Notes collect:', notes);
    const notesData = Array.from(notes).map(note => {
        // Fetch the deadline input correctly assuming it's the first input within .deadline-section
        const deadlineInput = note.querySelector(".deadline-section input[type='datetime-local']");
        const deadlineValue = deadlineInput ? deadlineInput.value : null;

        console.log('Collecting deadline for note:', note.id, 'Value:', deadlineValue);

        return {
            id: note.id,
            title: note.querySelector(".title").innerText,
            content: note.querySelector(".content").innerText,
            deadline: deadlineValue,
            color: note.querySelector(".color-picker").value,
            top: note.style.top,
            left: note.style.left
        };
    });
    return notesData;
}



function loadNotesFromServer() {
    console.log('Loading notes from server');
    fetch('/api/notes')
    .then(response => response.json())
    .then(notes => {
        const container = document.getElementById('container');
        container.innerHTML = ''; // Clear previous notes
        notes.forEach(note => {
            console.log('Creating note:', note);
            createNoteOnPage(note); // This function now also handles deadlines
        });
    })
    .catch(error => console.error('Error loading notes:', error));
}



async function sendNotesToServer() {
    let kanbanData = null; // Initialize as null

    // Check if the Kanban board exists in the DOM
    if (document.querySelector('.kanban-label')) {
        kanbanData = collectKanbanBoardData(); // Collect data only if the board exists
        try {
            const kanbanResponse = await fetch('/save_kanban', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({kanbanBoard: kanbanData})
            });

            if (!kanbanResponse.ok) {
                throw new Error(`HTTP error! Status: ${kanbanResponse.status}`);
            }
        } catch (error) {
            console.error('Error saving Kanban board:', error);
            return; // Stop execution if the Kanban save fails
        }
    }

    const notesData = collectNotesData();
    console.log("notesData", notesData);
    console.log("kanbanData", kanbanData);

    try {
        const notesResponse = await fetch('/save_notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes: notesData })
        });

        if (!notesResponse.ok) {
            throw new Error(`HTTP error! Status: ${notesResponse.status}`);
        }
    } catch (error) {
        console.error('Error saving notes:', error);
    }
}


function changeDeadline(noteId, newDeadline) {
    console.log('noteId received:', noteId);

    const note = document.getElementById(noteId);
    console.log('Element found:', note);

    note.querySelector(".deadline").value = newDeadline;
    console.log('Changing deadline for note:', noteId, 'To:', newDeadline);

}

function resetNotes() {
    console.log('Resetting notes');
    fetch('/reset_notes', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => console.log('Reset response:', data))
    .catch(error => console.error('Error resetting notes:', error));


    const container = document.getElementById("container");
    container.innerHTML = "";
    noteId = 0;
    localStorage.removeItem("stickyNotes");
}







function collectKanbanBoardData() {
    const boardTitle = document.querySelector('.board-title').innerText; // Get the current board title text
    const boardDeadline = document.querySelector('.board-deadline').innerText; // Get the current board deadline text
    const container = document.getElementById('container'); // Get the Kanban board container
    const columns = document.querySelectorAll('.kanban-column'); // Select all columns

    // Gather container position using getBoundingClientRect
    const rect = container.getBoundingClientRect();
    const containerPosition = {
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height
    };
    // Map over each column and extract the height
    const boardData = Array.from(columns).map(column => {
        const columnHeight = column.offsetHeight; // Gets the height of the column in pixels

        return {
            columnHeight: columnHeight
        };
    });

    return {
        title: boardTitle,
        deadline: boardDeadline,
        containerPosition: containerPosition,
        columns: boardData
    };
}


function loadKanbanFromServer() {
    fetch('/api/kanban')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("Received Kanban data:", data);  // Log the entire response data
        if (data && data[0]) {
            // Initialize containerPosition and columns with defaults to avoid undefined errors
            let containerPosition = {};
            let columns = [];

            try {
                containerPosition = data[0].containerPosition ? JSON.parse(data[0].containerPosition) : {};
                columns = data[0].columns ? JSON.parse(data[0].columns) : [];
            } catch (error) {
                console.error('Error parsing JSON from Kanban data:', error);
            }

            // Pass the parsed or default data to create the Kanban board
            const kanbanData = {
                ...data[0],
                containerPosition,
                columns
            };
            createKanbanBoardfromdb(kanbanData);
            console.log('Kanban board created:', kanbanData);
        } else {
            console.error('No Kanban board data received');
        }
    })
    .catch(error => console.error('Error loading Kanban board:', error));
}

function createKanbanBoardfromdb(kanbanData) {
    const containerkanban = document.getElementById('containerkanban');
    const columns = ["Backlog", "To do", "In progress", "Testing", "Done"];
    const colors = ["red", "orange", "yellow", "green", "blue"]; // Predefined colors
    containerkanban.innerHTML = '';  // Clear previous contents

    const board = document.createElement('div');
    board.className = 'kanban-board';
    board.style.position = 'absolute';
    board.style.top = `${kanbanData.containerPosition.top || 0}px`;
    board.style.left = `${kanbanData.containerPosition.left || 0}px`;
    board.style.width = `${kanbanData.containerPosition.width || 1000}px`; // Set to total width
    board.style.height = `${kanbanData.containerPosition.height || 500}px`; // Set to total height

    // Set board title and deadline
    const boardTitle = document.createElement('div');
    boardTitle.className = "board-title";
    boardTitle.innerText = kanbanData.title || 'No Title';
    board.appendChild(boardTitle);

    const boardDeadline = document.createElement('div');
    boardDeadline.className = "board-deadline";
    boardDeadline.innerText = `Deadline: ${kanbanData.deadline || 'No Deadline'}`;
    board.appendChild(boardDeadline);

    // Calculate column width based on the board width and number of columns
    const columnWidth = parseInt(board.style.width) / columns.length;

    kanbanData.columns.forEach((col, index) => {
        const column = document.createElement('div');
        column.className = `kanban-column ${colors[index % colors.length]}`;
        column.style.height = `${col.columnHeight || 100}px`;
        column.style.width = `${columnWidth}px`;  // Distribute width evenly
        column.style.position = 'absolute';
        column.style.left = `${index * columnWidth}px`;  // Position columns side by side

        const columnLabel = document.createElement('div');
        columnLabel.className = "column-label";
        columnLabel.innerText = columns[index];
        column.appendChild(columnLabel);

        board.appendChild(column);
    });

    containerkanban.appendChild(board);
}
