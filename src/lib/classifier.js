import store from '../renderer/store';

import { PythonShell } from 'python-shell';

function classifyColor(colorId) {
    return new Promise((resolve, reject) => {
        const color = store.getters.colorByColorId(colorId);

        if (color.datapoints.length <= 5) {
            // Needs at least 5 samples to train the classifier
            resolve();
            return;
        }

        let pyshell = new PythonShell(`${__dirname}/classifier.py`, {
            pythonPath: `${__dirname}/../../.node-virtualenv/bin/python3`
        });
        pyshell.send(JSON.stringify(color.datapoints));
        const buffer = [];
        pyshell.on('message', (message) => {
            console.log(message);
            buffer.push(message);
        });
        pyshell.end((err) => {
            if (err) {
                reject(err);
                return;
            }

            resolve(JSON.parse(buffer.join("")));
        })
    });
}

export {
    classifyColor
};
