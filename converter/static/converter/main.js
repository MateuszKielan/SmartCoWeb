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

const matchTables = document.querySelectorAll('.match-table');

matchTables.forEach(table => {
    table.addEventListener('click', function(e) {

        // Only handle clicks on table cells
        // When row is clicked open a popup with the further action choice
        if (e.target.tagName === 'TD') {
            const insertPopup = document.getElementById('insert-popup');
            insertPopup.style.display = 'flex';
        }

        console.log(e.target.textContent);

    });
});

function create_match_tables(header) {
    const headers = JSON.parse(document.getElementById('headers').textContent);

    // Exit if wrong input
    if (!headers.includes(header)){
        return;
    }

    // Retrieve DOM elements
    const popup = document.getElementById('matchContainer');
    const title = document.getElementById('match-header-text');
    const table = document.getElementById('match-table');
    const bestMatchTable = document.getElementById('best-match-table-element');

    // Create the table headers
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');
    const headerRow = document.createElement('tr');

    // Create the best match table headers
    const tBestHead = document.createElement('thead');
    const tBestBody = document.createElement('tbody');
    const headerBestRow = document.createElement('tr');

    // Retrieve data
    const allMatches = JSON.parse(document.getElementById('all-matches-data').textContent);
    const bestMatchIndexes = JSON.parse(document.getElementById('best-match-index-data').textContent);
    const vocabCoverageScore = JSON.parse(document.getElementById('vocab-coverage-score-data').textContent);
    const sortedVocabs = JSON.parse(document.getElementById('sorted-vocabs-data').textContent);
    const listOfTitles = ['prefixedName', 'vocabualry.prefix', 'uri', 'type', 'score'];

    table.innerHTML = "";
    bestMatchTable.innerHTML = "";

     // If the first vocab card was pressed
     if (header == "Vocabularies") {
        console.log(vocabCoverageScore);
        console.log(sortedVocabs)
    }


    // create the headers of the table 
    listOfTitles.forEach(title => {
        const th = document.createElement('th');
        const th2 = document.createElement('th');

        th.textContent = title;
        th2.textContent = title;

        headerRow.appendChild(th);
        headerBestRow.appendChild(th2);
    })
    
    thead.append(headerRow);
    table.append(thead);
    
    tBestHead.append(headerBestRow);
    bestMatchTable.append(tBestHead);

    // Populate the best match table 
    const bestBodyRow = document.createElement('tr');
    const bestMatchElement = allMatches[header][bestMatchIndexes[header]];

    for (let j =0; j < allMatches[header][0].length; j++) {
        const bestTd = document.createElement('td');

        if (bestMatchElement[j] instanceof Array) {
            bestTd.textContent = bestMatchElement[j][0];
        } else {
            bestTd.textContent = bestMatchElement[j];
        }
        bestBodyRow.appendChild(bestTd);
    }
    tBestBody.appendChild(bestBodyRow);
    bestMatchTable.appendChild(tBestBody);

    // Populate all match table
    allMatches[header].forEach(match => {

        const bodyRow = document.createElement('tr');   

        for (let i =0; i < match.length; i++) {
            const td = document.createElement('td');
            // Strip the array to string
            if (match[i] instanceof Array) {
                td.textContent = match[i][0];
            } else {
                td.textContent = match[i];
            }
            bodyRow.appendChild(td);
        }
        tbody.appendChild(bodyRow);

    });

    table.appendChild(tbody);

    title.textContent = header

    popup.style.display = 'block';
}


const cardButtons = document.querySelectorAll('.card-button');
// This creates a table dynamically when clicked on the corresponding header card 
cardButtons.forEach(button => {
        button.addEventListener('click', function() {
        
        const header = this.dataset.header;
        create_match_tables(header);
       
    });
});


const searchButton = document.getElementById('search-button');
// This create a table dynamically when using the search bar
searchButton.addEventListener('click', function(){
    const header_search = document.getElementById('header-search').value;
    create_match_tables(header_search);
});

const convert_btn  = document.getElementById("convert-button-start");
const loader = document.getElementById("loader_page");

if (convert_btn && loader){
    convert_btn.addEventListener('click', e => {
        console.log('registered button click');
        loader.style.display = 'flex';    
    });
}



const container = document.getElementById('matchContainer');
const resizer = document.getElementById('matchResizer');

let startY, startHeight, isResizing = false;

if (resizer) {
    resizer.addEventListener('mousedown', e => {
    isResizing = true;
    startY = e.clientY;
    startHeight = container.offsetHeight;
    document.addEventListener('mousemove', resize);
    document.addEventListener('mouseup', stopResize);
    });
}


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
