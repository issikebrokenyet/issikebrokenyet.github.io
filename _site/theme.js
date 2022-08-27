// Deal with dark/light theme
var toggle = document.getElementById("theme-toggle");
var storedTheme = localStorage.getItem('theme') || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
if (storedTheme){
  document.documentElement.setAttribute('data-theme', storedTheme)
  buttonText = (storedTheme == "light" ? "Dark Theme" : "Light Theme")
  toggle.innerText = buttonText;
}
else{
  document.documentElement.setAttribute('data-theme', "light");
  toggle.innerText = "Dark Theme";
}

toggle.onclick = function() {
  var currentTheme = document.documentElement.getAttribute("data-theme");
  var targetTheme = "light";

  if (currentTheme === "light") {
      targetTheme = "dark";
  }

  document.documentElement.setAttribute('data-theme', targetTheme)
  localStorage.setItem('theme', targetTheme);
  buttonText = (targetTheme == "light" ? "Dark Theme" : "Light Theme")
  toggle.innerText = buttonText;
};