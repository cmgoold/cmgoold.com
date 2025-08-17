function getSystemTheme(localTheme, systemSettingDark) {
    if (localTheme) return localTheme;
    return systemSettingDark.matches ? "dark": "light";
}

function updateButton({ buttonElement, isDark }) {
    const sun = buttonElement.querySelector("#sun");
    const moon = buttonElement.querySelector("#moon");

    sun.classList.toggle("hidden", !isDark);
    moon.classList.toggle("hidden", isDark);

    buttonElement.setAttribute(
        "aria-label", 
        isDark ? "Toggle light mode" : "Toggle dark mode"
    );
}

function updateThemeOnHtmlElement({ theme }) {
    document.documentElement.setAttribute("data-theme", theme);
}

function updatePictureElements(theme) {
    document.querySelectorAll("picture img").forEach(img => {
        const basePath = img.getAttribute("src").replace(/-(light|dark)\.png$/, "");
        img.src = `${basePath}-${theme}.png`;
    });
}

function updateCodeTheme(theme) {
    const lightLink = document.getElementById("light-code");
    const darkLink = document.getElementById("dark-code");

    darkLink.disabled = theme === "dark" ? false : true;
    lightLink.disabled = theme == "dark" ? true : false;

    hljs.highlightAll();
}


const button = document.querySelector("[data-theme-toggle]");
const localTheme = localStorage.getItem("theme");
console.log(localTheme);
const systemSettingDark = window.matchMedia("(prefers-color-scheme: dark)");

let currentTheme = getSystemTheme(localTheme, systemSettingDark);

updateButton({ buttonElement: button, isDark: currentTheme == "dark" });
updateThemeOnHtmlElement({ theme: currentTheme });
updatePictureElements(currentTheme);
updateCodeTheme(currentTheme);

button.addEventListener("click", (event) => {
    const newTheme = currentTheme == "dark" ? "light" : "dark";

    localStorage.setItem("theme", newTheme);
    updateButton({ buttonElement: button, isDark: newTheme == "dark" });
    updateThemeOnHtmlElement({ theme: newTheme });
    updatePictureElements(newTheme);
    updateCodeTheme(newTheme);
    currentTheme = newTheme;
});
