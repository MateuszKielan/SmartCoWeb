// Get input and label fields
const fileInput = document.getElementById('csv_file')
const fileLabelElement = document.querySelector('.file-label')

// Change the filed name to the selected file name 
fileInput.addEventListener("change", () => {
    fileLabelElement.textContent = fileInput.files[0].name;

    //fileInput.form.submit();
})