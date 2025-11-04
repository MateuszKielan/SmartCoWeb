// REMINDER FOR MY FUTURE SELF:::
// REWRITE THIS ABOMINATION OF A CODE
// Thanks (previous self)

// Get input and label fields (guard if not present on this page)
const fileInput = document.getElementById('csv_file')
const fileLabelElement = document.querySelector('.file-label')

if (fileInput && fileLabelElement) {
    fileInput.addEventListener("change", () => {
        fileLabelElement.textContent = fileInput.files[0].name;
    })
}

function toggleSideBar(){
    const navigationSideBar = document.getElementById('navigation-side-bar');
    const overlay = document.getElementById('main-overlay');

    navigationSideBar.classList.toggle('active');
    overlay.classList.toggle('active');
}

const toggleMenuButton = document.getElementById('hamburger');

toggleMenuButton.addEventListener('click', () => {
    toggleSideBar()
})


window.addEventListener('click', (e) => {
    const navigationSideBar = document.getElementById('navigation-side-bar');
    const overlay = document.getElementById('main-overlay');
    
    // If sidebar is open and click is outside sidebar
    if (navigationSideBar.classList.contains('active') && 
        !navigationSideBar.contains(e.target) && 
        e.target !== hamburger) {
        navigationSideBar.classList.remove('active');
        overlay.classList.remove('active');
    }
});

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

            const row = e.target.closest('tr'); 
            // Collect all cell values in this row
            const rowValues = Array.from(row.querySelectorAll('td')).map(td => td.textContent);
            const currentHeader = document.getElementById('match-header-text').textContent;

            console.log(currentHeader)

            // Send the request to django so that it can be stored in the session
            fetch('/store_selected_row/', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ 
                    selected_row: rowValues,
                    current_header: currentHeader
                 })
            });
        }
    });
});


function create_vocabulary_table(vocabularyData) {
    const listOfTitles = ['Vocabulary', 'Average Match Score', ' Nr of Produced Matches', 'Combi Score'];

    const popup = document.getElementById('matchContainer');
    const title = document.getElementById('match-header-text');
    const table = document.getElementById('match-table');

    // Create the table headers
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');
    const headerRow = document.createElement('tr');

    const bestMatchTable = document.getElementById('best-match-table');
    const matchHeaderText = document.getElementById('match-header-text');

    matchHeaderText.textContent = 'Vocabulary ranking';
    bestMatchTable.style.display = 'None';

    table.innerHTML = "";

    listOfTitles.forEach(title => {

        const th = document.createElement('th');
        th.textContent = title;
        headerRow.appendChild(th);

    })
    
    thead.append(headerRow);
    table.append(thead);

    for(const [key, value] of Object.entries(vocabularyData)) {
        const bodyRow = document.createElement('tr'); 
        const data = [key, value[0], value[1], value[2]];

        for (let i = 0; i < data.length; i++) {
            const bodyEntry = document.createElement('td');

            bodyEntry.textContent = data[i];
            bodyRow.appendChild(bodyEntry);
        }
        tbody.appendChild(bodyRow);
    }
    table.appendChild(tbody);

    console.log(vocabularyData);

    popup.style.display = 'block';
};


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
    const listOfTitles = ['prefixedName', 'vocabualry.prefix', 'uri', 'type', 'score'];

    table.innerHTML = "";
    bestMatchTable.innerHTML = "";

     // If the first vocab card was pressed
     if (header == "Vocabularies") {
        // HERE CALL THE FUNCTION to build vocabulary table 
        console.log(vocabCoverageScore);
        console.log(sortedVocabs);

        return;
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

const cardVocabButton = document.getElementById('vocab-card-button');
const cardButtons = document.querySelectorAll('#card-button');

// This creates a table dynamically when clicked on the corresponding header card 
cardButtons.forEach(button => {
    button.addEventListener('click', function() {
        
        const header = this.dataset.header;
        create_match_tables(header);

    });
});

cardVocabButton.addEventListener('click', function() {
    const vocabCoverageScore = JSON.parse(document.getElementById('vocab-coverage-score-data').textContent);
    const sortedVocabs = JSON.parse(document.getElementById('sorted-vocabs-data').textContent);
    const vocabularyData = JSON.parse(document.getElementById('vocabulary-data').textContent);

    create_vocabulary_table(vocabularyData);
});

const searchButton = document.getElementById('search-button');
// This create a table dynamically when using the search bar
searchButton.addEventListener('click', function(){
    const header_search = document.getElementById('header-search').value;
    create_match_tables(header_search);
});


const sourceButton = document.getElementById('source-btn');

// MAYBE ADD THIS in a Function when the row was clicked ?
sourceButton.addEventListener('click', ()=> {
    // Initialize the new tab here
    const newTab = window.open('about:blank', '_blank');

    fetch('/store_selected_row/')  // URL of the Django view
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok' && data.redirect_link) {
            console.log(data.redirect_link)
            newTab.location.href = data.redirect_link 
        } else {
            console.error('Redirect link not found');
        }
    });
});


function loadingScreen() {
    const convert_btn  = document.getElementById("convert-button-start");
    const loader = document.getElementById("loader_page");

    if (convert_btn && loader){
        loader.style.display = 'flex';    
    }
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
