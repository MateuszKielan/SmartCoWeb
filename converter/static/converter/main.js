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

function triggerNQuadsConversion() {
    fetch('/convert/nquads/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);  // Replace with styled popup if needed
    })
    .catch(error => {
        console.error('Conversion error:', error);
        alert("An error occurred during conversion.");
    });
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
