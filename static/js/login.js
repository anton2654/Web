document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.getElementById("login-form");

  if (loginForm) {
    const usernameError = document.getElementById("login-username-error");
    const passwordError = document.getElementById("login-password-error");

    loginForm.addEventListener("submit", function (event) {
      if (usernameError) { usernameError.style.display = "none"; usernameError.textContent = ""; }
      if (passwordError) { passwordError.style.display = "none"; passwordError.textContent = ""; }

      const usernameInput = document.getElementById("login-username");
      const passwordInput = document.getElementById("login-password");
      const username = usernameInput.value.trim();
      const password = passwordInput.value;

      let isValid = true;

      if (username === "") {
        if (usernameError) {
          usernameError.textContent = "Введіть ім'я користувача.";
          usernameError.style.display = "block";
        }
        isValid = false;
      }

      if (password === "") {
        if (passwordError) {
          passwordError.textContent = "Введіть пароль.";
          passwordError.style.display = "block";
        }
        isValid = false;
      }

      if (!isValid) {
        event.preventDefault(); 
      }
    });
  }
});