document.addEventListener('DOMContentLoaded', () => {

    // get items from the dashboard to HTML
    const visualButtons = document.querySelectorAll('.visual-button');
    const mainVisual = document.querySelector('.dashboard-main-visual img');
    
    // listens for clicks on the 'visual buttons' in the dashboard other visuals section
    visualButtons.forEach(button => {
        button.addEventListener('click', () => {
            const newVisual = button.getAttribute('data-visual');
            if (mainVisual) {
                mainVisual.src = newVisual;
            } else {
                const newImg = document.createElement('img');
                newImg.src = newVisual;
                newImg.alt = "Visual";
                document.querySelector('.dashboard-main-visual').innerHTML = "";
                document.querySelector('.dashboard-main-visual').appendChild(newImg);
            }

            // highlight for the selected visual
            visualButtons.forEach(btn => btn.classList.remove('active-visual'));
            button.classList.add('active-visual');
        });
    });

    // get form objects
    const saveDatasetForm = document.getElementById("saveDatasetForm");
    const formParent = document.querySelector('.save-this-dataset'); 
    if (saveDatasetForm) {
        saveDatasetForm.addEventListener("submit", (event) => {
            // listen for the "yes" button click
            const yesButton = event.target.querySelector('button[name="save_dataset"][value="yes"]');
            if (yesButton && yesButton === document.activeElement) {
                // hide the form after submission
                formParent.style.display = 'none';

                // create success message to pop up
                const successDiv = document.createElement('div');
                successDiv.style.position = 'fixed';
                successDiv.style.top = '10px';
                successDiv.style.left = '50%';
                successDiv.style.transform = 'translateX(-50%)';
                successDiv.style.backgroundColor = '#28a745';
                successDiv.style.color = 'white';
                successDiv.style.padding = '15px';
                successDiv.style.borderRadius = '5px';
                successDiv.style.textAlign = 'center';
                successDiv.innerText = 'Dataset saved';
                successDiv.style.zIndex = '9999'; 

                // show the popup by appending it to the template (body)
                document.body.appendChild(successDiv);

                // remove the success message after 2 seconds
                setTimeout(() => {
                    successDiv.remove();
                }, 2000);
            }
        });
    }

});
