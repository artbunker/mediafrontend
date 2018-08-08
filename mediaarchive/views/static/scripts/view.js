'use strict';

document.documentElement.classList.add('scripts_enabled');

let tags = document.querySelector('.tags');
// restrict tags wrapper to the width of its associated medium
//TODO wait until summary is fully loaded to get accurate width
tags.style.display = 'none';
tags.style.width = tags.parentNode.querySelector('.medium').clientWidth + 'px';
tags.style.display = '';

// blacklisted tags
let blacklisted_tags = localStorage.getItem('media_preference_blacklisted_tags');
if (blacklisted_tags) {
	blacklisted_tags = blacklisted_tags.split('#');
	let medium_tags = document.querySelectorAll('.tags .tag');
	for (let i = 0; i < medium_tags.length; i++) {
		if (-1 < blacklisted_tags.indexOf(medium_tags[i].dataset.tag)) {
			document.querySelector('.medium').classList.add('blacklist');
			break;
		}
	}
}
// auto slideshow
let slideshow_delay_s = localStorage.getItem('media_preference_slideshow_delay_s');
let medium_prev = document.querySelector('#medium_prev');
let medium_next = document.querySelector('#medium_next');
if (slideshow_delay_s) {
	if ('backward' != localStorage.getItem('media_slideshow_direction')) {
		if (medium_next) {
			setTimeout(() => {
				window.location = (medium_next.href);
			}, slideshow_delay_s * 1000);
		}
	}
	else if (medium_prev) {
		setTimeout(() => {
			window.location = (medium_prev.href);
		}, slideshow_delay_s * 1000);
	}
}
// slideshow navigation direction
if (medium_prev) {
	medium_prev.addEventListener('navigate', e => {
		localStorage.setItem('media_slideshow_direction', 'backward');
	});
	medium_prev.addEventListener('click', e => {
		localStorage.setItem('media_slideshow_direction', 'backward');
	});
}
if (medium_next) {
	medium_next.addEventListener('navigate', e => {
		localStorage.setItem('media_slideshow_direction', 'forward');
	});
	medium_next.addEventListener('click', e => {
		localStorage.setItem('media_slideshow_direction', 'forward');
	});
}
