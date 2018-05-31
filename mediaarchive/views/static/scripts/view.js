'use strict';
import { TagEditor } from './tageditor.js';

function count_visible_tags(tags_list) {
	let visible_tags = 0;
	for (let i = 0; i < tags_list.length; i++) {
		let tag = tags_list[i];
		if (
			'filename:' != tag.substring(0, 9)
			&& 'set:' != tag.substring(0, 4)
			&& 'cover:' != tag.substring(0, 6)
			&& 'mirror:' != tag.substring(0, 7)
			&& 'superior of:' != tag.substring(0, 12)
			&& 'inferior of:' != tag.substring(0, 12)
			&& 'next:' != tag.substring(0, 5)
			&& 'prev:' != tag.substring(0, 5)
			&& 'suppress:' != tag.substring(0, 9)
		) {
			visible_tags++;
		}
	}
	return visible_tags;
}

let tags = document.querySelector('.tags');
if (tags) {
	// restrict tags wrapper to the width of its associated medium
	tags.style.display = 'none';
	tags.style.width = tags.parentNode.querySelector('.medium').clientWidth + 'px';
	tags.style.display = '';
}
let tags_editor = document.querySelector('.tags_editor');
if (tags_editor) {
	// get medium view
	let view = tags_editor.parentNode;
	document.body.classList.add('scripts_enabled');

	// create tag editor
	let strings = {
		'show_link': tags_editor.dataset.showLink,
		'save_link': tags_editor.dataset.saveLink,
		'discard_link': tags_editor.dataset.discardLink,
		'copy_link': tags_editor.dataset.copyLink,
		'placeholder': tags_editor.dataset.placeholder,
		'saving_placeholder': tags_editor.dataset.savingPlaceholder,
		'saving_in_progress': tags_editor.dataset.savingInProgress,
		'remove_tag': tags_editor.dataset.removeTag,
		'': '',
	};
	let editor = new TagEditor(tags_editor.querySelector('[name="tags"]'), strings);

	// add classes to editor components
	editor.preview.classList.add('tags_preview');

	// insert tag editor controls into info bar
	let info = document.querySelector('.info');
	for (let control in editor.controls) {
		editor.controls[control].classList.add('tag_editor_control');
		info.insertBefore(editor.controls[control], info.childNodes[1]);
	}
	editor.controls.show.classList.add('show_tag_editor');
	// add tag editor controls listeners
	editor.controls.show.addEventListener('click', e => {
		document.body.classList.add('editing_tags');
	});
	editor.controls.discard.addEventListener('click', e => {
		if (editor.input.disabled) {
			e.stopPropagation();
			return false;
		}
		document.body.classList.remove('editing_tags');
	});
	// add save listeners
	editor.input.addEventListener('save_success', e => {
		editor.target_input.value = editor.to_string(editor.tags_list);
		let inner_tags = document.querySelector('.inner_tags');
		inner_tags.innerHTML = '';
		editor.tags_list.sort();
		let visible_tags = count_visible_tags(editor.tags_list);
		// build tags
		for (let i = 0; i < editor.tags_list.length; i++) {
			let tag = editor.tags_list[i];
			let el = editor.create_tag_element(
				tag,
				tags_editor.dataset.searchTagTitle,
				tags_editor.dataset.searchUri
			);
			// add newly built tag to actual tags container
			inner_tags.appendChild(el);
		}
		inner_tags.parentNode.dataset.visibleTags = visible_tags;
		editor.clear();
		document.body.classList.remove('editing_tags');
	});
	editor.input.addEventListener('save_failure', e => {
		alert(tags_editor.dataset.problemSaving);
	});

	// add tag editor components to tags wrapper
	tags.appendChild(editor.preview);
	tags.appendChild(editor.input);

	// listener for management keys
	window.addEventListener('keydown', e => {
		// get first tag editor
		if ('Escape' == e.key) {
			editor.controls.discard.click();
			return;
		}
		// ignore editor open if in an input
		if ('INPUT' == document.activeElement.tagName) {
			return;
		}
		if ('t' == e.key) {
			editor.controls.show.click();
		}
	});
	// add listener for leaving page to check if any tags are still processing
	window.addEventListener('beforeunload', e => {
		if (document.querySelector('.editing_tags')) {
			(e || window.event).returnValue = true;
			return true;
		}
	});
}
