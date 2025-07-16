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
        // If this note has a category, warn user that manual color change will override category color
        const categoryColor = note.dataset.categoryColor;
        if (categoryColor && color !== categoryColor) {
            console.log('Manual color change detected for categorized note');
            // Set manual override flag
            note.dataset.manualOverride = 'true';
        }
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
            color: note.dataset.categoryColor || note.querySelector(".color-picker").value, // Use category color if available
            top: note.style.top,
            left: note.style.left,
            category_id: note.dataset.categoryId || null,
            ai_tags: note.dataset.aiTags ? JSON.parse(note.dataset.aiTags) : [],
            ai_confidence: note.dataset.aiConfidence ? parseFloat(note.dataset.aiConfidence) : null,
            is_ai_categorized: note.dataset.isAiCategorized === 'true',
            manual_override: note.dataset.manualOverride === 'true'
        };
    });
    return notesData;
}

// =================================================================================
// ===== UPDATED FUNCTION: loadNotesFromServer (made async) ========================
// =================================================================================
async function loadNotesFromServer() {
    console.log('Loading notes from server');
    try {
        const response = await fetch('/api/notes');
        const notes = await response.json();
        const container = document.getElementById('container');
        container.innerHTML = ''; // Clear previous notes and headers
        
        // Group notes by category
        const categorizedNotes = groupNotesByCategory(notes);
        
        // Asynchronously position notes by category to prevent overlap
        await positionNotesByCategory(categorizedNotes);
        
        // Update note colors based on categories
        setTimeout(() => {
            updateNotesColorsByCategory();
        }, 100);
        
        // Add category indicators after notes are loaded
        setTimeout(() => {
            addCategoryIndicators();
        }, 150);
    } catch (error) {
        console.error('Error loading notes:', error);
    }
}

