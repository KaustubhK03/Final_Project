// document.getElementById("uploadForm").addEventListener("submit", async function (e) {
//     e.preventDefault();

//     const form = e.target;
//     const formData = new FormData(form);

//     const response = await fetch("", {
//         method: "POST",
//         body: formData,
//     });

//     if (response.redirected || response.ok) {
//         const socket = new WebSocket("ws://" + window.location.host + "/ws/run_video");

//         socket.onopen = () => console.log("WebSocket connected");

//         socket.onmessage = (e) => {
//             const data = JSON.parse(e.data);
//             console.log("Prediction data:", data);
//             // Render prediction result here
//         };

//         socket.onclose = () => console.log("WebSocket closed");
//     } else {
//         alert("Video upload failed.");
//     }
// });

const videoInput = document.getElementById("videoInput");
const videoElement = document.getElementById("videoElement");
const canvas = document.getElementById("frameCanvas");
const ctx = canvas.getContext("2d");
let lineY = 200; // Default line Y

videoInput.addEventListener("change", function () {
    const file = videoInput.files[0];
    if (!file) return;

    const url = URL.createObjectURL(file);
    videoElement.src = url;

    videoElement.addEventListener("loadeddata", () => {
        videoElement.currentTime = 0;
    }, { once: true });

    videoElement.addEventListener("seeked", () => {
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        drawLine();
    }, { once: true });
});

// Draw draggable horizontal line
function drawLine() {
    ctx.beginPath();
    ctx.moveTo(0, lineY);
    ctx.lineTo(canvas.width, lineY);
    ctx.strokeStyle = "red";
    ctx.lineWidth = 2;
    ctx.stroke();
}

canvas.addEventListener("click", (e) => {
    const rect = canvas.getBoundingClientRect();
    lineY = e.clientY - rect.top;  // Get Y-coordinate relative to canvas

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    drawLine();
});

// canvas.addEventListener("mousedown", (e) => {
//     const y = e.offsetY;
//     if (Math.abs(y - lineY) < 10) {
//         const onMouseMove = (eMove) => {
//             lineY = eMove.offsetY;
//             ctx.clearRect(0, 0, canvas.width, canvas.height);
//             ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
//             drawLine();
//         };

//         const onMouseUp = () => {
//             canvas.removeEventListener("mousemove", onMouseMove);
//             canvas.removeEventListener("mouseup", onMouseUp);
//         };

//         canvas.addEventListener("mousemove", onMouseMove);
//         canvas.addEventListener("mouseup", onMouseUp);
//     }
// });

// Show modal before upload
document.getElementById("showConfirmModalBtn").addEventListener("click", () => {
    const modal = new bootstrap.Modal(document.getElementById("confirmUploadModal"));
    modal.show();
});

// Form submission
document.getElementById("uploadForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const modalEl = document.getElementById("confirmUploadModal");
    const modalInstance = bootstrap.Modal.getInstance(modalEl);
    modalInstance.hide(); // Hide the modal when uploading

    const formData = new FormData(this);
    formData.append("lineY", lineY);  // Pass user-set line
    formData.append("canvasHeight", canvas.height); 

    const response = await fetch("", {
        method: "POST",
        body: formData,
    });

    if (response.ok) {
        const socket = new WebSocket("ws://" + window.location.host + "/ws/run_video");

        document.getElementById("stopDetectionBtn").classList.remove("d-none");

        socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            const image = new Image();
            image.onload = () => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
            };
            image.src = "data:image/jpeg;base64," + data.frame_image;
        };

        document.getElementById("stopDetectionBtn").onclick = () => {
            socket.close();
            document.getElementById("downloadCsvBtn").classList.remove("d-none");
        };
    } else {
        alert("Upload failed.");
    }
});