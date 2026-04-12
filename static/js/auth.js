// =============================================
// MOUIN 360 — Auth Pages JavaScript
// Handles the Pannellum 360° background viewer
// =============================================

// Read panorama image path from the data attribute on the body
(function () {
    const panoramaUrl = document.body.dataset.panorama;
    if (typeof pannellum !== 'undefined' && panoramaUrl) {
        pannellum.viewer('panorama', {
            type: 'equirectangular',
            panorama: panoramaUrl,
            autoLoad: true,
            autoRotate: -2,
            showControls: false,
            mouseZoom: false,
            draggable: false,
            disableKeyboardCtrl: true
        });
    }
})();
