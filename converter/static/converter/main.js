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
        alert(data.message);  
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

const cardButtons = document.querySelectorAll('.card-button');
// This creates a table dynamically when clicked on the corresponding header card 
cardButtons.forEach(button => {
        button.addEventListener('click', function() {

        // Retrieve DOM elements
        const popup = document.getElementById('matchContainer');
        const title = document.getElementById('match-header-text');
        const table = document.getElementById('match-table');
        table.innerHTML = "";
        const thead = document.createElement('thead');
        const tbody = document.createElement('tbody');
        const headerRow = document.createElement('tr');
        // Retrieve data
        const allMatches = JSON.parse(document.getElementById('all-matches-data').textContent);
        const listOfTitles = ['prefixedName', 'vocabualry.prefix', 'uri', 'type', 'score'];


        // create the headers of the table 
        listOfTitles.forEach(title => {
            const th = document.createElement('th');
            th.textContent = title;
            headerRow.appendChild(th);
        })
        
        thead.append(headerRow);
        table.append(thead)

        allMatches[this.dataset.header].forEach(match => {

            const bodyRow = document.createElement('tr');

            for (let i =0; i<= match.length; i++) {

                const td = document.createElement('td');

                // Strip the array to string
                if (match[i] instanceof Array) {
                    td.textContent = match[i][0];
                } else {
                    td.textContent = match[i];
                }
                bodyRow.appendChild(td);
            
            tbody.appendChild(bodyRow);

            }
        });

        table.appendChild(tbody);

        title.textContent = this.dataset.header

        popup.style.display = 'block';

    });
});


const container = document.getElementById('matchContainer');
const resizer = document.getElementById('matchResizer');

let startY, startHeight, isResizing = false;

resizer.addEventListener('mousedown', e => {
  isResizing = true;
  startY = e.clientY;
  startHeight = container.offsetHeight;
  document.addEventListener('mousemove', resize);
  document.addEventListener('mouseup', stopResize);
});


function resize(e) {
  if (!isResizing) return;
  const dy = startY - e.clientY; // drag up = increase height
  container.style.height = `${startHeight + dy}px`;
}

function stopResize() {
  isResizing = false;
  document.removeEventListener('mousemove', resize);
  document.removeEventListener('mouseup', stopResize);
}
