'use strict';
import { TagSearch } from './tagsearch.js';
import { fetch_tag_suggestions } from './tagfield.js';

let target_input = document.getElementById('tags');
if (target_input) {
	document.documentElement.classList.add('scripts_enabled');

	// create tag search
	let strings = {
		'placeholder': target_input.dataset.placeholder,
		'remove_tag': target_input.dataset.removeTag,
	};
	let search = new TagSearch(target_input, strings);

	// add classes to editor components
	search.preview.classList.add('tags_preview');

	// add tag editor components to search form
	let preview_wrapper = document.createElement('div');
	preview_wrapper.classList.add('tags_preview_wrapper');
	preview_wrapper.append(search.preview);
	search.target_form.insertBefore(preview_wrapper, search.target_input);
	search.target_form.insertBefore(search.input, search.target_input);

	// listener for search key
	window.addEventListener('keydown', e => {
		if ('s' == e.key) {
			search.input.focus();
		}
	});
	// listeners for add and remove tags on tags this page actions
	let actions = document.querySelectorAll('#tags_this_page .action');
	for (let i = 0; i < actions.length; i++) {
		let action = actions[i];
		actions[i].addEventListener('click', e => {
			e.preventDefault();
			if (actions[i].classList.contains('add')) {
				search.add_tag(e.currentTarget.parentNode.dataset.tag);
			}
			else if (actions[i].classList.contains('remove')) {
				search.add_tag('-' + e.currentTarget.parentNode.dataset.tag);
			}
		});
	}
	fetch_tag_suggestions();
}
let tags_this_page = document.querySelector('#tags_this_page');
if (tags_this_page) {
	tags_this_page.classList.add('closed');
	tags_this_page.querySelector('.header').addEventListener('click', e => {
		e.currentTarget.parentNode.classList.toggle('closed');
	});
}
// thumbnail hover previews
let thumbnails = document.querySelectorAll('.thumbnail');
for (let i = 0; i < thumbnails.length; i++) {
	let thumbnail = thumbnails[i];
	if (thumbnail.dataset.hasOwnProperty('preview')) {
		let picture = thumbnail.querySelector('picture');
		if ('image/gif' == thumbnail.dataset.mime) {
			let preview_picture = document.createElement('picture');
			preview_picture.classList.add('preview');
			let preview_image = document.createElement('img');
			preview_image.src = thumbnail.dataset.preview;
			preview_picture.appendChild(preview_image);

			picture.parentNode.insertBefore(preview_picture, picture);

			thumbnail.addEventListener('mouseover', e => {
				e.currentTarget.classList.add('hover');
			});
			thumbnail.addEventListener('mouseout', e => {
				e.currentTarget.classList.remove('hover');
			});
		}
		else if ('video' == thumbnail.dataset.category) {
			let preview_video = document.createElement('video');
			preview_video.classList.add('preview');
			preview_video.loop = true;
			preview_video.preload = 'auto';
			//TODO add original thumb image as poster?
			let preview_source = document.createElement('source');
			preview_source.src = thumbnail.dataset.preview;
			preview_source.type = 'video/webm';
			preview_video.appendChild(preview_source);

			picture.parentNode.insertBefore(preview_video, picture);

			thumbnail.addEventListener('mouseover', e => {
				e.currentTarget.classList.add('hover');
				e.currentTarget.querySelector('.preview').play();
			});
			thumbnail.addEventListener('mouseout', e => {
				e.currentTarget.classList.remove('hover');
				e.currentTarget.querySelector('.preview').pause();
			});
		}
	}
}
