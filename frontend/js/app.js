const API_BASE_URL = "http://127.0.0.1:8000";

// Helper function to prevent XSS attacks when rendering text
function escapeHTML(str) {
    if (!str) return "";

    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ==================================================
// UPLOAD DOCUMENT
// ==================================================

const uploadButton = document.getElementById("uploadButton");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");

if (uploadButton && fileInput && uploadStatus) {
    uploadButton.addEventListener("click", async function () {
        const file = fileInput.files[0];

        if (!file) {
            uploadStatus.textContent = "Please select a file first.";
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        uploadButton.disabled = true;
        uploadStatus.textContent = "Uploading...";

        try {
            const response = await fetch(`${API_BASE_URL}/documents/upload`, {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                uploadStatus.textContent = data.detail || "Upload failed.";
                return;
            }

            uploadStatus.textContent =
                `Upload successful. ${data.chunk_count} chunk(s) indexed.`;

            fileInput.value = "";

            await loadDocuments();

        } catch (error) {
            console.error("Upload error:", error);
            uploadStatus.textContent = "Unable to connect to the backend.";
        } finally {
            uploadButton.disabled = false;
        }
    });
}

// ==================================================
// SEARCH DOCUMENTS
// ==================================================
// ==================================================
// SEARCH DOCUMENTS
// ==================================================

const searchButton = document.getElementById("searchButton");
const searchInput = document.getElementById("searchInput");
const resultsContainer = document.getElementById("resultsContainer");

// Search button click event
if (searchButton && searchInput && resultsContainer) {

    searchButton.addEventListener("click", function () {

        console.log("Search button clicked");

        searchDocuments(searchInput, resultsContainer);

    });

    // Search when Enter key is pressed
    searchInput.addEventListener("keydown", function (event) {

        if (event.key === "Enter") {

            event.preventDefault();

            searchDocuments(searchInput, resultsContainer);

        }

    });

} else {

    console.error("Search elements not found. Check HTML element IDs.");

}

async function searchDocuments(
    inputEl = typeof searchInput !== "undefined"
        ? searchInput
        : document.getElementById("searchInput"),

    containerEl = typeof resultsContainer !== "undefined"
        ? resultsContainer
        : document.getElementById("results")
) {
    if (!inputEl || !containerEl) return;

    const query = inputEl.value.trim();

    const documentTypeFilter =
        document.getElementById("documentTypeFilter");

    const selectedType = documentTypeFilter
        ? documentTypeFilter.value
        : "all";

    if (!query) {
        containerEl.innerHTML =
            "<p class='empty-message'>Please enter a search query.</p>";
        return;
    }

    containerEl.innerHTML =
        "<p class='empty-message'>Searching...</p>";

    try {
        const url =
            `${API_BASE_URL}/search/?query=${encodeURIComponent(query)}&top_k=5&document_type=${encodeURIComponent(selectedType)}`;

        console.log("Search URL:", url);

        const response = await fetch(url);

        console.log("Search response status:", response.status);

        let data = {};
        const contentType = response.headers.get("content-type");

        if (contentType && contentType.includes("application/json")) {
            data = await response.json().catch(() => ({}));
        }

        console.log("Search response data:", data);

        if (!response.ok) {
            const safeEscape = typeof escapeHTML === "function"
                ? escapeHTML
                : (str) => String(str ?? "")
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;");

            const errorMsg = safeEscape(
                data.detail || `Server error (Status: ${response.status})`
            );

            containerEl.innerHTML =
                `<p class='empty-message'>Search failed: ${errorMsg}</p>`;

            return;
        }

        const results = Array.isArray(data)
            ? data
            : data.results;

        displayResults(results, containerEl);

        saveSearchHistory(query);

    } catch (error) {
        console.error("Search error:", error);

        containerEl.innerHTML =
            "<p class='empty-message'>Unable to connect to the backend. Check whether the backend is running.</p>";
    }
}
// ==================================================
// DISPLAY SEARCH RESULTS
// ==================================================
function displayResults(
    results,
    container = document.getElementById("resultsContainer")
) {
    if (!container) return;

    const safeEscape = typeof escapeHTML === "function"
        ? escapeHTML
        : (str) => String(str ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    if (!Array.isArray(results) || results.length === 0) {
        container.innerHTML =
            "<p class='empty-message'>No matching documents found.</p>";
        return;
    }

    const fragment = document.createDocumentFragment();

    results.forEach(function (result, index) {

        const resultElement = document.createElement("div");
        resultElement.className = "result";

        const filename = safeEscape(
            result.filename || "Unknown document"
        );

        const documentType = safeEscape(
            result.document_type || "Unknown"
        );

        const matchingChunkCount = safeEscape(
            result.matching_chunk_count ?? 0
        );

        const distance = typeof result.distance === "number"
            ? result.distance.toFixed(4)
            : "N/A";

        const similarityValue = typeof result.similarity_score === "number"
            ? Math.max(0, Math.min(100, result.similarity_score))
            : null;

        const similarity = similarityValue !== null
            ? similarityValue.toFixed(2) + "%"
            : "N/A";

        const progressWidth = similarityValue !== null
            ? similarityValue
            : 0;

        const snippet = highlightText(
            result.chunk || "No matching text available.",
            searchInput ? searchInput.value : ""
        );

        resultElement.innerHTML = `
            <div class="result-header">
                <span class="result-number">#${index + 1}</span>
                <h3>${filename}</h3>
            </div>

            <div class="result-label">Document type</div>
            <p>${documentType}</p>

            <div class="result-label">Matching text</div>
            <p class="result-snippet">${snippet}</p>

            <div class="similarity-section">
                <div class="similarity-header">
                    <span>Similarity Score</span>
                    <strong>${similarity}</strong>
                </div>

                <div class="similarity-bar">
                    <div
                        class="similarity-fill"
                        style="width: ${progressWidth}%"
                    ></div>
                </div>
            </div>

            <div class="result-score">
                <span class="score-label">Vector distance</span>
                <span class="score-value">${distance}</span>
            </div>

            <div class="result-score">
                <span class="score-label">Matching chunks</span>
                <span class="score-value">${matchingChunkCount}</span>
            </div>

            <div class="result-note">
                ${index === 0
                    ? "Top matching result"
                    : "Additional matching result"}
            </div>
        `;

        fragment.appendChild(resultElement);
    });

    container.innerHTML = "";
    container.appendChild(fragment);
}
function highlightText(text, query) {
    const safeText = escapeHTML(text);

    const words = query
        .trim()
        .split(/\s+/)
        .filter(word => word.length > 2);

    let highlightedText = safeText;

    words.forEach(function (word) {
        const escapedWord = word.replace(
            /[.*+?^${}()|[\]\\]/g,
            "\\$&"
        );

        const regex = new RegExp(
            `(${escapedWord})`,
            "gi"
        );

        highlightedText = highlightedText.replace(
            regex,
            "<mark>$1</mark>"
        );
    });

    return highlightedText;
}

// ==================================================
// LOAD DOCUMENTS
// ==================================================

const documentsContainer = document.getElementById("documents");

async function loadDocuments() {
    if (!documentsContainer) return;

    try {
        const response = await fetch(`${API_BASE_URL}/documents/`);
        const data = await response.json();

        if (!response.ok) {
            console.error("Documents API error:", data);

            documentsContainer.innerHTML =
                '<p class="empty-message">Unable to load documents.</p>';

            return;
        }

        displayDocuments(data.documents);

    } catch (error) {
        console.error("Document loading error:", error);

        documentsContainer.innerHTML =
            '<p class="empty-message">Unable to connect to the backend.</p>';
    }
}

// ==================================================
// DISPLAY DOCUMENTS
// ==================================================

function displayDocuments(documents) {
    if (!documentsContainer) return;

    if (!documents || documents.length === 0) {
        documentsContainer.innerHTML =
            '<p class="empty-message">No documents uploaded.</p>';

        return;
    }

    documentsContainer.innerHTML = "";

    documents.forEach(function (doc) {
        const documentElement = document.createElement("div");
        documentElement.className = "result";

        documentElement.innerHTML = `
            <div class="result-header">
                <h3>${escapeHTML(doc.filename)}</h3>
            </div>

            <p>${doc.chunk_count} chunk(s) indexed</p>

            <button
                type="button"
                class="preview-button">
                Preview
            </button>

            <button
                type="button"
                class="delete-button">
                Delete
            </button>

            <div class="preview-content"></div>
        `;

        const previewButton =
            documentElement.querySelector(".preview-button");

        const deleteButton =
            documentElement.querySelector(".delete-button");

        previewButton.addEventListener("click", function () {
            previewDocument(
                doc.filename,
                previewButton,
                documentElement.querySelector(".preview-content")
            );
        });

        deleteButton.addEventListener("click", function () {
            deleteDocument(doc.filename, deleteButton);
        });

        documentsContainer.appendChild(documentElement);
    });
}

// ==================================================
// PREVIEW DOCUMENT
// ==================================================

async function previewDocument(filename, button, previewContent) {
    if (!filename || !button || !previewContent) return;

    button.disabled = true;
    previewContent.textContent = "Loading preview...";

    try {
        const response = await fetch(
            `${API_BASE_URL}/documents/${encodeURIComponent(filename)}/preview`
        );

        if (!response.ok) {
            previewContent.textContent = "Unable to load document preview.";
            return;
        }

        const data = await response.json();
        const preview = data.preview ?? data.content ?? data.text ?? "";
        previewContent.textContent = String(preview) || "No preview available.";
    } catch (error) {
        console.error("Document preview error:", error);
        previewContent.textContent = "Unable to connect to the backend.";
    } finally {
        button.disabled = false;
    }
}
window.addEventListener("DOMContentLoaded", function () {
    loadDocuments();
});
// ==================================================
// DELETE DOCUMENT
// ==================================================

async function deleteDocument(filename, button) {
    if (!filename || !button) return;

    const confirmed = confirm(
        `Are you sure you want to delete "${filename}"?`
    );

    if (!confirmed) {
        return;
    }

    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = "Deleting...";

    try {
        const response = await fetch(
            `${API_BASE_URL}/documents/${encodeURIComponent(filename)}`,
            {
                method: "DELETE"
            }
        );

        let data = {};
        // Safely attempt to parse JSON response body if content exists
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            data = await response.json().catch(() => ({}));
        }

        if (!response.ok) {
            alert(data.detail || `Unable to delete document. (Status: ${response.status})`);
            return;
        }

        alert("Document deleted successfully.");

        // Reload document list after successful deletion
        if (typeof loadDocuments === "function") {
            await loadDocuments();
        }

    } catch (error) {
        console.error("Document deletion error:", error);
        alert("Unable to connect to the backend.");
    } finally {
        // Reset button state only if element is still connected to the DOM
        if (button && button.isConnected) {
            button.disabled = false;
            button.textContent = originalText;
        }
    }
}
// ==========================================
// SEARCH HISTORY USING LOCAL STORAGE
// ==========================================

const HISTORY_KEY = "semanticSearchHistory";

// Get saved search history
function getSearchHistory() {
    return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
}

// Save a new search query
function saveSearchHistory(query) {
    let history = getSearchHistory();

    // Avoid duplicate consecutive searches
    history = history.filter(item => item !== query);

    history.unshift(query);

    // Keep only the latest 10 searches
    history = history.slice(0, 10);

    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));

    displaySearchHistory();
}

// Display search history
function displaySearchHistory() {
    const historyContainer = document.getElementById("searchHistory");

    if (!historyContainer) return;

    const history = getSearchHistory();

    historyContainer.innerHTML = "";

    if (history.length === 0) {
        historyContainer.textContent = "No search history available.";
        return;
    }

    history.forEach(function (query) {
        const item = document.createElement("div");
        item.className = "history-item";

        const queryText = document.createElement("span");
        queryText.textContent = query;

        const searchAgainButton = document.createElement("button");
        searchAgainButton.textContent = "Search Again";

        searchAgainButton.addEventListener("click", function () {
            searchInput.value = query;
            searchDocuments();
        });

        item.appendChild(queryText);
        item.appendChild(searchAgainButton);

        historyContainer.appendChild(item);
    });
}

// Clear search history
const clearHistoryButton =
    document.getElementById("clearHistoryButton");

if (clearHistoryButton) {
    clearHistoryButton.addEventListener("click", function () {
        localStorage.removeItem(HISTORY_KEY);
        displaySearchHistory();
    });
}

// Load history when website opens
displaySearchHistory();