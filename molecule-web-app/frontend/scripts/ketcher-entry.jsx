import React from 'react';
import { createRoot } from 'react-dom/client';
import { Editor } from 'ketcher-react';
import { StandaloneStructServiceProvider } from 'ketcher-standalone';
import 'ketcher-react/dist/index.css';

const rootElement = document.getElementById('root');
const root = createRoot(rootElement);
const structServiceProvider = new StandaloneStructServiceProvider();

function notifyReady(ketcher) {
    window.ketcher = ketcher;
    window.parent.postMessage({ type: 'ketcher-ready' }, window.location.origin);
}

function notifyError(message) {
    window.parent.postMessage({ type: 'ketcher-error', message }, window.location.origin);
}

try {
    root.render(
        React.createElement(Editor, {
            staticResourcesUrl: './',
            structServiceProvider,
            onInit: notifyReady,
            errorHandler: notifyError,
        })
    );
} catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to load Ketcher.';
    rootElement.innerHTML = `<div class="ketcher-load-error">${message}</div>`;
    notifyError(message);
}
