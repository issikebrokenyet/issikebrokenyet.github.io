
  // Select all comment checkboxes with the name using querySelectorAll.
  var commentButtons = document.querySelectorAll("button.cbtn");

  // Use Array.forEach to add an event listener to each checkbox.
  commentButtons.forEach(function(button) {
    button.addEventListener('click', function() {
      this.toggleAttribute("aria-expanded")
      const buttonId = this.id;
      const commentId = buttonId.replace("!button", "");
      const commentEle = document.getElementById(commentId);
      commentEle.classList.toggle("hidden-row");
    })
  });

  // Select all checkboxes with the name 'settings' using querySelectorAll.
  var variantButtons = document.querySelectorAll("button.vbtn");

  // Use Array.forEach to add an event listener to each checkbox.
  variantButtons.forEach(function(button) {
    button.addEventListener('click', function() {
      this.toggleAttribute("aria-expanded")
      const buttonId = this.id;
      const variantClassName = buttonId.replace("!button", "");
      var variantElements = document.getElementsByClassName(variantClassName);
      console.log(variantElements)

      Array.prototype.forEach.call(variantElements, function(variantElement) {
        variantElement.classList.toggle("hidden-row");
    
        // Nasty hack so that if a variant is hidden while a comment is open
        // We close the comment.
        commentId = "comment-" + variantElement.id
        commentCheckboxId = commentId + "!button";

        // Grab the comment
        variantComment = document.getElementById(commentId);
        // If the variant is currently visible AND we have hidden the variant
        // Hide the comment and remove the check from the checkbox.
        if (!variantComment.classList.contains("hidden-row") && 
             variantElement.classList.contains("hidden-row")){
            document.getElementById(commentCheckboxId).click()  
        }
      });
    });
  });
  
  // Allow touch control for abbr elements
  var abbr_elements = document.querySelectorAll("abbr");
  // Use Array.forEach to add an event listener to each abbr element.
  abbr_elements.forEach(function(abbr_element) {
    // Show label on touch
    abbr_element.addEventListener('touchstart', function() {
      abbr_element.classList.toggle("touched");
    });
    // hide element when finger lifted after 2s delay
    abbr_element.addEventListener('touchend', function() {
      setTimeout(function () {
        if (abbr_element.classList.contains("touched")) {
            abbr_element.classList.remove("touched");
        }
      }, 2000);
    })
  });

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




