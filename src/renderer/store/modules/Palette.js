import Vue from 'vue';


const state = {
    activeColorId: null,
    colors: []
}

function colorByColorId(state, colorId) {
    for (let color of state.colors) {
        if (color.id == colorId) {
            return color;
        }
    }
    return null;
};

const getters = {
    colors: function (state) {
        return state.colors;
    },

    activeColorId: function (state) {
        return state.activeColorId;
    },

    activeColor: function (state) {
        return colorByColorId(state, state.activeColorId);
    },

    colorByColorId: function (state) {
        return (colorId) => {
            return colorByColorId(state, colorId);
        }
    }
}

const mutations = {
    SET_ACTIVE_COLOR(state, { colorId }) {
        state.activeColorId = colorId;

        if (!state.colors.some(c => c.id == colorId)) {
            state.colors.push({
                id: colorId,
                name: "unnamed",
                datapoints: []
            });
        }
    },

    SET_ACTIVE_COLOR_PROPS(state, { props }) {
        const activeColor = colorByColorId(state, state.activeColorId);
        if (!activeColor) return;
        
        for (let key in props) {
            Vue.set(activeColor, key, props[key]);
        }
    },

    DELETE_COLOR(state, { colorId }) {
        if (state.activeColorId == colorId) {
            // Deselect active color if it's being deleted
            state.activeColorId = null;
        }

        state.colors = state.colors.filter(c => c.id != colorId);
    },

    ADD_COLOR_DATAPOINT(state, { x, y, z, b }) {
        const activeColor = colorByColorId(state, state.activeColorId);
        if (!activeColor) return;

        activeColor.datapoints.push([x, y, z, b]);
    }
}

const actions = {
    addColorDatapoint({ state, commit }, { x, y, z, b }) {
        commit("ADD_COLOR_DATAPOINT", { x, y, z, b });
    },

    setActiveColor({ state, commit }, colorId) {
        commit("SET_ACTIVE_COLOR", { colorId });
    },

    deleteColor({ state, commit }, colorId) {
        commit("DELETE_COLOR", { colorId });
    },

    setActiveColorProps({ state, commit }, props) {
        commit("SET_ACTIVE_COLOR_PROPS", { props });
    }
}

export default {
    state,
    getters,
    mutations,
    actions
}
