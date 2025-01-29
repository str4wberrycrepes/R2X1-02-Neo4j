clientip = ""

// Fetch the IP address from the API
fetch("https://api.ipify.org?format=json")
.then(response => response.json())
.then(data => {
    clientip = data.ip;
})
.catch(error => {
    console.error("Error fetching IP address:", error);
});

document.getElementById("pushButton").addEventListener("click", function () {
    // Get input values from the textareas
    const title = document.getElementById("title").value;
    const authors = document.getElementById("authors").value;
    const resCode = document.getElementById("resCode").value;
    const batch = document.getElementById("batch").value;
    const address = document.getElementById("address").value;

    // Get all keyword textareas
    const keywordTextareas = document.querySelectorAll("textarea[name='keywords']");

    // Create a new XML DOM document
    const parser = new DOMParser();
    const serializer = new XMLSerializer();

    // Load the base XML (I do NOT know why the tags needa be indented like this nor do I care)
    const xmlString = `<?xml version="1.0" encoding="UTF-8"?> 
<research_papers>
</research_papers>`;
    const xmlDoc = parser.parseFromString(xmlString, "application/xml");

    // Create the <paper> element
    const paperElement = xmlDoc.createElement("paper");
    paperElement.setAttribute("name", title || "NONE");
    paperElement.setAttribute("batch", batch || "NONE");

    // Create and append <address> element
    const addressElement = xmlDoc.createElement("address");
    addressElement.textContent = address;
    paperElement.appendChild(addressElement);

    // Create and append <authors> element
    const authorsElement = xmlDoc.createElement("authors");
    authorsElement.textContent = authors;
    paperElement.appendChild(authorsElement);

    // Create and append <keyword> elements for each keyword textarea
    keywordTextareas.forEach((textarea) => {
        const keywordElement = xmlDoc.createElement("keyword");
        keywordElement.textContent = textarea.value.trim(); // Trim to remove unnecessary spaces
        paperElement.appendChild(keywordElement);
    });

    // Append the new <paper> element to the <research_papers> root
    const root = xmlDoc.getElementsByTagName("research_papers")[0];
    root.appendChild(paperElement);

    // Serialize the updated XML document to a string
    const updatedXmlString = formatXml(serializer.serializeToString(xmlDoc));

    // Log the updated XML string to the console (or use it as needed)
    console.log(updatedXmlString);

    fetchMessage();
    sendMessage(updatedXmlString);

    const figcaption = document.querySelector("#push figcaption");
    figcaption.textContent = "Pushed Successfully!";
});

async function fetchMessage() {
    try {
        const response = await fetch("http://localhost:5000/api/message");
        const data = await response.json();
        console.log(data);
    } catch(err) {
        console.error(error)
    }
}

async function sendMessage(xml) {
    message = {
        xml: xml,
        source: clientip
    }

    try {
        const response = await fetch("http://localhost:5000/api/data", {
            method: "POST", // Send data using POST
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(message)
        });

        const responseData = await response.json(); // Parse the JSON response
        console.log("Server response:", responseData);
    } catch (error) {
        console.error("Error sending data:", error);
    }
}

// I stole this from the internet
function formatXml(xml) {
    const PADDING = "  ";
    const reg = /(>)(<)(\/*)/g;
    let formatted = "";
    let pad = 0;

    xml = xml.replace(reg, "$1\n$2$3");
    xml.split("\n").forEach((node) => {
        let indent = 0;
        if (node.match(/.+<\/\w[^>]*>$/)) {
            indent = 0;
        } else if (node.match(/^<\/\w/)) {
            pad -= 1;
        } else if (node.match(/^<\w([^>]*[^/])?>.*$/)) {
            indent = 1;
        } else {
            indent = 0;
        }

        formatted += PADDING.repeat(pad) + node + "\n";
        pad += indent;
    });

    return formatted.trim();
}
