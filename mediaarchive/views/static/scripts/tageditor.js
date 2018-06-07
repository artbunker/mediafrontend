'use strict';
import { TagField } from './tagfield.js';
import { autocopy } from './autocopy.js';

export class TagEditor extends TagField {
	constructor(target_input, strings) {
		super(strings);
		this.target_input = target_input;
		this.additional_fields = {};
		// strings
		if ('undefined' == typeof strings) {
			strings = {};
		}
		if (!strings.hasOwnProperty('saving_placeholder')) {
			strings.saving_placeholder = 'Saving...';
		}
		if (!strings.hasOwnProperty('saving_in_progress')) {
			strings.saving_in_progress = 'Saving in progress';
		}
		if (!strings.hasOwnProperty('copy_alert')) {
			strings.copy_alert = 'Copy raw tags manually';
		}
		if (!strings.hasOwnProperty('autocopy_alert')) {
			strings.autocopy_alert = 'Tags copied to clipboard';
		}
		this.strings.saving_placeholder = strings.saving_placeholder;
		this.strings.saving_in_progress = strings.saving_in_progress;
		this.strings.copy_alert = strings.copy_alert;
		this.strings.autocopy_alert = strings.autocopy_alert;
		// create control buttons
		this.controls = {
			show: null,
			copy: null,
			save: null,
			discard: null,
		}
		for (let control in this.controls) {
			this.strings[control + '_link'] = strings[control + '_link'] || control.charAt(0).toUpperCase() + control.slice(1);
			this.controls[control] = document.createElement('span');
			this.controls[control].innerText = this.strings[control + '_link'];
		}
		// add default control listeners
		this.controls.show.addEventListener('click', e => {
			this.clear();
			this.add_tags(this.to_list(this.target_input.value));
			setTimeout(() => {
				this.input.focus();
			}, 1);
		});
		this.controls.copy.addEventListener('click', e => {
			this.copy();
		});
		this.controls.save.addEventListener('click', () => {
			this.save();
		});
		this.controls.discard.addEventListener('click', e => {
			if (!this.input.disabled) {
				this.discard();
				return;
			}
			alert(this.strings.saving_in_progress);
			e.stopPropagation();
			
		});
		// add event listener for enter submit
		this.input.addEventListener('submit', () => {
			this.save();
		});
		// add listener to prevent invalid tags
		this.input.addEventListener('added', e => {
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
		});
	}
	save() {
		let form = this.target_input.parentNode;
		while ('FORM' != form.tagName) {
			if (document.body == form) {
				// traversed up from target input and didn't find a form element
				// dispatch failure event
				this.input.dispatchEvent(
					new CustomEvent('submit_failure')
				);
				return;
			}
		}
		this.input.disabled = true;
		this.input.placeholder = this.strings.saving_placeholder;
		let fd = new FormData();
		fd.append(this.target_input.name, this.to_string(this.tags_list));
		//TODO add other fields in the current form to formdata
		//TODO instead of using custom additional_fields property?
		for (field in this.additional_fields) {
			fd.append(field, this.additional_fields[field]);
		}
		// send save request
		let xhr = new XMLHttpRequest();
		xhr.onreadystatechange = () => {
			if (xhr.readyState == XMLHttpRequest.DONE) {
				this.input.disabled = false;
				this.input.placeholder = this.strings.placeholder;
				if (200 == xhr.status) {
					this.target_input.value = this.to_string(this.tags_list);
					// dispatch success event
					this.input.dispatchEvent(
						new CustomEvent('save_success')
					);
				}
				else {
					// dispatch failure event
					this.input.dispatchEvent(
						new CustomEvent('save_failure')
					);
				}
			}
		};
		let method = form.method.toUpperCase();
		let action = form.action;
		xhr.open(method, action + (-1 != action.indexOf('?') ? '&' : '?') + '_' + new Date().getTime(), true);
		xhr.withCredentials = true;
		xhr.send(fd);
	}
	copy() {
		let tag_string = this.to_string(this.tags_list).replace(' #', '#');
		autocopy(tag_string, this.strings.autocopy_alert, this.strings.copy_alert);
		this.input.focus();
	}
}
