<template>
  <canvas class="color-canvas" ref="canvas"></canvas>
</template>

<script>
export default {
  props: ["color"],

  data: function() {
    return {
      program: null,
      indexBuffer: null,
      colorLocation: null
    };
  },

  methods: {
    redrawColor(color) {
      const canvas = this.$refs.canvas;
      const gl = canvas.getContext("experimental-webgl");

      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(this.program);
      gl.uniform3fv(this.colorLocation, color);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.indexBuffer);
      gl.drawElements(gl.TRIANGLES, 3, gl.UNSIGNED_SHORT, 0);
    }
  },

  watch: {
    color: function(newVal, oldVal) {
      this.redrawColor(newVal);
    }
  },

  mounted: function() {
    const canvas = this.$refs.canvas;
    const gl = canvas.getContext("experimental-webgl");

    const vertices = [2, 0, 0, 2, 0, 0];

    const indices = [0, 1, 2];

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

    const vertexShaderSource = `
      precision mediump float;

      attribute vec2 coordinates;

      void main(void) {
        gl_Position = vec4(coordinates * 2.0 - vec2(1.0), 0.0, 1.0);
      }
    `;

    const fragmentShaderSource = `
      precision mediump float;
      
      #define GAMMA_CORRECTION 1.0/2.2

      uniform vec3 color_xyY;

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

    this.program = gl.createProgram();
    gl.attachShader(this.program, vertexShader);
    gl.attachShader(this.program, fragmentShader);
    gl.linkProgram(this.program);

    const coordLocation = gl.getAttribLocation(this.program, "coordinates");
    this.colorLocation = gl.getUniformLocation(this.program, "color_xyY");

    gl.useProgram(this.program);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.indexBuffer);
    {
      gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
      gl.vertexAttribPointer(coordLocation, 2, gl.FLOAT, false, 0, 0);
      gl.enableVertexAttribArray(coordLocation);
    }

    this.redrawColor(this.$props.color);
  }
};
</script>

<style>
.color-canvas {
  display: block;
}
</style>