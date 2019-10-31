<template>
  <div class="color-search-quad-color">
    <color-canvas :color="color.xyY" v-if="color"/>
    <!-- {{ color.name }} --> 
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
  background-color: #FFF;
  width: 100%;
  height: 100%;

  canvas {
    width: 100%;
    height: 100%;
  }
}
</style>
