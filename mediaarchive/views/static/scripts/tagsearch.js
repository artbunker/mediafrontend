'use strict';
import { TagField } from './tagfield.js';

export class TagSearch extends TagField {
	constructor(target_input, strings) {
		super(strings);
		this.target_input = target_input;
		this.target_form = target_input.parentNode;
		// parse target input value on creation
		this.clear();
		this.add_tags(this.to_list(this.target_input.value));
		// add event listener for enter submit
		this.input.addEventListener('submit', () => {
			this.submit();
		});
		// add listener to swap negation and regular tags
		this.input.addEventListener('added', e => {
			if ('-' == e.detail.tag[0]) {
				this.remove_tag(e.detail.tag.substring(1));
			}
			else {
				this.remove_tag('-' + e.detail.tag);
			}
		});
		// add listeners for submit
		this.target_form.addEventListener('submit', e => {
			if ('' != this.input.value) {
				// commit any tag still in input
				this.add_tags(this.to_list(this.input.value));
				this.clear_input();
				e.preventDefault();
				return false;
			}
			this.submit();
		});
		this.target_input.addEventListener('submit', e => {
			this.submit();
		});
	}
	submit() {
		this.target_input.value = this.to_string(this.tags_list);
		this.target_form.submit();
	}
}
