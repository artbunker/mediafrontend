'use strict';

document.documentElement.classList.add('scripts_enabled');

let tags = document.querySelector('.tags');
// restrict tags wrapper to the width of its associated medium
//TODO wait until summary is fully loaded to get accurate width
tags.style.display = 'none';
tags.style.width = tags.parentNode.querySelector('.medium').clientWidth + 'px';
tags.style.display = '';
