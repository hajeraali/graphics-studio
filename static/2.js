document.addEventListener('DOMContentLoaded', function() {
    // Event listeners for sliders
    document.getElementById('blurSlider').addEventListener('input', function() {
        processImage('blur', this.value);
    });

    document.getElementById('contrastSlider').addEventListener('input', function() {
        processImage('contrast', this.value);
    });

    document.getElementById('sharpenSlider').addEventListener('input', function() {
        processImage('sharpen', this.value);
    });

    document.getElementById('invertSlider').addEventListener('input', function() {
        processImage('invert', this.value);
    });

    document.getElementById('detectWhiteCheckbox').addEventListener('change', function() {
        if (this.checked) {
            processImage('detect_white', 0); // Pass a dummy value, as threshold value is not used
        }
    });
    document.getElementById('detectColor').addEventListener('input', function() {
        const colorValue = this.value;
        processImage('detect_color', colorValue);
    });
    

    // Function to process image based on operation and value
    function processImage(operation, value) {
        const originalFilename = document.getElementById('originalImage').dataset.filename;

        fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename: originalFilename, operation: operation, value: value })
        }).then(response => response.json())
          .then(data => {
              document.getElementById('processedImage').src = data.processedImagePath + '?' + new Date().getTime(); // Add a timestamp to ensure the image reloads
              document.getElementById('processedImage').dataset.filename = data.newProcessedFilename;
          }).catch(error => console.error('Error:', error));
    }

    // Initial image upload handling
    document.getElementById('uploadForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);

        fetch('/upload', {
            method: 'POST',
            body: formData
        }).then(response => response.blob())
          .then(blob => {
              const url = URL.createObjectURL(blob);
              document.getElementById('originalImage').src = url;
              document.getElementById('processedImage').src = ''; // Reset processed image
              document.getElementById('originalImage').dataset.filename = formData.get('image').name;
          }).catch(error => console.error('Error:', error));
    });
});
