document.addEventListener('DOMContentLoaded', function() {

    const solverForm = document.getElementById('solver-form'); 
     if (solverForm) {
         solverForm.addEventListener('submit', function(event) {
             const matrixInput = document.getElementById('matrix_a').value.trim(); 
             const vectorInput = document.getElementById('vector_b').value.trim(); 
             
             if (matrixInput === '' || vectorInput === '') {
                 alert('Помилка: Матриця А та вектор b не можуть бути порожніми.');
                 event.preventDefault();
             }

         });
     }

});