function createNoteOnPage(note) {
    const container = document.getElementById('container');
    const noteElement = document.createElement('div');
    noteElement.className = 'note sticky-note';
    noteElement.id = note.id;
    noteElement.style.position = 'absolute'; // Ensure position is absolute for top/left to work
    noteElement.style.top = note.top;
    noteElement.style.left = note.left;
    
    // FORCE category color if available, otherwise use note's original color
    const noteColor = note.category_color || note.color;
    noteElement.style.backgroundColor = noteColor;
    
    // Set category data attributes
    noteElement.dataset.categoryId = note.category_id || '';
    noteElement.dataset.categoryName = note.category_name || '';
    noteElement.dataset.categoryColor = note.category_color || '';
    noteElement.dataset.aiTags = JSON.stringify(note.ai_tags || []);
    noteElement.dataset.aiConfidence = note.ai_confidence || '';
    noteElement.dataset.isAiCategorized = note.is_ai_categorized || 'false';
    noteElement.dataset.manualOverride = note.manual_override || 'false';
    noteElement.dataset.category = note.category_name || '';
    noteElement.dataset.tags = JSON.stringify(note.ai_tags || []);
    noteElement.dataset.confidence = note.ai_confidence || '';
    
    const deadlineValue = note.deadline ? note.deadline.replace(' ', 'T') : '';
    
    noteElement.innerHTML = `
        <div class="title" contenteditable="true" onclick="hidePlaceholder(this)">${note.title}</div>
        <div class="content" contenteditable="true" onclick="hidePlaceholder(this)">${note.content}</div>
        <input type="color" class="color-picker" onchange="changeNoteColor('${note.id}', this.value)" value="${noteColor}">
        <div class="deadline-section">
            <label class="deadline" for="deadline-${note.id}">Deadline:</label>
            <input type="datetime-local" class="deadline" value="${deadlineValue}" onchange="changeDeadline('${note.id}', this.value)">
        </div>
        <div class="header">
            <span class="delete" onclick="deleteStickyNote('${note.id}')">Delete</span>
        </div>
    `;
    
    // Add right-click context menu for category management
    noteElement.addEventListener('contextmenu', (event) => handleNoteRightClick(event, noteElement));
    noteElement.addEventListener('mousedown', startDragNote);
    
    container.appendChild(noteElement);
    
    // Force apply category color immediately after creating the element
    if (note.category_color) {
        console.log(`Applying category color ${note.category_color} to note ${note.id}`);
        noteElement.style.backgroundColor = note.category_color;
        const colorPicker = noteElement.querySelector('.color-picker');
        if (colorPicker) {
            colorPicker.value = note.category_color;
        }
    }
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

// AI Categorization Functions
let currentCategories = [];
let currentRightClickedNote = null;

// Toggle category panel
function toggleCategoryPanel() {
    const panel = document.getElementById('categoryPanel');
    panel.classList.toggle('open');
    
    // Save panel state in localStorage
    localStorage.setItem('categoryPanelOpen', panel.classList.contains('open'));
    
    if (panel.classList.contains('open')) {
        loadCategories();
    }
}

// Load categories from server
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();
        currentCategories = categories;
        displayCategories(categories);
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Display categories in the panel
function displayCategories(categories) {
    const categoryList = document.getElementById('categoryList');
    const statusElement = document.getElementById('categorizationStatus');
    
    if (categories.length === 0) {
        categoryList.innerHTML = '<p style="text-align: center; opacity: 0.7;">No categories yet. Click "AI Categorize" to get started!</p>';
        statusElement.textContent = 'Ready for AI categorization';
    } else {
        categoryList.innerHTML = categories.map(category => {
            const numberedTitles = category.note_titles && category.note_titles.length > 0 
                ? category.note_titles.map((title, index) => `${index + 1}. ${title}`).join('<br>')
                : 'No notes yet';
            
            return `
                <div class="category-item" style="border-left-color: ${category.color}">
                    <div class="category-name">${category.name}</div>
                    <div class="category-description">${numberedTitles}</div>
                    <div class="category-meta">
                        <span class="category-note-count">${category.note_count} notes</span>
                        <span class="${category.created_by_ai ? 'ai-badge' : 'manual-badge'}">
                            ${category.created_by_ai ? 'AI' : 'Manual'}
                        </span>
                    </div>
                </div>
            `;
        }).join('');
        
        statusElement.textContent = `${categories.length} categories, organizing your ideas`;
    }
}

// AI Categorize notes
async function categorizeNotes() {
    const statusElement = document.getElementById('categorizationStatus');
    const originalText = statusElement.textContent;
    
    statusElement.innerHTML = '<span class="categorization-loading"></span> AI is analyzing your notes...';
    
    try {
        const response = await fetch('/categorize_notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            statusElement.textContent = `✅ Successfully categorized ${result.updated_notes.length} notes`;
            loadCategories();
            loadNotesFromServer(); // Refresh notes to show new category indicators and colors
            
            // Show success message
            setTimeout(() => {
                statusElement.textContent = `${result.categories.length} categories active`;
            }, 3000);
        } else {
            statusElement.textContent = `❌ Error: ${result.error}`;
            setTimeout(() => {
                statusElement.textContent = originalText;
            }, 3000);
        }
    } catch (error) {
        console.error('Error categorizing notes:', error);
        statusElement.textContent = '❌ Failed to categorize notes';
        setTimeout(() => {
            statusElement.textContent = originalText;
        }, 3000);
    }
}

// Clear all categories
async function clearCategories() {
    if (!confirm('Are you sure you want to clear all categories? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/clear_categories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Refresh the display
            loadCategories();
            loadNotesFromServer();
            document.getElementById('categorizationStatus').textContent = 'All categories cleared';
        } else {
            alert('Error clearing categories: ' + result.error);
        }
    } catch (error) {
        console.error('Error clearing categories:', error);
        alert('Failed to clear categories');
    }
}

// Handle right-click on notes for category management
function handleNoteRightClick(event, noteElement) {
    event.preventDefault();
    currentRightClickedNote = noteElement;
    
    const contextMenu = document.getElementById('noteContextMenu');
    contextMenu.style.display = 'block';
    contextMenu.style.left = event.pageX + 'px';
    contextMenu.style.top = event.pageY + 'px';
}

// Hide context menu
function hideContextMenu() {
    document.getElementById('noteContextMenu').style.display = 'none';
}

// Show category selector
function showCategorySelector() {
    if (!currentRightClickedNote) return;
    
    const categories = currentCategories.map(cat => cat.name);
    const currentCategory = currentRightClickedNote.dataset.category;
    
    const newCategory = prompt(`Select category for this note:\n\nAvailable categories:\n${categories.join('\n')}\n\nCurrent: ${currentCategory || 'None'}\n\nEnter category name (or leave empty to remove):`, currentCategory || '');
    
    if (newCategory !== null) {
        updateNoteCategory(currentRightClickedNote.id, newCategory);
    }
    
    hideContextMenu();
}

// Show note tags
function showNoteTags() {
    if (!currentRightClickedNote) return;
    
    const tags = currentRightClickedNote.dataset.tags || '[]';
    const confidence = currentRightClickedNote.dataset.confidence || 'N/A';
    
    try {
        const tagList = JSON.parse(tags);
        alert(`AI Tags: ${tagList.join(', ')}\nConfidence: ${confidence}`);
    } catch (e) {
        alert('No AI tags available for this note');
    }
    
    hideContextMenu();
}

// Update note category
async function updateNoteCategory(noteId, categoryName) {
    try {
        const response = await fetch('/update_note_category', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                note_id: noteId,
                category_name: categoryName
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Refresh the display
            loadNotesFromServer();
            loadCategories();
        } else {
            alert('Error updating category: ' + result.error);
        }
    } catch (error) {
        console.error('Error updating category:', error);
        alert('Failed to update category');
    }
}

// Hide context menu when clicking elsewhere
document.addEventListener('click', function(event) {
    const contextMenu = document.getElementById('noteContextMenu');
    if (!contextMenu.contains(event.target)) {
        hideContextMenu();
    }
});

// Add category indicators to notes
function addCategoryIndicators() {
    const notes = document.querySelectorAll('.sticky-note');
    notes.forEach(note => {
        // Remove existing indicators
        const existingIndicators = note.querySelectorAll('.note-category-indicator, .note-ai-badge, .note-tags, .note-confidence');
        existingIndicators.forEach(indicator => indicator.remove());
        
        // Add new indicators based on data attributes
        if (note.dataset.categoryColor) {
            const indicator = document.createElement('div');
            indicator.className = 'note-category-indicator';
            indicator.style.backgroundColor = note.dataset.categoryColor;
            indicator.title = `Category: ${note.dataset.categoryName || 'Unknown'}`;
            note.appendChild(indicator);
        }
        
        if (note.dataset.isAiCategorized === 'true') {
            const badge = document.createElement('div');
            badge.className = 'note-ai-badge';
            badge.textContent = 'AI';
            badge.title = 'AI Categorized';
            note.appendChild(badge);
        }
        
        if (note.dataset.tags && note.dataset.tags !== '[]') {
            const tags = document.createElement('div');
            tags.className = 'note-tags';
            try {
                const tagList = JSON.parse(note.dataset.tags);
                tags.textContent = tagList.slice(0, 2).join(', ');
                tags.title = `Tags: ${tagList.join(', ')}`;
            } catch (e) {
                tags.textContent = 'Tags';
            }
            note.appendChild(tags);
        }
        
        if (note.dataset.confidence && note.dataset.confidence !== 'null') {
            const confidence = document.createElement('div');
            confidence.className = 'note-confidence';
            confidence.textContent = `${Math.round(parseFloat(note.dataset.confidence) * 100)}%`;
            confidence.title = `AI Confidence: ${confidence.textContent}`;
            note.appendChild(confidence);
        }
    });
}

// Create default notes for team 1
async function createDefaultNotes() {
    if (!confirm('This will add default project tasks to your workspace. Existing notes will be preserved. Continue?')) {
        return;
    }
    
    try {
        const response = await fetch('/load_default_notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Default project tasks loaded successfully!');
            loadNotesFromServer(); // Refresh the display
            // Also refresh categories since new ones might have been created
            setTimeout(() => {
                displayCategories();
            }, 200);
        } else {
            alert('Error loading default tasks: ' + result.error);
        }
    } catch (error) {
        console.error('Error creating default notes:', error);
        alert('Failed to load default tasks');
    }
}

