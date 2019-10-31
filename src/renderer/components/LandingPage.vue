<template>
  <color-search-quad-canvas id="page-landing"></color-search-quad-canvas>
</template>

<script>
import ColorSearchQuadCanvasVue from "./ColorSearchQuadCanvas/ColorSearchQuadCanvas";

export default {
  components: {
    "color-search-quad-canvas": ColorSearchQuadCanvasVue
  }
};
</script>

<style>
#page-landing {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
