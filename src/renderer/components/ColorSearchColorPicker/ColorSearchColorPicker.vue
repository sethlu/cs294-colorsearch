<template>
  <div class="color-picker" v-if="activeColorId">
    <div class="color-picker-info">
      <!-- <div class="color-picker-preview">
        <color-canvas :color="xyY"/>
      </div> -->
      <div class="color-picker-props">
        Name <input v-model="name" />
      </div>
    </div>
    <canvas
      ref="canvas"
      class="color-picker-canvas"
      width="400"
      height="400"
      @wheel="handleCanvasWheel"
    ></canvas>
    <div class="color-picker-classifier">
      <div class="color-picker-classifier-prompt">Is this color {{ name }}?</div>
      <color-canvas class="color-picker-classifier-preview" :color="userClassifierSample"/>
      <div class="color-picker-classifier-actions">
        <button @click="handleUserClassifierResponse(true)">yes</button>
        <button @click="handleUserClassifierResponse(false)">no</button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from "vuex";

import ColorCanvasVue from "./ColorCanvas.vue";
import { classifyColor } from "../../../lib/classifier";

function mapActiveColorProps(props) {
  const getters = {};

  for (let prop of props) {
    getters[prop] = {
      get() {
        return this.$store.getters.activeColor[prop];
      },
      set(val) {
        this.$store.dispatch("setActiveColorProps", { [prop]: val });
      }
    };
  }

  return getters;
}