// Show default notes button for team 1
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on team 1
    const currentPath = window.location.pathname;
    if (currentPath.includes('/team/1')) {
        const defaultBtn = document.getElementById('defaultNotesBtn');
        if (defaultBtn) {
            defaultBtn.style.display = 'inline-block';
        }
    } else {
        // Hide button for other teams
        const defaultBtn = document.getElementById('defaultNotesBtn');
        if (defaultBtn) {
            defaultBtn.style.display = 'none';
        }
    }
});

// Group notes by category for organized display
function groupNotesByCategory(notes) {
    const categorizedNotes = {};
    const uncategorizedNotes = [];
    
    notes.forEach(note => {
        if (note.category_name) {
            if (!categorizedNotes[note.category_name]) {
                categorizedNotes[note.category_name] = {
                    category: note.category_name,
                    color: note.category_color,
                    notes: []
                };
            }
            categorizedNotes[note.category_name].notes.push(note);
        } else {
            uncategorizedNotes.push(note);
        }
    });
    
    return { categorizedNotes, uncategorizedNotes };
}

// =================================================================================
// ===== UPDATED FUNCTION: positionNotesByCategory (now async) =====================
// =================================================================================
// This function now asynchronously places notes to wait for the browser to render
// each one, allowing for accurate height measurement and preventing overlap.
async function positionNotesByCategory(groupedNotes) {
    const { categorizedNotes, uncategorizedNotes } = groupedNotes;
    
    const COLUMN_WIDTH = 300;
    const DYNAMIC_NOTE_SPACING = 100; // Increased from 10px to 25px for better spacing
    const COLUMN_SPACING = 50;
    const START_X = 50;
    const START_Y = 180; // Y position to start the first note in a column
    const HEADER_HEIGHT = 50;
    const NOTES_PER_COLUMN = 6; // A soft limit for notes before creating a continuation column
    const MIN_NOTE_HEIGHT = 120; // Minimum assumed note height for fallback
    
    let currentColumn = 0;
    
    // Position categorized notes using an async-compatible for...of loop
    for (const categoryGroup of Object.values(categorizedNotes)) {
        let columnX = START_X + (currentColumn * (COLUMN_WIDTH + COLUMN_SPACING));
        let currentY = START_Y;
        
        createCategoryHeader(categoryGroup.category, categoryGroup.color, columnX, START_Y - HEADER_HEIGHT);
        
        // Use .entries() to get both index and note object
        for (const [index, note] of categoryGroup.notes.entries()) {
            if (index > 0 && index % NOTES_PER_COLUMN === 0) {
                currentColumn++;
                columnX = START_X + (currentColumn * (COLUMN_WIDTH + COLUMN_SPACING));
                currentY = START_Y;
                createCategoryHeader(`${categoryGroup.category} (cont.)`, categoryGroup.color, columnX, START_Y - HEADER_HEIGHT);
            }
            
            note.top = `${currentY}px`;
            note.left = `${columnX}px`;
            
            createNoteOnPage(note);
            
            // Wait for the browser to render the note and calculate its height
            await new Promise(resolve => setTimeout(resolve, 15)); // Increased wait time
            
            const noteElement = document.getElementById(note.id);
            if (noteElement) {
                const noteHeight = noteElement.offsetHeight;
                // Use the actual note height plus spacing, with a minimum height fallback
                const actualHeight = Math.max(noteHeight, MIN_NOTE_HEIGHT);
                currentY += actualHeight + DYNAMIC_NOTE_SPACING;
                console.log(`Note ${note.id}: height=${actualHeight}px, next Y=${currentY}px`);
            } else {
                // Fallback with increased spacing
                currentY += MIN_NOTE_HEIGHT + DYNAMIC_NOTE_SPACING;
                console.log(`Note ${note.id}: fallback height, next Y=${currentY}px`);
            }
        }
        
        currentColumn++;
    }
    
    // Position uncategorized notes
    if (uncategorizedNotes.length > 0) {
        let columnX = START_X + (currentColumn * (COLUMN_WIDTH + COLUMN_SPACING));
        let currentY = START_Y;
        
        createCategoryHeader('Uncategorized', '#CCCCCC', columnX, START_Y - HEADER_HEIGHT);
        
        for (const [index, note] of uncategorizedNotes.entries()) {
            if (index > 0 && index % NOTES_PER_COLUMN === 0) {
                currentColumn++;
                columnX = START_X + (currentColumn * (COLUMN_WIDTH + COLUMN_SPACING));
                currentY = START_Y;
                createCategoryHeader('Uncategorized (cont.)', '#CCCCCC', columnX, START_Y - HEADER_HEIGHT);
            }
            
            note.top = `${currentY}px`;
            note.left = `${columnX}px`;
            
            createNoteOnPage(note);
            
            // Wait for the browser to render the note and calculate its height
            await new Promise(resolve => setTimeout(resolve, 15));

            const noteElement = document.getElementById(note.id);
            if (noteElement) {
                const noteHeight = noteElement.offsetHeight;
                const actualHeight = Math.max(noteHeight, MIN_NOTE_HEIGHT);
                currentY += actualHeight + DYNAMIC_NOTE_SPACING;
                console.log(`Uncategorized note ${note.id}: height=${actualHeight}px, next Y=${currentY}px`);
            } else {
                currentY += MIN_NOTE_HEIGHT + DYNAMIC_NOTE_SPACING;
                console.log(`Uncategorized note ${note.id}: fallback height, next Y=${currentY}px`);
            }
        }
    }
}

