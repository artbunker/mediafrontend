'use strict';

export function add_hover_preview(thumbnail) {
	let picture = thumbnail.querySelector('picture');
	if ('image/gif' == thumbnail.dataset.mime) {
		let preview_picture = document.createElement('picture');
		preview_picture.classList.add('preview');
		let preview_image = document.createElement('img');
		preview_image.src = thumbnail.dataset.preview;
		preview_picture.appendChild(preview_image);

		picture.parentNode.insertBefore(preview_picture, picture);

		if (thumbnail.classList.contains('previewable')) {
			return;
		}
		thumbnail.classList.add('previewable');
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

		if (thumbnail.classList.contains('previewable')) {
			return;
		}
		thumbnail.classList.add('previewable');
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
