<template>
  <div class="color-search-quad-color">
    <color-canvas :color="previewColor" v-if="color" />
    <div class="color-search-quad-color-name" v-if="color">
      <span>{{ color.name.split(" ").map(w => w[0]).join("") }}</span>
    </div>
  </div>
</template>

<script>
import ColorCanvasVue from "../ColorSearchColorPicker/ColorCanvas.vue";

export default {
  props: ["color"],
  components: {
    "color-canvas": ColorCanvasVue
  },
  computed: {
    previewColor() {
      const color = this.color;
      if (!color) return [0, 0, 0];
      const datapoints = color.datapoints;
      if (!datapoints) return [0, 0, 0];
      let acc_x = 0,
        acc_y = 0,
        acc_z = 0,
        acc_b = 0;
      for (let [x, y, z, b] of datapoints) {
        if (b == 1) {
          acc_x += x;
          acc_y += y;
          acc_z += z;
          acc_b += 1;
        }
      }
      return [acc_x / acc_b, acc_y / acc_b, acc_z / acc_b];
    }
  }
};
</script>

<style lang="scss">
@import "../global.scss";

.color-search-quad-color {
  overflow: hidden;
  position: relative;
  background-color: #fff;
  width: 100%;
  height: 100%;

  canvas {
    width: 100%;
    height: 100%;
  }

  .color-search-quad-color-name {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    display: grid;
    justify-content: center;
    align-content: center;
    color: rgba(0, 0, 0, 0.8);
    font-weight: 700;
  }
}
</style>
