<template>
  <div class="color-search-quad-canvas">
    <div class="color-search-quad-canvas-palette">
      <div class="color" v-for="color in colors" @click="handlePickColor(color.id)">
        <div class="color-name">{{ color.name }}</div>
        <drag class="color-blob" :transfer-data="color">
          <color-search-quad-color :color="color"/>
        </drag>
        <div @click.stop="handleDeleteColor(color.id)">x</div>
      </div>
      <div class="color" @click="handlePickNewColor()">
        <div class="color-name">new</div>
      </div>
    </div>
    <div class="color-search-quad-canvas-area">
      <drop @drop="handleColorDrop(i, ...arguments)" v-for="cell, i in grid">
        <color-search-quad-color :color="cell && cell.colorId ? colorByColorId(cell.colorId) : null"/>
      </drop>
    </div>
    <div class="color-search-quad-canvas-result">
      <button @click="handleSelectDirectory()">Choose directory</button>
      <div>{{ directory }}</div>
      <button @click="handleSearch()">Search</button>
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
      directory: "No Directory Selected",
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
      await query(this.directory, flat(this.grid).map(i => i ? i.colorId : null));
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
  grid-template-columns: 150px 1fr 1fr;
  border: 1px solid $color-border;

  .color-search-quad-canvas-area {
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
    display: flex;
    flex-direction: column;
    justify-content: center;
    border-top-left-radius: 1.5em;
    border-bottom-left-radius: 1.5em;

    .color {
      height: 3em;
      background-color: $color-gray-tint;
      display: flex;
      align-items: center;

      border-right: 1px solid $color-border;
      border-top: 1px solid $color-border;
      &:first-child {
        border-top-right-radius: 6px;
      }
      &:last-child {
        border-bottom: 1px solid $color-border;
        border-bottom-right-radius: 6px;
      }

      .color-name {
        flex: 1;
        margin-left: 1em;
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
    border-left: 1px solid $color-border;
  }
}
</style>
