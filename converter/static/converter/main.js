const fileInput = document.getElementById('csv_file')
const fileLabelElement = document.querySelector('.file-label')

fileInput.addEventListener("change", () => {
    fileLabelElement.textContent = fileInput.files[0].name;

    fileInput.form.submit();
})