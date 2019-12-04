<template>
  <div class="color-search-quad-canvas">
    <div class="color-search-quad-canvas-bar">
      <div class="directory">{{ directory ? directory : "No Directory Selected" }}</div>
      <button @click="handleSelectDirectory()">Select Directory</button>
      <button @click="handleSearch()" :disabled="!directory">Search</button>
    </div>
    <div class="color-search-quad-canvas-palette">
      <div class="color" v-for="color in colors" @click="handlePickColor(color.id)">
        <div class="color-name">{{ color.name }}</div>
        <drag class="color-blob" :transfer-data="color">
          <color-search-quad-color :color="color"/>
        </drag>
        <div @click.stop="handleDeleteColor(color.id)">&nbsp;x&nbsp;</div>
      </div>
      <div class="color" @click="handlePickNewColor()">
        <div class="color-name">+ New Color</div>
      </div>
    </div>
    <div class="color-search-quad-canvas-area">
      <drop @drop="handleColorDrop(i, ...arguments)" v-for="cell, i in grid">
        <color-search-quad-color :color="cell && cell.colorId ? colorByColorId(cell.colorId) : null"/>
      </drop>
    </div>
    <div class="color-search-quad-canvas-result">
      <div v-if="searchStatus">
        Searching...
      </div>
      <div class="color-search-quad-canvas-result-wrapper" v-else-if="searchResultImages.length > 0">
        <div class="result-title">Search results</div>
        <div class="result-entry" v-for="image in searchResultImages" :key="image">
          <img :src="'file://' + directory + '/' + image">
        </div>
      </div>
      <div v-else>
        No search results.
      </div>
    </div>
  </div>
</template>

<script>
import { ipcRenderer } from 'electron';
import Vue from 'vue';
import { mapGetters, mapActions } from 'vuex';
import { Drag, Drop } from 'vue-drag-drop';
import uuidv4 from 'uuid/v4';

import { query } from '../../../lib/query';

import ColorSearchQuadColorVue from './ColorSearchQuadColor.vue';

function flat(a) {
  const flattened = [];
  function flatHelper(a) {
    if (!Array.isArray(a)) return flattened.push(a);
    a.forEach(flatHelper);
  }
  flatHelper(a);
  return flattened;
}

export default {
  data: function () {
    return {
      grid: [
        null, null, null, null,
        null, null, null, null,
        null, null, null, null,
        null, null, null, null
      ],
      directory: "",
      searchResultImages: [],
      searchStatus: false,
    }
  },

  computed: {
    ...mapGetters([
      'colors',
      'colorByColorId'
    ])
  },

  components: {
    'drag': Drag,
    'drop': Drop,
    'color-search-quad-color': ColorSearchQuadColorVue
  },

  methods: {
    ...mapActions([
      'setActiveColor',
      'deleteColor'
    ]),

    handleColorDrop: function (i, color) {
      Vue.set(this.grid, i, {
        colorId: color.id
      });
    },

    handlePickColor: function (colorId) {
      this.setActiveColor(colorId);
      ipcRenderer.send('focus-color-picker-window');
      console.log(this.colorByColorId);
    },

    handlePickNewColor: function () {
      this.setActiveColor(uuidv4());
      ipcRenderer.send('focus-color-picker-window')
    },

    handleDeleteColor: function (colorId) {
      this.deleteColor(colorId);
    },

    handleSearch: async function () {
      this.searchStatus = true;
      const images = await query(this.directory, flat(this.grid).map(i => i ? i.colorId : null));
      console.log(images);
      this.searchResultImages = images;
      this.searchStatus = false;
    },

    handleSelectDirectory: async function () {
      this.directory = await new Promise((resolve) => {
        ipcRenderer.send('choose-directory');
        ipcRenderer.on('choose-directory', (event, dir) => {
          resolve(dir);
        });
      });
    },
  }
};
</script>

<style lang="scss">
@import "../global.scss";

.color-search-quad-canvas {
  box-sizing: border-box;
  display: grid;
  grid-template-areas:
    "bar bar result"
    "palette canvas result";
  grid-template-columns: 12em 1fr 1fr;
  grid-template-rows: 3em 1fr;
  border: 1px solid $color-border;

  .color-search-quad-canvas-bar {
    grid-area: bar;
    display: flex;
    background-color: $color-gray-tint;
    border-bottom: 1px solid $color-border;

    button {
      flex: none;
      -webkit-appearance: none;
      border: none;
      border-left: 1px solid $color-border;
      background: transparent;
      font-size: 1em;
      padding: 0 1em;
      transition: background-color ease 0.1s, color ease 0.1s;

      &:not(:disabled):hover {
        background-color: $color-accent-tint;
        color: #FFF;
      }

      &:disabled {
        color: $color-border;
      }
    }

    .directory {
      flex: 1 1 auto;
      line-height: 3em;
      padding: 0 1em;
      overflow-x: auto;
      white-space: nowrap;
    }    
  }

  .color-search-quad-canvas-area {
    grid-area: canvas;
    display: grid;
    grid-template-columns: repeat(4, 100px);
    align-content: center;
    justify-content: center;
    grid-gap: 0.25em;
    padding: 1em;

    > * {
      width: 100%;
      height: 100%;

      .color-search-quad-color {
        border: 1px dotted $color-border;
      }
    }

    > *::before {
      // Some tricks to get a square aspect ratio
      content: "";
      display: block;
      width: 0;
      height: 0;
      padding-bottom: 100%;
      float: right;
    }
  }

  .color-search-quad-canvas-palette {
    grid-area: palette;
    border-right: 1px solid $color-border;
    background-color: $color-gray-tint;
    overflow-y: auto;
    
    .color {
      height: 3em;
      display: flex;
      align-items: center;

      border-top: 1px solid $color-border;
      &:first-child {
        border-top: none;
      }

      .color-name {
        flex: 1;
        margin-left: 1em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .color-blob {
        flex: none;
        box-sizing: border-box;
        width: 2.5em;
        height: 2.5em;
        border: 1px solid $color-border;
        margin: 0.25em;
      }
    }
  }
  
  .color-search-quad-canvas-result {
    grid-area: result;
    border-left: 1px solid $color-border;
    padding: 1em;
    overflow-y: auto;

    .color-search-quad-canvas-result-wrapper {
      max-width: 30em;
      margin: 0 auto;
    }

    .result-title {

    }

    .result-entry {
      margin: 1em 0 0 0;
    }

    img {
      display: block;
      width: 100%;
    }
  }
}
</style>
