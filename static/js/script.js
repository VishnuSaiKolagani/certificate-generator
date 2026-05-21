const canvas = document.getElementById("editorCanvas");
const ctx = canvas.getContext("2d");
const layout = {};
const history = [];
let currentImage = null;

// Parse embedded JSON data for session restoration
;(function restoreGlobalsFromJson() {
    try {
        var formDataNode = document.getElementById('formDataJson');
        var sessionDataNode = document.getElementById('sessionDataJson');
        if (formDataNode) {
            window.formData = JSON.parse(formDataNode.textContent || 'null');
        }
        if (sessionDataNode) {
            window.sessionData = JSON.parse(sessionDataNode.textContent || 'null');
        }
    } catch (e) {
        // Fallback to nulls on parse failure
        window.formData = window.formData || null;
        window.sessionData = window.sessionData || null;
    }
})();

document.getElementById("bgInput").addEventListener("change", function(e) {
    const reader = new FileReader();
    reader.onload = function(event) {
        const img = new Image();
        img.onload = function() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            currentImage = img;
            redrawAll();
        };
        img.src = event.target.result;
    };
    reader.readAsDataURL(e.target.files[0]);
});

canvas.addEventListener("click", function(e) {
    const field = document.getElementById("fieldText").value.trim();
    if (field) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const cleanField = field.replace(/[()]/g, "");
        
        // Handle signature field naming
        if (cleanField.toLowerCase() === 'signature') {
            // Check if this is the first signature or a numbered one
            const existingSignatures = Object.keys(layout).filter(key => key.startsWith('signature'));
            if (existingSignatures.length === 0) {
                layout['signature'] = [x, y];
                history.push('signature');
            } else {
                // Find the next available signature number
                let sigNumber = 2;
                while (layout[`signature${sigNumber}`]) {
                    sigNumber++;
                }
                layout[`signature${sigNumber}`] = [x, y];
                history.push(`signature${sigNumber}`);
            }
        } else {
            layout[cleanField] = [x, y];
            history.push(cleanField);
        }
        redrawAll();
    }
});

function addField() {
    const fieldText = document.getElementById("fieldText").value.trim();
    if (!fieldText) {
        alert("Please enter a field name (e.g., name, event, date, signature) in the text box first.");
        return;
    }
    
    if (fieldText.toLowerCase() === 'signature') {
        const existingSignatures = Object.keys(layout).filter(key => key.startsWith('signature'));
        const sigNumber = existingSignatures.length + 1;
        alert(`Now click on the canvas where you want to place Signature ${sigNumber}. You can add multiple signatures by typing "signature" again and clicking different positions.`);
    } else {
        alert("Now click on the canvas where you want to place the '" + fieldText + "' text.");
    }
}

function undoField() {
    const last = history.pop();
    if (last) {
        delete layout[last];
        redrawAll();
    }
}

function saveLayout() {
    if (Object.keys(layout).length === 0) {
        alert("No layout to save. Please add some fields first.");
        return;
    }
    
    fetch('/save_layout', {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(layout)
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            alert("Layout saved successfully!");
        } else {
            alert("Error saving layout: " + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Error saving layout. Please try again.");
    });
}

function redrawAll() {
    if (currentImage) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(currentImage, 0, 0, canvas.width, canvas.height);
        ctx.font = "20px Arial";
        ctx.fillStyle = "black";
        for (let key in layout) {
            let [x, y] = layout[key];
            if (key.startsWith('signature')) {
                // Draw signature placeholder differently
                ctx.fillStyle = "red";
                ctx.font = "16px Arial";
                const sigNumber = key === 'signature' ? '1' : key.replace('signature', '');
                ctx.fillText(`✍️ SIGNATURE ${sigNumber}`, x, y);
                ctx.fillStyle = "black";
                ctx.font = "20px Arial";
            } else {
                ctx.fillText(key, x, y);
            }
        }
    }
}

function toggleMenu() {
  const menu = document.getElementById("dropdownMenu");
  menu.style.display = (menu.style.display === "block") ? "none" : "block";
}

// Optional: Close menu if clicked outside
window.addEventListener("click", function(e) {
  if (!e.target.closest('.menu-container')) {
    document.getElementById("dropdownMenu").style.display = "none";
  }
});

window.addEventListener('DOMContentLoaded', function() {
    // Restore layout if available
    fetch('/static/uploads/layout.json')
        .then(response => response.json())
        .then(savedLayout => {
            let restored = false;
            for (let key in savedLayout) {
                layout[key] = savedLayout[key];
                history.push(key);
                restored = true;
            }
            if (restored) {
                redrawAll();
                const info = document.getElementById('restoredFieldsInfo');
                if (info) info.style.display = 'block';
            }
        })
        .catch(() => {});

    // Restore previous template image on canvas if available (when coming back from review)
    if (window.sessionData && window.formData && window.formData.template_filename) {
        var sessionId = window.sessionData.session_id;
        var templateFilename = window.formData.template_filename;
        if (sessionId && templateFilename) {
            var img = new Image();
            img.onload = function() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                currentImage = img;
                redrawAll();
            };
            img.src = '/static/generated/' + sessionId + '/' + templateFilename;
        }
    }
});

// Template image preview and auto-canvas load
const templateInput = document.getElementById('templateInput');

if (templateInput) {
    templateInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                // Draw on canvas as background
                const img = new Image();
                img.onload = function() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    currentImage = img;
                    redrawAll();
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        } else {
            // clear canvas background
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            currentImage = null;
            redrawAll();
        }
    });
}

// Ensure preview is shown when restoring from session
if (window.sessionData && window.formData && window.formData.template_filename) {
    var sessionId = window.sessionData.session_id;
    var templateFilename = window.formData.template_filename;
    if (sessionId && templateFilename) {
        var img2 = new Image();
        img2.onload = function() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img2, 0, 0, canvas.width, canvas.height);
            currentImage = img2;
            redrawAll();
        };
        img2.src = '/static/generated/' + sessionId + '/' + templateFilename;
    }
}

