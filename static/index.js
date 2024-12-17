
let data;
let isRecording = false;
let canvas, ctx;

const player = videojs("videoElement", {
    controls: false,
    fluid: true,
    autoMuteDevice: true,
    // videoMimeType: "video/webm;codecs=H264",
    videoMimeType: "video/mp4",
    plugins: {
        record: {
            audio: false,
            video: true,
            maxLength: 100,
            debug: false,
            timeSlice: 1000,
            // videoMimeType: "video/mp4",
            // videoRecorderType: 'auto',
        }
    }
}, function () {
    // print version information at startup
    let msg = 'Using video.js ' + videojs.VERSION +
        ' with videojs-record ' + videojs.getPluginVersion('record') +
        ' and recordrtc ' + RecordRTC.version;
    videojs.log(msg);
});

player.on('deviceError', function () {
    console.warn('Device error:', player.deviceErrorCode);
});
player.on('error', function (error) {
    console.log('Error:', error);
});
player.on('deviceReady', () => {
    console.log('device is ready!');
    player.record().start();
});
player.on('timestamp', async function () {
    data = player.recordedData;
    console.log(data)

    if (data && data.length > 0) {
        let binaryData = data.at(-1);

        console.log(binaryData)

        let formData = new FormData();
        formData.append('stream', binaryData);

        const results = await sendToServer(formData);
        drawResults(results)
    }
});
player.on('finishRecord', async function () {
    console.log('finished recording: ', player.recordedData);

    let formData = new FormData();
    formData.append('stream', player.recordedData);

    sendToServer(formData)

    const results = await sendToServer(formData);
    drawResults(results)
});

function drawResults(detections) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    detections.forEach(obj => {
        const { class: className, confidence, box } = obj;
        const [x1, y1, x2, y2] = box;

        // Draw bounding box
        ctx.strokeStyle = 'red'; // Set the box color
        ctx.lineWidth = 2; // Set the box line width
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1); // Draw the rectangle

        // Draw label with confidence
        ctx.fillStyle = 'red'; // Set the text color
        ctx.font = '16px Poppins'; // Set the font style
        ctx.fillText(`${className} (${(confidence * 100).toFixed(1)}%)`, x1, y1 - 10); // Draw the label above the box
    });
}


async function startRecording() {
    try {
        if (!player.record) {
            throw new Error("Recording plugin not initialized.");
        }

        document.getElementById("wrapper").style.display = "block";
        canvas = document.getElementById("canvas");
        ctx = canvas.getContext("2d");
        resizeCanvas();
        player.record().getDevice();
    } catch (error) {
        console.error("Error starting recording:", error);
    }
}


function stopRecording() {
    try {
        if (player.record().isRecording()) {
            player.record().stop();
        }

        player.record().stopDevice();
        player.reset();

        document.getElementById("wrapper").style.display = "none";
        ctx?.clearRect(0, 0, canvas.width, canvas.height); // Clear canvas
    } catch (error) {
        console.error("Error stopping recording:", error);
    }
}

async function sendToServer(formData) {
    try {
        const API_BASE_URL = "http://127.0.0.1:8000"
        const response = await fetch(`${API_BASE_URL}/stream/`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        return data?.detections ?? [];
    } catch (error) {
        console.error("Error sending video data to server:", error);
        return [];
    }
}



function toggleRecording() {
    const btn = document.getElementById("recordToggleBtn");
    if (!isRecording) {
        isRecording = true;
        startRecording();
        btn.innerText = "Stop";
    } else {
        isRecording = false;
        stopRecording();
        btn.innerText = "Start";
    }
}

function resizeCanvas() {
    const video = videoElement;

    if (video.videoWidth > 0 && video.videoHeight > 0) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
    }
}

window.addEventListener('resize', resizeCanvas);