// Create category header label
function createCategoryHeader(categoryName, categoryColor, x, y) {
    const container = document.getElementById('container');
    
    // Remove existing header at the same position to prevent duplicates on refresh
    const existingHeaders = container.querySelectorAll('.category-header-label');
    existingHeaders.forEach(header => {
        if (header.style.left === `${x}px` && header.style.top === `${y}px`) {
            header.remove();
        }
    });
    
    const header = document.createElement('div');
    header.className = 'category-header-label';
    header.style.position = 'absolute';
    header.style.left = `${x}px`;
    header.style.top = `${y}px`;
    header.style.width = '280px';
    header.style.height = '40px'; 
    header.style.backgroundColor = categoryColor;
    header.style.color = '#333';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.justifyContent = 'center';
    header.style.fontWeight = 'bold';
    header.style.borderRadius = '8px';
    header.style.fontSize = '14px';
    header.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
    header.style.zIndex = '50';
    header.textContent = categoryName;
    
    container.appendChild(header);
}

// Manually arrange notes by category
function arrangeNotesByCategory() {
    loadNotesFromServer(); // This will automatically arrange notes by category
}

// Function to update all notes in the same category with the category color
function updateNotesColorsByCategory() {
    console.log('Updating note colors by category...');
    const notes = document.getElementsByClassName("note");
    Array.from(notes).forEach(note => {
        const categoryColor = note.dataset.categoryColor;
        const categoryId = note.dataset.categoryId;
        
        console.log(`Note ${note.id}: categoryId=${categoryId}, categoryColor=${categoryColor}`);
        
        if (categoryColor && categoryId) {
            console.log(`Applying category color ${categoryColor} to note ${note.id}`);
            // Update note background color
            note.style.backgroundColor = categoryColor;
            
            // Update color picker value
            const colorPicker = note.querySelector('.color-picker');
            if (colorPicker) {
                colorPicker.value = categoryColor;
            }
        }
    });
}

