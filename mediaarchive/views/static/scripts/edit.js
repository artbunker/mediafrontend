'use strict';

import { add_hover_preview } from './add_hover_preview.js';

let thumbnail = document.querySelector('.thumbnail');
if (thumbnail.dataset.hasOwnProperty('preview')) {
	add_hover_preview(thumbnail);
}
