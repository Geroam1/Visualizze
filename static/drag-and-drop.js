// html objects
const dropbox = document.getElementById('dropbox');
const fileInput = document.getElementById('fileInput');
const uploadForm = document.getElementById('uploadForm');

// prevents the browsers default reaction to drag drop, 
// such as automatically opening the file in the browser when it's dragged into a page
const eventsToPreventDefault = ['dragenter', 'dragover', 'dragleave', 'drop'];
eventsToPreventDefault.forEach(event => {
    // add an event listener for each element in the list using an arrow function.
    dropbox.addEventListener(event, e => e.preventDefault());
});

// give the html element the 'dragover' class when a user drags a file over it, 
// or removes it when the user drags a file away from it or drops the file
// This is purely visual
dropbox.addEventListener('dragover', () => dropbox.classList.add('dragover'));
dropbox.addEventListener('dragleave', () => dropbox.classList.remove('dragover'));
dropbox.addEventListener('drop', () => dropbox.classList.remove('dragover'));

// what happens when a user drops a file
dropbox.addEventListener('drop', function(e) {
    const files = e.dataTransfer.files;

    // defines allowed file extensions
    const allowedExtensions = ['.csv', '.xlsx'];

    // for each file in files
    let validFiles = [];

    for (let file of files) {
        // get file extension
        const fileExtension = file.name.split('.').pop().toLowerCase();

        // validate file uploaded
        if (allowedExtensions.includes(`.${fileExtension}`)) {
            validFiles.push(file);
        } else {
            alert(`File type not allowed: ${file.name}, only .xlsx or .csv is accepted`);
        }
    }

    // alert user of file drop
    if (validFiles.length > 0) {
        // grab first file in files
        const file = validFiles[0];
        
        // update dropbox text
        dropbox.textContent = `File dropped: ${file.name}`;

        // inputs the dropped file to the 'fileInput' input object in the upload form
        const dataTransfer = new DataTransfer();
        validFiles.forEach(f => dataTransfer.items.add(f));
        fileInput.files = dataTransfer.files;
    }
});

// handle file upload form submission
uploadForm.addEventListener('submit', function(e) {
    // ensure the form has an inputted file
    if (fileInput.files.length === 0) {
        alert('Please select a file first!');
        e.preventDefault();  // prevent form submission
    }
});

// browse button functionality
browseButton.addEventListener('click', function() {
    // opens file selction pop up for the hidden type="file" input on click of the browseButton
    fileInput.click();
});

// listens for the change event, which is trigger when a user selects a file
fileInput.addEventListener('change', function() {

    // get file
    const file = fileInput.files[0];

    // if file exists display file selected text
    if (file) {
        dropbox.textContent = `File selected: ${file.name}`;
    }
});