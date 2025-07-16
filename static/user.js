// Function to toggle theme
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    if (document.body.classList.contains('dark-theme')) {
        localStorage.setItem('theme', 'light');
        console.log("Switched to light theme");
    } else {
        localStorage.setItem('theme', 'dark');
        console.log("Switched to not light theme");
    }
}






// Function to handle theme based on localStorage
function handleStoredTheme() {
    var storedTheme = localStorage.getItem('theme');
    if (storedTheme === 'light') {
        document.body.classList.add('light-theme');
    }
}



// Function to handle feedback form submission
function handleFeedbackFormSubmission() {
    document.getElementById('feedbackForm').onsubmit = function(event) {
        event.preventDefault();
        var idea = document.getElementById('idea').value;
        fetch('/submit_idea', {
            method: 'POST',
            body: JSON.stringify({idea: idea}),
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(response => response.json())
          .then(data => {
              alert(data.message);
              modal.style.display = 'none';
          });
    };
}

// Function to add login and signup event listeners
function addLoginSignupEventListeners() {
    var loginModal = document.getElementById('loginModal');
    var signupModal = document.getElementById('signupModal');
    var loginBtn = document.getElementById('loginBtn');
    var signupBtn = document.getElementById('signupBtn');

    if (loginBtn && signupBtn) {
        loginBtn.onclick = function() {
            loginModal.style.display = "block";
        };

        signupBtn.onclick = function() {
            signupModal.style.display = "block";
        };
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

                    <li><a href="/logout">Log out</a></li>
                    <li><a href="/delete_user">Delete Account</a></li>

                </ul>
            </details>


        `;
    } else {
        authContainer.innerHTML = `
            <button id="loginBtn" class="login-button">Login</button>
            <button id="signupBtn" class="signup-button">Sign Up</button>
        `;
        addLoginSignupEventListeners();
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
    handleStoredTheme();
    handleNavTabClick();
    handleFeedbackFormSubmission();
    addModalEventListeners();
    handleSignupFormSubmission();
    handleLoginFormSubmission();
    updateAuthDisplay(loggedInUsername);

}


// Event listener for DOMContentLoaded
document.addEventListener('DOMContentLoaded', onDOMContentLoaded);



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


