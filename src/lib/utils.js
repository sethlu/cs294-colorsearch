/**
 * Returns an array with the given range, similar to the Python range() function
 */
function range(n) {
    if (arguments.length == 2) {
        const [a, b] = arguments;
        return [...Array(b - a).keys()].map(i => a + i);
    }
    return [...Array(n).keys()];
}

/**
 * Tests if the point [px,py] is inside the triangle [x0,y0], [x1,y1], [x2,y2]
 * 
 * @param {number} px 
 * @param {number} py 
 * @param {number} x0 
 * @param {number} y0 
 * @param {number} x1 
 * @param {number} y1 
 * @param {number} x2 
 * @param {number} y2 
 */
function inTriangle(px, py, x0, y0, x1, y1, x2, y2) {
    function left(px, py, ax, ay, bx, by) {
        let dx = bx - ax;
        let dy = by - ay;
        let nx = -dy;
        let ny = dx;
        let tx = px - ax;
        let ty = py - ay;
        return nx * tx + ny * ty > 0;
    }
    let t1 = left(px, py, x0, y0, x1, y1);
    let t2 = left(px, py, x1, y1, x2, y2);
    let t3 = left(px, py, x2, y2, x0, y0);
    return t1 == t2 && t2 == t3;
}

export {
    range,
    inTriangle
};
