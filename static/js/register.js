document.addEventListener('DOMContentLoaded', function() {


    const registerForm = document.getElementById('register-form'); // 
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const username = document.getElementById('register-username').value.trim(); 
            const password = document.getElementById('register-password').value; 
            const password2 = document.getElementById('register-password2').value; 
            
            let isValid = true;

            if (username === '' || password === '' || password2 === '') {
                alert('Будь ласка, заповніть усі поля.');
                isValid = false;
            } else if (password !== password2) {
                alert('Паролі не збігаються.');
                isValid = false;
            }

            if (!isValid) {
                event.preventDefault(); 
            }
        });
    }

});