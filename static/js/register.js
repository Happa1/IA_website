document.addEventListener('DOMContentLoaded', () => {
    const signUpButton = document.getElementById('signUp');
    const signInButton = document.getElementById('signIn');
    const container = document.getElementById('container');

    // 初期状態でSign Up画面を表示
    container.classList.add("right-panel-active");

    signInButton.addEventListener('click', () => {
        container.classList.remove("right-panel-active");
    });

    signUpButton.addEventListener('click', () => {
        container.classList.add("right-panel-active");
    });
});

let eye = document.getElementById("eye");
eye.addEventListener('click', function () {
     if (this.previousElementSibling.getAttribute('type') == 'password') {
          this.previousElementSibling.setAttribute('type', 'text');
          this.classList.toggle('fa-eye');
          this.classList.toggle('fa-eye-slash');
     } else {
          this.previousElementSibling.setAttribute('type', 'password');
          this.classList.toggle('fa-eye');
          this.classList.toggle('fa-eye-slash');
     }
})

let eye2 = document.getElementById("eye2");
eye2.addEventListener('click', function () {
     if (this.previousElementSibling.getAttribute('type') == 'password') {
          this.previousElementSibling.setAttribute('type', 'text');
          this.classList.toggle('fa-eye');
          this.classList.toggle('fa-eye-slash');
     } else {
          this.previousElementSibling.setAttribute('type', 'password');
          this.classList.toggle('fa-eye');
          this.classList.toggle('fa-eye-slash');
     }
})
