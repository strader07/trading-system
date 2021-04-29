import _ from 'lodash';

export const DRAWER_WIDTH = 240;

const SET_DRAWER_OPEN = '@Redux/Layout/SET_DRAWER_OPEN';

const DEFAULT_STATE = {
  drawerOpen: false,
};

export default function LayoutReducer(state = DEFAULT_STATE, action) {
  if (action.type === SET_DRAWER_OPEN) {
    return _.assign({}, state, action.payload);
  } else {
    return state;
  }
}

export function setDrawerOpen(drawerOpen) {
  return {
    type: SET_DRAWER_OPEN,
    payload: {
      drawerOpen,
    },
  };
}
