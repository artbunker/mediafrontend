'use strict';

document.documentElement.classList.add('scripts_enabled');

class Upload {
	constructor() {
		this.form = document.querySelector('form');
		this.form.addEventListener('submit', e => {
			e.preventDefault();
		});

		// hide advanced options
		this.advanced = document.createElement('div');
		this.advanced.id = 'advanced';
		this.advanced.innerText = this.form.dataset.advanced;
		this.advanced.addEventListener('click', (e) => {
			document.body.classList.toggle('advanced');
		});
		this.form.parentNode.insertBefore(this.advanced, this.form);

		// checkbox preferences
		let checkboxes = this.form.querySelectorAll('input[type=checkbox]');
		for (let i = 0; i < checkboxes.length; i++) {
			let checkbox = checkboxes[i];
			checkbox.checked = false;
			let checkbox_preference = localStorage.getItem('media_upload_' + checkbox.id);
			if (checkbox_preference) {
				checkbox.checked = true;
			}
			checkbox.addEventListener('change', e => {
				if (e.currentTarget.checked) {
					localStorage.setItem('media_upload_' + e.currentTarget.id, 1);
				}
				else {
					localStorage.removeItem(e.currentTarget.id);
				}
			});
		}
		// select preferences
		let select_ids = ['searchability', 'protection'];
		for (let i = 0; i < select_ids.length; i++) {
			let select_id = select_ids[i];
			let select = document.querySelector('#' + select_id);
			if (!select) {
				continue;
			}
			let select_preference = localStorage.getItem('media_upload_' + select.id);
			if (select_preference) {
				select.value = select_preference;
			}
			select.addEventListener('change', e => {
				let select_value = e.currentTarget.options[e.currentTarget.selectedIndex].value;
				localStorage.setItem('media_upload_' + e.currentTarget.id, select_value);
			});
		}

		// previews
		this.previews = document.createElement('div');
		this.previews.id = 'previews';
		this.form.parentNode.insertBefore(this.previews, this.form.nextSibling);

		// upload
		this.file_upload = this.form.querySelector('#file_upload');
		// remove file upload name so that it isn't submitted
		this.file_upload_name = this.file_upload.name;
		this.file_upload.name = '';
		this.file_upload.multiple = true;
		this.file_upload.addEventListener('change', e => {
			// parse files
			for (let i = 0; i < this.file_upload.files.length; i++) {
				if (parseInt(this.file_upload.dataset.maximumUploadFilesize) > this.file_upload.files[i].size) {
					let fd = new FormData(this.form);
					fd.append(this.file_upload_name, this.file_upload.files[i]);
					this.add_preview(this.file_upload.files[i].name, fd)
					continue;
				}
				this.add_preview(this.file_upload.files[i]);
			}
			//TODO clear file upload input
		});

		// uri
		this.file_uri = this.form.querySelector('#file_uri');
		this.file_uri.addEventListener('keydown', e => {
			if (
				'Enter' != e.key
				|| 0 == this.file_uri.value.length
				|| -1 == this.file_uri.value.indexOf('/')
				|| -1 == this.file_uri.value.indexOf('http')
			) {
				return;
			}
			let filename = this.file_uri.value.split('/');
			this.add_preview(filename[filename.length - 1], new FormData(this.form));
			this.file_uri.value = '';
		});
	}
	add_preview(filename, fd) {
		let preview = document.createElement('div');
		preview.classList.add('preview');
		preview.filename = document.createElement('div');
		preview.filename.classList.add('filename');
		preview.filename.innerText = filename;
		preview.placeholder = document.createElement('div');
		preview.placeholder.classList.add('placeholder');
		preview.appendChild(preview.filename);
		preview.appendChild(preview.placeholder);
		this.previews.appendChild(preview);

		if ('undefined' == typeof fd) {
			//TODO create dead preview card with payload too large error
			this.preview.classList.add('failure');
			this.preview.placeholder.innerText = this.file_upload.dataset.fileTooLarge;
			return;
		}

		preview.classList.add('uploading');
		let xhr = new XMLHttpRequest();
		xhr.preview = preview;
		xhr.uploaded_timeout = null;
		xhr.onreadystatechange = () => {
			if (xhr.readyState == XMLHttpRequest.DONE) {
				if (xhr.uploaded_timeout) {
					clearTimeout(xhr.uploaded_timeout);
					if (xhr.preview.progress && xhr.preview.progress.parentNode == xhr.preview) {
						xhr.preview.removeChild(xhr.preview.progress);
					}
					xhr.preview.classList.remove('uploading');
				}
				xhr.preview.classList.add('complete');
				xhr.preview.classList.remove('processing');
				if (200 == xhr.status) {
					// add thumbnail in placeholder
					xhr.preview.placeholder.innerHTML = xhr.response.thumbnail;
					// wait for complete animation
					setTimeout(() => {
						xhr.preview.classList.add('success');
						xhr.preview.classList.remove('complete');
					}, 250);
					return;
				}
				// duplicate
				if (409 == xhr.status) {
					// create view link around placeholder
					let link = document.createElement('a');
					link.href = xhr.response.status_data.view_uri;
					xhr.preview.appendChild(link);
					link.appendChild(xhr.preview.placeholder);
				}
				// server error
				else if (500 == xhr.status) {
					//TODO create retry link tied to this xhr around placeholder?
				}
				// errors returned
				if (
					xhr.response
					&& xhr.response.status_data
					&& xhr.response.status_data.errors
				) {
					for (let i = 0; i < xhr.response.status_data.errors.length; i++) {
						let error = document.createElement('div');
						error.classList.add('error');
						error.innerText = xhr.response.status_data.errors[i];
						xhr.preview.placeholder.appendChild(error);
					}
				}
				// wait for complete animation
				setTimeout(() => {
					xhr.preview.classList.add('failure');
					xhr.preview.classList.remove('complete');
				}, 250);
			}
		};
		if (xhr.upload) {
			xhr.preview.progress = document.createElement('div');
			xhr.preview.progress.classList.add('progress');
			xhr.preview.progress.style.width = '0px';
			xhr.preview.appendChild(preview.progress);
			xhr.upload.addEventListener('progress', e => {
				if (e.lengthComputable) {
					let progress = Math.floor((e.loaded / e.total) * 100);
					//console.log('progress: ' + progress);
					if (100 > progress) {
						xhr.preview.progress.style.width = progress + '%';
						return;
					}
					xhr.preview.progress.style.width = '100%';
					xhr.uploaded_timeout = setTimeout(() => {
						xhr.uploaded_timeout = null;
						xhr.preview.removeChild(xhr.preview.progress);
						xhr.preview.classList.remove('uploading');
						xhr.preview.classList.add('processing');
					}, 250);
				}
			});
		}
		let action = this.form.dataset.actionUpload;
		xhr.open('POST', action + (-1 != action.indexOf('?') ? '&' : '?') + '_' + new Date().getTime(), true);
		xhr.withCredentials = true;
		xhr.responseType = 'json';
		xhr.send(fd);
	}
};

let upload = new Upload();
