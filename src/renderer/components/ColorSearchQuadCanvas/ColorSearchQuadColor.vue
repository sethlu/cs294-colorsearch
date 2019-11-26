<template>
  <div class="color-search-quad-color">
    <!-- <color-canvas :color="color.xyY" v-if="color"/> -->
    <div class="color-search-quad-color-name" v-if="color">{{ color.name }}</div>
  </div>
</template>

<script>
import ColorCanvasVue from '../ColorSearchColorPicker/ColorCanvas.vue';

export default {
  props: ["color"],
  components: {
    'color-canvas': ColorCanvasVue
  }
};
</script>

<style lang="scss">
@import "../global.scss";

.color-search-quad-color {
  overflow: hidden;
  position: relative;
  background-color: #FFF;
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
  }
}
</style>
