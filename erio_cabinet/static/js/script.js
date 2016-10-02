'use strict';

function createNode(html) {
    var node = document.createElement('div');
    node.outerHTML = html;
    return node;
}

document.addEventListener('DOMContentLoaded', function () {
    const body = document.querySelector('body');
    const title = document.querySelector('h1');
    const form = document.querySelector('form');
    const fileFormHTML = document.querySelector('#form-file').outerHTML;
    const submitButton = document.querySelector('#btn-submit');
    const submitButtonWrapper = document.querySelector('#form-submit');

    submitButton.addEventListener('click', function (evt) {
        evt.preventDefault();
        let fileForm = document.querySelector('#form-file');
        let file = fileForm.querySelector('#file-select').files[0];

        let flashes = document.querySelector('.flashes');
        console.log(file);
        if (!file) {
            if (!flashes || !flashes.querySelector('.error')) {
                let node = document.createElement('div');
                node.innerHTML = '<ul class="flashes"><li class="error">No file selected</li></ul>';
                node = node.childNodes[0];
                title.parentNode.insertBefore(node, title)
            }
            return false;
        }

        // Clean flashes
        if (flashes) {
            flashes.outerHTML = '';
        }

        // Replace selector for file upload progress
        fileForm.innerHTML = '<progress value="0" max="100"></progress>';
        // Save selector to progress dialog
        let progress = fileForm.querySelector('progress');
        // Change class
        fileForm.id = '';
        fileForm.className = 'form-upload';
        // Add new file upload form
        let node = document.createElement('div');
        node.innerHTML = fileFormHTML;
        node = node.childNodes[0];
        form.insertBefore(node, submitButtonWrapper);

        // Start XHR
        let xhr = new XMLHttpRequest();
        let formData = new FormData();
        formData.append('file', file);
        xhr.addEventListener('load', function (evt) {
            let resp = JSON.parse(xhr.responseText);
            fileForm.innerHTML = `<a href="${resp.url}">${resp.url}</a>`
        });
        xhr.addEventListener('error', function (evt) {
            fileForm.innerHTML = '<p class="error">Upload failed.</p>'
        });
        xhr.addEventListener('progress', function (evt) {
            if (evt.lengthComputable) {
                console.log(evt.loaded / evt.total);
                progress.value = evt.loaded / evt.total;
            }
        });

        // Do the POST
        xhr.open('POST', '/upload', true);
        xhr.setRequestHeader("Accept", "application/json");
        xhr.send(formData);
    });
});