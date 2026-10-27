function updateFontButton({ buttonElement, isSerif }) {
    const font = buttonElement.querySelector("#font");
    font.classList.toggle("serif", isSerif);
    font.classList.toggle("sans-serif", !isSerif);
    buttonElement.setAttribute(
        "aria-label",
        isSerif ? "Toggle serif font" : "Toggle sans-serif font"
    );
}

function updateFontOnHtmlElement({ font }) {
    document.documentElement.setAttribute("font-theme", font);
}

const fontButton = document.querySelector(".font-toggle-button");
const localFont = localStorage.getItem("font");
let currentFont = localFont == "serif" ? "serif" : "sans-serif";

updateFontButton({ buttonElement: fontButton, isSerif: currentFont == "serif" });
updateFontOnHtmlElement({ font: currentFont });

fontButton.addEventListener("click", (event) => {
    const newFont = currentFont == "sans-serif" ? "serif" : "sans-serif";

    localStorage.setItem("font", newFont);
    updateFontButton({ buttonElement: fontButton, isSerif: newFont == "serif" });
    updateFontOnHtmlElement({ font: newFont });
    currentFont = newFont;
});