export default {
  components: {
    "color-canvas": ColorCanvasVue
  },

  data: function() {
    return {
      colorY: 1,
      userClassifierSample: [0, 0, 0]
    };
  },

  computed: {
    ...mapGetters(["activeColorId", "activeColor", "colors"]),
    ...mapActiveColorProps(["name", "xyY", "perceptron"]),

    flatPerceptronWeights() {
      const flattened = [];
      function flat(a) {
        if (!Array.isArray(a)) return flattened.push(a);
        a.forEach(flat);
      }
      if (this.perceptron && this.perceptron.coefs) {
        flat(this.perceptron.coefs);
      }
      return flattened;
    },

    flatPerceptronIntercepts() {
      const flattened = [];
      function flat(a) {
        if (!Array.isArray(a)) return flattened.push(a);
        a.forEach(flat);
      }
      if (this.perceptron && this.perceptron.intercepts) {
        flat(this.perceptron.intercepts);
      }
      return flattened;
    }
  },

  methods: {
    ...mapActions([
      'addColorDatapoint',
    ]),

    updateUserClassifierSample() {
      const vertices = [0.64, 0.33, 0.3, 0.6, 0.15, 0.06];
      function inTriangle(px, py, x0, y0, x1, y1, x2, y2) {
        function leftOfLine(px, py, ax, ay, bx, by) {
          let dx = bx - ax;
          let dy = by - ay;
          let nx = -dy;
          let ny = dx;
          let tx = px - ax;
          let ty = py - ay;
          return nx * tx + ny * ty > 0;
        }
        let t1 = leftOfLine(px, py, x0, y0, x1, y1);
        let t2 = leftOfLine(px, py, x1, y1, x2, y2);
        let t3 = leftOfLine(px, py, x2, y2, x0, y0);
        return t1 == t2 && t2 == t3;
      }

      let sample;
      do {
        sample = [Math.random(), Math.random(), Math.random()];
      } while (!inTriangle(sample[0], sample[1], ...vertices));

      this.userClassifierSample = sample;
    },

    async handleUserClassifierResponse(response) {
      let [x, y, z] = this.userClassifierSample;
      let b = response ? 1 : 0;
      this.addColorDatapoint({ x, y, z, b });
  
      this.perceptron = await classifyColor(this.activeColorId);

      this.redraw();

      this.updateUserClassifierSample();
    },

    async handleCanvasClick(event) {
      const x =
        (event.pageX - this.$refs.canvas.offsetLeft) /
        this.$refs.canvas.offsetWidth;
      const y =
        1 -
        (event.pageY - this.$refs.canvas.offsetTop) /
          this.$refs.canvas.offsetHeight;
      this.xyY = [x, y, 1];
      this.addColorDatapoint({ x: x, y: y, z: 1, b: event.shiftKey ? 0 : 1});

      this.perceptron = await classifyColor(this.activeColorId);

      this.redraw();
    },

    handleCanvasWheel(event) {
      this.colorY = Math.min(1, Math.max(0, this.colorY + event.deltaY / 500));
      this.redraw();
    },

    redraw() {
      const canvas = this.$refs.canvas;
      const gl = canvas.getContext("webgl2");

      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.clear(gl.COLOR_BUFFER_BIT);

      if (!this.perceptron) return;

      const flatPerceptronWeights = this.flatPerceptronWeights;
      const flatPerceptronIntercepts = this.flatPerceptronIntercepts;

      // console.log("Perceptron weights", flatPerceptronWeights);
      // console.log("Perceptron intercepts", flatPerceptronIntercepts);

      const std140perceptron = new Float32Array((this.perceptron.mean.length + this.perceptron.scale.length + flatPerceptronWeights.length + flatPerceptronIntercepts.length) * 4);
      this.perceptron.mean.forEach((v, i) => 
        std140perceptron[i * 4] = v);
      this.perceptron.scale.forEach((v, i) => 
        std140perceptron[(this.perceptron.mean.length + i) * 4] = v);
      flatPerceptronWeights.forEach((v, i) => 
        std140perceptron[(this.perceptron.mean.length + this.perceptron.scale.length + i) * 4] = v);
      flatPerceptronIntercepts.forEach((v, i) => 
        std140perceptron[(this.perceptron.mean.length + this.perceptron.scale.length + flatPerceptronWeights.length + i) * 4] = v);

      gl.bindBuffer(gl.UNIFORM_BUFFER, this.perceptronBuffer);
      gl.bufferData(gl.UNIFORM_BUFFER, std140perceptron, gl.DYNAMIC_DRAW);
      gl.bindBuffer(gl.UNIFORM_BUFFER, null);

      gl.useProgram(this.program);
      gl.uniform1f(this.colorYLocation, this.colorY);
      this.perceptronWeightsBlockIndex = gl.getUniformBlockIndex(this.program, "PerceptronBlock");
      gl.uniformBlockBinding(this.program, this.perceptronWeightsBlockIndex, 1);
      gl.bindBufferBase(gl.UNIFORM_BUFFER, 1, this.perceptronBuffer);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.indexBuffer);
      gl.drawElements(gl.TRIANGLES, 3, gl.UNSIGNED_SHORT, 0);
    }
  },

  watch: {
    activeColorId: function(newVal, oldVal) {
      this.redraw();
    }
  },

  created: function () {
    this.updateUserClassifierSample();
  },

  mounted: function() {
    const canvas = this.$refs.canvas;

    canvas.style.width = `${canvas.width}px`;
    canvas.style.height = `${canvas.height}px`;

    canvas.width = canvas.width * window.devicePixelRatio;
    canvas.height = canvas.height * window.devicePixelRatio;

    const gl = canvas.getContext("webgl2");

    // sRGB
    const vertices = [0.64, 0.33, 0.3, 0.6, 0.15, 0.06];

    // Apple RGB
    // const vertices = [0.625, 0.34, 0.28, 0.595, 0.155, 0.07];

    // CIE XYZ
    // const vertices = [1, 0, 0, 1, 0, 0];

    // CIE (1931) RGB
    // const vertices = [0.7347, 0.2653, 0.2738, 0.7174, 0.1666, 0.0089];

    const indices = [0, 1, 2];

    const color = [0.3, 0.4, 0.5];

    const vertexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.STATIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER, null);

    this.indexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.indexBuffer);
    gl.bufferData(
      gl.ELEMENT_ARRAY_BUFFER,
      new Uint16Array(indices),
      gl.STATIC_DRAW
    );
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, null);

    this.perceptronBuffer = gl.createBuffer();

    const vertexShaderSource = `#version 300 es

      precision mediump float;

      in vec2 coordinates;

      out vec2 xy;

      void main(void) {
        gl_Position = vec4(coordinates * 2.0 - vec2(1.0), 0.0, 1.0);
        xy = coordinates;
      }
    `;

    function range(n) {
      return [...Array(n).keys()];
    }

    let weights = 0, intercepts = 0;
    function genLayer(prev, prevDim, cur, curDim, activation) {
      return `
        float ${cur}[${curDim}];
        // Intercepts
        ${range(curDim).map(i => `${cur}[${i}] = perceptron.intercepts[${intercepts++}];`).join(" ")}
        // Weights
        ${range(prevDim * curDim).map((i) => `${cur}[${i % curDim}] += ${prev}[${Math.floor(i / curDim)}] * perceptron.weights[${weights++}];`).join(" ")}
        // Activation
        ${activation == "relu" ?
          `${range(curDim).map(i => `${cur}[${i}] = max(0.0, ${cur}[${i}]);`).join(" ")} // ReLU` :
          activation == "tanh" ?
            `${range(curDim).map(i => `${cur}[${i}] = tanh(${cur}[${i}]);`).join(" ")} // tanh` :
            `${range(curDim).map(i => `${cur}[${i}] = 1.0 / (1.0 + exp(-${cur}[${i}]));`).join(" ")} // Logistic`
        }`;
    }

    const fragmentShaderSource = `#version 300 es

      precision mediump float;

      #define GAMMA_CORRECTION 1.0/2.2

      layout (std140) uniform PerceptronBlock {
        float mean[3];
        float scale[3];
        float weights[${3 * 100 + 100 * 1}];
        float intercepts[${100 + 1}];
      } perceptron;

      uniform float Y;

      in vec2 xy;

      out vec4 fragmentColor;

      float classify(vec3 xyY) {
        float a[3];
        a[0] = (xyY[0] - perceptron.mean[0]) / perceptron.scale[0];
        a[1] = (xyY[1] - perceptron.mean[1]) / perceptron.scale[1];
        a[2] = (xyY[2] - perceptron.mean[2]) / perceptron.scale[2];

        ${genLayer("a", 3, "b", 100, "relu")}
        ${genLayer("b", 100, "z", 1, "logistic")}

        return z[0];
      }

      vec3 xyY2sRGB(vec3 xyY) {
        vec3 XYZ =
          vec3(xyY[0] * xyY[2] / xyY[1],
               xyY[2],
               (1.0 - xyY[0] - xyY[1]) * xyY[2] / xyY[1]);

        vec3 sRGB =
          mat3(3.2404542, -0.9692660, 0.0556434,
               -1.5371385, 1.8760108, -0.2040259,
               -0.4985314, 0.0415560, 1.0572252) * XYZ;

        return sRGB;
      }

      void main(void) {
        vec3 color_xyY = vec3(xy, Y);
        vec3 sRGB = xyY2sRGB(color_xyY);
        vec3 gammaCorrected = vec3(pow(sRGB.x, GAMMA_CORRECTION),
                                   pow(sRGB.y, GAMMA_CORRECTION),
                                   pow(sRGB.z, GAMMA_CORRECTION));
        float c = classify(color_xyY);

        // fragmentColor = vec4(c, c, c, 1);
        // return;

        if (c > 0.5) {
          if (sRGB.x < 0.0 || sRGB.y < 0.0 || sRGB.z < 0.0) {
            fragmentColor = vec4(0, 0, 0, 1);
          } else {    
            fragmentColor = vec4(gammaCorrected, 1);
          }
        } else {
          fragmentColor = vec4(0.4, 0.4, 0.4, 1);
        }
      }
    `;

    console.log(fragmentShaderSource);

    const vertexShader = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vertexShader, vertexShaderSource);
    gl.compileShader(vertexShader);

    console.log(gl.getShaderInfoLog(vertexShader));

    const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fragmentShader, fragmentShaderSource);
    gl.compileShader(fragmentShader);

    console.log(gl.getShaderInfoLog(fragmentShader));

    this.program = gl.createProgram();
    gl.attachShader(this.program, vertexShader);
    gl.attachShader(this.program, fragmentShader);
    gl.linkProgram(this.program);

    const coordLocation = gl.getAttribLocation(this.program, "coordinates");
    this.colorYLocation = gl.getUniformLocation(this.program, "Y");

    gl.useProgram(this.program);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.indexBuffer);
    {
      gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
      gl.vertexAttribPointer(coordLocation, 2, gl.FLOAT, false, 0, 0);
      gl.enableVertexAttribArray(coordLocation);
    }

    this.redraw();
  }
};
</script>

<style lang="scss">
@import "../global.scss";

.color-picker {
  display: grid;
  grid-template-areas: "info classifier"
                       "canvas classifier";
  grid-template-rows: 1fr 400px;
  grid-template-columns: 400px 1fr;
  flex-direction: column;
  background-color: $color-gray-tint;

  .color-picker-info {
    grid-area: info;
    display: flex;
    padding: 8px;

    .color-picker-preview {
      flex: none;
      margin-right: 8px;

      canvas {
        box-sizing: border-box;
        width: 48px;
        height: 48px;
        border: 1px solid $color-border;
      }
    }

    .color-picker-props {
      flex: 1 0 auto;
    }
  }

  .color-picker-canvas {
    grid-area: canvas;
    border-top: 1px solid $color-border;
    background-color: hsl(0, 0, 25%);
  }

  .color-picker-classifier {
    grid-area: classifier;
    border-left: 1px solid $color-border;

    display: flex;
    flex-direction: column;
    text-align: center;
    padding: 8px;
    justify-content: space-between;

    .color-picker-classifier-preview {
      width: 64px;
      height: 64px;
      margin: 0 auto;
    }
  }
}
</style>