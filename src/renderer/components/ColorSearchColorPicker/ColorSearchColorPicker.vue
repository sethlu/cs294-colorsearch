<template>
  <div class="color-picker">
    <div class="color-picker-info">
      <div class="color-picker-props" v-if="activeColor">
        Name
        <input v-model="name" />
      </div>
      <div v-else>
        No Color Selected
      </div>
    </div>
    <canvas
      ref="canvas"
      class="color-picker-canvas"
      @wheel="handleCanvasWheel"
      @click="handleCanvasClick"
    ></canvas>
    <div class="color-picker-classifier">
      <div class="color-picker-classifier-prompt">
        <span v-if="activeColor">Is this color {{ name }}?</span>
      </div>
      <color-canvas class="color-picker-classifier-preview" :color="userClassifierSample" />
      <div class="color-picker-classifier-actions">
        <button @click="handleUserClassifierResponse(true)">yes</button>
        <button @click="handleUserClassifierResponse(false)">no</button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from "vuex";

import {
  classifyColor,
  makeTrainingDatapoints,
  generateFillerDatapoints
} from "../../../lib/classifier";
import { range, inTriangle } from "../../../lib/utils.js";

import ColorCanvasVue from "./ColorCanvas.vue";

// sRGB
const triangle = [0.64, 0.33, 0.3, 0.6, 0.15, 0.06];

// Apple RGB
// const triangle = [0.625, 0.34, 0.28, 0.595, 0.155, 0.07];

// CIE XYZ
// const triangle = [1, 0, 0, 1, 0, 0];

// CIE (1931) RGB
// const triangle = [0.7347, 0.2653, 0.2738, 0.7174, 0.1666, 0.0089];