// Function to apply category color to a specific note
function applyNoteCategoryColor(noteElement, categoryColor) {
    if (categoryColor) {
        noteElement.style.backgroundColor = categoryColor;
        const colorPicker = noteElement.querySelector('.color-picker');
        if (colorPicker) {
            colorPicker.value = categoryColor;
        }
    }
}

// Force update all note colors to match their categories (for debugging/manual trigger)
function forceUpdateAllNoteColors() {
    console.log('Force updating all note colors...');
    const notes = document.getElementsByClassName("note");
    let updated = 0;
    
    Array.from(notes).forEach(note => {
        const categoryColor = note.dataset.categoryColor;
        const categoryName = note.dataset.categoryName;
        
        if (categoryColor && categoryName) {
            console.log(`Forcing color ${categoryColor} for note ${note.id} in category ${categoryName}`);
            note.style.backgroundColor = categoryColor;
            
            const colorPicker = note.querySelector('.color-picker');
            if (colorPicker) {
                colorPicker.value = categoryColor;
            }
            updated++;
        }
    });
    
    console.log(`Force updated ${updated} notes with category colors`);
    return updated;
}

// Add this function to window for manual testing
window.forceUpdateAllNoteColors = forceUpdateAllNoteColors;

// Gantt chart functions

// Function to generate Gantt chart
async function generateGanttChart() {
    const ganttContainer = document.getElementById('ganttChartContainer');
    const originalContent = ganttContainer.innerHTML;
    
    // Show loading indicator
    ganttContainer.innerHTML = '<div class="gantt-loading"></div> Generating chart...';
    
    try {
        const response = await fetch('/generate_gantt_chart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            if (result.tasks_count === 0) {
                ganttContainer.innerHTML = '<p class="gantt-placeholder">No tasks with deadlines found. Add deadlines to your notes first.</p>';
                return;
            }
            
            // Display the Gantt chart
            displayGanttChart(result.gantt_chart);
        } else {
            ganttContainer.innerHTML = `<p class="gantt-placeholder">Error: ${result.error}</p>`;
        }
    } catch (error) {
        console.error('Error generating Gantt chart:', error);
        ganttContainer.innerHTML = '<p class="gantt-placeholder">Failed to generate chart. Please try again.</p>';
    }
}

