// ephemera.

// import
const express = require("express");
const cors = require("cors");
const fs = require("fs");
const xml2js = require("xml2js");

// variables
const xmlFilePath = "../../../../sampledb.xml"

const app = express();
app.use(cors()); //enable cross origin
app.use(express.json()); //allow json requests

// get
app.get("/api/message", (req, res) => {
    res.json({ message: "Hi." });
});

// post
app.post("/api/data", (req, res) => {
    const receivedData = req.body; // Get the JSON data sent from frontend
    console.log("Received data:", receivedData); // Log it on the server

    updateXML(receivedData);

    // Send a response back to the frontend
    res.json({ message: "Data received successfully!", receivedData });
});

// Start the server
const PORT = 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

function updateXML(json) {
    // Read xml file
    fs.readFile(xmlFilePath, 'utf8', (err, data) => {
        // Error handling
        if (err) {
            console.error('Error reading file (XML):', err);
            return;
        }
    
        // Parse XML into object
        xml2js.parseString(data, (err, result) => {
            // Error handling once again (y r computers so finnicky bruh)
            if (err) {
                console.error('Error parsing XML:', err);
                return;
            }
    
            // do NOT ask me I wrote the succeeding 10 lines in an incorrect state of mind

            let resultant = {paper: []};
            id = 0;

            if(result.research_papers.paper) {
                result.research_papers.paper.forEach(element => {
                    resultant.paper.push(element);
                    id++;
                });
            }
            
            json.paper.$.id = id; // add simple id to paper
            resultant.paper.push(json.paper);

            // Convert object back to XML
            const builder = new xml2js.Builder({ headless: true, rootName: "research_papers"});
            const xml = builder.buildObject(resultant);
    
            // Write updated XML back to file
            fs.writeFile(xmlFilePath, xml, 'utf8', err => {
                if (err) {
                    console.error('Error writing to file (XML):', err);
                } else {
                    console.log('XML file updated!');
                }
            });
        });
    });
}
