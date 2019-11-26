import { PythonShell } from 'python-shell';

import store from '../renderer/store';
import { range, inTriangle } from './utils';

/**
 * Generates datapoints given a set of datapoints
 * This is first used to arbitrarily generate additional training data given some existing user input so the classifier model is constrained to some small area
 *
 * @param {number[][]} datapoints List of datapoints for which to find the boundary
 * @param {number} chromaticityBuckets Number of buckets across the chromatic x & y dimensions
 * @param {number} intensityBuckets Number of buckets across the achromatic/intensity Y dimension
 * @param {number} fillerValue Value used for the generated datapoints
 * @param {number[]} triangle Three pairs of 2D positions such that the generated datapoints has to be in
 * @param {boolean} fillInterior Whether to also generate points in the interior, otherwise only boundary datapoints are generated
 */
function generateFillerDatapoints(datapoints, chromaticityBuckets, intensityBuckets, fillerValue = 0, triangle = null, fillInterior = false) {
    const boundary = 1;
    const chromaticityBucketsAndPadding = chromaticityBuckets + 2 * boundary;
    const intensityBucketsAndPadding = intensityBuckets + 2 * boundary;

    const occupancyBuckets = new Array(chromaticityBucketsAndPadding * chromaticityBucketsAndPadding * intensityBucketsAndPadding).fill(0);

    function hash(x, y, z) {
        return (Math.min(intensityBuckets, Math.floor(z * intensityBuckets)) + 1) * chromaticityBucketsAndPadding * chromaticityBucketsAndPadding +
            (Math.min(chromaticityBuckets, Math.floor(y * chromaticityBuckets)) + 1) * chromaticityBucketsAndPadding +
            Math.min(chromaticityBuckets, Math.floor(x * chromaticityBuckets)) + 1;
    }

    for (let sample of datapoints) {
        if (sample[3] == 0) continue;

        for (let dz of range(-boundary, boundary + 1)) {
            for (let dy of range(-boundary, boundary + 1)) {
                for (let dx of range(-boundary, boundary + 1)) {
                    if (!fillInterior && !(Math.abs(dx) >= boundary || Math.abs(dy) >= boundary || Math.abs(dz) >= boundary)) {
                        occupancyBuckets[hash(
                            sample[0] + dx / chromaticityBuckets,
                            sample[1] + dy / chromaticityBuckets,
                            sample[2] + dz / intensityBuckets)] -= 10000;
                    }

                    occupancyBuckets[hash(
                        sample[0] + dx / chromaticityBuckets,
                        sample[1] + dy / chromaticityBuckets,
                        sample[2] + dz / intensityBuckets)] += 1;
                }
            }
        }
    }

    const fillers = [];

    for (let z of range(intensityBuckets)) {
        for (let y of range(chromaticityBuckets)) {
            for (let x of range(chromaticityBuckets)) {
                const h = hash(
                    x / chromaticityBuckets,
                    y / chromaticityBuckets,
                    z / intensityBuckets);
                if (occupancyBuckets[h] > 0) {
                    const px = (x + 0.5) / chromaticityBuckets;
                    const py = (y + 0.5) / chromaticityBuckets;

                    if (triangle && !inTriangle(px, py, ...triangle)) {
                        continue;
                    }

                    fillers.push([
                        px,
                        py,
                        (z + 0.5) / intensityBuckets,
                        fillerValue]);
                }
            }
        }
    }

    return fillers;
}

/**
 * Returns datapoints plus some additional fillers for subjectively better models
 */
function makeTrainingDatapoints(datapoints, fillerValue = 0, triangle = null) {
    return [
        ...datapoints,
        ...generateFillerDatapoints(datapoints, 6, 6, fillerValue, triangle)
    ];
}

/**
 * Returns a classifier for the specified color
 * 
 * @param {string} colorId Color ID
 * @param {number[]} triangle Three pairs of 2D positions such that the generated filler datapoints has to be in
 */
function classifyColor(colorId, triangle = null) {
    return new Promise((resolve, reject) => {
        const color = store.getters.colorByColorId(colorId);

        const training = makeTrainingDatapoints(color.datapoints, 0, triangle);

        const zeros = training.filter(v => v[3] == 0).length;
        if (training.length <= 2 || training.length == zeros || zeros == 0) {
            console.log("Needs at least 2 samples & different binary responses to train the classifier")
            resolve();
            return;
        }

        let pyshell = new PythonShell(`${__dirname}/classifier.py`, {
            pythonPath: `${__dirname}/../../.node-virtualenv/bin/python3`
        });
        pyshell.send(JSON.stringify(training));
        const buffer = [];
        pyshell.on('message', (message) => {
            // console.log('message', message);
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
    classifyColor,
    makeTrainingDatapoints,
    generateFillerDatapoints
};
