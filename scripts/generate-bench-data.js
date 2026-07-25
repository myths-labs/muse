const fs = require('fs');

const updateTemplates = [
    { old: "The server IP is 192.168.1.10.", new: "The server IP has changed to 10.0.0.5.", q: "What is the server IP?", ans: "10.0.0.5" },
    { old: "Alice's favorite color is blue.", new: "Alice's favorite color is now green.", q: "What is Alice's favorite color?", ans: "green" },
    { old: "The project code is X99.", new: "The project code was updated to Y77.", q: "What is the project code?", ans: "Y77" },
    { old: "Meeting is on Tuesday.", new: "Meeting is rescheduled to Friday.", q: "When is the meeting?", ans: "Friday" },
    { old: "Admin password is 'qwerty'.", new: "Admin password has been securely reset to 'admin123'.", q: "What is the admin password?", ans: "admin123" }
];

const temporalTemplates = [
    {
        expired: "[TEMPORAL:2025-01-01] The discount code is NY2025.",
        active: "[FACT] The standard price is $99.",
        q: "What is the discount code?",
        ans: "I don't know / none active / not provided"
    },
    {
        expired: "[TEMPORAL:2026-03-23] The API key is ABC.",
        active: "[TEMPORAL:2026-12-31] The API key is DEF.",
        q: "What is the API key?",
        ans: "DEF"
    },
    {
        expired: "[TEMPORAL:2026-03-01] Launch is delayed.",
        active: "[FACT] Launch is currently scheduled for May.",
        q: "When is the launch?",
        ans: "May"
    },
    {
        expired: "[TEMPORAL:2024-05-05] The database is down.",
        active: "[FACT] The database is operational.",
        q: "Is the database down?",
        ans: "operational / no / not / running"
    },
    {
        expired: "[TEMPORAL:2025-09-09] User is on vacation.",
        active: "[FACT] User is at work.",
        q: "Is the user on vacation?",
        ans: "work / no / off"
    }
];

let items = [];
let idCounter = 1;

for (let i = 0; i < 500; i++) {
    const t = updateTemplates[i % updateTemplates.length];

    // Vary the text slightly so it's not perfectly uniform
    const prefix = i % 2 === 0 ? "User stated: " : "Note: ";

    const oldFact = `[FACT] ${prefix}${t.old}`;
    const newFact = `[FACT] ${prefix}${t.new}`;

    const ragContext = `${oldFact}\n${newFact}`;
    const museContext = `~~${oldFact}~~ (historical)\n${newFact}`;

    items.push({
        id: `update-${idCounter++}`,
        category: 'update',
        question: t.q,
        expected_answer_contains: t.ans,
        rag_context: ragContext,
        muse_context: museContext
    });
}

for (let i = 0; i < 500; i++) {
    const t = temporalTemplates[i % temporalTemplates.length];

    const r = i % 3;
    const padding = r === 0 ? "" : r === 1 ? "\n[FACT] The weather is nice.\n" : "\n[DECISION] Log it.\n";

    const ragContext = `${t.expired}${padding}\n${t.active}`;
    const museContext = `${padding}\n${t.active}`;

    items.push({
        id: `temporal-${idCounter++}`,
        category: 'temporal',
        question: t.q,
        expected_answer_contains: t.ans,
        rag_context: ragContext,
        muse_context: museContext
    });
}

fs.writeFileSync(__dirname + '/bench-data.json', JSON.stringify(items, null, 2));
console.log(`Generated ${items.length} benchmark cases to scripts/bench-data.json`);
