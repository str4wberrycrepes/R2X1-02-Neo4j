// import
const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors()); //enable cross origin
app.use(express.json()); //allow text requests

// get
app.get("/api/message", (req, res) => {
    res.json({ message: "Backend !" });
});

// post
app.post("/api/data", (req, res) => {
    const receivedData = req.body; // Get the JSON data sent from frontend
    console.log("Received data:", receivedData); // Log it on the server

    // Send a response back to the frontend
    res.json({ message: "Data received successfully!", receivedData });
});

// Start the server
const PORT = 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));