function mapActiveColorProps(props) {
  const getters = {};

  for (let prop of props) {
    getters[prop] = {
      get() {
        const activeColor = this.$store.getters.activeColor;
        return activeColor ? activeColor[prop] : null;
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
    ...mapActions(["addColorDatapoint"]),

    /**
     * Samples a color randomly
     */
    updateUserClassifierSampleRandom() {
      let sample;
      do {
        sample = [Math.random(), Math.random(), Math.random()];
      } while (!inTriangle(sample[0], sample[1], ...triangle));

      this.userClassifierSample = sample;
    },

    /**
     * Samples a color based on the binary user input collected thus far
     * It randomly samples at positions inside & around the decision boundary so users trying to create a "magenta" color model won't see randomly chosen green colors for classifying
     */
    updateUserClassifierSampleBoundary() {
      if (!this.activeColor) {
        console.log(
          "Cannot sample gradient without active color, fallback to random sampling"
        );
        this.updateUserClassifierSampleRandom();
        return;
      }

      const chromaticityBuckets = 6;
      const intensityBuckets = 6;

      const boundary = generateFillerDatapoints(
        this.activeColor.datapoints,
        chromaticityBuckets,
        intensityBuckets,
        null, // Don't care, as we're only requesting the boundary
        triangle,
        true
      );

      if (boundary.length == 0) {
        console.log("No boundary found, fallback to random sampling");
        this.updateUserClassifierSampleRandom();
        return;
      }

      let sample;
      let trials = 1000;
      do {
        if (trials-- == 0) {
          console.log("Running out of trials, fallback to random sampling");
          this.updateUserClassifierSampleRandom();
          return;
        }

        const bucket =
          boundary[
            Math.min(
              Math.floor(Math.random() * boundary.length),
              boundary.length - 1
            )
          ];

        sample = [
          bucket[0] + (Math.random() - 0.5) / chromaticityBuckets,
          bucket[1] + (Math.random() - 0.5) / chromaticityBuckets,
          bucket[2] + (Math.random() - 0.5) / intensityBuckets
        ];
      } while (
        !inTriangle(sample[0], sample[1], ...triangle) ||
        sample[2] < 0 ||
        sample[2] > 1
      );

      this.userClassifierSample = sample;
    },

    async handleUserClassifierResponse(response) {
      let [x, y, z] = this.userClassifierSample;
      let b = response ? 1 : 0;

      await this.$store.dispatch("addColorDatapoint", { x, y, z, b });

      const perceptron = await classifyColor(this.activeColorId, triangle);
      await this.$store.dispatch("setActiveColorProps", { perceptron });

      this.redraw();

      this.updateUserClassifierSampleBoundary();
    },

    async handleCanvasClick(event) {
      const x =
        (event.pageX - this.$refs.canvas.offsetLeft) /
        this.$refs.canvas.offsetWidth;
      const y =
        1 -
        (event.pageY - this.$refs.canvas.offsetTop) /
          this.$refs.canvas.offsetHeight;
      const xyY = [x, y, this.colorY];

      this.userClassifierSample = xyY;
    },

    handleCanvasWheel(event) {
      this.colorY = Math.min(1, Math.max(0, this.colorY + event.deltaY / 1000));
      this.redraw();
    },

    redraw() {
      const canvas = this.$refs.canvas;
      const gl = canvas.getContext("webgl2");

      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.clear(gl.COLOR_BUFFER_BIT);

      // Draw diagram with perceptron classified area highlighted
      {
        gl.useProgram(this.program);
        gl.uniform1f(this.colorYLocation, this.colorY);

        if (this.perceptron) {
          const flatPerceptronWeights = this.flatPerceptronWeights;
          const flatPerceptronIntercepts = this.flatPerceptronIntercepts;

          // console.log("Perceptron weights", flatPerceptronWeights);
          // console.log("Perceptron intercepts", flatPerceptronIntercepts);

          const std140perceptron = new Float32Array(
            (this.perceptron.mean.length +
              this.perceptron.scale.length +
              flatPerceptronWeights.length +
              flatPerceptronIntercepts.length) *
              4
          );
          this.perceptron.mean.forEach((v, i) => (std140perceptron[i * 4] = v));
          this.perceptron.scale.forEach(
            (v, i) =>
              (std140perceptron[(this.perceptron.mean.length + i) * 4] = v)
          );
          flatPerceptronWeights.forEach(
            (v, i) =>
              (std140perceptron[
                (this.perceptron.mean.length +
                  this.perceptron.scale.length +
                  i) *
                  4
              ] = v)
          );
          flatPerceptronIntercepts.forEach(
            (v, i) =>
              (std140perceptron[
                (this.perceptron.mean.length +
                  this.perceptron.scale.length +
                  flatPerceptronWeights.length +
                  i) *
                  4
              ] = v)
          );

          gl.bindBuffer(gl.UNIFORM_BUFFER, this.perceptronBuffer);
          gl.bufferData(gl.UNIFORM_BUFFER, std140perceptron, gl.DYNAMIC_DRAW);
          gl.bindBuffer(gl.UNIFORM_BUFFER, null);
        } else {
          // No perceptron

          const std140perceptron = new Float32Array(507 * 4);

          gl.bindBuffer(gl.UNIFORM_BUFFER, this.perceptronBuffer);
          gl.bufferData(gl.UNIFORM_BUFFER, std140perceptron, gl.DYNAMIC_DRAW);
          gl.bindBuffer(gl.UNIFORM_BUFFER, null);
        }

        gl.uniform1i(
          gl.getUniformLocation(this.program, "flag_use_perceptron"),
          this.perceptron ? 1 : 0
        );

        gl.uniformBlockBinding(
          this.program,
          this.perceptronWeightsBlockIndex,
          1
        );
        gl.bindBufferBase(gl.UNIFORM_BUFFER, 1, this.perceptronBuffer);

        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.indexBuffer);

        gl.bindBuffer(gl.ARRAY_BUFFER, this.vertexBuffer);
        gl.vertexAttribPointer(this.coordLocation, 2, gl.FLOAT, false, 0, 0);
        gl.enableVertexAttribArray(this.coordLocation);

        gl.drawElements(gl.TRIANGLES, 3, gl.UNSIGNED_SHORT, 0);
      }

      // Plot points
      if (this.activeColor) {
        const datapoints = makeTrainingDatapoints(
          this.activeColor.datapoints,
          -1
        ).filter(v => Math.abs(v[2] - this.colorY) < 1 / 32);

        if (datapoints.length > 0) {
          const points = new Float32Array(datapoints.length * 4);
          datapoints.forEach((v, i) => {
            points[i * 4] = v[0];
            points[i * 4 + 1] = v[1];
            points[i * 4 + 2] = v[2];
            points[i * 4 + 3] = v[3];
          });

          gl.useProgram(this.pointProgram);

          gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, null);

          gl.bindBuffer(gl.ARRAY_BUFFER, this.pointVertexBuffer);
          gl.bufferData(gl.ARRAY_BUFFER, points, gl.DYNAMIC_DRAW);
          gl.vertexAttribPointer(
            this.pointProgramCoordLocation,
            4,
            gl.FLOAT,
            false,
            0,
            0
          );
          gl.enableVertexAttribArray(this.pointProgramCoordLocation);

          gl.drawArrays(gl.POINTS, 0, datapoints.length);
        }
      }
    }
  },

  watch: {
    activeColorId: function(newVal, oldVal) {
      this.redraw();
    }
  },

  created: function() {
    this.updateUserClassifierSampleBoundary();
  },

  mounted: function() {
    const canvas = this.$refs.canvas;

    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;

    const gl = canvas.getContext("webgl2");

    const indices = [0, 1, 2];

    this.vertexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(triangle), gl.STATIC_DRAW);
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

    this.pointVertexBuffer = gl.createBuffer();

    const vertexShaderSource = `#version 300 es

      precision mediump float;

      in vec2 coordinates;

      out vec2 xy;

      void main(void) {
        gl_Position = vec4(coordinates * 2.0 - vec2(1.0), 0.0, 1.0);
        xy = coordinates;
      }
    `;

    let weights = 0,
      intercepts = 0;
    function genLayer(prev, prevDim, cur, curDim, activation) {
      return `
        float ${cur}[${curDim}];
        // Intercepts
        ${range(curDim)
          .map(i => `${cur}[${i}] = perceptron.intercepts[${intercepts++}];`)
          .join(" ")}
        // Weights
        ${range(prevDim * curDim)
          .map(
            i =>
              `${cur}[${i % curDim}] += ${prev}[${Math.floor(
                i / curDim
              )}] * perceptron.weights[${weights++}];`
          )
          .join(" ")}
        // Activation
        ${
          activation == "relu"
            ? `${range(curDim)
                .map(i => `${cur}[${i}] = max(0.0, ${cur}[${i}]);`)
                .join(" ")} // ReLU`
            : activation == "tanh"
            ? `${range(curDim)
                .map(i => `${cur}[${i}] = tanh(${cur}[${i}]);`)
                .join(" ")} // tanh`
            : `${range(curDim)
                .map(i => `${cur}[${i}] = 1.0 / (1.0 + exp(-${cur}[${i}]));`)
                .join(" ")} // Logistic`
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

      uniform bool flag_use_perceptron;

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

        if (!flag_use_perceptron || c > 0.5) {
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

    console.log("Fragment shader source", fragmentShaderSource);

    const pointVertexShaderSource = `#version 300 es

      precision mediump float;

      in vec4 xyYb;

      out float b;
      out float radius;

      void main(void) {
        vec2 coordinates = xyYb.xy;
        gl_Position = vec4(coordinates * 2.0 - vec2(1.0), 0.0, 1.0);
        if (xyYb[3] == 1.0) {
          radius = 10.0;
        } else if (xyYb[3] == 0.0) {
          radius = 4.0;
        } else if (xyYb[3] == -1.0) {
          radius = 2.0;
        }
        gl_PointSize = 2.0 * radius;
      }
    `;

    const pointFragmentShaderSource = `#version 300 es

      precision mediump float;

      in float b;
      in float radius;

      out vec4 fragmentColor;

      void main(void) {
        float dist = length(gl_PointCoord - vec2(0.5, 0.5)) * 2.0 * radius;
        if (abs(dist - (radius - 2.0)) > 2.0) {
          discard;
        }

        // fragmentColor = vec4(1.0, 1.0, 1.0, 1);
        fragmentColor = vec4(0, 0, 0, 0);
      }
    `;

    const vertexShader = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vertexShader, vertexShaderSource);
    gl.compileShader(vertexShader);

    console.log("Vertex shader", gl.getShaderInfoLog(vertexShader));

    const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fragmentShader, fragmentShaderSource);
    gl.compileShader(fragmentShader);

    console.log("Fragment shader", gl.getShaderInfoLog(fragmentShader));

    const pointVertexShader = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(pointVertexShader, pointVertexShaderSource);
    gl.compileShader(pointVertexShader);

    console.log("Point vertex shader", gl.getShaderInfoLog(pointVertexShader));

    const pointFragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(pointFragmentShader, pointFragmentShaderSource);
    gl.compileShader(pointFragmentShader);

    console.log(
      "Point fragment shader",
      gl.getShaderInfoLog(pointFragmentShader)
    );

    // Diagram program

    this.program = gl.createProgram();
    gl.attachShader(this.program, vertexShader);
    gl.attachShader(this.program, fragmentShader);
    gl.linkProgram(this.program);

    this.coordLocation = gl.getAttribLocation(this.program, "coordinates");
    this.colorYLocation = gl.getUniformLocation(this.program, "Y");
    this.perceptronWeightsBlockIndex = gl.getUniformBlockIndex(
      this.program,
      "PerceptronBlock"
    );

    // Point program

    this.pointProgram = gl.createProgram();
    gl.attachShader(this.pointProgram, pointVertexShader);
    gl.attachShader(this.pointProgram, pointFragmentShader);
    gl.linkProgram(this.pointProgram);

    this.pointProgramCoordLocation = gl.getAttribLocation(
      this.pointProgram,
      "xyYb"
    );

    this.redraw();
  }
};
</script>

<style lang="scss">
@import "../global.scss";

.color-picker {
  display: grid;
  grid-template-areas:
    "info classifier"
    "canvas classifier";
  grid-template-rows: 3.5em 500px;
  grid-template-columns: 500px 1fr;
  flex-direction: column;
  background-color: $color-gray-tint;

  .color-picker-info {
    grid-area: info;
    padding: 1em;
    line-height: 1.5;
  }

  .color-picker-canvas {
    grid-area: canvas;
    border-top: 1px solid $color-border;
    background-color: hsl(0, 0, 25%);
    width: 100%;
    height: 100%;
  }

  .color-picker-classifier {
    grid-area: classifier;
    border-left: 1px solid $color-border;

    display: flex;
    flex-direction: column;
    text-align: center;
    padding: 1em;
    justify-content: space-between;

    .color-picker-classifier-preview {
      width: 64px;
      height: 64px;
      margin: 0 auto;
    }
  }
}
</style>