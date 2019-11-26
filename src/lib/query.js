import store from '../renderer/store';
import { PythonShell } from 'python-shell';

function query(canvas) {
    return new Promise((resolve, reject) => {
        const palette = {};

        for (let color of store.getters.colors) {
            palette[color.id] = {
                "perceptron": color.perceptron
            };
        }

        let pyshell = new PythonShell(`${__dirname}/query.py`, {
            pythonPath: `${__dirname}/../../.node-virtualenv/bin/python3`
        });
        pyshell.send(JSON.stringify({
            palette, canvas
        }));
        const buffer = [];
        pyshell.on('message', (message) => {
            console.log("stdout", message);
            buffer.push(message);
        });
        pyshell.on('stderr', (stderr) => {
            console.log("stderr", stderr);
        });
        pyshell.end((err) => {
            if (err) {
                reject(err);
                return;
            }

            resolve(JSON.parse(buffer.join("")));
        })
    })
}

export {
    query
};
