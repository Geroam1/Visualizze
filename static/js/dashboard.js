document.addEventListener('DOMContentLoaded', () => {

    // get items from the dashboard to html
    const visualButtons = document.querySelectorAll('.visual-button');
    const mainVisual = document.querySelector('.dashboard-main-visual img');
    
    // listens for clicks on the 'visual buttons' in the dashboard other visuals section
    visualButtons.forEach(button => {
        button.addEventListener('click', () => {
            // if clicked change the main visual to the selected visual
            const newVisual = button.getAttribute('data-visual');
            if (mainVisual) {
                /* 
                changes the src of mainVisual's value in dashboard.html, to the
                src of the selected visual
                */
                mainVisual.src = newVisual;
            } else {
                // create the img element if not already present
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
});