'use strict';

document.documentElement.classList.add('scripts_enabled');

let tags = document.querySelector('.tags');
// restrict tags wrapper to the width of its associated medium
//TODO wait until summary is fully loaded to get accurate width
tags.style.display = 'none';
tags.style.width = tags.parentNode.querySelector('.medium').clientWidth + 'px';
tags.style.display = '';
// blacklisted tags
let blacklisted_tags = localStorage.getItem('blacklisted_tags');
if (blacklisted_tags) {
	blacklisted_tags = blacklisted_tags.split('#');
	let thumbnails = document.querySelectorAll('.thumbnail');
	for (let i = 0; i < thumbnails.length; i++) {
		let thumbnail = thumbnails[i];
		// blacklisted tags
		for (let j = 0; j < blacklisted_tags.length; j++) {
			let blacklisted_tag = blacklisted_tags[j]
			if (
				thumbnail.title.includes('#' + blacklisted_tag + '#')
				|| '#' + blacklisted_tag == thumbnail.title.substring(thumbnail.title.length - (blacklisted_tag.length + 1))
			) {
				thumbnail.classList.add('blacklist');
			}
		}
	}
}
