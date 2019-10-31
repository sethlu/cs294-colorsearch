<template>
  <div class="color-picker" v-if="activeColorId">
    <div class="color-picker-preview">
      <color-canvas :color="xyY" width="32" height="32" />
    </div>
    <div class="color-picker-props">
      Name <input v-model="name" />
    </div>
    <canvas
      ref="canvas"
      class="color-picker-canvas"
      width="400"
      height="400"
      @click="handleCanvasClick"
    ></canvas>
  </div>
</template>

<script>
import { mapGetters } from "vuex";

import ColorCanvasVue from "./ColorCanvas.vue";

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
    return {};
  },

  computed: {
    ...mapGetters(["activeColorId", "activeColor", "colors"]),
    ...mapActiveColorProps(["name", "xyY"])
  },

  methods: {
    handleCanvasClick(event) {
      const x =
        (event.pageX - this.$refs.canvas.offsetLeft) /
        this.$refs.canvas.offsetWidth;
      const y =
        1 -
        (event.pageY - this.$refs.canvas.offsetTop) /
          this.$refs.canvas.offsetHeight;
      this.xyY = [x, y, 1];
    }
  },

  mounted: function() {
    const canvas = this.$refs.canvas;

    canvas.style.width = `${canvas.width}px`;
    canvas.style.height = `${canvas.height}px`;

    canvas.width = canvas.width * window.devicePixelRatio;
    canvas.height = canvas.height * window.devicePixelRatio;

    const gl = canvas.getContext("experimental-webgl");

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

    const indexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
    gl.bufferData(
      gl.ELEMENT_ARRAY_BUFFER,
      new Uint16Array(indices),
      gl.STATIC_DRAW
    );
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, null);

    const vertexShaderSource = `
      precision mediump float;

      attribute vec2 coordinates;

      varying vec2 xy;

      void main(void) {
        gl_Position = vec4(coordinates * 2.0 - vec2(1.0), 0.0, 1.0);
        xy = coordinates;
      }
    `;

    const fragmentShaderSource = `
      precision mediump float;
      
      #define GAMMA_CORRECTION 1.0/2.2
      #define Y 1.0

      varying vec2 xy;

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

        if (sRGB.x < 0.0 || sRGB.y < 0.0 || sRGB.z < 0.0) {
          gl_FragColor = vec4(0, 0, 0, 1);
        } else {
          gl_FragColor = vec4(gammaCorrected, 1);
        }
      }
    `;

    const vertexShader = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vertexShader, vertexShaderSource);
    gl.compileShader(vertexShader);

    console.log(gl.getShaderInfoLog(vertexShader));

    const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fragmentShader, fragmentShaderSource);
    gl.compileShader(fragmentShader);

    console.log(gl.getShaderInfoLog(fragmentShader));

    const program = gl.createProgram();
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);

    const coordLocation = gl.getAttribLocation(program, "coordinates");

    gl.useProgram(program);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
    {
      gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
      gl.vertexAttribPointer(coordLocation, 2, gl.FLOAT, false, 0, 0);
      gl.enableVertexAttribArray(coordLocation);
    }

    // Render

    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(program);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
    gl.drawElements(gl.TRIANGLES, indices.length, gl.UNSIGNED_SHORT, 0);
  }
};
</script>

<style lang="scss">
@import "../global.scss";

.color-picker {
  display: grid;
  grid-template-areas: "preview info" "canvas canvas";
  grid-template-rows: 1fr 400px;
  grid-template-columns: 64px 1fr;
  flex-direction: column;
  background-color: $color-gray-tint;

  .color-picker-preview {
    grid-area: "preview";
    padding: 8px;

    canvas {
      box-sizing: border-box;
      width: 48px;
      height: 48px;
      border: 1px solid $color-border;
    }
  }

  .color-picker-props {
    grid-area: "info";
    padding: 8px 8px 8px 0;
  }

  .color-picker-canvas {
    grid-area: "canvas";
    border-top: 1px solid $color-border;
    background-color: white;
  }
}
</style>