// Function to generate AI-optimized Gantt chart
async function generateAIGanttChart() {
    const ganttContainer = document.getElementById('ganttChartContainer');
    const originalContent = ganttContainer.innerHTML;
    
    // Show loading indicator
    ganttContainer.innerHTML = '<div class="gantt-loading"></div> AI is optimizing your schedule...';
    
    try {
        const response = await fetch('/ai_generate_gantt_chart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            if (result.tasks_count === 0) {
                ganttContainer.innerHTML = '<p class="gantt-placeholder">No tasks found. Add notes first.</p>';
                return;
            }
            
            // Display the AI-optimized Gantt chart
            displayGanttChart(result.gantt_chart);
        } else {
            ganttContainer.innerHTML = `<p class="gantt-placeholder">Error: ${result.error}</p>`;
        }
    } catch (error) {
        console.error('Error generating AI Gantt chart:', error);
        ganttContainer.innerHTML = '<p class="gantt-placeholder">Failed to generate chart. Please try again.</p>';
    }
}

// Function to display the Gantt chart in the container
function displayGanttChart(base64Image) {
    const ganttContainer = document.getElementById('ganttChartContainer');
    const ganttModalContent = document.getElementById('ganttChartModalContent');
    
    // Create image for container
    const img = document.createElement('img');
    img.src = `data:image/png;base64,${base64Image}`;
    img.alt = 'Project Schedule Gantt Chart';
    img.onclick = openGanttModal;
    
    // Clear container and add image
    ganttContainer.innerHTML = '';
    ganttContainer.appendChild(img);
    
    // Prepare modal content
    const modalImg = document.createElement('img');
    modalImg.src = `data:image/png;base64,${base64Image}`;
    modalImg.alt = 'Project Schedule Gantt Chart (Full Size)';
    
    // Clear modal and add full-size image
    ganttModalContent.innerHTML = '';
    ganttModalContent.appendChild(modalImg);
}

// Function to open the Gantt chart modal
function openGanttModal() {
    const modal = document.getElementById('ganttModal');
    modal.style.display = 'block';
}

// Function to close the Gantt chart modal
function closeGanttModal() {
    const modal = document.getElementById('ganttModal');
    modal.style.display = 'none';
}

// Close the modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('ganttModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

// Load categories when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Set the initial theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
    }
    
    // Load categories if available
    loadCategories();
    
    // Initialize category panel
    const categoryPanel = document.getElementById('categoryPanel');
    if (categoryPanel) {
        const savedPanelState = localStorage.getItem('categoryPanelOpen');
        if (savedPanelState === 'true') {
            categoryPanel.classList.add('open');
        }
    }
});