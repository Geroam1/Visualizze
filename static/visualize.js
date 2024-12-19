/* 
    functions
*/

// menu button functionality
function toggleMenu() {
    // get menu div from html
    const menu = document.getElementById('menu');

    // give the menu div the open class, toggle turns the class on and off when clicked again
    menu.classList.toggle('open');
}

// password confirmation functionality
function checkRegisterPasswords(event) {

    // get passwords inputted upon registration
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    // get the submit button for registration
    const registerButton = document.getElementById('register-button');

    // conditionals
    if (password === confirmPassword) {
        // if match, submit the form
        alert('Passwords match, submitting form!');
        document.querySelector('form').submit();  // Proceed with form submission
    } else {
        // if not match, disable the register button and show alert
        alert('Passwords do not match!');
        // prevent form submission if passwords don't match
        event.preventDefault();
    }
}

/* 
    event listeners 
*/

// registeration password check on submit button click
document.getElementById('register-button').addEventListener('click', checkRegisterPasswords);
