'use strict';
import { TagEditor } from './tageditor.js';

let tags = document.querySelectorAll('.tags');
for (let i = 0; i < tags.length; i++) {
	// restricts tags wrapper to the width of their associated medium
	tags[i].style.display = 'none';
	tags[i].style.width = tags[i].parentNode.querySelector('.medium').clientWidth + 'px';
	tags[i].style.display = '';
}
let tags_editors = document.querySelectorAll('.tags_editor');
if (0 < tags_editors.length) {
	for (let i = 0; i < tags_editors.length; i++) {
		let tags_editor = tags_editors[i];
		let view = tags_editor.parentNode;

		view.classList.add('scripts_enabled');

		// create tag editor
		let tag_editor = new TagEditor();
		tag_editor.original_input = tags_editor.querySelector('[name="tags"]');
		tag_editor.preview.classList.add('tags_preview');
		tag_editor.input.placeholder = tags_editor.dataset.inputPlaceholder;

		// add references to elements to tag editor
		tag_editor.view = view;
		tag_editor.tags = view.querySelector('.tags');
		tag_editor.tags_editor = tags_editor;

		// add reference to tag editor to element
		tags_editor.tag_editor = tag_editor;

		// insert tag editor controls into info bar
		let info = view.querySelector('.info');
		tag_editor.controls = {
			copy: null,
			show: null,
			discard: null,
			save: null,
		}
		for (let control in tag_editor.controls) {
			tag_editor.controls[control] = document.createElement('span');
			tag_editor.controls[control].innerText = tags_editor.dataset[control + 'Link'];
			tag_editor.controls[control].classList.add('tag_editor_control');
			info.insertBefore(tag_editor.controls[control], info.childNodes[1]);
		}
		tag_editor.controls.show.classList.add('show_tag_editor');

		// add tag editor controls listeners
		tag_editor.controls.copy.addEventListener('click', function(e) {
			this.copy();
		}.bind(tag_editor));
		tag_editor.controls.show.addEventListener('click', function(e) {
			this.clear();
			this.add_tags(this.to_list(this.original_input.value));
			this.view.classList.add('editing_tags');
			setTimeout(() => {
				this.input.focus();
			}, 1);
		}.bind(tag_editor));
		tag_editor.controls.discard.addEventListener('click', function(e) {
			if (this.input.disabled) {
				//TODO get this string from tags element
				alert('Saving in progress')
				return;
			}
			this.discard();
			this.view.classList.remove('editing_tags');
		}.bind(tag_editor));
		tag_editor.controls.save.addEventListener('click', function(e) {
			let tags_string = this.to_string(this.tags_list);
			this.view.querySelector('[name=tags]').value = tags_string;
			this.input.disabled = true;
			this.input.placeholder = this.tags_editor.dataset.inputSaving;
			let fd = new FormData();
			fd.append('tags', this.to_string(this.tags_list));
			// send save request
			let xhr = new XMLHttpRequest();
			xhr.onreadystatechange = function() {
				if (xhr.readyState == XMLHttpRequest.DONE) {
					this.input.disabled = false;
					this.input.placeholder = this.tags_editor.dataset.inputPlaceholder;
					if (200 == xhr.status) {
						let inner_tags = this.tags.querySelector('.inner_tags');
						inner_tags.innerHTML = '';
						// build tags from tags_list
						let visible_tags = 0;
						this.tags_list.sort();
						for (let i = 0; i < this.tags_list.length; i++) {
							let tag = this.tags_list[i];
							let el = this.create_tag_element(tag);

							// create search link
							let link = document.createElement('a');
							link.href = this.tags_editor.dataset.searchUri.replace('{}', encodeURIComponent(tag));
							//TODO title tip

							// swap inner tag element for link
							let inner_el = el.childNodes[0];
							link.innerText = inner_el.innerText;
							el.removeChild(inner_el);
							el.appendChild(link);

							// add newly built tag to actual tags container
							inner_tags.appendChild(el);

							//TODO apply actual rendering changes for rendering tags
							// check if tag is visible
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
						this.tags.dataset.visibleTags = visible_tags;
						this.clear();
						this.view.classList.remove('editing_tags');
					}
					else {
						alert(this.dataset.problemSaving);
					}
				}
			}.bind(this);
			let action = tag_editor.tags_editor.querySelector('form').action;
			xhr.open('POST', action + (-1 != action.indexOf('?') ? '&' : '?') + '_' + new Date().getTime(), true);
			xhr.withCredentials = true;
			xhr.send(fd);
		}.bind(tag_editor));

		// add submit on enter listener
		tag_editor.input.addEventListener('keydown', function(e) {
			if (
				'Enter' == e.key
				&& '' == e.currentTarget.value
			) {
				this.controls.save.click();
			}
		}.bind(tag_editor));

		// add listener to prevent invalid tags
		tag_editor.input.addEventListener('added', function(e) {
			if (
				'-' == e.detail.tag[0]
				|| 'sort:' == e.detail.tag.substring(0, 5)
				|| 'order:' == e.detail.tag.substring(0, 6)
				|| 'perpage:' == e.detail.tag.substring(0, 8)
				|| 'group:' == e.detail.tag.substring(0, 6)
				|| 'uploaded after:' == e.detail.tag.substring(0, 15)
				|| 'uploaded before:' == e.detail.tag.substring(0, 16)
				|| 'created after:' == e.detail.tag.substring(0, 14)
				|| 'created before:' == e.detail.tag.substring(0, 15)
				|| 'mimetype:' == e.detail.tag.substring(0, 9)
				|| 'size:' == e.detail.tag.substring(0, 5)
				|| (
					'data' == e.detail.tag.substring(0, 4)
					&& (
						' more than:' == e.detail.tag.substring(5, 16)
						|| ' less than:' == e.detail.tag.substring(5, 16)
					)
				)
				|| 'protection:' == e.detail.tag.substring(0, 11)
				|| 'searchability:' == e.detail.tag.substring(0, 14)
				|| 'id:' == e.detail.tag.substring(0, 3)
				|| 'origin:' == e.detail.tag.substring(0, 7)
				|| 'uploader:' == e.detail.tag.substring(0, 9)
				|| 'owner:' == e.detail.tag.substring(0, 6)
				|| 'status:' == e.detail.tag.substring(0, 7)
			) {
				this.remove_tag(e.detail.tag);
			}
		}.bind(tag_editor));

		// add tag editor components to tags wrapper
		tag_editor.tags.appendChild(tag_editor.preview);
		tag_editor.tags.appendChild(tag_editor.input);
	}
}

// listener for management keys
window.addEventListener('keydown', e => {
	// get first tag editor
	let tag_editor = document.querySelector('.tags_editor').tag_editor;
	if ('Escape' == e.key) {
		tag_editor.controls.discard.click();
		return;
	}
	// ignore editor open if in an input
	if ('INPUT' == document.activeElement.tagName) {
		return;
	}
	if ('t' == e.key) {
		tag_editor.controls.show.click();
	}
});
// add listener for leaving page to check if any tags are still processing
window.addEventListener('beforeunload', e => {
	if (document.querySelector('.editing_tags')) {
		(e || window.event).returnValue = true;
		return true;
	}
});
