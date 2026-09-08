const express = require("express");
const cors = require("cors");
const crypto = require("crypto");
const { MongoClient } = require("mongodb");

const app = express();
const port = 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

const MONGODB_URI =
    "mongodb+srv://202351049_db_user:jb202351049@cluster0.32ckfvu.mongodb.net/?appName=Cluster0";

const client = new MongoClient(MONGODB_URI);

let collection;

async function start() {
    await client.connect();

    const database = client.db("credential_lab");
    collection = database.collection("login_attempts");

    console.log("MongoDB connected");

    app.listen(port, () => {
        console.log(`Server running at http://localhost:${port}`);
    });
}

app.post("/login-attempt", async (req, res) => {
    try {
        const { email, passwordEntered } = req.body;

        const passwordHash = crypto
            .createHash("sha256")
            .update(passwordEntered || "")
            .digest("hex");

        await collection.insertOne({
            email: email || "",
            passwordHash: passwordHash,
            timestamp: new Date()
        });

        res.json({ success: true });

    } catch (error) {
        console.error(error);
        res.status(500).json({ success: false });
    }
});

start().catch(console.error);