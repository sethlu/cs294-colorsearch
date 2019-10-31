<template>
  <color-search-color-picker id="page-color-picker" />
</template>

<script>
import ColorSearchColorPickerVue from "./ColorSearchColorPicker/ColorSearchColorPicker.vue";

export default {
  components: {
    "color-search-color-picker": ColorSearchColorPickerVue
  }
};
</script>

<style>
#page-color-picker {
  width: 100%;
  height: 100%;
}
</style>