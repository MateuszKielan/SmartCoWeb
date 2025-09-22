// Get input and label fields (guard if not present on this page)
const fileInput = document.getElementById('csv_file')
const fileLabelElement = document.querySelector('.file-label')

if (fileInput && fileLabelElement) {
    fileInput.addEventListener("change", () => {
        fileLabelElement.textContent = fileInput.files[0].name;
    })
}


// DON'T FORGET REMAKE TO OPEN HELPER POPUPS
// Function to open the popup 
function openDatasetForm() {
    const popup = document.getElementById('dataset_popup');

    popup.style.display = 'block';
}

// Function to close the popup 
function closeDatasetForm() {
    const popup = document.getElementById('dataset_popup');

    popup.style.display = 'none';
}

// Helper popup open/close
function openHelperPopup(element) {
    const helper = document.getElementById(element);
    helper.style.display = 'block';
}

function closeHelperPopup(element) {
    const helper = document.getElementById(element);
    helper.style.display = 'none';
}