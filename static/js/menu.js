// menu button functionality
function toggleMenu() {
    // get menu div from html
    const menu = document.getElementById('menu');

    // give the menu div the open class, toggle turns the class on and off when clicked again
    menu.classList.toggle('open');
}