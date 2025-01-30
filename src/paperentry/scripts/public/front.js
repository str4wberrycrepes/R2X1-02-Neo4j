// ephemera.

// Variables
let clientConnected = attemptConnection();

// Buttons
function pushButton() {
    // check if connected
    clientConnected = attemptConnection();
    if(!clientConnected) {
        console.error("Disconnected from server!")
        return
    }

    // Get all keyword textareas
    const keywordInputs = document.querySelectorAll("textarea[name='keywords']");

    let keywords = []

    // Append all keywords from the textareas
    keywordInputs.forEach((textarea) => {
        keywords.push(textarea.value.trim());
    });

    // Compile all data into a json
    message = {
        paper: {
            $: {
                title: document.getElementById("title").value,
                authors: document.getElementById("authors").value,
                resCode: document.getElementById("resCode").value,
                batch: document.getElementById("batch").value,
                address: document.getElementById("address").value
            },
            keyword: keywords
        }
    }

    // Send data to server
    sendData(message);
}

function addButton() {
    // Get button and figure parent
    const button = document.getElementById('addKeyword');
    const keywordsFig = button.closest('figure');

    // Make new textarea
    const textarea = document.createElement('textarea');

    // Add attribs
    textarea.name = 'keywords';
    textarea.id = 'keywords';
    textarea.style.marginTop = '8px';

    // Add the new textarea
    keywordsFig.appendChild(textarea);
}

async function attemptConnection() {
    try {
        const response = await fetch("http://18.136.103.218:5000/api/message");
        const data = await response.json();

        console.log("connected to server.");
        document.querySelector("#ifconnected").innerText = "Status: Connected.";

        return true;
    } catch(err) {
        console.error(err);
        document.querySelector("#ifconnected").innerText = "Status: Error; Disconnected.";

        return false;
    }
}

async function sendData(msg) {
    try {
        const response = await fetch("http://18.136.103.218:5000/api/data", {
            method: "POST", // Send data using POST
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(msg)
        });

        const responseData = await response.json(); // Parse the JSON response

        console.log("Server response:", responseData);
    } catch (err) {
        console.error("Error sending data:", err);
    }
}