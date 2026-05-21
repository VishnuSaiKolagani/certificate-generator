// Add loading state for images
// (This is optional, but included for parity with the original inline script)
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('.certificate-image');
    let loadedCount = 0;
    images.forEach(img => {
        if (img.complete) {
            loadedCount++;
        } else {
            img.addEventListener('load', () => {
                loadedCount++;
            });
            img.addEventListener('error', () => {
                loadedCount++;
            });
        }
    });
    // Close download menu when clicking outside
    document.addEventListener('click', function(e) {
        const menu = document.getElementById('downloadMenu');
        const trigger = e.target.closest('.download-dropdown');
        if (!trigger && menu) {
            menu.style.display = 'none';
        }
    });
});

// Modal functionality for certificate viewing
let currentCertificateFile = null;
let currentSessionId = null;

function openCertificateModal(certFile, certNumber, studentName) {
    currentCertificateFile = certFile;
    
    const modal = document.getElementById('certificateModal');
    const modalImage = document.getElementById('modalImage');
    const modalTitle = document.getElementById('modalTitle');
    const modalStudentName = document.getElementById('modalStudentName');
    const modalCertificateNumber = document.getElementById('modalCertificateNumber');
    
    // Set modal content
    modalTitle.textContent = `Certificate ${certNumber}`;
    modalStudentName.textContent = studentName;
    modalCertificateNumber.textContent = certFile;
    
    // Get session ID from the URL or from the existing image sources
    let sessionId = null;
    const existingImages = document.querySelectorAll('.certificate-image');
    if (existingImages.length > 0) {
        const firstImageSrc = existingImages[0].src;
        const match = firstImageSrc.match(/\/static\/generated\/([^\/]+)\//);
        if (match) {
            sessionId = match[1];
        }
    }
    
    if (sessionId) {
        modalImage.src = `/static/generated/${sessionId}/${certFile}`;
        currentSessionId = sessionId;
    } else {
        console.error('Could not determine session ID');
        modalImage.src = ''; // Fallback
    }
    
    // Show modal
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function closeCertificateModal() {
    const modal = document.getElementById('certificateModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto'; // Restore scrolling
}

function downloadSingleCertificate() {
    if (currentCertificateFile && currentSessionId) {
        // Create a temporary link to download the single certificate
        const link = document.createElement('a');
        link.href = `/static/generated/${currentSessionId}/${currentCertificateFile}`;
        link.download = currentCertificateFile;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('certificateModal');
    if (event.target === modal) {
        closeCertificateModal();
    }
}

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeCertificateModal();
    }
}); 

// Download dropdown toggle
function toggleDownloadMenu() {
    const menu = document.getElementById('downloadMenu');
    if (!menu) return;
    menu.style.display = (menu.style.display === 'block') ? 'none' : 'block';
}